"""
Test F5-TTS Vietnamese: non-autoregressive, không hụt hơi/vỡ giọng.
Model: hynt/F5-TTS-Vietnamese-ViVoice (1000h Vietnamese data)
"""
import os
import sys

os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import soundfile as sf

OUTPUT_DIR = "/workspace/tts_test_output/f5tts"
CAU_TEST = "/workspace/docs/cau-test.txt"
REF_AUDIO = "/workspace/tts_service/model/nutrem.wav"
REF_TEXT = "Xin chào, tôi là trợ lý ảo thông minh của bạn."

os.makedirs(OUTPUT_DIR, exist_ok=True)

from huggingface_hub import hf_hub_download

from f5_tts.api import F5TTS

# ckpt_file phải là ĐƯỜNG DẪN FILE .pt — không truyền repo_id (torch.load sẽ FileNotFoundError).
_REPO = "hynt/F5-TTS-Vietnamese-ViVoice"
_CKPT_NAME = "model_last.pt"
ckpt_path = os.environ.get("F5TTS_CKPT") or hf_hub_download(
    repo_id=_REPO,
    filename=_CKPT_NAME,
)

print("Khởi tạo F5-TTS Vietnamese...")
print(f"  checkpoint: {ckpt_path}")
tts = F5TTS(model_type="F5-TTS", ckpt_file=ckpt_path)
print("Model loaded OK!")

# Đọc 18 câu test tiếng Việt
lines = [
    ln.strip()
    for ln in open(CAU_TEST, encoding="utf-8").readlines()
    if ln.strip()
]

# Thêm câu song ngữ Việt-Anh
bilingual_lines = [
    "Xin chào! My name is Emily, mình là trợ lý thông minh của bạn.",
    "Hôm nay trời đẹp quá, let's go outside and play together!",
    "Mình rất vui được gặp bạn, nice to meet you today!",
    "Bạn có muốn học tiếng Anh không? It's really fun and easy!",
    "Chúc bạn ngủ ngon nhé, sweet dreams and see you tomorrow!",
]

all_lines = lines + bilingual_lines

print(f"\nXuất {len(all_lines)} file → {OUTPUT_DIR}")
print(f"  - {len(lines)} câu tiếng Việt")
print(f"  - {len(bilingual_lines)} câu song ngữ Việt-Anh\n")

for i, text in enumerate(all_lines, start=1):
    print(f"[{i:03d}/{len(all_lines)}] {text[:70]}...")
    out_path = os.path.join(OUTPUT_DIR, f"{i:03d}.wav")

    try:
        wav, sr, _ = tts.infer(
            ref_file=REF_AUDIO,
            ref_text=REF_TEXT,
            gen_text=text,
        )
        sf.write(out_path, wav, sr)
        duration = len(wav) / sr
        fsize = os.path.getsize(out_path)
        print(f"  OK: {out_path} ({fsize // 1024}KB, {duration:.1f}s)")
    except Exception as e:
        print(f"  LỖI: {e}")

print(f"\nXong! Kiểm tra {OUTPUT_DIR}")
