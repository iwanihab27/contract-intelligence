from datetime import datetime
from typing import Optional
from app.enums import ContractEnums, ProcessingEnums
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class ContractCreate(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class ContractResponse(BaseModel):
    uuid: UUID
    name: str
    file_name: str
    contract_type: ContractEnums
    status: ProcessingEnums
    summary: Optional[str] = None
    overall_risk_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ContractListResponse(BaseModel):
    uuid: UUID
    name: str
    contract_type: ContractEnums
    status: ProcessingEnums
    overall_risk_score: Optional[float] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)