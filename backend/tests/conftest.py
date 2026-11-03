import pytest
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.db.database import SessionLocal, engine, Base
from app.models.orm_models import Lead

@pytest.fixture(scope="session")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def sample_lead_dict():
    return {
        "first_name": "Alex",
        "last_name": "Morgan",
        "email": "alex.morgan@techcorp.com",
        "phone": "+1-555-0199",
        "company": "TechCorp Global",
        "title": "VP of Revenue Operations",
        "industry": "Technology",
        "company_size": "201-500",
        "country": "USA",
        "lead_source": "Website Form",
        "lead_status": "New",
        "sales_stage": "Qualified",
        "budget_range": "$50k-$100k",
        "purchase_timeline": "1-3 months",
        "decision_maker_status": True,
        "pain_points": "Manual data entry bottlenecks SDR response latency.",
        "product_interest": "NexusFlow Sales Intelligence Cloud",
        "business_need": "Automate sales qualification workflows and reduce customer response latency.",
        "engagement_score": 88.5,
        "website_visits": 12,
        "email_opens": 8,
        "email_clicks": 4,
        "meeting_count": 2,
        "is_converted": False
    }
