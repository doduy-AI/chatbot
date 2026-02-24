
from pydantic_settings import BaseSettings , SettingsConfigDict

class Settings(BaseSettings):
        REDIS_HOST : str = "REDIS_HOST"
        REDIS_PORT : str = "REDIS_PORT"
        API_LLM : str = "API_LLM"
        MODEL_NAME : str = "MODEL_NAME"     
        model_config = SettingsConfigDict(env_file=".env",env_file_encoding='utf-8')


settings = Settings()