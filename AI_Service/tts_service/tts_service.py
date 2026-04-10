from omnivoice.models.omnivoice import OmniVoice
from omnivoice.utils.common import str2bool
import argparse
import logging
import os
import torch
import torchaudio
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_best_device():
    if torch.cuda.is_available(): return "cuda"
    return "cpu"
def run_inference():
    MODEL_PATH = "./models"
    OUTPUT_PATH = "./output/audio.wav"
    REF_AUDIO = "./input/audio.wav"
    REF_TEXT = "Hey, even though it's raining heavily and the wind is blowing strongly outside the window, we can still sit here, read books together and drink a warm cup of hot cocoa."

    device = get_best_device()

    logging.info(f"[TTS] Đang khởi tạo BYTEHOME_TTS_SERVICE trên {device}")

    model = OmniVoice.from_pretrained(
        MODEL_PATH,
        device_map = device,
        dtype=torch.float16 if device == "cuda" else torch.float32   
          )
    text_to_speak = "Today is September 23"
    
    logging.info(f" Đang nhái giọng từ file mẫu: {REF_AUDIO}")
    
    audios = model.generate(
        text=text_to_speak,
        ref_audio=REF_AUDIO,
        ref_text=REF_TEXT,
        num_step=32,      
        language="en",
        guidance_scale=2.0,
        speed=1.0           
    )

    # 4. Lưu kết quả
    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_PATH)), exist_ok=True)
    torchaudio.save(OUTPUT_PATH, audios[0], model.sampling_rate)
    logging.info(f" Đã lưu giọng nói tại: {OUTPUT_PATH}")



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_inference()