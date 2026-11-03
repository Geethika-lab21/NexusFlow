import os
import re
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict
from rank_bm25 import BM25Okapi

from app.config import settings
from app.schemas.knowledge_schemas import RetrievedChunk

logger = logging.getLogger(__name__)


def tokenize_text(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"\w+", text) if len(w) > 1]


class RetrievalService:
    _instance: Optional["RetrievalService"] = None

    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.embedding_fn = None
        self.bm25_index = None
        self.corpus_chunks: List[Dict[str, Any]] = []
        self._init_backend()

    @classmethod
    def get_instance(cls) -> "RetrievalService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_backend(self):
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            try:
                self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=settings.EMBEDDING_MODEL
                )
            except Exception:
                self.embedding_fn = None

            if self.embedding_fn:
                self.collection = self.chroma_client.get_or_create_collection(
                    name="nexusflow_kb",
                    embedding_function=self.embedding_fn
                )
            else:
                self.collection = self.chroma_client.get_or_create_collection(name="nexusflow_kb")
            
            self.refresh_bm25()
        except Exception as e:
            logger.warning(f"ChromaDB retrieval initialization fallback: {e}")
            self.chroma_client = None
            self.collection = None
            self.refresh_bm25()

    def refresh_bm25(self):
        """Loads all documents from ChromaDB and builds BM25 index."""
        self.corpus_chunks = []
        if self.collection is not None:
            try:
                all_data = self.collection.get()
                ids = all_data.get("ids", [])
                docs = all_data.get("documents", [])
                metas = all_data.get("metadatas", [])

                for chunk_id, text, meta in zip(ids, docs, metas):
                    self.corpus_chunks.append({
                        "chunk_id": chunk_id,
                        "text": text,
                        "document_id": meta.get("document_id", ""),
                        "document_name": meta.get("document_name", "Unknown"),
                        "category": meta.get("category", "General"),
                        "source": meta.get("source", "")
                    })
            except Exception as e:
                logger.error(f"Error fetching docs for BM25: {e}")

        if self.corpus_chunks:
            tokenized_corpus = [tokenize_text(c["text"]) for c in self.corpus_chunks]
            self.bm25_index = BM25Okapi(tokenized_corpus)
            logger.info(f"Built BM25 index over {len(self.corpus_chunks)} chunks.")
        else:
            self.bm25_index = None

    def search_semantic(self, query: str, top_k: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        if self.collection is None:
            return results

        try:
            where_filter = {"category": category} if category else None
            query_results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, max(1, self.collection.count())),
                where=where_filter
            )

            ids = query_results.get("ids", [[]])[0]
            docs = query_results.get("documents", [[]])[0]
            metas = query_results.get("metadatas", [[]])[0]
            distances = query_results.get("distances", [[]])[0] if "distances" in query_results else [0.0] * len(ids)

            for chunk_id, text, meta, dist in zip(ids, docs, metas, distances):
                # Convert cosine distance to similarity score
                sim = max(0.0, 1.0 - (dist if dist is not None else 0.5))
                results.append({
                    "chunk_id": chunk_id,
                    "text": text,
                    "document_id": meta.get("document_id", ""),
                    "document_name": meta.get("document_name", ""),
                    "category": meta.get("category", ""),
                    "semantic_score": round(sim, 4)
                })
        except Exception as e:
            logger.error(f"Error during semantic query: {e}")

        return results

    def search_bm25(self, query: str, top_k: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.bm25_index or not self.corpus_chunks:
            return []

        tokens = tokenize_text(query)
        if not tokens:
            return []

        raw_scores = self.bm25_index.get_scores(tokens)
        scored_pairs = list(enumerate(raw_scores))
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_pairs:
            chunk = self.corpus_chunks[idx]
            if category and chunk.get("category") != category:
                continue
            if score <= 0:
                continue
            results.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "document_id": chunk["document_id"],
                "document_name": chunk["document_name"],
                "category": chunk["category"],
                "bm25_score": round(float(score), 4)
            })
            if len(results) >= top_k:
                break

        return results

    def search(self, query: str, top_k: int = 5, category: Optional[str] = None) -> List[RetrievedChunk]:
        """Hybrid search combining Semantic and BM25 using Reciprocal Rank Fusion (RRF)."""
        if not self.corpus_chunks and self.collection is not None:
            self.refresh_bm25()

        semantic_hits = self.search_semantic(query, top_k=top_k * 2, category=category)
        bm25_hits = self.search_bm25(query, top_k=top_k * 2, category=category)

        # Reciprocal Rank Fusion (RRF) with constant k=60
        K_RRF = 60
        rrf_scores = defaultdict(float)
        chunk_map = {}

        # Process semantic ranks
        for rank, hit in enumerate(semantic_hits, start=1):
            cid = hit["chunk_id"]
            rrf_scores[cid] += 1.0 / (K_RRF + rank)
            if cid not in chunk_map:
                chunk_map[cid] = hit.copy()
            chunk_map[cid]["semantic_score"] = hit.get("semantic_score")

        # Process BM25 ranks
        for rank, hit in enumerate(bm25_hits, start=1):
            cid = hit["chunk_id"]
            rrf_scores[cid] += 1.0 / (K_RRF + rank)
            if cid not in chunk_map:
                chunk_map[cid] = hit.copy()
            chunk_map[cid]["bm25_score"] = hit.get("bm25_score")

        # If no hits from either, return empty
        if not rrf_scores:
            return []

        # Sort by final RRF score descending
        sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        final_chunks: List[RetrievedChunk] = []
        for cid in sorted_cids[:top_k]:
            data = chunk_map[cid]
            final_chunks.append(
                RetrievedChunk(
                    chunk_id=cid,
                    document_id=data.get("document_id", ""),
                    document_name=data.get("document_name", ""),
                    category=data.get("category", "General"),
                    text=data.get("text", ""),
                    semantic_score=data.get("semantic_score"),
                    bm25_score=data.get("bm25_score"),
                    rrf_score=round(rrf_scores[cid], 5),
                    retrieval_method="hybrid_rrf"
                )
            )

        return final_chunks
