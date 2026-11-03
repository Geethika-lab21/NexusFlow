from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from app.db.database import get_db
from app.models.orm_models import LeadAnalysis, Lead
from app.schemas.analysis_schemas import LeadAnalysisResponse, PredictionResult, ScoringResult
from app.services.lead_service import LeadService
from app.services.scoring_service import ScoringService
from app.services.prediction_service import PredictionService
from app.core.exceptions import NotFoundException
from app.utils.helpers import safe_json_loads

router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.get("/leads/{lead_id}", response_model=Optional[LeadAnalysisResponse])
def get_latest_lead_analysis(lead_id: str, db: Session = Depends(get_db)):
    # Verify lead exists
    LeadService.get_lead_by_id(db, lead_id)

    analysis = (
        db.query(LeadAnalysis)
        .filter(LeadAnalysis.lead_id == lead_id)
        .order_by(desc(LeadAnalysis.created_at))
        .first()
    )
    if not analysis:
        return None

    return LeadAnalysisResponse(
        id=analysis.id,
        lead_id=analysis.lead_id,
        conversion_probability=analysis.conversion_probability,
        priority_score=analysis.priority_score,
        priority_category=analysis.priority_category,
        positive_indicators=safe_json_loads(analysis.positive_indicators, []),
        negative_indicators=safe_json_loads(analysis.negative_indicators, []),
        missing_information=safe_json_loads(analysis.missing_information, []),
        feature_contributions=safe_json_loads(analysis.feature_contributions, []),
        recommended_action=analysis.recommended_action,
        action_rationale=analysis.action_rationale,
        model_version=analysis.model_version,
        created_at=analysis.created_at
    )


@router.post("/leads/{lead_id}/score", response_model=ScoringResult)
def calculate_lead_score(lead_id: str, db: Session = Depends(get_db)):
    lead = LeadService.get_lead_by_id(db, lead_id)
    return ScoringService.calculate_priority_score(lead)


@router.post("/leads/{lead_id}/predict", response_model=PredictionResult)
def predict_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = LeadService.get_lead_by_id(db, lead_id)
    pred_service = PredictionService.get_instance()
    lead_dict = {
        "engagement_score": lead.engagement_score,
        "website_visits": lead.website_visits,
        "email_opens": lead.email_opens,
        "email_clicks": lead.email_clicks,
        "meeting_count": lead.meeting_count,
        "industry": lead.industry,
        "lead_source": lead.lead_source,
        "company_size": lead.company_size,
        "budget_range": lead.budget_range,
        "purchase_timeline": lead.purchase_timeline,
        "decision_maker_status": lead.decision_maker_status
    }
    return pred_service.predict(lead_dict)
