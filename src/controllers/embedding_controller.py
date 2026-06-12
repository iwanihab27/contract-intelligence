import asyncio
import logging
import cohere
from src.controllers.base_controller import BaseController
from src.controllers.cache_controller import CacheController
from src.core.cache import get_redis
from src.core.config import Settings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EmbeddingController(BaseController):
    def __init__(self, db: AsyncSession, settings: Settings):
        super().__init__(db, settings)
        self.client = cohere.ClientV2(api_key=self.settings.COHERE_API_KEY)
        self.model = "embed-multilingual-v3.0"
        self.cache = CacheController(get_redis())

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = [None] * len(texts)
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            cached = await self.cache.get_embedding(text)
            if cached:
                vectors[i] = cached
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        if uncached_texts:
            response = await asyncio.to_thread(
                self.client.embed,
                texts=uncached_texts,
                model=self.model,
                input_type="search_document",
                embedding_types=["float"]
            )
            for idx, text, vector in zip(uncached_indices, uncached_texts, response.embeddings.float_):
                await self.cache.set_embedding(text, vector)
                vectors[idx] = vector

        logger.info(f"Embedded {len(texts)} documents ({len(uncached_texts)} from Cohere, {len(texts) - len(uncached_texts)} from cache)")
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        cached = await self.cache.get_embedding(text)
        if cached:
            logger.info("Embedded query (cache hit)")
            return cached

        response = await asyncio.to_thread(
            self.client.embed,
            texts=[text],
            model=self.model,
            input_type="search_query",
            embedding_types=["float"]
        )
        vector = response.embeddings.float_[0]
        await self.cache.set_embedding(text, vector)
        logger.info("Embedded query (Cohere)")
        return vector