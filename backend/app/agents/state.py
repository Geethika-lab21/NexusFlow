from typing import TypedDict, Optional, List, Any
from datetime import datetime

class AgentState(TypedDict):
    # Input
    lead_id: str
    run_id: str
    requested_by: str
    
    # Lead data
    lead: Optional[dict]
    interactions: List[dict]
    existing_analyses: List[dict]
    existing_drafts: List[dict]
    
    # Intelligence
    conversion_probability: Optional[float]
    priority_score: Optional[float]
    priority_category: Optional[str]
    positive_indicators: List[str]
    negative_indicators: List[str]
    missing_information: List[str]
    feature_contributions: List[dict]
    
    # Retrieval
    retrieval_query: Optional[str]
    retrieved_chunks: List[dict]
    source_ids: List[str]
    
    # Decision
    recommended_action: Optional[str]
    action_rationale: Optional[str]
    
    # Draft
    draft: Optional[dict]
    draft_id: Optional[str]
    channel: Optional[str]
    
    # Workflow control
    current_node: str
    errors: List[str]
    warnings: List[str]
    requires_human_approval: bool
    approval_status: Optional[str]
    skip_reason: Optional[str]
    retry_count: int
    
    # Metadata
    llm_mode: str
    started_at: str
    completed_at: Optional[str]
    step_traces: List[dict]
