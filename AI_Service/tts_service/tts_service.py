import os
import json
import torch
import re , time
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import numpy as np
import soundfile as sf
output_dir = "/content/drive/MyDrive/git/debug_audio"

# 2. Tạo thư mục nếu chưa có
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

MODEL_DIR = "model/"
speaker_audio_file = f"{MODEL_DIR}giongnuhanoi6s.wav" 
device = "cuda:0" if torch.cuda.is_available() else "cpu"

VOICE_PROFILES={
    "nuhanoi":{
        "audio": f"{MODEL_DIR}giongnuhanoi6s.wav",
        "inference": {
            "temperature": 0.7,
            "top_p": 0.80,
            "top_k": 8,
            "speed": 1.0,
            "repetition_penalty": 20.0,
            "num_beams": 1,
            "length_penalty": 1.0,
        }

    },
    "nutreem":{
        "audio": f"{MODEL_DIR}hn_nganha_begai.wav",
        "inference": {
        "temperature": 0.8,
        "top_p": 0.9,
        "top_k": 30,
        "speed": 1.05,
        "repetition_penalty": 1.5,
        "num_beams": 1,
        "length_penalty": 1.0,
    }

    }
}




print(" Đang khởi tạo mô hình XTTS...")

config = XttsConfig()
config.load_json(f"{MODEL_DIR}config.json")
XTTS_MODEL = Xtts.init_from_config(config)
XTTS_MODEL.load_checkpoint(
    config,
    checkpoint_path=f"{MODEL_DIR}model.pth",
    vocab_path=f"{MODEL_DIR}vocab.json",
    use_deepspeed=False
)
XTTS_MODEL.to(device)

print("Đang trích xuất đặc trưng giọng nói...")
VOICE_LATENTS = {}
for voice_id, profile in VOICE_PROFILES.items():
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

# ----------------------------------------------

print(" Mô hình XTTS đã sẵn sàng.")



def split_text_smartly(text, max_words=12):
    sentences = re.split(r'([.!?;])', text)
    chunks = []

    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i].strip()
        punct = sentences[i+1]

        full_sentence = sentence + punct

        # 👉 nếu câu ngắn → giữ nguyên
        if len(full_sentence.split()) <= max_words:
            chunks.append(full_sentence.strip())
        else:
            # 👉 nếu dài → mới split theo dấu ,
            sub_chunks = re.split(r',', full_sentence)

            for sc in sub_chunks:
                sc = sc.strip()
                if not sc:
                    continue

                # 💥 FIX QUAN TRỌNG: nếu kết thúc bằng dấu , → đổi thành .
                if not sc.endswith('.'):
                    sc = sc.rstrip(',') + '.'

                chunks.append(sc)

    return chunks

def clean_text(text):
    return re.sub(r"[^\w\s.,]", "", text).strip()

def float_to_pcm_bytes(wav: np.ndarray, sample_rate=24000, fade_ms=20, is_first_chunk=False):
    wav = np.array(wav, dtype=np.float32)
    
    # Chỉ Fade-in ở chunk đầu tiên để tránh bị 'bụp' vào tai
    if is_first_chunk:
        fade_len = int(sample_rate * fade_ms / 1000)
        if len(wav) > fade_len:
            fade = np.linspace(0, 1, fade_len, dtype=np.float32)
            wav[:fade_len] *= fade

    # Chuyển sang 16-bit PCM (chuẩn WAV)
    pcm = (wav * 32767.0).astype(np.int16)
    return pcm.tobytes()

def generate_tts(text: str,voice:str):
    latents = VOICE_LATENTS[voice]
    inf_cfg = VOICE_PROFILES[voice]["inference"]
    # chunks = split_text_smartly(text)
    chunks = [clean_text(chunk) for chunk in split_text_smartly(text)]

    first_chunk = True

    with torch.inference_mode():
        for text_chunk in chunks:
            print(text_chunk)
            full_text = text_chunk.strip() + "..."

            # 1. Chạy model
            outputs = XTTS_MODEL.inference(
                text=full_text,
                language="vi",
                gpt_cond_latent=latents["gpt_cond_latent"],
                speaker_embedding=latents["speaker_embedding"],
                **inf_cfg,
            )

            wav = outputs["wav"]
            
            # 2. Xử lý PCM bytes (đã tự bao gồm logic fade-in trong hàm)
            audio_chunk = float_to_pcm_bytes(wav, is_first_chunk=first_chunk)

            # 3. Yield thẳng ra queue, KHÔNG thêm gì khác
            yield audio_chunk
            
            # 4. Đánh dấu để các chunk sau không bị fade-in nữa
            first_chunk = False
            