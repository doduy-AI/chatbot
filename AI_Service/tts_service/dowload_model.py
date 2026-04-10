import os 
from huggingface_hub import snapshot_download
from config.config import settings
def dowload_checkpoint_bytehomeTTS():
        repo_id = settings.MODEL_NAME
        model_dir = "./models"
        token = settings.TOKEN_HF
        print(repo_id,model_dir,token)

if __name__ == "__main__":
        dowload_checkpoint_bytehomeTTS()