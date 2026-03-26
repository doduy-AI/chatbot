import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

import torch
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

from tts_paths import model_dir_str
from tts_pipeline import (
    SAMPLE_RATE,
    clean_text,
    concat_wav_chunks,
    merge_short_text_chunks,
    split_text_smartly,
    wav_to_pcm_stream,
)


MODEL_DIR = model_dir_str()
device = "cuda:0" if torch.cuda.is_available() else "cpu"

VOICE_PROFILES = {
    "nuhanoi": {
        "audio": f"{MODEL_DIR}giongnuhanoi6s.wav",
        "inference": {
            "temperature": 0.7,
            "top_p": 0.80,
            "top_k": 8,
            "speed": 1.0,
            "repetition_penalty": 5.0,
            "num_beams": 1,
            "length_penalty": 1.0,
        },
    },
    "nutreem": {
        "audio": f"{MODEL_DIR}nutrem.wav",
        "inference": {
            "temperature": 0.7,
            "top_p": 0.85,
            "top_k": 8,
            "speed": 1.0,
            "repetition_penalty": 5.0,
            "num_beams": 1,
            "length_penalty": 1.0,
        },
    },
}


def _voice_profiles_with_files() -> dict:
    """Chỉ giữ profile có file giọng mẫu (tránh crash khi thiếu nutrem.wav trên server)."""
    out = {}
    for vid, profile in VOICE_PROFILES.items():
        ap = Path(profile["audio"])
        if ap.is_file():
            out[vid] = profile
        else:
            print(f"  [bỏ qua {vid}] không thấy file: {ap}")
    if not out:
        raise FileNotFoundError(
            f"Không có giọng nào khả dụng. Cần ít nhất một file trong {MODEL_DIR} "
            "(vd. giongnuhanoi6s.wav hoặc nutrem.wav)."
        )
    return out


VOICE_PROFILES_LOADED = _voice_profiles_with_files()
DEFAULT_VOICE = "nuhanoi" if "nuhanoi" in VOICE_PROFILES_LOADED else next(iter(VOICE_PROFILES_LOADED))
AVAILABLE_VOICES = tuple(VOICE_PROFILES_LOADED.keys())

print(f" Đang khởi tạo mô hình XTTS... (MODEL_DIR={MODEL_DIR})")

config = XttsConfig()
config.load_json(f"{MODEL_DIR}config.json")
XTTS_MODEL = Xtts.init_from_config(config)
XTTS_MODEL.load_checkpoint(
    config,
    checkpoint_path=f"{MODEL_DIR}model.pth",
    vocab_path=f"{MODEL_DIR}vocab.json",
    use_deepspeed=False,
    eval=True,
)
XTTS_MODEL.to(device)

print("Đang trích xuất đặc trưng giọng nói...")
VOICE_LATENTS = {}
for voice_id, profile in VOICE_PROFILES_LOADED.items():
    print(f"  [{voice_id}] ← {profile['audio']}")
    gpt_cond_latent, speaker_embedding = XTTS_MODEL.get_conditioning_latents(
        audio_path=profile["audio"],
        gpt_cond_len=config.gpt_cond_len,
        max_ref_length=config.max_ref_len,
        sound_norm_refs=config.sound_norm_refs,
    )
    VOICE_LATENTS[voice_id] = {
        "gpt_cond_latent": gpt_cond_latent,
        "speaker_embedding": speaker_embedding,
    }

print(f" Mô hình XTTS đã sẵn sàng. Giọng: {', '.join(AVAILABLE_VOICES)} (mặc định: {DEFAULT_VOICE})")


def generate_tts(text: str, voice: str):
    """
    Nhiều lần inference theo chunk → ghép sóng có crossfade → stream PCM.
    """
    if voice not in VOICE_LATENTS:
        raise KeyError(
            f"Giọng {voice!r} không có (thiếu file mẫu hoặc chưa load). "
            f"Có sẵn: {list(VOICE_LATENTS)}"
        )
    latents = VOICE_LATENTS[voice]
    inf_cfg = VOICE_PROFILES_LOADED[voice]["inference"]
    raw_chunks = split_text_smartly(text)
    min_w = int(os.environ.get("TTS_MIN_WORDS_PER_CHUNK", "0"))
    if min_w > 1:
        raw_chunks = merge_short_text_chunks(raw_chunks, min_w)
    text_chunks = [clean_text(c) for c in raw_chunks if clean_text(c)]

    if not text_chunks:
        return

    wav_parts = []
    with torch.inference_mode():
        for text_chunk in text_chunks:
            print(text_chunk)
            outputs = XTTS_MODEL.inference(
                text=text_chunk.strip(),
                language="vi",
                gpt_cond_latent=latents["gpt_cond_latent"],
                speaker_embedding=latents["speaker_embedding"],
                **inf_cfg,
            )
            wav_parts.append(outputs["wav"])

    merged = concat_wav_chunks(wav_parts, sample_rate=SAMPLE_RATE)
    for pcm_block in wav_to_pcm_stream(merged, sample_rate=SAMPLE_RATE):
        yield pcm_block
