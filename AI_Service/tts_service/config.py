from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    REDIS_HOST: str = "REDIS_HOST"
    REDIS_PORT: int = "REDIS_PORT" 

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()