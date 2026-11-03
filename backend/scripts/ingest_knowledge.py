import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.db.init_db import init_db
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.retrieval_service import RetrievalService

DOCUMENT_CATEGORIES = {
    "01_product_overview.md": "Overview",
    "02_feature_documentation.md": "Product",
    "03_pricing_packaging.md": "Pricing",
    "04_enterprise_plan.md": "Enterprise",
    "05_integrations.md": "Integrations",
    "06_security_compliance.md": "Security",
    "07_sales_objections.md": "Objections",
    "08_competitor_comparison.md": "Competitive",
    "09_onboarding_guide.md": "Customer Success",
    "10_sales_playbook.md": "Playbook",
    "11_email_guidelines.md": "Guidelines",
    "12_discount_policy.md": "Policy",
    "13_case_studies.md": "Case Studies",
    "14_product_limitations.md": "Technical"
}


def ingest_all_knowledge_documents():
    init_db()
    ingestion_service = DocumentIngestionService()
    kb_dir = Path(settings.KNOWLEDGE_BASE_DIR)

    if not kb_dir.exists():
        print(f"Error: Knowledge base directory {kb_dir} does not exist.")
        return

    md_files = sorted(list(kb_dir.glob("*.md")))
    if not md_files:
        print(f"No .md files found in {kb_dir}")
        return

    print(f"Found {len(md_files)} knowledge base files. Starting ingestion...")

    total_chunks = 0
    successful_docs = 0

    for file_path in md_files:
        filename = file_path.name
        category = DOCUMENT_CATEGORIES.get(filename, "General")
        doc_title = file_path.stem.replace("_", " ").title()

        res = ingestion_service.ingest_file(
            file_path_str=str(file_path),
            category=category,
            document_name=doc_title
        )

        if res.status == "indexed":
            successful_docs += 1
            total_chunks += res.chunk_count
            print(f"  [OK] {filename:<30} -> {res.chunk_count:>2} chunks ({category})")
        else:
            print(f"  [FAIL] {filename:<28} -> {res.message}")

    # Refresh retrieval index
    retrieval_service = RetrievalService.get_instance()
    retrieval_service.refresh_bm25()

    print(f"\nIngestion Complete: {successful_docs}/{len(md_files)} documents indexed ({total_chunks} total chunks).")


if __name__ == "__main__":
    ingest_all_knowledge_documents()
