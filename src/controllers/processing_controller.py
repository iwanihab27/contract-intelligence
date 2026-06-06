import logging
import re
import nltk
from pathlib import Path
from nltk.tokenize import sent_tokenize
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.controllers.base_controller import BaseController
from src.core.config import Settings
from src.models.contract import Contract
from src.models.chunk import Chunk
from src.models.risk_score import RiskScore
from src.enums.file_enums import FileEnums
from src.enums import ProcessingEnums, ChunkEnums
from src.controllers.cohere_controller import CohereController
from src.controllers.qdrant_controller import QdrantController
from src.controllers.LLM.llm_controller import LLMController

logger = logging.getLogger(__name__)


class ProcessingController(BaseController):
    def __init__(self, db: AsyncSession, settings: Settings):
        super().__init__(db, settings)
        self.cohere = CohereController(db=db, settings=settings)
        self.qdrant = QdrantController(db=db, settings=settings)
        self.llm = LLMController(db=db, settings=settings)

    async def process(self, contract_id: str):
        result = await self.db.execute(select(Contract).where(Contract.uuid == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            return False, "Contract not found"

        await self.update_status(contract, ProcessingEnums.PROCESSING)

        text = self.load_document(contract.file_path)
        if not text:
            await self.update_status(contract, ProcessingEnums.FAILED)
            return False, "Failed to extract text from document"

        chunks = await self.chunk_text(text, contract.id)
        await self.embed_and_store(chunks)
        await self.analyze(contract, text)
        await self.update_status(contract, ProcessingEnums.COMPLETED)

        return True, "Contract processed successfully"

    async def update_status(self, contract: Contract, status: ProcessingEnums):
        contract.status = status
        await self.db.commit()
        await self.db.refresh(contract)

    def load_document(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        file_type = FileEnums.from_extension(ext)

        if not file_type:
            logger.error(f"No loader registered for file type: {ext}")
            return ""

        logger.info(f"Loading {ext} with {file_type.loader_class.__name__}")
        documents = file_type.loader_class(file_path).load()

        full_text = "\n".join(doc.page_content for doc in documents if doc.page_content.strip())
        logger.info(f"Loaded {len(documents)} sections, {len(full_text)} chars")
        return full_text

    async def chunk_text(self, text: str, contract_id: str) -> list:
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)

        child_size = self.settings.CHILD_CHUNK_WORDS
        overlap_sentences = self.settings.CHUNK_OVERLAP_SENTENCES
        chunks = []

        section_pattern = r'\n(?=(?:Section\s+\d+|SECTION\s+\d+|\d+\.\s+[A-Z]))'
        sections = re.split(section_pattern, text)
        sections = [s.strip() for s in sections if s.strip()]

        if len(sections) <= 1:
            sections = [text]

        for section in sections:
            lines = section.split("\n")
            section_title = lines[0].strip()
            section_text = "\n".join(lines[1:]).strip() if len(lines) > 1 else section

            if not section_text:
                section_text = section

            parent = Chunk(
                contract_id=contract_id,
                chunk_type=ChunkEnums.PARENT,
                text=section_text,
                section_title=section_title,
            )
            self.db.add(parent)
            await self.db.flush()

            sentences = sent_tokenize(section_text)
            current_chunk = []
            current_word_count = 0

            for sentence in sentences:
                current_chunk.append(sentence)
                current_word_count += len(sentence.split())

                if current_word_count >= child_size:
                    child = Chunk(
                        contract_id=contract_id,
                        parent_id=parent.id,
                        chunk_type=ChunkEnums.CHILD,
                        text=" ".join(current_chunk),
                        section_title=section_title,
                    )
                    self.db.add(child)
                    chunks.append(child)

                    current_chunk = current_chunk[-overlap_sentences:]
                    current_word_count = sum(len(s.split()) for s in current_chunk)

            if current_chunk:
                remaining_text = " ".join(current_chunk)
                if len(remaining_text.split()) >= 10:
                    child = Chunk(
                        contract_id=contract_id,
                        parent_id=parent.id,
                        chunk_type=ChunkEnums.CHILD,
                        text=remaining_text,
                        section_title=section_title,
                    )
                    self.db.add(child)
                    chunks.append(child)

        await self.db.commit()
        return chunks

    async def embed_and_store(self, chunks: list):
        texts = [chunk.text for chunk in chunks]
        dense_vectors = await self.cohere.embed_documents(texts)
        sparse_vectors = await self.qdrant.embed_sparse(texts)
        self.qdrant.ensure_collection()
        self.qdrant.store_chunks(chunks, dense_vectors, sparse_vectors)

    async def analyze(self, contract: Contract, text: str):
        result = await self.llm.analyze_contract(text)

        contract.summary = result.get("summary")
        contract.overall_risk_score = result.get("overall_risk_score")
        contract.contract_type = result.get("contract_type", "other")
        await self.db.commit()

        risk = RiskScore(
            contract_id=contract.id,
            overall_score=result.get("overall_risk_score", 0),
            ip_clauses_score=result.get("ip_clauses_score"),
            termination_score=result.get("termination_score"),
            non_compete_score=result.get("non_compete_score"),
            payment_score=result.get("payment_score"),
            auto_renewal_score=result.get("auto_renewal_score"),
            red_flags=str(result.get("red_flags", []))
        )
        self.db.add(risk)
        await self.db.commit()
        logger.info(f"Analysis completed for contract: {contract.id}")