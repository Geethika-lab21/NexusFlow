from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class FollowUpDraftBase(BaseModel):
    lead_id: str
    agent_run_id: Optional[str] = None
    channel: str = "email"
    subject: Optional[str] = None
    body: str
    personalization_points: List[str] = []
    rationale: str = ""
    source_references: List[Dict[str, Any]] = []
    call_to_action: Optional[str] = None
    status: str = "pending_approval"

class FollowUpDraftCreate(FollowUpDraftBase):
    pass

class FollowUpDraftUpdate(BaseModel):
    channel: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    personalization_points: Optional[List[str]] = None
    call_to_action: Optional[str] = None
    status: Optional[str] = None

class ApprovalRequest(BaseModel):
    approved_by: str = "Sales Manager"

class RejectionRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)

class FollowUpDraftResponse(BaseModel):
    id: str
    lead_id: str
    agent_run_id: Optional[str] = None
    channel: str
    subject: Optional[str] = None
    body: str
    personalization_points: List[str]
    rationale: str
    source_references: List[Dict[str, Any]]
    call_to_action: Optional[str] = None
    status: str
    approved_by: Optional[str] = None
    approval_decision_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    simulated_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lead_name: Optional[str] = None
    lead_company: Optional[str] = None

    class Config:
        from_attributes = True

class PaginatedDraftsResponse(BaseModel):
    items: List[FollowUpDraftResponse]
    total: int
    skip: int
    limit: int
