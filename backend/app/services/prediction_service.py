import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import joblib
import pandas as pd
import numpy as np

from app.config import settings
from app.schemas.analysis_schemas import PredictionResult

logger = logging.getLogger(__name__)

COMPANY_SIZE_MAP = {
    "1-10": 1, "11-50": 2, "51-200": 3,
    "201-500": 4, "501-2000": 5, "2001+": 6
}
BUDGET_MAP = {
    "Under $5k": 1, "$5k-$20k": 2, "$20k-$50k": 3,
    "$50k-$100k": 4, "$100k+": 5
}
TIMELINE_MAP = {
    "Immediate": 5, "1-3 months": 4, "3-6 months": 3,
    "6-12 months": 2, "12+ months": 1
}


class PredictionService:
    _instance: Optional["PredictionService"] = None

    def __init__(self):
        self.model = None
        self.metadata = None
        self.load_model()

    @classmethod
    def get_instance(cls) -> "PredictionService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self):
        model_path = Path(settings.MODEL_PATH)
        meta_path = Path(settings.PREPROCESSOR_PATH)

        if model_path.exists():
            try:
                self.model = joblib.load(model_path)
                logger.info(f"Loaded ML model from {model_path}")
            except Exception as e:
                logger.error(f"Error loading model from {model_path}: {e}")
                self.model = None

        if meta_path.exists():
            try:
                with open(meta_path, "r") as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded model metadata from {meta_path}")
            except Exception as e:
                logger.error(f"Error loading metadata from {meta_path}: {e}")
                self.metadata = None

    def predict(self, lead_data: Dict[str, Any]) -> PredictionResult:
        if self.model is None:
            # Fallback heuristic calculation if model not yet trained
            eng = float(lead_data.get("engagement_score", 50.0) or 50.0)
            dm = 1.0 if lead_data.get("decision_maker_status") else 0.0
            prob = round(float(np.clip(0.3 * (eng / 100) + 0.3 * dm + 0.2, 0.05, 0.95)), 4)
            return PredictionResult(
                probability=prob,
                is_high_confidence=abs(prob - 0.5) >= 0.25,
                model_version="heuristic-fallback-1.0",
                feature_contributions=[
                    {"feature": "engagement_score", "value": eng, "direction": "positive" if eng > 50 else "negative", "weight": 0.3},
                    {"feature": "decision_maker_status", "value": dm, "direction": "positive" if dm else "negative", "weight": 0.3}
                ],
                feature_importances={}
            )

        # Feature transformations matching training pipeline
        row = {
            "engagement_score": float(lead_data.get("engagement_score", 50.0) or 50.0),
            "website_visits": int(lead_data.get("website_visits", 0) or 0),
            "email_opens": int(lead_data.get("email_opens", 0) or 0),
            "email_clicks": int(lead_data.get("email_clicks", 0) or 0),
            "meeting_count": int(lead_data.get("meeting_count", 0) or 0),
            "days_since_created": float(lead_data.get("days_since_created", 30.0) or 30.0),
            "industry": str(lead_data.get("industry", "Technology")),
            "lead_source": str(lead_data.get("lead_source", "Website Form")),
            "company_size_encoded": COMPANY_SIZE_MAP.get(str(lead_data.get("company_size")), 2),
            "budget_range_encoded": BUDGET_MAP.get(str(lead_data.get("budget_range")), 2),
            "timeline_encoded": TIMELINE_MAP.get(str(lead_data.get("purchase_timeline")), 3),
            "decision_maker_status": 1 if lead_data.get("decision_maker_status") else 0
        }

        df = pd.DataFrame([row])
        proba = float(self.model.predict_proba(df)[0, 1])
        prob_rounded = round(proba, 4)

        contributions = [
            {
                "feature": "engagement_score",
                "value": row["engagement_score"],
                "direction": "positive" if row["engagement_score"] >= 50 else "negative",
                "weight": round(abs(row["engagement_score"] - 50) / 100, 3)
            },
            {
                "feature": "decision_maker_status",
                "value": bool(row["decision_maker_status"]),
                "direction": "positive" if row["decision_maker_status"] == 1 else "negative",
                "weight": 0.25 if row["decision_maker_status"] == 1 else 0.15
            },
            {
                "feature": "budget_range",
                "value": lead_data.get("budget_range", "$5k-$20k"),
                "direction": "positive" if row["budget_range_encoded"] >= 3 else "negative",
                "weight": round(row["budget_range_encoded"] * 0.05, 3)
            },
            {
                "feature": "purchase_timeline",
                "value": lead_data.get("purchase_timeline", "1-3 months"),
                "direction": "positive" if row["timeline_encoded"] >= 4 else "negative",
                "weight": round(row["timeline_encoded"] * 0.05, 3)
            },
            {
                "feature": "meeting_count",
                "value": row["meeting_count"],
                "direction": "positive" if row["meeting_count"] > 0 else "neutral",
                "weight": 0.15 if row["meeting_count"] > 0 else 0.05
            }
        ]

        top_importances = {}
        if self.metadata and "feature_importances" in self.metadata:
            for item in self.metadata["feature_importances"][:8]:
                top_importances[item["feature"]] = item["importance"]

        version = self.metadata.get("model_version", "1.0.0") if self.metadata else "1.0.0"

        return PredictionResult(
            probability=prob_rounded,
            is_high_confidence=abs(prob_rounded - 0.5) >= 0.20,
            model_version=version,
            feature_contributions=contributions,
            feature_importances=top_importances
        )

    def get_model_metadata(self) -> Dict[str, Any]:
        if self.metadata:
            return self.metadata
        return {
            "model_type": "Not Loaded",
            "model_version": "none",
            "threshold": 0.5,
            "metrics": {}
        }
