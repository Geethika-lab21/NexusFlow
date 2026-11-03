import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List

from app.db.database import get_db
from app.models.orm_models import AgentRun, Lead
from app.schemas.agent_schemas import (
    AgentRunCreate, AgentRunResponse, AgentRunDetailResponse, PaginatedAgentRunsResponse
)
from app.agents.graph import run_agent_workflow
from app.services.lead_service import LeadService
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/agent-runs", tags=["Agent Runs"])


@router.post("", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED)
def start_agent_run(run_in: AgentRunCreate, db: Session = Depends(get_db)):
    # Validate lead exists
    LeadService.get_lead_by_id(db, run_in.lead_id)

    run_id = str(uuid.uuid4())
    run_record = AgentRun(
        id=run_id,
        lead_id=run_in.lead_id,
        requested_by=run_in.requested_by,
        trigger_source=run_in.trigger_source,
        status="running",
        started_at=datetime.utcnow()
    )
    db.add(run_record)
    db.commit()

    # Execute workflow synchronously
    final_state = run_agent_workflow(
        lead_id=run_in.lead_id,
        run_id=run_id,
        db=db,
        requested_by=run_in.requested_by
    )

    db.refresh(run_record)
    return run_record


@router.get("", response_model=PaginatedAgentRunsResponse)
def list_agent_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    lead_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AgentRun)
    if lead_id:
        query = query.filter(AgentRun.lead_id == lead_id)
    if status_filter:
        query = query.filter(AgentRun.status == status_filter)

    total = query.count()
    runs = query.order_by(desc(AgentRun.started_at)).offset(skip).limit(limit).all()

    return PaginatedAgentRunsResponse(
        items=runs,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{run_id}", response_model=AgentRunDetailResponse)
def get_agent_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise NotFoundException(f"Agent run {run_id} not found.")

    lead = db.query(Lead).filter(Lead.id == run.lead_id).first()
    detail = AgentRunDetailResponse.model_validate(run)
    if lead:
        detail.lead_name = f"{lead.first_name} {lead.last_name}"
        detail.lead_company = lead.company

    return detail
