from pydantic_settings import BaseSettings , SettingsConfigDict
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
class Settings(BaseSettings):
    MODEL_NAME : str = "MODEL_NAME" ,
    TOKEN_HF : str = "TOKEN_HF",
    REDIS_HOST: str = "REDIS_HOST"
    REDIS_PORT: int = "REDIS_PORT" 
    EXTERNAL_HOST: str = "EXTERNAL_HOST" 
    EXTERNAL_PORT: int = "EXTERNAL_PORT" 
    QUEUE_MAXSIZE: int = "QUEUE_MAXSIZE" 
    STREAM_GET_TIMEOUT: float = "STREAM_GET_TIMEOUT" 
    QUEUE_PUT_TIMEOUT : float = "QUEUE_PUT_TIMEOUT"
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR,".env"),
        env_file_encoding='utf-8'
    )

settings = Settings()