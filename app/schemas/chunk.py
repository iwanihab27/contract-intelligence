from pydantic import BaseModel
from typing import Optional, List
from app.enums import ChunkEnums


class ChunkResponse(BaseModel):
    id: str
    contract_id: str
    parent_id: Optional[str] = None
    chunk_type: ChunkEnums
    text: str
    section_title: Optional[str] = None
    page_number: Optional[int] = None

    class Config:
        from_attributes = True


class ParentChunkResponse(BaseModel):
    id: str
    contract_id: str
    chunk_type: ChunkEnums
    text: str
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    children: List[ChunkResponse] = []

    class Config:
        from_attributes = True