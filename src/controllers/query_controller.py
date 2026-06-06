import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.controllers.base_controller import BaseController
from src.controllers.cohere_controller import CohereController
from src.controllers.qdrant_controller import QdrantController
from src.controllers.LLM.llm_controller import LLMController
from src.core.config import Settings
from src.models.contract import Contract
from src.models.chunk import Chunk
from src.models.chat_history import ChatHistory

logger = logging.getLogger(__name__)


class QueryController(BaseController):
    def __init__(self, db: AsyncSession, settings: Settings):
        super().__init__(db, settings)
        self.cohere = CohereController(db=db, settings=settings)
        self.qdrant = QdrantController(db=db, settings=settings)
        self.llm = LLMController(db=db, settings=settings)

    async def query(self, contract_id: str, question: str):
        result = await self.db.execute(select(Contract).where(Contract.uuid == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            return False, "Contract not found", None

        dense_vector = await self.cohere.embed_query(question)
        results = await self.qdrant.search(dense_vector, question, limit=15)
        chunks = await self.get_context_chunks(results)
        answer = await self.llm.answer_question(question, chunks, contract.name)

        await self.save_chat_history(contract.id, question, answer)

        return True, "Query answered successfully", answer

    async def get_context_chunks(self, results: list) -> list:
        context = []
        for result in results:
            parent_id = result.payload.get("parent_id")
            if parent_id:
                chunk_result = await self.db.execute(select(Chunk).where(Chunk.id == parent_id))
                parent = chunk_result.scalar_one_or_none()
                if parent:
                    result.payload["text"] = parent.text
            context.append(result)
        return context

    async def save_chat_history(self, contract_id: int, question: str, answer: dict):
        chat = ChatHistory(
            contract_id=contract_id,
            question=question,
            answer=answer.get("answer", ""),
            sources=json.dumps(answer.get("sources", [])),
            query_type=answer.get("query_type"),
            risk_score=answer.get("risk_score")
        )
        self.db.add(chat)
        await self.db.commit()
        logger.info(f"Chat history saved for contract: {contract_id}")