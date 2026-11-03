from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from app.db.database import get_db
from app.models.orm_models import EvaluationRun
from app.schemas.analytics_schemas import EvaluationRunResponse
from app.evaluation.evaluator import SystemEvaluator
from app.utils.helpers import safe_json_loads

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.post("/run", response_model=EvaluationRunResponse)
def trigger_evaluation(db: Session = Depends(get_db)):
    eval_record = SystemEvaluator.run_full_evaluation(db)
    return EvaluationRunResponse(
        id=eval_record.id,
        evaluation_type=eval_record.evaluation_type,
        model_version=eval_record.model_version,
        dataset_name=eval_record.dataset_name,
        sample_count=eval_record.sample_count,
        metrics=safe_json_loads(eval_record.metrics, {}),
        feature_importance=safe_json_loads(eval_record.feature_importance, []),
        confusion_matrix=safe_json_loads(eval_record.confusion_matrix, {}),
        status=eval_record.status,
        error_message=eval_record.error_message,
        created_at=eval_record.created_at.isoformat()
    )


@router.get("/latest", response_model=Optional[EvaluationRunResponse])
def get_latest_evaluation(db: Session = Depends(get_db)):
    eval_record = db.query(EvaluationRun).order_by(desc(EvaluationRun.created_at)).first()
    if not eval_record:
        # Trigger an evaluation if none exists
        eval_record = SystemEvaluator.run_full_evaluation(db)

    return EvaluationRunResponse(
        id=eval_record.id,
        evaluation_type=eval_record.evaluation_type,
        model_version=eval_record.model_version,
        dataset_name=eval_record.dataset_name,
        sample_count=eval_record.sample_count,
        metrics=safe_json_loads(eval_record.metrics, {}),
        feature_importance=safe_json_loads(eval_record.feature_importance, []),
        confusion_matrix=safe_json_loads(eval_record.confusion_matrix, {}),
        status=eval_record.status,
        error_message=eval_record.error_message,
        created_at=eval_record.created_at.isoformat()
    )


@router.get("/history", response_model=List[EvaluationRunResponse])
def get_evaluation_history(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    runs = db.query(EvaluationRun).order_by(desc(EvaluationRun.created_at)).limit(limit).all()
    return [
        EvaluationRunResponse(
            id=r.id,
            evaluation_type=r.evaluation_type,
            model_version=r.model_version,
            dataset_name=r.dataset_name,
            sample_count=r.sample_count,
            metrics=safe_json_loads(r.metrics, {}),
            feature_importance=safe_json_loads(r.feature_importance, []),
            confusion_matrix=safe_json_loads(r.confusion_matrix, {}),
            status=r.status,
            error_message=r.error_message,
            created_at=r.created_at.isoformat()
        )
        for r in runs
    ]
