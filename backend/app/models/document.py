from typing import Optional
from pydantic import BaseModel


class IngestResponse(BaseModel):
    status: str
    filename: str
    total_chunks: int
    text_chunks: int
    image_chunks: int
    message: Optional[str] = None
