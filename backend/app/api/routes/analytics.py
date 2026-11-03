from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics_schemas import AnalyticsOverview

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(db: Session = Depends(get_db)):
    return AnalyticsService.get_overview_metrics(db)
