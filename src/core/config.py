from pydantic_settings import BaseSettings
from functools import lru_cache
from src.enums.llm_enums import LLMProvider


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
    GROQ_MAX_CONTEXT_TOKENS: int = 7000
    OPENAI_API_KEY: str = ""

    LLM_PROVIDER: LLMProvider = LLMProvider.GROQ
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_MODEL: str = "gpt-4o"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    UPLOAD_DIR: str
    MAX_FILE_SIZE_MB: int

    ALLOWED_EXTENSIONS: str = ".pdf,.docx,.doc,.txt"

    PARENT_CHUNK_CHARS: int = 8000
    CHILD_CHUNK_WORDS: int = 100
    CHUNK_OVERLAP_SENTENCES: int = 2

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_MAX_CONNECTIONS: int = 10

    def get_allowed_extensions(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()