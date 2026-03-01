import os
import json
import torch
import re
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

# =========================================================
# 1. KHỞI TẠO MÔ HÌNH (load 1 lần duy nhất khi import file)
# =========================================================
MODEL_DIR = "model/"
latents_file = f"{MODEL_DIR}vi_man_latents.pth"
device = "cuda:0" if torch.cuda.is_available() else "cpu"

print("🔧 Đang khởi tạo mô hình XTTS...")

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

latents = torch.load(latents_file, map_location=device, weights_only=True)
gpt_cond_latent = latents["gpt_cond_latent"].to(device)
speaker_embedding = latents["speaker_embedding"].to(device)

print("✅ Mô hình XTTS đã sẵn sàng.")


# =========================================================
# 2. HÀM TÁCH VĂN BẢN THÔNG MINH
# =========================================================
def split_text_smartly(text, min_words=5):
    phrases = re.split(r'([.,!?;])', text)
    chunks = []
    current_chunk = ""
    for i in range(0, len(phrases) - 1, 2):
        phrase = phrases[i].strip()
        punct = phrases[i+1].strip()
        if not phrase:
            continue
        current_chunk += phrase + punct + " "
        if len(current_chunk.split()) >= min_words:
            chunks.append(current_chunk.strip())
            current_chunk = ""
    if len(phrases) % 2 != 0 and phrases[-1].strip():
        current_chunk += phrases[-1].strip()
    if current_chunk.strip():
        if chunks:
            chunks[-1] += " " + current_chunk.strip()
        else:
            chunks.append(current_chunk.strip())
    return chunks


# =========================================================
# 3. HÀM SINH ÂM THANH TỪ TEXT
# =========================================================
# =========================================================
# 3. HÀM SINH ÂM THANH TỪ TEXT (GENERATOR VERSION)
# =========================================================
def generate_tts(text: str):
    """
    Sinh giọng nói từ text đầu vào dưới dạng Generator để hỗ trợ Streaming.
    Yields: bytes audio (PCM 16bit) của từng đoạn nhỏ.
    """
    chunks = split_text_smartly(text)
    print(f"🎙️  Tạo giọng nói từ {len(chunks)} đoạn...")

    with torch.inference_mode():
        for i, text_chunk in enumerate(chunks):
            # Inference từng đoạn nhỏ
            outputs = XTTS_MODEL.inference(
                text=text_chunk,
                language="vi",
                gpt_cond_latent=gpt_cond_latent,
                speaker_embedding=speaker_embedding,
                repetition_penalty=2.5,
                temperature=0.7,
                speed=0.85
            )
            
            # Chuyển đổi tensor sang bytes PCM 16bit
            audio_chunk = (outputs["wav"] * 32767).astype('int16').tobytes()
            
            # QUAN TRỌNG: Thay vì cộng dồn, ta 'bắn' nó đi ngay lập tức
            yield audio_chunk
            
            print(f"  ✅ Đã sinh và đẩy chunk {i+1}/{len(chunks)} vào ống dẫn")

    print("🏁 Hoàn tất TTS toàn bộ câu.")