from omnivoice.models.omnivoice import OmniVoice
from omnivoice.utils.common import str2bool
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


def split_sentences(text: str, min_words: int = 10) -> list[str]:
    """
    Cắt text thành các câu theo dấu câu.
    Merge câu quá ngắn vào câu tiếp theo để tránh artifact.
    """
    raw = re.split(r'(?<=[.!?…])\s+|\n+', text.strip())
    raw = [s.strip() for s in raw if s.strip()]

    merged = []
    buffer = ""
    for sentence in raw:
        buffer = (buffer + " " + sentence).strip()
        if len(buffer.split()) >= min_words:
            merged.append(buffer)
            buffer = ""

    if buffer:
        if merged:
            merged[-1] += " " + buffer
        else:
            merged.append(buffer)

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
            logging.info(f"[TTS] Chunk {i+1}/{len(chunks)}: {chunk!r}")
            audios = OMNIVOICE_MODEL.generate(
                text=chunk,
                ref_audio=profile["ref_audio"],
                ref_text=profile["ref_text"],
                num_step=32,
                guidance_scale=2.0,
                speed=1.0
            )
            wav = audios[0].squeeze().cpu().numpy()
            yield wav_numpy_to_mp3_bytes(wav, OMNIVOICE_MODEL.sampling_rate)


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

    run_inference(run.text,run.voice)



if __name__ == "__main__":
    main()