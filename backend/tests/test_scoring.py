from app.services.scoring_service import ScoringService

def test_high_priority_scoring(sample_lead_dict):
    res = ScoringService.calculate_priority_score(sample_lead_dict)
    assert res.score >= 65.0
    assert res.category == "high"
    assert "engagement" in res.breakdown
    assert res.breakdown["decision_maker"] == 100.0

def test_low_priority_scoring():
    low_lead = {
        "engagement_score": 10.0,
        "budget_range": "Under $5k",
        "purchase_timeline": "12+ months",
        "decision_maker_status": False,
        "pain_points": None,
        "business_need": None,
        "website_visits": 0,
        "email_opens": 0,
        "email_clicks": 0,
        "meeting_count": 0
    }
    res = ScoringService.calculate_priority_score(low_lead)
    assert res.score < 40.0
    assert res.category == "low"
    assert res.breakdown["decision_maker"] == 30.0

def test_custom_weights(sample_lead_dict):
    custom = {
        "engagement": 0.50,
        "budget_fit": 0.10,
        "timeline": 0.10,
        "decision_maker": 0.10,
        "product_fit": 0.10,
        "recent_activity": 0.10
    }
    res = ScoringService.calculate_priority_score(sample_lead_dict, custom_weights=custom)
    assert 0.0 <= res.score <= 100.0
