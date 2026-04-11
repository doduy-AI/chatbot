from omnivoice.models.omnivoice import OmniVoice
from omnivoice.utils.common import str2bool
import argparse
import logging
import os
import torch
import torchaudio
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
from input.voice_profiles import VOICE_PROFILE
import argparse


def get_best_device():
    if torch.cuda.is_available(): return "cuda"
    return "cpu"


def run_inference(text: str , voice: str ):
    MODEL_PATH = "./models"
    OUTPUT_PATH = "./output/audio.wav"

    device = get_best_device()
    profile = VOICE_PROFILE.get(voice)
    if profile is None:
        available = list(VOICE_PROFILE.keys())
        logging.error(f"[TTS Service] Giọng {voice} không được hỗ trợ . các giọng được hộ trợ hiện có :{available}")
        raise ValueError(f"Giọng {voice} không tồn tại")

    logging.info(f"[TTS] Đang khởi tạo BYTEHOME_TTS_SERVICE trên {device}")

    model = OmniVoice.from_pretrained(
        MODEL_PATH,
        device_map = device,
        dtype=torch.float16 if device == "cuda" else torch.float32   
          )
    
    logging.info(f" Đang xuất giọng từ file mẫu: {profile['ref_text']}")
    
    audios = model.generate(
        text=text,
        ref_audio=profile["ref_audio"],
        ref_text=profile["ref_text"],
        num_step=32,      
        guidance_scale=2.0,
        speed=1.0           
    )

    # 4. Lưu kết quả
    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_PATH)), exist_ok=True)
    torchaudio.save(OUTPUT_PATH, audios[0], model.sampling_rate)
    logging.info(f" Đã lưu giọng nói tại: {OUTPUT_PATH}")


def main():
    parser = argparse.ArgumentParser(description="TTS Service")
    parser.add_argument("--voice", type=str, default="nuhanoi",help="Tên giọng đọc")
    parser.add_argument("--text",required=True , help="Vắn Bản cần đọc")
    parser.add_argument("--output", type=str , default="./output/audio.wav" , help="Đường dẫn audio")

    run = parser.parse_args()

    run_inference(run.text,run.voice)



if __name__ == "__main__":
    main()