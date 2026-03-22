import uuid as uuid_lib
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4)

    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)

    overall_score = Column(Float, nullable=False)
    ip_clauses_score = Column(Float, nullable=True)
    termination_score = Column(Float, nullable=True)
    non_compete_score = Column(Float, nullable=True)
    payment_score = Column(Float, nullable=True)
    auto_renewal_score = Column(Float, nullable=True)
    red_flags = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_risk_scores_uuid', 'uuid'),
        Index('ix_risk_scores_contract_id', 'contract_id'),
    )