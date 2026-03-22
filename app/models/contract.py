import uuid as uuid_lib
from datetime import datetime
from sqlalchemy import Column, String, Float, Index, Integer, Text, DateTime, Enum as SAEnum
from app.core.database import Base
from app.enums import ContractEnums, ProcessingEnums
from sqlalchemy.dialects.postgresql import UUID

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4)

    name = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)

    contract_type = Column(SAEnum(ContractEnums), nullable=False, default=ContractEnums.OTHER)
    status = Column(SAEnum(ProcessingEnums), nullable=False, default=ProcessingEnums.PENDING)

    summary = Column(Text, nullable=True)
    overall_risk_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_contracts_uuid', 'uuid'),
        Index('ix_contracts_status', 'status'),
    )