import os
from huggingface_hub import hf_hub_download, snapshot_download
_DIR = os.path.dirname(os.path.abspath(__file__))
import os 
from config.config import settings
import logging

_DIR = os.path.dirname(os.path.abspath(__file__))
HF_REPO = "doduy1911/audio_TTS"
HF_MODEL_REPO = settings.MODEL_NAME
MODEL_PATH = os.path.join(_DIR, "..", "models")

if not os.path.exists(MODEL_PATH) or not os.listdir(MODEL_PATH):
    logging.info("[TTS] Đang tải model weights từ HuggingFace...")
    snapshot_download(
        repo_id=HF_MODEL_REPO,
        local_dir=MODEL_PATH,
        token=settings.TOKEN_HF
    )
    logging.info("[TTS] Tải model xong.")

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
        "ref_text":"Xin chào, mình là robot Chiko, mình sẽ là người bạn đồng hành cùng bạn trong bất kỳ lúc nào bạn cần nhé, mình sẽ kể chuyện vui, giải đáp thắc mắc và dạy bạn nói tiếng anh để bạn có thể cái thiện tiếng anh từng ngày nha."
    },

    "nuhanoi":{
        "ref_audio": get_voice_path("giongnuhanoi6s.wav"),
        "ref_text":"Xin chào, tôi là một người yêu thích công nghệ và sáng tạo. Trong công việc hằng ngày, tôi thường đọc tài liệu"
    },
    "nam":{
        "ref_audio": get_voice_path("nam.wav"),
        "ref_text":"Đây là câu chuyện về một trong những vụ gian lận kế toán lớn nhất lịch sử. Hàng tỷ đô bị cướp mất, hàng chục nghìn công"
    }
}