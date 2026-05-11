
from pydantic_settings import BaseSettings , SettingsConfigDict
import os 
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
class Settings(BaseSettings):
        REDIS_HOST : str = "REDIS_HOST"
        REDIS_PORT : str = "REDIS_PORT"
        MODEL_NAME : str = "MODEL_NAME"  
        QDRANT_HOST : str = "QDRANT_HOST"   
        QDRANT_PORT : int = "QDRANT_PORT"
        MODEL_QDRANT : str = "MODEL_QDRANT"
        PASS_REDIS : str = "PASS_REDIS",
        OCR1 : str = "OCR1"
        OCR2 : str = "OCR2"
        OCR3 : str = "OCR3"
        OCR4 : str = "OCR4"
        OCR5 : str = "OCR5"
        OCR6 : str = "OCR6"
        GCP_PROJECT_ID : str = "GCP_PROJECT_ID",
        GCP_LOCATION : str = "GCP_LOCATION"
        model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),  
        env_file_encoding='utf-8'
    )


settings = Settings()