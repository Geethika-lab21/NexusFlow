import json
from app.db.database import Base, engine, SessionLocal
from app.models.orm_models import AppSettings
from app.config import settings

def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        defaults = [
            ("llm_provider", settings.LLM_PROVIDER, "LLM inference provider (demo or openai)", "llm"),
            ("openai_model", settings.OPENAI_MODEL, "OpenAI model name if openai provider chosen", "llm"),
            ("high_priority_threshold", str(settings.HIGH_PRIORITY_THRESHOLD), "Priority score threshold for High category", "scoring"),
            ("medium_priority_threshold", str(settings.MEDIUM_PRIORITY_THRESHOLD), "Priority score threshold for Medium category", "scoring"),
            ("weight_engagement", str(settings.WEIGHT_ENGAGEMENT), "Weight for engagement score", "scoring"),
            ("weight_budget_fit", str(settings.WEIGHT_BUDGET_FIT), "Weight for budget fit score", "scoring"),
            ("weight_timeline", str(settings.WEIGHT_TIMELINE), "Weight for purchase timeline score", "scoring"),
            ("weight_decision_maker", str(settings.WEIGHT_DECISION_MAKER), "Weight for decision maker status", "scoring"),
            ("weight_product_fit", str(settings.WEIGHT_PRODUCT_FIT), "Weight for product fit score", "scoring"),
            ("weight_recent_activity", str(settings.WEIGHT_RECENT_ACTIVITY), "Weight for recent activity score", "scoring"),
            ("chunk_size", str(settings.CHUNK_SIZE), "RAG text chunk size in characters", "rag"),
            ("chunk_overlap", str(settings.CHUNK_OVERLAP), "RAG text chunk overlap in characters", "rag"),
            ("top_k_final", str(settings.TOP_K_FINAL), "Number of hybrid search passages to return", "rag"),
            ("max_followups_per_week", str(settings.MAX_FOLLOWUPS_PER_WEEK), "Max followups per lead per 7 days", "policy"),
            ("require_approval", "true" if settings.REQUIRE_APPROVAL else "false", "Whether SDR follow-up drafts require approval", "policy"),
        ]
        
        for key, val, desc, cat in defaults:
            existing = db.query(AppSettings).filter(AppSettings.key == key).first()
            if not existing:
                setting = AppSettings(key=key, value=val, description=desc, category=cat)
                db.add(setting)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")
