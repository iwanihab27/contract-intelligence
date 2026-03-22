from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str
    APP_ENV: str

    DATABASE_URL: str

    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION_NAME: str

    COHERE_API_KEY: str

    GROQ_API_KEY: str

    UPLOAD_DIR: str
    MAX_FILE_SIZE_MB: int

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()