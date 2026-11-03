from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.database import get_db
from app.services.followup_service import FollowUpService
from app.schemas.followup_schemas import (
    FollowUpDraftCreate,
    FollowUpDraftUpdate,
    FollowUpDraftResponse,
    PaginatedDraftsResponse,
    ApprovalRequest,
    RejectionRequest
)
from app.utils.helpers import safe_json_loads

router = APIRouter(prefix="/follow-ups", tags=["Follow-Ups"])


@router.get("", response_model=PaginatedDraftsResponse)
def list_drafts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    lead_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    items, total = FollowUpService.get_drafts(
        db=db,
        skip=skip,
        limit=limit,
        status=status_filter,
        lead_id=lead_id
    )
    return PaginatedDraftsResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{draft_id}", response_model=FollowUpDraftResponse)
def get_draft(draft_id: str, db: Session = Depends(get_db)):
    draft = FollowUpService.get_draft_by_id(db, draft_id)
    return FollowUpDraftResponse(
        id=draft.id,
        lead_id=draft.lead_id,
        agent_run_id=draft.agent_run_id,
        channel=draft.channel,
        subject=draft.subject,
        body=draft.body,
        personalization_points=safe_json_loads(draft.personalization_points, []),
        rationale=draft.rationale,
        source_references=safe_json_loads(draft.source_references, []),
        call_to_action=draft.call_to_action,
        status=draft.status,
        approved_by=draft.approved_by,
        approval_decision_at=draft.approval_decision_at,
        rejection_reason=draft.rejection_reason,
        simulated_sent_at=draft.simulated_sent_at,
        created_at=draft.created_at,
        updated_at=draft.updated_at
    )


@router.post("", response_model=FollowUpDraftResponse, status_code=status.HTTP_201_CREATED)
def create_draft(draft_in: FollowUpDraftCreate, db: Session = Depends(get_db)):
    draft = FollowUpService.create_draft(db, draft_in)
    return FollowUpDraftResponse(
        id=draft.id,
        lead_id=draft.lead_id,
        agent_run_id=draft.agent_run_id,
        channel=draft.channel,
        subject=draft.subject,
        body=draft.body,
        personalization_points=safe_json_loads(draft.personalization_points, []),
        rationale=draft.rationale,
        source_references=safe_json_loads(draft.source_references, []),
        call_to_action=draft.call_to_action,
        status=draft.status,
        approved_by=draft.approved_by,
        approval_decision_at=draft.approval_decision_at,
        rejection_reason=draft.rejection_reason,
        simulated_sent_at=draft.simulated_sent_at,
        created_at=draft.created_at,
        updated_at=draft.updated_at
    )


@router.patch("/{draft_id}", response_model=FollowUpDraftResponse)
def update_draft(draft_id: str, updates: FollowUpDraftUpdate, db: Session = Depends(get_db)):
    draft = FollowUpService.update_draft(db, draft_id, updates)
    return FollowUpDraftResponse(
        id=draft.id,
        lead_id=draft.lead_id,
        agent_run_id=draft.agent_run_id,
        channel=draft.channel,
        subject=draft.subject,
        body=draft.body,
        personalization_points=safe_json_loads(draft.personalization_points, []),
        rationale=draft.rationale,
        source_references=safe_json_loads(draft.source_references, []),
        call_to_action=draft.call_to_action,
        status=draft.status,
        approved_by=draft.approved_by,
        approval_decision_at=draft.approval_decision_at,
        rejection_reason=draft.rejection_reason,
        simulated_sent_at=draft.simulated_sent_at,
        created_at=draft.created_at,
        updated_at=draft.updated_at
    )


@router.post("/{draft_id}/approve")
def approve_draft(draft_id: str, req: ApprovalRequest, db: Session = Depends(get_db)):
    draft = FollowUpService.approve_draft(db, draft_id, approved_by=req.approved_by)
    return {"success": True, "draft_id": draft.id, "status": draft.status, "approved_by": draft.approved_by}


@router.post("/{draft_id}/reject")
def reject_draft(draft_id: str, req: RejectionRequest, db: Session = Depends(get_db)):
    draft = FollowUpService.reject_draft(db, draft_id, reason=req.reason)
    return {"success": True, "draft_id": draft.id, "status": draft.status, "rejection_reason": draft.rejection_reason}


@router.post("/{draft_id}/simulate-send")
def simulate_send_draft(draft_id: str, db: Session = Depends(get_db)):
    res = FollowUpService.simulate_send(db, draft_id)
    return res
