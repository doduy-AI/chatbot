import os
import json
import torch
import re
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts


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

def generate_tts(text: str):
    chunks = split_text_smartly(text)
    
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
            audio_chunk = (outputs["wav"] * 32767).astype('int16').tobytes()
            yield audio_chunk