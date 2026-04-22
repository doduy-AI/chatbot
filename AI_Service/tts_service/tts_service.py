from omnivoice.models.omnivoice import OmniVoice
import logging
import re
import torch
from typing import Generator
import numpy as np
import lameenc

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
from input.voice_profiles import VOICE_PROFILE


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
    raw = re.split(r'(?<=[.!?…])\s+|\n+', text.strip())
    raw = [s.strip() for s in raw if s.strip()]

    sub_chunks = []
    for sentence in raw:
        if len(sentence.split()) > max_words:
            parts = re.split(r'(?<=[,;:])\s+', sentence)
            sub_chunks.extend([p.strip() for p in parts if p.strip()])
        else:
            sub_chunks.append(sentence)

    merged = []
    for chunk in sub_chunks:
        if merged and len(chunk.split()) < min_words:
            merged[-1] += " " + chunk  # gắn vào câu trước
        else:
            merged.append(chunk)

    return merged


def float_to_pcm_bytes(wav: np.ndarray, sample_rate=24000, fade_ms=50, is_last_chunk=False):
    wav = np.asarray(wav, dtype=np.float32).squeeze()
    
    if len(wav) < 512:
        return b""
    
    fade_len = int(sample_rate * fade_ms / 1000)
    
    if len(wav) > fade_len:
        fade_in = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
        wav[:fade_len] *= fade_in
    
    if is_last_chunk and len(wav) > fade_len * 2:
        fade_out = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)
        wav[-fade_len:] *= fade_out
    
    np.clip(wav, -1.0, 1.0, out=wav)
    pcm = (wav * 32767.0).astype(np.int16)
    return pcm.tobytes()

def generate_tts_stream(text: str, voice: str , audio_format: str) -> Generator[bytes, None, None]:
    profile = VOICE_PROFILE.get(voice)
    if profile is None:
        raise ValueError(f"Giọng '{voice}' không tồn tại. Có sẵn: {list(VOICE_PROFILE)}")

    chunks = split_sentences(text)
    logging.info(f"[TTS] Tổng {len(chunks)} chunk: {chunks}")

    use_mp3 = audio_format.lower() == "mp3"

    if use_mp3:
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(128)
        encoder.set_in_sample_rate(24000)
        encoder.set_channels(1)
        encoder.set_quality(2)

    with torch.inference_mode():        
        for i, text_chunk in enumerate(chunks):
            print(f"[TTS Chunk {i+1}/{len(chunks)}]: {text_chunk}")
            
            outputs = OMNIVOICE_MODEL.generate(        
                text=text_chunk,
                ref_audio=profile["ref_audio"],
                ref_text=profile["ref_text"],
                num_step=8,        
                guidance_scale=2.0,
                speed=1.0
            )
            
 
            if isinstance(outputs, dict):
                wav = outputs.get("wav") or outputs.get("audio")
            elif isinstance(outputs, list):
                wav = outputs[0] if outputs else np.zeros(0)
            else:
                wav = outputs  # fallback

            if wav is None:
                logging.warning(f"Chunk {i+1} trả về None")
                continue

            # Chuyển thành numpy nếu cần
            if torch.is_tensor(wav):
                wav = wav.squeeze().cpu().numpy()
            elif not isinstance(wav, np.ndarray):
                wav = np.array(wav, dtype=np.float32)
                print(f"[TTS] wav shape: {wav.shape}, sample_rate: {OMNIVOICE_MODEL.sampling_rate}")


            if use_mp3:
                pcm_int16 = (wav * 32767).clip(-32768, 32767).astype(np.int16)
                mp3_chunk = encoder.encode(pcm_int16.tobytes())
                if mp3_chunk:
                    yield mp3_chunk
            else:
                audio_chunk = float_to_pcm_bytes(
                    wav, 
                    sample_rate=OMNIVOICE_MODEL.sampling_rate,  
                    fade_ms=50,                                 
                )
                yield audio_chunk
            
        if use_mp3:
            final_bytes = encoder.flush()
            if final_bytes:
                yield final_bytes