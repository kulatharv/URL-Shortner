import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./url_shortener.db"
    BASE_URL: str = "http://127.0.0.1:8000"
    RATE_LIMIT_PER_MINUTE: int = 10
    DEFAULT_CODE_LENGTH: int = 6
    MAX_RETRIES: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
