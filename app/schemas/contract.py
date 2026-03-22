from datetime import datetime
from typing import Optional
from app.enums import ContractEnums, ProcessingEnums
from pydantic import BaseModel, ConfigDict

class ContractCreate(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)

class ContractResponse(BaseModel):
    id: str
    name: str
    file_name: str
    contract_type: ContractEnums
    status: ProcessingEnums
    summary: Optional[str] = None
    overall_risk_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    id: str
    name: str
    contract_type: ContractEnums
    status: ProcessingEnums
    overall_risk_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True