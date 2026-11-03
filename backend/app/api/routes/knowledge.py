import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from app.db.database import get_db
from app.models.orm_models import KnowledgeDocument
from app.schemas.knowledge_schemas import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeDocumentResponse,
    IngestionResult
)
from app.services.retrieval_service import RetrievalService
from app.services.document_ingestion_service import DocumentIngestionService
from app.config import settings
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(req: KnowledgeSearchRequest):
    retrieval_service = RetrievalService.get_instance()
    results = retrieval_service.search(
        query=req.query,
        top_k=req.top_k,
        category=req.category
    )
    return KnowledgeSearchResponse(
        query=req.query,
        results=results,
        total_found=len(results),
        retrieval_method="hybrid_rrf"
    )


@router.get("/documents", response_model=List[KnowledgeDocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(KnowledgeDocument).order_by(desc(KnowledgeDocument.created_at)).all()
    return docs


@router.post("/documents/upload", response_model=IngestionResult)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("General"),
    db: Session = Depends(get_db)
):
    upload_dir = Path(settings.KNOWLEDGE_BASE_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    dest_file = upload_dir / file.filename
    with open(dest_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ingestion_service = DocumentIngestionService()
    result = ingestion_service.ingest_file(
        file_path_str=str(dest_file),
        category=category,
        document_name=dest_file.stem.replace("_", " ").title()
    )

    # Refresh BM25
    retrieval_service = RetrievalService.get_instance()
    retrieval_service.refresh_bm25()

    return result


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise NotFoundException(f"Document with ID {doc_id} not found.")

    db.delete(doc)
    db.commit()

    retrieval_service = RetrievalService.get_instance()
    retrieval_service.refresh_bm25()
    return None
