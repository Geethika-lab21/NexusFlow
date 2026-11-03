# NexusFlow RAG Pipeline

## Pipeline Design
The Retrieval-Augmented Generation pipeline powers grounded sales outreach and objection handling by searching authoritative company collateral.

### Ingestion
1. Multi-format support: Markdown (`.md`), plain text (`.txt`), PDF (`.pdf`), Word (`.docx`).
2. Content-hash deduplication (SHA-256) preventing redundant chunks.
3. Paragraph-aware chunking with target chunk size (500 chars) and overlap (50 chars).
4. Metadata association (document ID, chunk index, title, category, source).

### Hybrid Retrieval
- **Dense Semantic Retrieval**: Vector cosine similarity over document embeddings.
- **Sparse BM25 Lexical Retrieval**: BM25Okapi over tokenized text chunks.
- **Fusion**: Reciprocal Rank Fusion (RRF) with constant `k=60`:
  $$RRF\_Score(d) = \sum_{m \in \{semantic, bm25\}} \frac{1}{k + rank_m(d)}$$
- Returns top ranked passages with explicit attribution citations.
