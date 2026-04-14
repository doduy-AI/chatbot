from omnivoice.models.omnivoice import OmniVoice
import argparse
import logging
import os
import re
import torch
import io
import torchaudio
from typing import Generator
from pydub import AudioSegment
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


def wav_numpy_to_mp3_bytes(wav: np.ndarray, sample_rate: int) -> bytes:
    """Chuyển numpy array → mp3 bytes."""
    pcm = (wav * 32767).astype(np.int16)
    audio_segment = AudioSegment(
        pcm.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    buf = io.BytesIO()
    audio_segment.export(buf, format="mp3", bitrate="128k")
    return buf.getvalue()


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
        for i, chunk in enumerate(chunks):
            t0 = time.time()
            audios = OMNIVOICE_MODEL.generate(
                text=chunk,
                ref_audio=profile["ref_audio"],
                ref_text=profile["ref_text"],
                num_step=16,
                guidance_scale=2.0,
                speed=1.0
            )
            t_infer = time.time()
            wav = audios[0].squeeze().cpu().numpy()
            mp3 = wav_numpy_to_mp3_bytes(wav, OMNIVOICE_MODEL.sampling_rate)
            t_encode = time.time()
            logging.info(
                f"[TTS] Chunk {i+1}/{len(chunks)} | "
                f"infer={t_infer-t0:.2f}s | "
                f"encode={t_encode-t_infer:.2f}s | "
                f"total={t_encode-t0:.2f}s | "
                f"{len(chunk.split())} words"
            )


            yield mp3


def run_inference(text: str, voice: str, output_path: str = OUTPUT_PATH):
    """Gom toàn bộ chunk lại, lưu thành 1 file mp3."""
    output_path = re.sub(r'\.wav$', '.mp3', output_path)

    all_bytes = b"".join(generate_tts_stream(text, voice))

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(all_bytes)
    logging.info(f"[TTS] Đã lưu tại: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="TTS Service")
    parser.add_argument("--voice", type=str, default="nuhanoi",help="Tên giọng đọc")
    parser.add_argument("--text",required=True , help="Vắn Bản cần đọc")
    parser.add_argument("--output", type=str , default="./output/audio.wav" , help="Đường dẫn audio")

    run = parser.parse_args()

    chunks = split_sentences(run.text)
    print(f"Số chunk: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"  [{i+1}] {c!r}")

    # run_inference(run.text,run.voice)



if __name__ == "__main__":
    main()