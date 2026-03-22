import uuid as uuid_lib
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, Float, ForeignKey, Enum as SAEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.enums import QueryEnums

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4)

    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)

    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)
    query_type = Column(SAEnum(QueryEnums), nullable=True)
    risk_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_chat_history_uuid', 'uuid'),
        Index('ix_chat_history_contract_id', 'contract_id'),
    )
