from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # App
    APP_NAME: str = "NexusFlow Sales Intelligence"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR.as_posix()}/data/nexusflow.db"
    
    # LLM Provider
    LLM_PROVIDER: str = "demo"  # "demo" or "openai"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 2
    
    # Vector Store
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chroma_db")
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # RAG
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_SEMANTIC: int = 5
    TOP_K_BM25: int = 5
    TOP_K_FINAL: int = 5
    
    # ML
    MODEL_PATH: str = str(BASE_DIR / "artifacts" / "lead_model.joblib")
    PREPROCESSOR_PATH: str = str(BASE_DIR / "artifacts" / "preprocessor_meta.json")
    MODEL_VERSION: str = "1.0.0"
    
    # Lead Scoring Weights (sum to 1.0)
    WEIGHT_ENGAGEMENT: float = 0.25
    WEIGHT_BUDGET_FIT: float = 0.20
    WEIGHT_TIMELINE: float = 0.15
    WEIGHT_DECISION_MAKER: float = 0.15
    WEIGHT_PRODUCT_FIT: float = 0.15
    WEIGHT_RECENT_ACTIVITY: float = 0.10
    
    # Priority Thresholds
    HIGH_PRIORITY_THRESHOLD: float = 65.0
    MEDIUM_PRIORITY_THRESHOLD: float = 40.0
    
    # Follow-up
    MAX_FOLLOWUPS_PER_WEEK: int = 2
    REQUIRE_APPROVAL: bool = True
    
    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Data paths
    SYNTHETIC_DATA_DIR: str = str(BASE_DIR / "data" / "synthetic")
    KNOWLEDGE_BASE_DIR: str = str(BASE_DIR / "data" / "knowledge_base")
    EVALUATION_DATA_DIR: str = str(BASE_DIR / "data" / "evaluation")
    ARTIFACTS_DIR: str = str(BASE_DIR / "artifacts")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
