import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.controllers.base_controller import BaseController
from src.controllers.qdrant_controller import QdrantController
from src.controllers.cache_controller import CacheController
from src.core.config import Settings
from src.core.cache import get_redis
from src.enums import ResponseEnums
from src.models.contract import Contract
from src.models.chunk import Chunk
from src.models.risk_score import RiskScore
from src.controllers.processing_controller import ProcessingController
from src.models.chat_history import ChatHistory

logger = logging.getLogger(__name__)


class ContractsController(BaseController):
    def __init__(self, db: AsyncSession, settings: Settings):
        super().__init__(db, settings)
        self.qdrant = QdrantController(db=db, settings=settings)
        self.cache = CacheController(get_redis())

    async def get_all(self) -> list[dict]:
        cached = await self.cache.get_contracts_list()
        if cached:
            return cached

        result = await self.db.execute(select(Contract))
        contracts = result.scalars().all()

        serialized = [
            {
                "uuid": str(c.uuid),
                "name": c.name,
                "contract_type": c.contract_type.value if hasattr(c.contract_type, "value") else c.contract_type,
                "status": c.status.value if hasattr(c.status, "value") else c.status,
                "overall_risk_score": c.overall_risk_score,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in contracts
        ]

        await self.cache.set_contracts_list(serialized)
        return serialized

    async def delete(self, contract_uuid: str):
        result = await self.db.execute(select(Contract).where(Contract.uuid == contract_uuid))
        contract = result.scalar_one_or_none()
        if not contract:
            return False, ResponseEnums.CONTRACT_NOT_FOUND.value

        result = await self.db.execute(
            select(Chunk).where(Chunk.contract_id == contract.id, Chunk.qdrant_id != None)
        )
        chunks = result.scalars().all()

        if chunks:
            qdrant_ids = [chunk.qdrant_id for chunk in chunks]
            await asyncio.to_thread(
                self.qdrant.client.delete,
                collection_name=self.settings.QDRANT_COLLECTION_NAME,
                points_selector=qdrant_ids
            )
            logger.info(f"Deleted {len(qdrant_ids)} vectors from Qdrant")

        await self.db.execute(delete(ChatHistory).where(ChatHistory.contract_id == contract.id))
        await self.db.execute(delete(RiskScore).where(RiskScore.contract_id == contract.id))
        await self.db.execute(delete(Chunk).where(Chunk.contract_id == contract.id))
        await self.db.commit()

        await self.db.delete(contract)
        await self.db.commit()
        logger.info(f"Deleted contract: {contract_uuid}")

        await self.cache.invalidate_contracts_list()
        await self.cache.invalidate_contract_queries(contract_uuid)

        return True, ResponseEnums.CONTRACT_DELETED.value

    async def reanalyze(self, contract_uuid: str):
        result = await self.db.execute(select(Contract).where(Contract.uuid == contract_uuid))
        contract = result.scalar_one_or_none()
        if not contract:
            return False, ResponseEnums.CONTRACT_NOT_FOUND.value

        processor = ProcessingController(db=self.db, settings=self.settings)
        text = processor.load_document(contract.file_path)
        if not text:
            return False, "Failed to extract text from document"

        await self.db.execute(delete(RiskScore).where(RiskScore.contract_id == contract.id))
        await self.db.commit()

        await processor.analyze(contract, text)
        logger.info(f"Reanalyzed contract: {contract_uuid}")

        await self.cache.invalidate_contract_queries(contract_uuid)
        await self.cache.invalidate_contracts_list()

        return True, ResponseEnums.CONTRACT_PROCESSED.value