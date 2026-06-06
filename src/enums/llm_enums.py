from enum import Enum


class LLMProvider(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"
    OLLAMA = "ollama"