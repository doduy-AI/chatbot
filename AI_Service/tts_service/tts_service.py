from omnivoice.models.omnivoice import OmniVoice
import argparse
import logging
import re
import torch
from typing import Generator
import numpy as np
import time
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
from input.voice_profiles import VOICE_PROFILE
import argparse

MODEL_PATH = "./models"
OUTPUT_PATH = "./output/audio.wav"
device = "cuda" if torch.cuda.is_available() else "cpu"

logging.info(f"[TTS] Đang khởi tạo BytehomeTTS trên {device}...")
OMNIVOICE_MODEL = OmniVoice.from_pretrained(
    MODEL_PATH,
    device_map=device,
    dtype=torch.float16 if device == "cuda" else torch.float32
)
logging.info("[TTS] Model đã sẵn sàng.")


def split_sentences(text: str, max_words: int = 30, min_words: int = 5) -> list[str]:
    """
    Cắt text thành các câu theo dấu câu.
    - Split theo dấu câu kết thúc VÀ dấu phẩy/chấm phẩy nếu câu quá dài
    - Merge câu quá ngắn vào câu liền trước (không phải câu sau)
    """
    # Bước 1: Split theo dấu kết câu trước
    raw = re.split(r'(?<=[.!?…])\s+|\n+', text.strip())
    raw = [s.strip() for s in raw if s.strip()]

    # Bước 2: Với câu quá dài, split thêm theo dấu , ; :
    sub_chunks = []
    for sentence in raw:
        if len(sentence.split()) > max_words:
            parts = re.split(r'(?<=[,;:])\s+', sentence)
            sub_chunks.extend([p.strip() for p in parts if p.strip()])
        else:
            sub_chunks.append(sentence)

    # Bước 3: Merge câu quá ngắn vào câu TRƯỚC (không phải sau)
    merged = []
    for chunk in sub_chunks:
        if merged and len(chunk.split()) < min_words:
            merged[-1] += " " + chunk  # gắn vào câu trước
        else:
            merged.append(chunk)

    return merged


def wav_numpy_to_pcm_bytes(wav: np.ndarray, sample_rate=24000, fade_ms=20):
    wav = np.array(wav, dtype=np.float32)
    
    # Số lượng mẫu cần để fade
    fade_len = int(sample_rate * fade_ms / 1000)
    
    if len(wav) > 2 * fade_len:
        # Fade In: Tránh tiếng lẹt xẹt lúc bắt đầu chunk
        fade_in = np.linspace(0, 1, fade_len, dtype=np.float32)
        wav[:fade_len] *= fade_in
        
        # Fade Out: Cực kỳ quan trọng để nối chunk mượt mà
        fade_out = np.linspace(1, 0, fade_len, dtype=np.float32)
        wav[-fade_len:] *= fade_out

    # Ép kiểu sang Int16 để giảm dung lượng stream và đúng chuẩn PCM
    return (wav * 32767.0).astype(np.int16).tobytes()


def generate_tts_stream(text: str, voice: str) -> Generator[bytes, None, None]:
    """
    Cắt text → inference từng chunk → yield từng đoạn mp3 bytes.
    Dùng cho streaming.
    """
    profile = VOICE_PROFILE.get(voice)
    if profile is None:
        raise ValueError(f"Giọng '{voice}' không tồn tại. Có sẵn: {list(VOICE_PROFILE)}")

    chunks = split_sentences(text)
    logging.info(f"[TTS] Tổng {len(chunks)} chunk: {chunks}")

    with torch.inference_mode():
        first_chunk = True
        for i, chunk in enumerate(chunks):
            t0 = time.time()
            audios = OMNIVOICE_MODEL.generate(
                text=chunk,
                ref_audio=profile["ref_audio"],
                ref_text=profile["ref_text"],
                num_step=8,
                guidance_scale=2.0,
                speed=1.0
            )
            t_infer = time.time()
            wav = audios[0].squeeze().cpu().numpy()
            t_encode = time.time()
            logging.info(
                f"[TTS] Chunk {i+1}/{len(chunks)} | "
                f"infer={t_infer-t0:.2f}s | "
                f"encode={t_encode-t_infer:.3f}s | "
                f"total={t_encode-t0:.2f}s | "
                f"{len(chunk.split())} words"
            )
            yield wav_numpy_to_pcm_bytes(wav, 
                                      sample_rate=OMNIVOICE_MODEL.sampling_rate,
                                      is_first_chunk=first_chunk)