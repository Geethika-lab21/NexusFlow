from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.db.database import get_db
from app.models.orm_models import AppSettings, Lead, Interaction, FollowUpDraft, AgentRun, AgentStep, LeadAnalysis
from app.schemas.analytics_schemas import SettingItem, SettingsUpdateRequest
from app.config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=List[SettingItem])
def get_settings(db: Session = Depends(get_db)):
    items = db.query(AppSettings).all()
    return items


@router.patch("")
def update_settings(req: SettingsUpdateRequest, db: Session = Depends(get_db)):
    updated = {}
    for key, val in req.settings.items():
        record = db.query(AppSettings).filter(AppSettings.key == key).first()
        if record:
            record.value = str(val)
            updated[key] = str(val)
        else:
            new_record = AppSettings(key=key, value=str(val), category="custom")
            db.add(new_record)
            updated[key] = str(val)

    # Reflect update in runtime settings if matching
    if "llm_provider" in updated:
        settings.LLM_PROVIDER = updated["llm_provider"]
    if "openai_model" in updated:
        settings.OPENAI_MODEL = updated["openai_model"]
    if "high_priority_threshold" in updated:
        settings.HIGH_PRIORITY_THRESHOLD = float(updated["high_priority_threshold"])
    if "medium_priority_threshold" in updated:
        settings.MEDIUM_PRIORITY_THRESHOLD = float(updated["medium_priority_threshold"])
    if "weight_engagement" in updated:
        settings.WEIGHT_ENGAGEMENT = float(updated["weight_engagement"])
    if "weight_budget_fit" in updated:
        settings.WEIGHT_BUDGET_FIT = float(updated["weight_budget_fit"])
    if "weight_timeline" in updated:
        settings.WEIGHT_TIMELINE = float(updated["weight_timeline"])
    if "weight_decision_maker" in updated:
        settings.WEIGHT_DECISION_MAKER = float(updated["weight_decision_maker"])
    if "weight_product_fit" in updated:
        settings.WEIGHT_PRODUCT_FIT = float(updated["weight_product_fit"])
    if "weight_recent_activity" in updated:
        settings.WEIGHT_RECENT_ACTIVITY = float(updated["weight_recent_activity"])

    db.commit()
    return {"success": True, "updated": updated}


@router.post("/reset-dataset")
def reset_dataset(db: Session = Depends(get_db)):
    # Clear pipeline records
    db.query(AgentStep).delete()
    db.query(AgentRun).delete()
    db.query(FollowUpDraft).delete()
    db.query(LeadAnalysis).delete()
    db.query(Interaction).delete()
    db.query(Lead).delete()
    db.commit()

    # Reseed
    from scripts.seed_data import seed_database
    seed_database(db)

    return {"success": True, "message": "Dataset successfully reset and reseeded from synthetic distributions."}
