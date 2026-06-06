import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.controllers.base_controller import BaseController
from app.controllers.groq_controller import GroqController
from app.controllers.qdrant_controller import QdrantController
from app.core.config import Settings
from app.enums import ResponseEnums
from app.models.contract import Contract
from app.models.chunk import Chunk
from app.models.risk_score import RiskScore
from app.controllers.processing_controller import ProcessingController
from app.models.chat_history import ChatHistory

logger = logging.getLogger(__name__)

class ContractsController(BaseController):
    def __init__(self, db: AsyncSession, settings: Settings):
        super().__init__(db, settings)
        self.groq = GroqController(db=db, settings=settings)
        self.qdrant = QdrantController(db=db, settings=settings)

    async def get_all(self):
        result = await self.db.execute(select(Contract))
        return result.scalars().all()

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

        return True, ResponseEnums.CONTRACT_DELETED.value

    async def reanalyze(self, contract_uuid: str):
        result = await self.db.execute(select(Contract).where(Contract.uuid == contract_uuid))
        contract = result.scalar_one_or_none()
        if not contract:
            return False, ResponseEnums.CONTRACT_NOT_FOUND.value

        processor = ProcessingController(db=self.db, settings=self.settings)
        text = processor._process_text(contract.file_path)

        await self.db.execute(delete(RiskScore).where(RiskScore.contract_id == contract.id))
        await self.db.commit()

        await processor._analyze(contract, text)
        logger.info(f"Reanalyzed contract: {contract_uuid}")

        return True, ResponseEnums.CONTRACT_PROCESSED.value