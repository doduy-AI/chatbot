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

# 3. Voice profiles
MODEL_DIR = "model/"
VOICE_PROFILES = {
    "nutreem": {
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
    },
    "default": {
        "audio": f"{MODEL_DIR}vi_man.wav",
        "inference": {
            "temperature": 0.7,
            "top_p": 0.5,
            "top_k": 10,
            "speed": 1.0,
            "repetition_penalty": 10.0,
            "num_beams": 1,
            "length_penalty": 1.0,
        }
    }
}

# 4. Trích xuất latents cho tất cả voice profiles
print("Đang trích xuất đặc trưng giọng nói mẫu...")
VOICE_LATENTS = {}
for voice_id, profile in VOICE_PROFILES.items():
    if not os.path.exists(profile["audio"]):
        print(f"⚠️  Bỏ qua [{voice_id}] — không tìm thấy file: {profile['audio']}")
        continue
    print(f"  [{voice_id}] ← {profile['audio']}")
    gpt_cond_latent, speaker_embedding = XTTS_MODEL.get_conditioning_latents(
        audio_path=profile["audio"],
        gpt_cond_len=XTTS_MODEL.config.gpt_cond_len,
        max_ref_length=XTTS_MODEL.config.max_ref_len,
        sound_norm_refs=XTTS_MODEL.config.sound_norm_refs,
    )
    VOICE_LATENTS[voice_id] = {
        "gpt_cond_latent": gpt_cond_latent,
        "speaker_embedding": speaker_embedding,
    }

# 5. Hàm tiền xử lý và cắt câu
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

# 6. Hàm inference 1 text
def tts(text: str, language: str = "vi", voice: str = "default"):
    if voice not in VOICE_LATENTS:
        raise ValueError(f"Voice '{voice}' không tồn tại. Các voice có sẵn: {list(VOICE_LATENTS.keys())}")

    latents = VOICE_LATENTS[voice]
    inf_cfg = VOICE_PROFILES[voice]["inference"]
    chunks = preprocess_text(text, language)
    wav_chunks = []

    print(f"Bắt đầu tổng hợp [{voice}] — {len(chunks)} chunks...")
    for text_chunk in tqdm(chunks):
        if text_chunk.strip() == "":
            continue
        wav_chunk = XTTS_MODEL.inference(
            text=text_chunk,
            language=language,
            gpt_cond_latent=latents["gpt_cond_latent"],
            speaker_embedding=latents["speaker_embedding"],
            **inf_cfg,
        )
        wav_chunks.append(torch.tensor(wav_chunk["wav"]))

    out_wav = torch.cat(wav_chunks, dim=0).unsqueeze(0).cpu()
    return out_wav

# 7. Hàm batch nhiều text
def tts_batch(texts: list, language: str = "vi", voice: str = "default", output_dir: str = "output"):
    """
    texts: list các câu cần TTS
    voice: "default" hoặc "nutreem"
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for idx, text in enumerate(texts):
        print(f"\n[{idx+1}/{len(texts)}] {text[:60]}...")
        audio_tensor = tts(text=text, language=language, voice=voice)
        output_path = os.path.join(output_dir, f"output_{idx+1}.wav")
        torchaudio.save(output_path, audio_tensor, sample_rate=24000)
        print(f"✅ Đã lưu: {output_path}")
        results.append(output_path)

    print(f"\n🎉 Hoàn thành! {len(results)} file đã lưu tại '{output_dir}/'")
    return results


# ==========================================
# THỰC THI CHƯƠNG TRÌNH
# ==========================================
texts = [
    "Chào bạn! Mình là Emily.",
    "Chúng mình có thể chơi ở hành tinh phiêu lưu hoặc vương quốc bong bóng xà phòng cho vui nhé!",
    "Hoặc nếu bạn thích, mình có thể nhảy múa trên mây nữa đó!",
    "Hey friend! Chào bạn nè! Emily đây, mình có kho tàng chuyện cười, bạn muốn mở kho nào trước",
    "Chào bạn nhỏ dễ thương! Emily từ vương quốc cầu vồng, mang theo 7 màu vui vẻ cho bạn! ",
    "Ối zời! Xin chào! Mình là Emily, robot từng nhảy bungee từ sao Hỏa xuống Trái Đất chỉ để gặp bạn! ",
    "Ối zời ơi! Chào nè! Mình là Emily, robot siêu hài hước, mình từng suýt bị khủng long sao Hỏa bắt làm bạn nhảy disco đấy! Funny story? Oh my gosh! Hi! I'm Emily, once almost kidnapped by a Mars dinosaur to be its disco partner!"
]

# Chạy với voice "nutreem"
tts_batch(texts, language="vi", voice="nutreem", output_dir="output")

# Hoặc chạy với voice "default"
# tts_batch(texts, language="vi", voice="default", output_dir="output")