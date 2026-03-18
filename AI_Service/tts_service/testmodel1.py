import os
import torch
import torchaudio
from tqdm import tqdm
from underthesea import sent_tokenize
from vinorm import TTSnorm
from huggingface_hub import snapshot_download
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

# 1. Tải trọng số model từ Hugging Face (nếu chưa có)
print("Đang kiểm tra và tải model...")
snapshot_download(repo_id="anhnh2002/vnTTS", repo_type="model", local_dir="model/")

# 2. Khởi tạo cấu hình và load model
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"Đang load model lên {device}...")

xtts_checkpoint = "model/model.pth"
xtts_config = "model/config.json"
xtts_vocab = "model/vocab.json"

config = XttsConfig()
config.load_json(xtts_config)
XTTS_MODEL = Xtts.init_from_config(config)
XTTS_MODEL.load_checkpoint(config,
                            checkpoint_path=xtts_checkpoint,
                            vocab_path=xtts_vocab,
                            use_deepspeed=False)
XTTS_MODEL.to(device)

# 3. Hàm tiền xử lý và cắt câu (Chunking)
def preprocess_text(text, language="vi"):
    if language == "vi":
        text = TTSnorm(text, unknown=False, lower=False, rule=True)
    
    if language in ["ja", "zh-cn"]:
        sentences = text.split("。")
    else:
        sentences = sent_tokenize(text)

    chunks = []
    chunk_i = ""
    len_chunk_i = 0
    for sentence in sentences:
        chunk_i += " " + sentence
        len_chunk_i += len(sentence.split())
        if len_chunk_i > 30:
            chunks.append(chunk_i.strip())
            chunk_i = ""
            len_chunk_i = 0

    if (len(chunks) > 0) and (len_chunk_i < 15):
        chunks[-1] += chunk_i
    else:
        chunks.append(chunk_i)

    return chunks

# 4. Trích xuất vector đặc trưng của giọng mẫu
speaker_audio_file = "model/vi_man.wav"
if not os.path.exists(speaker_audio_file):
    raise FileNotFoundError(f"Vui lòng đặt file âm thanh mẫu vào đường dẫn: {speaker_audio_file}")

print("Đang trích xuất đặc trưng giọng nói mẫu...")
gpt_cond_latent, speaker_embedding = XTTS_MODEL.get_conditioning_latents(
    audio_path=speaker_audio_file,
    gpt_cond_len=XTTS_MODEL.config.gpt_cond_len,
    max_ref_length=XTTS_MODEL.config.max_ref_len,
    sound_norm_refs=XTTS_MODEL.config.sound_norm_refs,
)

# 5. Hàm chạy suy luận (Inference) - 1 text
def tts(model: Xtts, text: str, language: str, gpt_cond_latent: torch.Tensor, speaker_embedding: torch.Tensor):
    chunks = preprocess_text(text, language)
    wav_chunks = []
    
    print(f"Bắt đầu tổng hợp giọng nói cho {len(chunks)} chunks...")
    for text_chunk in tqdm(chunks):
        if text_chunk.strip() == "":
            continue
        wav_chunk = model.inference(
            text=text_chunk,
            language=language,
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
            length_penalty=1.0,
            repetition_penalty=10.0,
            top_k=10,
            top_p=0.5,
        )
        wav_chunks.append(torch.tensor(wav_chunk["wav"]))

    out_wav = torch.cat(wav_chunks, dim=0).unsqueeze(0).cpu()
    return out_wav

# 6. Hàm chạy batch nhiều text
def tts_batch(texts: list, language: str = "vi", output_dir: str = "output"):
    """
    texts: list các câu cần TTS
    ví dụ: ["Xin chào!", "Tôi là Emily.", "Hôm nay trời đẹp."]
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for idx, text in enumerate(texts):
        print(f"\n[{idx+1}/{len(texts)}] Đang xử lý: {text[:50]}...")
        
        audio_tensor = tts(
            model=XTTS_MODEL,
            text=text,
            language=language,
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
        )
        
        output_path = os.path.join(output_dir, f"output_{idx+1}.wav")
        torchaudio.save(output_path, audio_tensor, sample_rate=24000)
        print(f"✅ Đã lưu: {output_path}")
        results.append(output_path)

    print(f"\n🎉 Hoàn thành! {len(results)} file đã được lưu tại '{output_dir}/'")
    return results


# ==========================================
# THỰC THI CHƯƠNG TRÌNH
# ==========================================
texts = [
    "Chào bạn Mình là Emily",
    "Chúng mình có thể chơi ở hành tinh phiêu lưu hoặc vương quốc bong bóng xà phòng cho vui nhé",
    "Hoặc nếu bạn thích mình có thể nhảy múa trên mây nữa đó",
    "Good evening nha Chào bạn nhỏ! Mình là Emily robot kể chuyện đêm khuya nhưng siêu hài hước",
    "Chào bé Emily đây mình biết mọi trò chơi vui trên đời bạn muốn chơi trò nào trước nào?",
    "Ồ hô hô! Xin chào! Mình là Emily robot siêu hoạt bát sẵn sàng nhảy múa cùng bạn ngay bây giờ!"

]

tts_batch(texts, language="vi", output_dir="output")