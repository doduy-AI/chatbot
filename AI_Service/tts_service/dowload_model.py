import os 
from huggingface_hub import snapshot_download
from config.config import settings
import logging
def dowload_checkpoint_bytehomeTTS():
        repo_id = settings.MODEL_NAME
        model_dir = "./models"
        token = settings.TOKEN_HF
        print(f"[TTS] bắt đầu dow checkpoint tts từ {repo_id}")
        os.makedirs(model_dir,exist_ok=True)
        try:
                snapshot_download(
                        repo_id=repo_id,
                        local_dir=model_dir,
                        token=token,
                        resume_download=True 
                )
                logging.info(f"[TTS] Tải model thành công về thư mục: {model_dir}")
        except Exception as e:
                logging.error(f"[TTS]  Lỗi tải model từ HF {e}")


        

if __name__ == "__main__":
        dowload_checkpoint_bytehomeTTS()