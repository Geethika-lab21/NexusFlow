from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class FeatureContribution(BaseModel):
    feature: str
    value: Any
    direction: str  # positive, negative, neutral
    weight: float

class LeadAnalysisBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    lead_id: str
    conversion_probability: float = Field(..., ge=0.0, le=1.0)
    priority_score: float = Field(..., ge=0.0, le=100.0)
    priority_category: str  # high, medium, low
    positive_indicators: List[str] = []
    negative_indicators: List[str] = []
    missing_information: List[str] = []
    feature_contributions: List[FeatureContribution] = []
    recommended_action: str
    action_rationale: str
    model_version: str = "1.0.0"

class LeadAnalysisCreate(LeadAnalysisBase):
    pass

class LeadAnalysisResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)
    id: str
    lead_id: str
    conversion_probability: float
    priority_score: float
    priority_category: str
    positive_indicators: List[str]
    negative_indicators: List[str]
    missing_information: List[str]
    feature_contributions: List[Dict[str, Any]]
    recommended_action: str
    action_rationale: str
    model_version: str
    created_at: datetime

class ScoringResult(BaseModel):
    score: float
    category: str
    breakdown: Dict[str, float]
    weights: Dict[str, float]

class PredictionResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    probability: float
    is_high_confidence: bool
    model_version: str
    feature_contributions: List[Dict[str, Any]]
    feature_importances: Optional[Dict[str, float]] = None
