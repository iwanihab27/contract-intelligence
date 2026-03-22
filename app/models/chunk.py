import uuid as uuid_lib
from datetime import datetime
from sqlalchemy import Column, String,Index, Integer, Text, DateTime, Enum as SAEnum, ForeignKey
from app.core.database import Base
from app.enums import ChunkEnums
from sqlalchemy.dialects.postgresql import UUID


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4)

    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("chunks.id"), nullable=True)

    chunk_type = Column(SAEnum(ChunkEnums), nullable=False)
    text = Column(Text, nullable=False)
    section_title = Column(String, nullable=True)
    page_number = Column(Integer, nullable=True)

    qdrant_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_chunks_uuid', 'uuid'),
        Index('ix_chunks_contract_id', 'contract_id'),
        Index('ix_chunks_parent_id', 'parent_id'),
    )