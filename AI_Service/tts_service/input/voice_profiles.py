import os
_DIR = os.path.dirname(os.path.abspath(__file__))
import os 
from huggingface_hub import hf_hub_download
from config.config import settings
import logging

_DIR = os.path.dirname(os.path.abspath(__file__))
HF_REPO = "doduy1911/audio_TTS"

def get_voice_path(filename: str) -> str: 
    local_path = os.path.join(_DIR, filename)
    
    if not os.path.exists(local_path):
        logging.info(f"Đang tải {filename} từ HuggingFace...")
        hf_hub_download(
            repo_id=HF_REPO,
            filename=f"{filename}",
            local_dir=_DIR,
            token=settings.TOKEN_HF
        )
    
    return local_path
VOICE_PROFILE = {
    "nutrem":{
        "ref_audio": get_voice_path("nutrem.wav"),
        "ref_text":"Xin chào, hôm nay là một ngày khá đặc biệt. Không phải vì có điều gì đó quá lớn lao xảy ra, mà đơn giản là tôi quyết định sẽ làm mọi thứ chậm lại một chút, để lắng nghe bản thân mình rõ hơn."
    },

    "nuhanoi":{
        "ref_audio": get_voice_path("giongnuhanoi6s.wav"),
        "ref_text":"Xin chào, tôi là một người yêu thích công nghệ và sáng tạo. Trong công việc hằng ngày, tôi thường đọc tài liệu"
    }
}