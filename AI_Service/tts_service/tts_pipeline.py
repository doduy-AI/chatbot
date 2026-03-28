"""
Tiền xử lý text + ghép sóng sau inference nhiều chunk (giảm vỡ giọng / click biên đoạn).
"""
from __future__ import annotations

import re
from typing import Generator, List

import numpy as np

try:
    from vinorm import TTSnorm
    _HAS_VINORM = True
except ImportError:
    _HAS_VINORM = False

try:
    from underthesea import sent_tokenize as _vn_sent_tokenize
    _HAS_UNDERTHESEA = True
except ImportError:
    _HAS_UNDERTHESEA = False

SAMPLE_RATE = 24000
DEFAULT_CROSSFADE_MS = 35.0
DEFAULT_STREAM_BLOCK_MS = 120.0
DEFAULT_FADE_IN_MS = 20.0
DEFAULT_SILENCE_MS = 350.0  # khoảng im giữa các chunk → chống hụt hơi


def normalize_vietnamese(text: str) -> str:
    """Chuẩn hóa tiếng Việt: số → chữ, viết tắt, ký tự đặc biệt..."""
    if _HAS_VINORM:
        try:
            text = TTSnorm(text, unknown=False, lower=False, rule=True)
        except Exception:
            pass  # fallback về text gốc nếu TTSnorm lỗi
    return text


def clean_text(text: str) -> str:
    """Chuẩn hóa khoảng trắng; giữ dấu câu và chữ Unicode (Việt/Anh)."""
    if not text or not text.strip():
        return ""
    text = text.replace("\u00a0", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_text_smartly(
    text: str,
    max_words: int = 30,
    max_chars: int = 250,
) -> List[str]:
    """
    Tách theo ranh giới câu trước; nếu câu quá dài thì tách thêm theo dấu phẩy hoặc theo từ.
    Giới hạn độ dài giúp tránh đoạn một lần inference quá dài.
    """
    text = normalize_vietnamese(text)
    text = clean_text(text)
    if not text:
        return []

    if _HAS_UNDERTHESEA:
        sentences = _vn_sent_tokenize(text)
    else:
        parts = re.split(r"(?<=[.!?…])\s+|\n+", text)
        sentences = [p.strip() for p in parts if p.strip()]
    if not sentences:
        return [text]

    chunks: List[str] = []
    buf: List[str] = []

    def flush_buf() -> None:
        nonlocal buf
        if buf:
            chunks.append(" ".join(buf).strip())
            buf = []

    for sent in sentences:
        nw = len(sent.split())
        slen = len(sent)

        if slen > max_chars or nw > max_words:
            flush_buf()
            subs = re.split(r"(?<=[,;])\s+", sent)
            if len(subs) > 1:
                tmp: List[str] = []
                for s in subs:
                    s = s.strip()
                    if not s:
                        continue
                    if len(s) <= max_chars and len(s.split()) <= max_words:
                        tmp.append(s)
                    else:
                        chunks.extend(_split_oversized_segment(s, max_words, max_chars))
                _pack_subchunks(tmp, chunks, max_words, max_chars)
            else:
                chunks.extend(_split_oversized_segment(sent, max_words, max_chars))
            continue

        trial = (" ".join(buf + [sent])).strip() if buf else sent
        if len(trial) <= max_chars and len(trial.split()) <= max_words:
            buf.append(sent)
        else:
            flush_buf()
            buf.append(sent)

    flush_buf()
    return [c for c in chunks if c.strip()]


def _split_oversized_segment(segment: str, max_words: int, max_chars: int) -> List[str]:
    words = segment.split()
    out: List[str] = []
    cur: List[str] = []
    for w in words:
        trial = (" ".join(cur + [w])).strip()
        if len(trial) > max_chars or len(cur) + 1 > max_words:
            if cur:
                out.append(" ".join(cur))
                cur = [w]
            else:
                out.append(w)
                cur = []
        else:
            cur.append(w)
    if cur:
        out.append(" ".join(cur))
    return out


def _pack_subchunks(
    subs: List[str], chunks: List[str], max_words: int, max_chars: int
) -> None:
    buf: List[str] = []
    for s in subs:
        if not buf:
            buf.append(s)
            continue
        trial = " ".join(buf + [s])
        if len(trial) <= max_chars and len(trial.split()) <= max_words:
            buf.append(s)
        else:
            chunks.append(" ".join(buf).strip())
            buf = [s]
    if buf:
        chunks.append(" ".join(buf).strip())


def merge_short_text_chunks(chunks: List[str], min_words: int = 15) -> List[str]:
    """
    Gộp các chunk liên tiếp cho đến khi đủ min_words (từ).
    Dùng với viXTTS: model card cảnh báo câu tiếng Việt < ~10 từ dễ lỗi.
    Mặc định 15 từ (theo kinh nghiệm testmodel1.py).
    """
    if min_words <= 1 or not chunks:
        return chunks
    merged: List[str] = []
    i = 0
    while i < len(chunks):
        cur = chunks[i]
        j = i + 1
        while j < len(chunks) and len(cur.split()) < min_words:
            cur = (cur + " " + chunks[j]).strip()
            j += 1
        merged.append(cur)
        i = j
    if len(merged) >= 2 and len(merged[-1].split()) < min_words:
        merged[-2] = (merged[-2] + " " + merged[-1]).strip()
        merged.pop()
    return merged


def concat_wav_chunks(
    chunks: List[np.ndarray],
    sample_rate: int = SAMPLE_RATE,
    crossfade_ms: float = DEFAULT_CROSSFADE_MS,
    silence_ms: float = DEFAULT_SILENCE_MS,
) -> np.ndarray:
    """
    Nối các đoạn float32 mono:
    - crossfade tuyến tính ở biên để giảm click / đổi màu giọng
    - chèn khoảng im (silence_ms) giữa các chunk → chống hụt hơi
    """
    if not chunks:
        return np.array([], dtype=np.float32)
    if len(chunks) == 1:
        return np.asarray(chunks[0], dtype=np.float32).reshape(-1)

    fade_len = int(sample_rate * crossfade_ms / 1000.0)
    fade_len = max(8, fade_len)
    silence_len = int(sample_rate * silence_ms / 1000.0)
    silence = np.zeros(silence_len, dtype=np.float32)

    out = np.asarray(chunks[0], dtype=np.float32).reshape(-1)
    for nxt in chunks[1:]:
        nxt = np.asarray(nxt, dtype=np.float32).reshape(-1)
        # Fade-out cuối chunk trước
        fl_out = min(fade_len, len(out) // 2)
        if fl_out > 0:
            out[-fl_out:] *= np.linspace(1.0, 0.0, fl_out, dtype=np.float32)
        # Fade-in đầu chunk sau
        fl_in = min(fade_len, len(nxt) // 2)
        if fl_in > 0:
            nxt[:fl_in] *= np.linspace(0.0, 1.0, fl_in, dtype=np.float32)
        # Chèn khoảng im giữa hai chunk
        out = np.concatenate([out, silence, nxt])
    return out


def apply_fade_in(wav: np.ndarray, sample_rate: int, fade_ms: float) -> np.ndarray:
    wav = np.asarray(wav, dtype=np.float32).reshape(-1)
    fl = int(sample_rate * fade_ms / 1000.0)
    if fl <= 0 or len(wav) <= fl:
        return wav
    fade = np.linspace(0.0, 1.0, fl, dtype=np.float32)
    out = wav.copy()
    out[:fl] *= fade
    return out


def wav_to_pcm_stream(
    wav: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
    block_ms: float = DEFAULT_STREAM_BLOCK_MS,
    fade_in_ms: float = DEFAULT_FADE_IN_MS,
) -> Generator[bytes, None, None]:
    """Chuyển wav float [-1,1] thành PCM16; chia nhỏ byte để stream (queue HTTP)."""
    wav = apply_fade_in(wav, sample_rate, fade_in_ms)
    pcm = (np.clip(wav, -1.0, 1.0) * 32767.0).astype(np.int16)
    block = max(1, int(sample_rate * block_ms / 1000.0))
    for i in range(0, len(pcm), block):
        yield pcm[i : i + block].tobytes()
