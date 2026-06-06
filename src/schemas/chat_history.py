from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.enums import QueryEnums


class ChatRequest(BaseModel):
    contract_id: str
    question: str


class ChatResponse(BaseModel):
    id: str
    contract_id: str
    question: str
    answer: str
    sources: Optional[str] = None
    query_type: Optional[QueryEnums] = None
    risk_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True