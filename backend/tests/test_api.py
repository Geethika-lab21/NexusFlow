import uuid
from datetime import datetime, timedelta

from app.models.orm_models import Lead, LeadAnalysis
from app.services.prediction_service import PredictionService

def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "app_name" in data

def test_leads_crud(client, sample_lead_dict):
    lead_data = sample_lead_dict.copy()
    lead_data["email"] = f"api_test_{uuid.uuid4().hex[:6]}@example.com"

    # Create
    resp = client.post("/api/leads", json=lead_data)
    assert resp.status_code == 201
    created = resp.json()
    lead_id = created["id"]
    assert created["company"] == lead_data["company"]

    # Read
    resp = client.get(f"/api/leads/{lead_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == lead_id

    # Update
    resp = client.patch(f"/api/leads/{lead_id}", json={"title": "Chief Revenue Officer"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Chief Revenue Officer"

    # List
    resp = client.get("/api/leads?limit=5")
    assert resp.status_code == 200
    assert "items" in resp.json()
    assert resp.json()["total"] > 0


def test_lead_detail_returns_latest_persisted_prediction_and_priority(
    client,
    db_session,
    sample_lead_dict,
):
    lead_id = str(uuid.uuid4())
    lead = Lead(id=lead_id, **{
        **sample_lead_dict,
        "email": f"detail_analysis_{uuid.uuid4().hex}@example.com",
    })
    db_session.add(lead)
    db_session.flush()

    older_analysis = LeadAnalysis(
        lead_id=lead_id,
        conversion_probability=0.42,
        priority_score=55.0,
        priority_category="medium",
        recommended_action="Send Personalized Follow-Up Email",
        action_rationale="Older analysis.",
        created_at=datetime.utcnow() - timedelta(minutes=1),
    )
    latest_analysis = LeadAnalysis(
        lead_id=lead_id,
        conversion_probability=0.8388,
        priority_score=91.38,
        priority_category="high",
        recommended_action="Schedule Technical Architecture Demo",
        action_rationale="Latest analysis.",
        created_at=datetime.utcnow(),
    )
    db_session.add_all([older_analysis, latest_analysis])
    db_session.commit()

    response = client.get(f"/api/leads/{lead_id}")

    assert response.status_code == 200
    assert response.json()["conversion_probability"] == 0.8388
    assert response.json()["priority_score"] == 91.38
    assert response.json()["priority_category"] == "high"


def test_lead_detail_without_analysis_matches_lead_list_prediction(
    client,
    db_session,
    sample_lead_dict,
):
    lead_id = str(uuid.uuid4())
    lead = Lead(id=lead_id, **{
        **sample_lead_dict,
        "email": f"detail_no_analysis_{uuid.uuid4().hex}@example.com",
    })
    db_session.add(lead)
    db_session.commit()

    detail = client.get(f"/api/leads/{lead_id}")
    lead_list = client.get("/api/leads", params={"search": lead.email, "limit": 5})

    assert detail.status_code == 200
    assert lead_list.status_code == 200
    assert detail.json()["conversion_probability"] is not None
    assert detail.json()["conversion_probability"] == lead_list.json()["items"][0]["conversion_probability"]
    assert detail.json()["priority_score"] == lead_list.json()["items"][0]["priority_score"]
    assert detail.json()["priority_category"] == lead_list.json()["items"][0]["priority_category"]


def test_lead_detail_reports_unavailable_prediction_as_null(
    client,
    db_session,
    sample_lead_dict,
    monkeypatch,
):
    lead_id = str(uuid.uuid4())
    lead = Lead(id=lead_id, **{
        **sample_lead_dict,
        "email": f"detail_no_prediction_{uuid.uuid4().hex}@example.com",
    })
    db_session.add(lead)
    db_session.commit()

    class UnavailablePredictor:
        @staticmethod
        def predict(lead_data):
            return None

    monkeypatch.setattr(
        PredictionService,
        "get_instance",
        staticmethod(lambda: UnavailablePredictor()),
    )

    response = client.get(f"/api/leads/{lead_id}")

    assert response.status_code == 200
    assert response.json()["conversion_probability"] is None

def test_analytics_overview(client):
    resp = client.get("/api/analytics/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_leads" in data
    assert "leads_by_stage" in data

def test_knowledge_search(client):
    resp = client.post("/api/knowledge/search", json={"query": "enterprise SSO", "top_k": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) > 0

def test_settings_endpoints(client):
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    assert len(resp.json()) > 0
