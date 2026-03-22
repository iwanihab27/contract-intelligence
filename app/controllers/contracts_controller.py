import logging
from sqlalchemy.orm import Session
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
    def __init__(self, db: Session, settings: Settings):
        super().__init__(db, settings)
        self.groq = GroqController(db=db, settings=settings)
        self.qdrant = QdrantController(db=db, settings=settings)

    def get_all(self):
        contracts = self.db.query(Contract).all()
        return contracts

    def delete(self, contract_uuid: str):
        contract = self.db.query(Contract).filter(Contract.uuid == contract_uuid).first()
        if not contract:
            return False, ResponseEnums.CONTRACT_NOT_FOUND.value

        chunks = self.db.query(Chunk).filter(
            Chunk.contract_id == contract.id,
            Chunk.qdrant_id != None
        ).all()

        if chunks:
            qdrant_ids = [chunk.qdrant_id for chunk in chunks]
            self.qdrant.client.delete(
                collection_name=self.settings.QDRANT_COLLECTION_NAME,
                points_selector=qdrant_ids
            )
            logger.info(f"Deleted {len(qdrant_ids)} vectors from Qdrant")

        self.db.query(ChatHistory).filter(ChatHistory.contract_id == contract.id).delete()
        self.db.query(RiskScore).filter(RiskScore.contract_id == contract.id).delete()
        self.db.query(Chunk).filter(Chunk.contract_id == contract.id).delete()
        self.db.commit()

        self.db.delete(contract)
        self.db.commit()
        logger.info(f"Deleted contract: {contract_uuid}")

        return True, ResponseEnums.CONTRACT_DELETED.value

    def reanalyze(self, contract_uuid: str):
        contract = self.db.query(Contract).filter(Contract.uuid == contract_uuid).first()
        if not contract:
            return False, ResponseEnums.CONTRACT_NOT_FOUND.value

        with open(contract.file_path, "rb") as f:
            processor = ProcessingController(db=self.db, settings=self.settings)
            text = processor._process_text(contract.file_path)

        self.db.query(RiskScore).filter(RiskScore.contract_id == contract.id).delete()
        self.db.commit()

        processor._analyze(contract, text)
        logger.info(f"Reanalyzed contract: {contract_uuid}")

        return True, ResponseEnums.CONTRACT_PROCESSED.value