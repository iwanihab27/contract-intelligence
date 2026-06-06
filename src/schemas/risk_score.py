from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RiskScoreResponse(BaseModel):
    id: str
    contract_id: str

    overall_score: float
    ip_clauses_score: Optional[float] = None
    termination_score: Optional[float] = None
    non_compete_score: Optional[float] = None
    payment_score: Optional[float] = None
    auto_renewal_score: Optional[float] = None
    red_flags: Optional[str] = None

    created_at: datetime

    class Config:
        from_attributes = True