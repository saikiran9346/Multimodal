from typing import List, Optional
from pydantic import BaseModel
from app.models.chunk import SourceChunk


class QueryRequest(BaseModel):
    query: str
    top_k: int = 20
    exclude_images: bool = False
    doc_name: Optional[str] = None
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceChunk]


class CritiqueLogEntry(BaseModel):
    attempt: int
    query_used: str
    confidence: float
    is_grounded: Optional[bool] = None
    is_complete: Optional[bool] = None
    reasoning: str = ""
    suggested_query: str = ""
    duration_ms: int = 0


class AgenticQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceChunk]
    critique_log: List[CritiqueLogEntry] = []
    attempts: int = 1
    final_query: str = ""
