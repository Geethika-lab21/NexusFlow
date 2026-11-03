from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    category: str
    text: str
    semantic_score: Optional[float] = None
    bm25_score: Optional[float] = None
    rrf_score: float
    retrieval_method: str = "hybrid"

class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    top_k: int = Field(5, ge=1, le=20)
    category: Optional[str] = None

class KnowledgeSearchResponse(BaseModel):
    query: str
    results: List[RetrievedChunk]
    total_found: int
    retrieval_method: str

class KnowledgeDocumentResponse(BaseModel):
    id: str
    title: str
    file_path: str
    category: str
    content_hash: str
    chunk_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class IngestionResult(BaseModel):
    document_id: str
    title: str
    chunk_count: int
    status: str
    message: str
