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
speaker_audio_file = f"{MODEL_DIR}hn_nganha_begai.wav" # <-- Đường dẫn file wav của bạn
device = "cuda:0" if torch.cuda.is_available() else "cpu"

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

print(f"[*] Đang trích xuất đặc trưng từ file: {speaker_audio_file}")
gpt_cond_latent, speaker_embedding = XTTS_MODEL.get_conditioning_latents(
    audio_path=speaker_audio_file,
    gpt_cond_len=config.gpt_cond_len,
    max_ref_length=config.max_ref_len,
    sound_norm_refs=config.sound_norm_refs,
)
# ----------------------------------------------

print(" Mô hình XTTS đã sẵn sàng.")


def split_text_smartly(text, min_words=8): 
    phrases = re.split(r'([.!?;])', text)
    chunks = []
    current_chunk = ""
    for i in range(0, len(phrases) - 1, 2):
        phrase = phrases[i].strip()
        punct = phrases[i+1].strip()
        if not phrase: continue
        current_chunk += phrase + punct + " "
        if len(current_chunk.split()) >= min_words:
            chunks.append(current_chunk.strip())
            current_chunk = ""
    if len(phrases) % 2 != 0 and phrases[-1].strip():
        current_chunk += phrases[-1].strip()
    if current_chunk.strip():
        if chunks: chunks[-1] += " " + current_chunk.strip()
        else: chunks.append(current_chunk.strip())
    return chunks

def float_to_pcm_bytes(wav: np.ndarray, sample_rate=24000, fade_ms=20):
    """Chuẩn hoá, áp fade-in/out, rồi convert sang PCM 16-bit bytes"""
    wav = wav.astype(np.float32)

    # Chuẩn hoá tránh clip
    max_amp = np.max(np.abs(wav)) if wav.size > 0 else 1.0
    if max_amp > 1.0:
        wav /= max_amp

    # Fade-in / fade-out khoảng 20ms để loại 'bụp'
    fade_len = int(sample_rate * fade_ms / 1000)
    if len(wav) > fade_len * 2:
        fade = np.linspace(0, 1, fade_len, dtype=np.float32)
        wav[:fade_len] *= fade
        wav[-fade_len:] *= fade[::-1]

    pcm = (wav * 32767.0).astype(np.int16)
    return pcm.tobytes()

def generate_tts(text: str):
    chunks = split_text_smartly(text)
    first_chunk = True
    silence_bytes = b"\x00" * int(0.1 * 24000 * 2)  # 100ms silence đầu tiên

    with torch.inference_mode():
        for text_chunk in chunks:
            full_text = text_chunk.strip() + " "

            outputs = XTTS_MODEL.inference(
                text=full_text,
                language="vi",
                gpt_cond_latent=gpt_cond_latent,
                speaker_embedding=speaker_embedding,
                num_beams=1,              
                repetition_penalty=2.0,   
                temperature=0.9,         
                top_p=0.6,                
                speed=1,         
                top_k=50,                 
                length_penalty=1.0
            )

            wav = outputs["wav"]
            print(f"[DEBUG] Chunk '{text_chunk[:30]}...' length: {len(wav)/24000:.2f}s, max_amp: {np.max(np.abs(wav)):.2f}")

            filename = f"{text_chunk}{int(time.time()*1000)}.wav"
            file_path = os.path.join(output_dir, filename)

            # 4. Lưu file
            sf.write(file_path, wav, 24000)

            # Xử lý fade + chuẩn hóa
            audio_chunk = float_to_pcm_bytes(wav)

            # Thêm đoạn im lặng 100ms trước chunk đầu tiên để loại 'bụp'
            if first_chunk:
                yield silence_bytes
                first_chunk = False

            yield audio_chunk
            