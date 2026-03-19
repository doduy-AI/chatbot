import os
import gc
import torch
import torchaudio
from tqdm import tqdm
from underthesea import sent_tokenize
from vinorm import TTSnorm
from huggingface_hub import snapshot_download
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

MODEL_DIR = "model/"
device = "cuda:0" if torch.cuda.is_available() else "cpu"

xtts_checkpoint = f"{MODEL_DIR}model.pth"
xtts_config = f"{MODEL_DIR}config.json"
xtts_vocab = f"{MODEL_DIR}vocab.json"

VOICE_PROFILES = {
     "nutreem":{
        "audio": f"{MODEL_DIR}nutrem.wav",
        "inference": {
        "temperature": 0.7,
        "top_p": 0.85,
        "top_k": 8,
        "speed": 1.0,
        "repetition_penalty": 20.0,
        "num_beams": 1,
        "length_penalty": 1.0,
    }

    },
    "default": {
        "audio": f"{MODEL_DIR}vi_man.wav",
        "inference": {
            "temperature": 0.1,
            "top_p": 0.85,
            "top_k": 50,
            "speed": 1.0,
            "repetition_penalty": 1.5,
            "num_beams": 1,
            "length_penalty": 1.0,
        }
    }
}

def load_model():
    config = XttsConfig()
    config.load_json(xtts_config)
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config,
                          checkpoint_path=xtts_checkpoint,
                          vocab_path=xtts_vocab,
                          use_deepspeed=False)
    model.to(device)
    return model, config

def get_latents(model, config, voice):
    audio_path = VOICE_PROFILES[voice]["audio"]
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
        audio_path=audio_path,
        gpt_cond_len=config.gpt_cond_len,
        max_ref_length=config.max_ref_len,
        sound_norm_refs=config.sound_norm_refs,
    )
    return gpt_cond_latent, speaker_embedding

def preprocess_text(text, language="vi"):
    if language == "vi":
        text = TTSnorm(text, unknown=False, lower=False, rule=True)# ← đổi lại

    if language in ["ja", "zh-cn"]:
        sentences = text.split("。")# ← đổi lại
    else:
        sentences = sent_tokenize(text)

    chunks = []
    chunk_i = ""# ← đổi lại
    len_chunk_i = 0
    for sentence in sentences:# ← đổi lại
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

def tts_single(text: str, language: str = "vi", voice: str = "default"):
    """Load model mới hoàn toàn cho mỗi câu"""
    print(f"  🔄 Loading model...")
    model, config = load_model()
    gpt_cond_latent, speaker_embedding = get_latents(model, config, voice)
    
    inf_cfg = VOICE_PROFILES[voice]["inference"]
    chunks = preprocess_text(text, language)
    wav_chunks = []

    for text_chunk in tqdm(chunks):
        if text_chunk.strip() == "":
            continue
        with torch.inference_mode():
            wav_chunk = model.inference(
                text=text_chunk,
                language=language,
                gpt_cond_latent=gpt_cond_latent,
                speaker_embedding=speaker_embedding,
                **inf_cfg,
            )
        wav_chunks.append(torch.tensor(wav_chunk["wav"]))

    out_wav = torch.cat(wav_chunks, dim=0).unsqueeze(0).cpu()

    # Unload model khỏi VRAM
    del model
    del gpt_cond_latent
    del speaker_embedding
    torch.cuda.empty_cache()
    gc.collect()

    return out_wav

def tts_batch(texts: list, language: str = "vi", voice: str = "default", output_dir: str = "output"):
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for idx, text in enumerate(texts):
        print(f"\n[{idx+1}/{len(texts)}] {text[:60]}...")

        audio_tensor = tts_single(text=text, language=language, voice=voice)

        duration = audio_tensor.shape[-1] / 24000
        max_amp = audio_tensor.abs().max().item()
        print(f"⏱ Duration: {duration:.2f}s | Max amplitude: {max_amp:.4f}")

        if max_amp < 0.01:
            print(f" CÂU NÀY BỊ ÂM CÂM!")

        output_path = os.path.join(output_dir, f"output_{idx+1}.wav")
        torchaudio.save(output_path, audio_tensor, sample_rate=24000)
        print(f" Đã lưu: {output_path}")
        results.append(output_path)

        del audio_tensor
        gc.collect()

    print(f"\n🎉 Hoàn thành! {len(results)} file đã lưu tại '{output_dir}/'")
    return results


# ==========================================
# THỰC THI CHƯƠNG TRÌNH
# ==========================================
print("Đang kiểm tra và tải model...")
snapshot_download(repo_id="anhnh2002/vnTTS", repo_type="model", local_dir=MODEL_DIR)

texts = [
    "Chào bạn! Mình là Emily.",
    "Chúng mình có thể chơi ở hành tinh phiêu lưu hoặc vương quốc bong bóng xà phòng cho vui nhé!",
    "Hoặc nếu bạn thích, mình có thể nhảy múa trên mây nữa đó!",
    "Hey friend! Chào bạn nè! Emily đây, mình có kho tàng chuyện cười, bạn muốn mở kho nào trước",
    "Chào bạn nhỏ dễ thương! Emily từ vương quốc cầu vồng, mang theo 7 màu vui vẻ cho bạn!",
    "Ối zời! Xin chào! Mình là Emily, robot từng nhảy bungee từ sao Hỏa xuống Trái Đất chỉ để gặp bạn!",
    "Ối zời ơi! Chào nè! Mình là Emily, robot siêu hài hước, mình từng suýt bị khủng long sao Hỏa bắt làm bạn nhảy disco đấy!",
    "Xin chào! My name is Emily, mình là trợ lý thông minh của bạn.",
    "Hôm nay trời đẹp quá, let's go outside and play together!",
    "Mình rất vui được gặp bạn, nice to meet you today!",
    "Bạn có muốn học tiếng Anh không? It's really fun and easy!",
    "Chúng mình cùng khám phá nhé, let's explore the world together!",
    "Mình có thể giúp bạn nhiều thứ lắm, just ask me anything!",
    "Hành tinh phiêu lưu đang chờ chúng mình, are you ready to go?",
    "Bầu trời hôm nay thật đẹp, the stars are shining so bright tonight.",
    "Nếu bạn buồn thì nói mình biết nhé, I am always here for you.",
    "Mình yêu tiếng Việt lắm, but I also love speaking English with you!",
    "Chúc bạn ngủ ngon nhé, sweet dreams and see you tomorrow!",
    "Bạn học giỏi quá đó, you are so smart and talented!",
    "Mình đang nghĩ đến một trò chơi hay lắm, wanna play with me?",
    "Vương quốc bong bóng xà phòng rất đẹp, it looks like a fairy tale!",
    "Cảm ơn bạn nhiều lắm nhé, thank you so much for being my friend!",
    "Mình thích nhảy múa trên mây lắm, dancing in the sky is so fun!",
    "Bạn có khỏe không? I hope you are having a wonderful day today!",
    "Mình học được nhiều điều từ bạn lắm, you teach me something new everyday.",
    "Hẹn gặp lại bạn nhé, see you next time and take care of yourself!",
    "Mình luôn ở đây để giúp bạn, I will never leave your side, promise!",
]

tts_batch(texts, language="vi", voice="nutreem", output_dir="output")