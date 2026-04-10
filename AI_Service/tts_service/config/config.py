from pydantic_settings import BaseSettings , SettingsConfigDict
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
class Settings(BaseSettings):
    MODEL_NAME : str = "MODEL_NAME" ,
    TOKEN_HF : str = "TOKEN_HF"
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR,".env"),
        env_file_encoding='utf-8'
    )

settings = Settings()