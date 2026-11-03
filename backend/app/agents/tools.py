import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.orm_models import (
    Lead, Interaction, LeadAnalysis, FollowUpDraft, AgentRun, AppSettings
)
from app.services.scoring_service import ScoringService
from app.services.prediction_service import PredictionService
from app.services.retrieval_service import RetrievalService
from app.utils.helpers import safe_json_dumps, safe_json_loads

logger = logging.getLogger(__name__)


# 1. get_lead
def get_lead(lead_id: str, db: Session) -> Optional[Dict[str, Any]]:
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return None
    return {
        "id": lead.id,
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "email": lead.email,
        "phone": lead.phone,
        "company": lead.company,
        "title": lead.title,
        "industry": lead.industry,
        "company_size": lead.company_size,
        "country": lead.country,
        "lead_source": lead.lead_source,
        "lead_status": lead.lead_status,
        "sales_stage": lead.sales_stage,
        "budget_range": lead.budget_range,
        "purchase_timeline": lead.purchase_timeline,
        "decision_maker_status": lead.decision_maker_status,
        "pain_points": lead.pain_points,
        "product_interest": lead.product_interest,
        "business_need": lead.business_need,
        "engagement_score": lead.engagement_score,
        "website_visits": lead.website_visits,
        "email_opens": lead.email_opens,
        "email_clicks": lead.email_clicks,
        "meeting_count": lead.meeting_count,
        "is_converted": lead.is_converted,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None
    }


# 2. get_interaction_history
def get_interaction_history(lead_id: str, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
    interactions = (
        db.query(Interaction)
        .filter(Interaction.lead_id == lead_id)
        .order_by(Interaction.occurred_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": i.id,
            "lead_id": i.lead_id,
            "interaction_type": i.interaction_type,
            "direction": i.direction,
            "subject": i.subject,
            "content": i.content,
            "occurred_at": i.occurred_at.isoformat() if i.occurred_at else None,
            "created_at": i.created_at.isoformat() if i.created_at else None
        }
        for i in interactions
    ]


# 3. search_knowledge_base
def search_knowledge_base(query: str, filters: Optional[Dict[str, Any]] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    retrieval_service = RetrievalService.get_instance()
    category = filters.get("category") if filters else None
    chunks = retrieval_service.search(query=query, top_k=top_k, category=category)
    return [chunk.model_dump() for chunk in chunks]


# 4. predict_conversion_probability
def predict_conversion_probability(lead_features: Dict[str, Any]) -> Dict[str, Any]:
    pred_service = PredictionService.get_instance()
    res = pred_service.predict(lead_features)
    return res.model_dump()


# 5. calculate_lead_priority
def calculate_lead_priority(lead_dict: Dict[str, Any]) -> Dict[str, Any]:
    res = ScoringService.calculate_priority_score(lead_dict)
    return res.model_dump()


# 6. save_lead_analysis
def save_lead_analysis(analysis_data: Dict[str, Any], db: Session) -> str:
    analysis_id = str(uuid.uuid4())
    record = LeadAnalysis(
        id=analysis_id,
        lead_id=analysis_data["lead_id"],
        conversion_probability=float(analysis_data["conversion_probability"]),
        priority_score=float(analysis_data["priority_score"]),
        priority_category=str(analysis_data["priority_category"]),
        positive_indicators=safe_json_dumps(analysis_data.get("positive_indicators", [])),
        negative_indicators=safe_json_dumps(analysis_data.get("negative_indicators", [])),
        missing_information=safe_json_dumps(analysis_data.get("missing_information", [])),
        feature_contributions=safe_json_dumps(analysis_data.get("feature_contributions", [])),
        recommended_action=str(analysis_data.get("recommended_action", "Send Follow-up")),
        action_rationale=str(analysis_data.get("action_rationale", "")),
        model_version=str(analysis_data.get("model_version", "1.0.0"))
    )
    db.add(record)
    db.commit()
    return analysis_id


# 7. create_follow_up_draft
def create_follow_up_draft(draft_data: Dict[str, Any], db: Session) -> str:
    draft_id = str(uuid.uuid4())
    record = FollowUpDraft(
        id=draft_id,
        lead_id=draft_data["lead_id"],
        agent_run_id=draft_data.get("agent_run_id"),
        channel=draft_data.get("channel", "email"),
        subject=draft_data.get("subject"),
        body=draft_data["body"],
        personalization_points=safe_json_dumps(draft_data.get("personalization_points", [])),
        rationale=draft_data.get("rationale", ""),
        source_references=safe_json_dumps(draft_data.get("source_references", [])),
        call_to_action=draft_data.get("call_to_action"),
        status=draft_data.get("status", "pending_approval")
    )
    db.add(record)
    db.commit()
    return draft_id


# 8. update_follow_up_draft
def update_follow_up_draft(draft_id: str, updates: Dict[str, Any], db: Session) -> Optional[Dict[str, Any]]:
    draft = db.query(FollowUpDraft).filter(FollowUpDraft.id == draft_id).first()
    if not draft:
        return None
    for k, v in updates.items():
        if hasattr(draft, k):
            if k in ["personalization_points", "source_references"] and isinstance(v, (list, dict)):
                setattr(draft, k, safe_json_dumps(v))
            else:
                setattr(draft, k, v)
    draft.updated_at = datetime.utcnow()
    db.commit()
    return {
        "id": draft.id,
        "lead_id": draft.lead_id,
        "status": draft.status,
        "subject": draft.subject,
        "body": draft.body
    }


# 9. check_contact_policy
def check_contact_policy(lead_id: str, db: Session) -> Dict[str, Any]:
    # Check max followups in the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_interactions = (
        db.query(Interaction)
        .filter(
            Interaction.lead_id == lead_id,
            Interaction.direction == "outbound",
            Interaction.occurred_at >= seven_days_ago
        )
        .count()
    )

    limit_setting = db.query(AppSettings).filter(AppSettings.key == "max_followups_per_week").first()
    max_limit = int(limit_setting.value) if limit_setting else 2

    if recent_interactions >= max_limit:
        return {
            "allowed": False,
            "reason": f"Contact frequency limit exceeded: {recent_interactions}/{max_limit} outbound contacts in the last 7 days.",
            "recent_contacts": recent_interactions
        }
    return {
        "allowed": True,
        "reason": f"Contact frequency policy passed ({recent_interactions}/{max_limit} contacts used).",
        "recent_contacts": recent_interactions
    }


# 10. record_approval
def record_approval(draft_id: str, decision: str, approved_by: str, db: Session) -> Dict[str, Any]:
    draft = db.query(FollowUpDraft).filter(FollowUpDraft.id == draft_id).first()
    if not draft:
        return {"success": False, "message": "Draft not found."}
    
    now = datetime.utcnow()
    if decision.lower() == "approved":
        draft.status = "approved"
        draft.approved_by = approved_by
        draft.approval_decision_at = now
    else:
        draft.status = "rejected"
        draft.rejection_reason = decision
        draft.approval_decision_at = now

    db.commit()
    return {
        "success": True,
        "draft_id": draft.id,
        "status": draft.status,
        "decision_at": now.isoformat()
    }


# 11. simulate_email_send
def simulate_email_send(draft_id: str, db: Session) -> Dict[str, Any]:
    draft = db.query(FollowUpDraft).filter(FollowUpDraft.id == draft_id).first()
    if not draft:
        return {"success": False, "simulated_at": None, "message": "Draft not found"}
    
    now = datetime.utcnow()
    draft.status = "simulated_sent"
    draft.simulated_sent_at = now
    db.commit()

    return {
        "success": True,
        "simulated_at": now.isoformat(),
        "message": f"Successfully simulated dispatch of {draft.channel} message to lead {draft.lead_id} (Demo Environment Sandbox)."
    }


# 12. log_interaction
def log_interaction(interaction_data: Dict[str, Any], db: Session) -> str:
    inter_id = str(uuid.uuid4())
    record = Interaction(
        id=inter_id,
        lead_id=interaction_data["lead_id"],
        interaction_type=interaction_data.get("interaction_type", "Email Sent"),
        direction=interaction_data.get("direction", "outbound"),
        subject=interaction_data.get("subject"),
        content=interaction_data["content"],
        occurred_at=datetime.utcnow()
    )
    db.add(record)
    db.commit()
    return inter_id


# 13. get_pipeline_metrics
def get_pipeline_metrics(db: Session) -> Dict[str, Any]:
    total_leads = db.query(Lead).count()
    converted_leads = db.query(Lead).filter(Lead.is_converted == True).count()
    open_pipeline = db.query(Lead).filter(Lead.sales_stage.notin_(["Closed Won", "Closed Lost"])).count()
    pending_approvals = db.query(FollowUpDraft).filter(FollowUpDraft.status == "pending_approval").count()

    conv_rate = round((converted_leads / total_leads * 100), 2) if total_leads > 0 else 0.0

    return {
        "total_leads": total_leads,
        "converted_leads": converted_leads,
        "conversion_rate": conv_rate,
        "open_pipeline_count": open_pipeline,
        "pending_approvals_count": pending_approvals
    }
