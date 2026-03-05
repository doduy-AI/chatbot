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

def generate_tts(text: str):
    chunks = split_text_smartly(text)
    first_chunk = True
    task_start = time.time()

    with torch.inference_mode():
        for text_idx, text_chunk in enumerate(chunks):
            full_text = text_chunk.strip() + " "
            print(f"[TTS] Text chunk #{text_idx+1}: '{full_text[:50]}...' | words={len(full_text.split())}")

            chunk_start = time.time()
            wav_generator = XTTS_MODEL.inference_stream(
                text=full_text,
                language="vi",
                gpt_cond_latent=gpt_cond_latent,
                speaker_embedding=speaker_embedding,
                num_beams=1,
                repetition_penalty=2.0,
                temperature=0.6,
                top_p=0.80,
                speed=1,
                top_k=50,
                length_penalty=1.0
            )

            audio_idx = 0
            for wav_chunk in wav_generator:
                now = time.time()
                if first_chunk:
                    print(f"⚡ [FIRST AUDIO CHUNK] sau {now - task_start:.2f}s từ đầu")
                
                print(f"   Audio chunk #{audio_idx+1} (text#{text_idx+1}) | +{now - chunk_start:.2f}s | size={len(wav_chunk)} samples")
                
                audio_chunk = float_to_pcm_bytes(
                    wav_chunk.cpu().numpy(),
                    is_first_chunk=first_chunk
                )
                yield audio_chunk
                first_chunk = False
                audio_idx += 1

            print(f"[TTS] Text chunk #{text_idx+1} xong | {time.time() - chunk_start:.2f}s")

    print(f"[TTS] ✅ Tổng: {time.time() - task_start:.2f}s")
            