import asyncio
import logging
import cohere
from app.controllers.base_controller import BaseController
from app.core.config import Settings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class CohereController(BaseController):
    def __init__(self, db: AsyncSession, settings: Settings):
        super().__init__(db, settings)
        self.client = cohere.ClientV2(api_key=self.settings.COHERE_API_KEY)
        self.model = "embed-multilingual-v3.0"

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = await asyncio.to_thread(
            self.client.embed,
            texts=texts,
            model=self.model,
            input_type="search_document",
            embedding_types=["float"]
        )
        logger.info(f"Embedded {len(texts)} documents")
        return response.embeddings.float_

    async def embed_query(self, text: str) -> list[float]:
        response = await asyncio.to_thread(
            self.client.embed,
            texts=[text],
            model=self.model,
            input_type="search_query",
            embedding_types=["float"]
        )
        logger.info(f"Embedded query")
        return response.embeddings.float_[0]