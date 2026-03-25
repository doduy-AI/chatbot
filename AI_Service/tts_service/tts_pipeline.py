"""
Tiền xử lý text + ghép sóng sau inference nhiều chunk (giảm vỡ giọng / click biên đoạn).
"""
from __future__ import annotations

import re
from typing import Generator, List

import numpy as np

SAMPLE_RATE = 24000
DEFAULT_CROSSFADE_MS = 35.0
DEFAULT_STREAM_BLOCK_MS = 120.0
DEFAULT_FADE_IN_MS = 20.0


def clean_text(text: str) -> str:
    """Chuẩn hóa khoảng trắng; giữ dấu câu và chữ Unicode (Việt/Anh)."""
    if not text or not text.strip():
        return ""
    text = text.replace("\u00a0", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_text_smartly(
    text: str,
    max_words: int = 28,
    max_chars: int = 220,
) -> List[str]:
    """
    Tách theo ranh giới câu trước; nếu câu quá dài thì tách thêm theo dấu phẩy hoặc theo từ.
    Giới hạn độ dài giúp tránh đoạn một lần inference quá dài.
    """
    text = clean_text(text)
    if not text:
        return []

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


def concat_wav_chunks(
    chunks: List[np.ndarray],
    sample_rate: int = SAMPLE_RATE,
    crossfade_ms: float = DEFAULT_CROSSFADE_MS,
) -> np.ndarray:
    """Nối các đoạn float32 mono; crossfade tuyến tính ở biên để giảm click / đổi màu giọng nhẹ."""
    if not chunks:
        return np.array([], dtype=np.float32)
    if len(chunks) == 1:
        return np.asarray(chunks[0], dtype=np.float32).reshape(-1)

    fade_len = int(sample_rate * crossfade_ms / 1000.0)
    fade_len = max(8, fade_len)

    out = np.asarray(chunks[0], dtype=np.float32).reshape(-1)
    for nxt in chunks[1:]:
        nxt = np.asarray(nxt, dtype=np.float32).reshape(-1)
        if len(out) < fade_len or len(nxt) < fade_len:
            out = np.concatenate([out, nxt])
            continue
        fl = min(fade_len, len(out) // 2, len(nxt) // 2)
        t = np.linspace(0.0, 1.0, fl, dtype=np.float32)
        a = out[-fl:]
        b = nxt[:fl]
        blended = a * (1.0 - t) + b * t
        out = np.concatenate([out[:-fl], blended, nxt[fl:]])
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
