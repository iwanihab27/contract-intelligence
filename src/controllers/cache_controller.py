import json
import hashlib
import logging
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class CacheController:
    QUERY_TTL     = 60 * 60
    EMBEDDING_TTL = 60 * 60 * 24
    CONTRACTS_TTL = 30

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    def query_key(self, contract_id: str, question: str) -> str:
        h = hashlib.sha256(question.encode()).hexdigest()[:16]
        return f"query:{contract_id}:{h}"

    def embedding_key(self, text: str) -> str:
        h = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"embedding:{h}"

    def contracts_list_key(self) -> str:
        return "contracts:list"

    def contract_queries_pattern(self, contract_id: str) -> str:
        return f"query:{contract_id}:*"

    async def get_query(self, contract_id: str, question: str) -> dict | None:
        key = self.query_key(contract_id, question)
        raw = await self.redis.get(key)
        if raw:
            logger.info(f"Cache HIT  query:{contract_id}")
            return json.loads(raw)
        logger.info(f"Cache MISS query:{contract_id}")
        return None

    async def set_query(self, contract_id: str, question: str, answer: dict) -> None:
        key = self.query_key(contract_id, question)
        await self.redis.setex(key, self.QUERY_TTL, json.dumps(answer))

    async def invalidate_contract_queries(self, contract_id: str) -> None:
        pattern = self.contract_queries_pattern(contract_id)
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} query cache entries for contract:{contract_id}")


    async def get_embedding(self, text: str) -> list[float] | None:
        key = self.embedding_key(text)
        raw = await self.redis.get(key)
        if raw:
            logger.info("Cache HIT  embedding")
            return json.loads(raw)
        return None

    async def set_embedding(self, text: str, vector: list[float]) -> None:
        key = self.embedding_key(text)
        await self.redis.setex(key, self.EMBEDDING_TTL, json.dumps(vector))


    async def get_contracts_list(self) -> list | None:
        raw = await self.redis.get(self.contracts_list_key())
        if raw:
            logger.info("Cache HIT  contracts:list")
            return json.loads(raw)
        return None

    async def set_contracts_list(self, contracts: list) -> None:
        await self.redis.setex(self.contracts_list_key(), self.CONTRACTS_TTL, json.dumps(contracts))

    async def invalidate_contracts_list(self) -> None:
        await self.redis.delete(self.contracts_list_key())
        logger.info("Invalidated contracts:list cache")