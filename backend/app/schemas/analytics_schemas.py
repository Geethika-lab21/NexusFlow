from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

class MetricSummary(BaseModel):
    title: str
    value: Any
    trend: Optional[str] = None
    trend_direction: Optional[str] = None  # up, down, neutral

class StageCount(BaseModel):
    stage: str
    count: int
    percentage: float

class SourceCount(BaseModel):
    source: str
    count: int
    percentage: float

class ConversionTrendPoint(BaseModel):
    month: str
    converted: int
    lost: int
    conversion_rate: float

class RecentActivityItem(BaseModel):
    id: str
    run_id: Optional[str] = None
    lead_id: str
    lead_name: str
    company: str
    action: str
    status: str
    timestamp: str

class LeadNeedingAttention(BaseModel):
    id: str
    name: str
    company: str
    priority_score: float
    priority_category: str
    conversion_probability: float
    sales_stage: str
    reason: str

class AnalyticsOverview(BaseModel):
    total_leads: int
    conversion_rate: float
    open_pipeline_count: int
    high_priority_count: int
    overdue_followups_count: int
    pending_approvals_count: int
    leads_by_stage: List[StageCount]
    leads_by_source: List[SourceCount]
    conversion_trend: List[ConversionTrendPoint]
    recent_agent_activity: List[RecentActivityItem]
    leads_needing_attention: List[LeadNeedingAttention]

class EvaluationMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion_matrix: Dict[str, int]
    class_distribution: Dict[str, int]

class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)
    id: str
    evaluation_type: str
    model_version: str
    dataset_name: str
    sample_count: int
    metrics: Dict[str, Any]
    feature_importance: Optional[List[Dict[str, Any]]] = None
    confusion_matrix: Optional[Dict[str, int]] = None
    status: str
    error_message: Optional[str] = None
    created_at: str

class SettingItem(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    category: str

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, str]
