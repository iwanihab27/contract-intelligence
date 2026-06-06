import logging
from sqlalchemy.ext.asyncio import AsyncSession
from src.controllers.base_controller import BaseController
from src.core.config import Settings
from src.controllers.LLM.providers.base_provider import BaseLLMProvider
from src.controllers.LLM.providers.groq_provider import GroqProvider
from src.controllers.LLM.providers.openai_provider import OpenAIProvider
from src.controllers.LLM.providers.ollama_provider import OllamaProvider
from src.enums.llm_enums import LLMProvider

logger = logging.getLogger(__name__)


class LLMController(BaseController):
    def __init__(self, db: AsyncSession, settings: Settings):
        super().__init__(db, settings)
        self.provider: BaseLLMProvider = self.load_provider()

    def load_provider(self) -> BaseLLMProvider:
        provider = self.settings.LLM_PROVIDER

        if provider == LLMProvider.GROQ:
            logger.info("LLM provider: Groq")
            return GroqProvider(
                api_key=self.settings.GROQ_API_KEY,
                model=self.settings.GROQ_MODEL
            )
        elif provider == LLMProvider.OPENAI:
            logger.info("LLM provider: OpenAI")
            return OpenAIProvider(
                api_key=self.settings.OPENAI_API_KEY,
                model=self.settings.OPENAI_MODEL
            )
        elif provider == LLMProvider.OLLAMA:
            logger.info("LLM provider: Ollama (local)")
            return OllamaProvider(
                base_url=self.settings.OLLAMA_BASE_URL,
                model=self.settings.OLLAMA_MODEL
            )

    async def analyze_contract(self, text: str) -> dict:
        return await self.provider.analyze_contract(text)

    async def answer_question(self, question: str, chunks: list, contract_name: str) -> dict:
        return await self.provider.answer_question(question, chunks, contract_name)