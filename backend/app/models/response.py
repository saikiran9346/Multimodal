from typing import List, Optional
from pydantic import BaseModel
from app.models.chunk import SourceChunk


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    exclude_images: bool = False
    doc_name: Optional[str] = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceChunk]
