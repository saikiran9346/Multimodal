from typing import List, Optional
from pydantic import BaseModel


class SourceChunk(BaseModel):
    index: int
    doc_name: Optional[str] = None
    page_no: Optional[int] = None
    headings: List[str] = []
    content_types: List[str] = ["text"]
    text: Optional[str] = None
    score: Optional[float] = None
