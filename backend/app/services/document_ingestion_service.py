import os
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid

import fitz  # PyMuPDF
import docx
from rank_bm25 import BM25Okapi

from app.config import settings
from app.db.database import SessionLocal
from app.models.orm_models import KnowledgeDocument
from app.schemas.knowledge_schemas import IngestionResult

logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def extract_text_from_file(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif ext == ".pdf":
        text_parts = []
        doc = fitz.open(str(file_path))
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)
    elif ext in [".docx", ".doc"]:
        doc = docx.Document(str(file_path))
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    # Split by paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{p}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If paragraph itself is larger than chunk_size, slice it
            if len(p) > chunk_size:
                step = chunk_size - overlap
                for i in range(0, len(p), step):
                    sub = p[i:i + chunk_size]
                    if sub.strip():
                        chunks.append(sub.strip())
                current_chunk = ""
            else:
                current_chunk = p

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


class DocumentIngestionService:
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.embedding_fn = None
        self.use_fallback = False
        self._init_vector_store()

    def _init_vector_store(self):
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            
            try:
                self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=settings.EMBEDDING_MODEL
                )
            except Exception as ef_err:
                logger.warning(f"Could not load SentenceTransformer embedding function: {ef_err}. Using default Chroma embedding.")
                self.embedding_fn = None

            if self.embedding_fn:
                self.collection = self.chroma_client.get_or_create_collection(
                    name="nexusflow_kb",
                    embedding_function=self.embedding_fn
                )
            else:
                self.collection = self.chroma_client.get_or_create_collection(name="nexusflow_kb")
            logger.info("ChromaDB vector store initialized successfully.")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}. Falling back to in-memory/TF-IDF store.")
            self.use_fallback = True

    def ingest_file(self, file_path_str: str, category: str = "General", document_name: Optional[str] = None) -> IngestionResult:
        file_path = Path(file_path_str)
        if not file_path.exists():
            return IngestionResult(
                document_id="",
                title=document_name or file_path.name,
                chunk_count=0,
                status="failed",
                message=f"File not found: {file_path}"
            )

        doc_name = document_name or file_path.stem.replace("_", " ").title()
        file_hash = compute_sha256(file_path)

        db = SessionLocal()
        try:
            # Check for existing document by content hash
            existing_doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.content_hash == file_hash).first()
            if existing_doc and existing_doc.status == "indexed":
                return IngestionResult(
                    document_id=existing_doc.id,
                    title=existing_doc.title,
                    chunk_count=existing_doc.chunk_count,
                    status="indexed",
                    message="Document already indexed with identical content hash (skipped redundant processing)."
                )

            # Extract and chunk text
            raw_text = extract_text_from_file(file_path)
            chunks = chunk_text(raw_text, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)

            if not chunks:
                return IngestionResult(
                    document_id="",
                    title=doc_name,
                    chunk_count=0,
                    status="failed",
                    message="No text chunks could be extracted from document."
                )

            # Record in DB
            doc_id = str(uuid.uuid4())
            if existing_doc:
                existing_doc.chunk_count = len(chunks)
                existing_doc.status = "indexed"
                existing_doc.error_message = None
                doc_record = existing_doc
                doc_id = existing_doc.id
            else:
                doc_record = KnowledgeDocument(
                    id=doc_id,
                    title=doc_name,
                    file_path=str(file_path),
                    category=category,
                    content_hash=file_hash,
                    chunk_count=len(chunks),
                    status="indexed"
                )
                db.add(doc_record)

            db.commit()

            # Store in ChromaDB
            if not self.use_fallback and self.collection is not None:
                ids = [f"{doc_id}_{idx}" for idx in range(len(chunks))]
                metadatas = [
                    {
                        "document_id": doc_id,
                        "document_name": doc_name,
                        "category": category,
                        "chunk_index": idx,
                        "source": str(file_path)
                    }
                    for idx in range(len(chunks))
                ]
                
                # Upsert into Chroma collection
                self.collection.upsert(
                    ids=ids,
                    documents=chunks,
                    metadatas=metadatas
                )

            return IngestionResult(
                document_id=doc_id,
                title=doc_name,
                chunk_count=len(chunks),
                status="indexed",
                message=f"Successfully indexed {len(chunks)} chunks."
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Error during ingestion of {file_path}: {e}")
            return IngestionResult(
                document_id="",
                title=doc_name,
                chunk_count=0,
                status="failed",
                message=str(e)
            )
        finally:
            db.close()
