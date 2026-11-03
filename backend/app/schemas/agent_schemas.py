from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AgentStepResponse(BaseModel):
    id: str
    run_id: str
    step_order: int
    node_name: str
    tool_name: Optional[str] = None
    status: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    duration_ms: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AgentRunCreate(BaseModel):
    lead_id: str
    requested_by: str = "user"
    trigger_source: str = "manual"

class AgentRunResponse(BaseModel):
    id: str
    lead_id: str
    requested_by: str
    status: str
    current_node: Optional[str] = None
    trigger_source: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    skip_reason: Optional[str] = None
    error_message: Optional[str] = None
    metadata_json: Optional[str] = None
    steps: List[AgentStepResponse] = []

    class Config:
        from_attributes = True

class AgentRunDetailResponse(AgentRunResponse):
    lead_name: Optional[str] = None
    lead_company: Optional[str] = None

class PaginatedAgentRunsResponse(BaseModel):
    items: List[AgentRunResponse]
    total: int
    skip: int
    limit: int
