import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.orm_models import FollowUpDraft, Lead, Interaction
from app.schemas.followup_schemas import FollowUpDraftCreate, FollowUpDraftUpdate
from app.core.exceptions import NotFoundException, BusinessRuleViolationException
from app.utils.helpers import safe_json_dumps, safe_json_loads


class FollowUpService:
    @staticmethod
    def get_draft_by_id(db: Session, draft_id: str) -> FollowUpDraft:
        draft = db.query(FollowUpDraft).filter(FollowUpDraft.id == draft_id).first()
        if not draft:
            raise NotFoundException(f"Follow-up draft {draft_id} not found.")
        return draft

    @staticmethod
    def get_drafts(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        lead_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = db.query(FollowUpDraft)

        if status and status.lower() != "all":
            query = query.filter(FollowUpDraft.status == status.lower())
        if lead_id:
            query = query.filter(FollowUpDraft.lead_id == lead_id)

        total = query.count()
        drafts = query.order_by(desc(FollowUpDraft.created_at)).offset(skip).limit(limit).all()

        results = []
        for d in drafts:
            lead = db.query(Lead).filter(Lead.id == d.lead_id).first()
            results.append({
                "id": d.id,
                "lead_id": d.lead_id,
                "agent_run_id": d.agent_run_id,
                "channel": d.channel,
                "subject": d.subject,
                "body": d.body,
                "personalization_points": safe_json_loads(d.personalization_points, []),
                "rationale": d.rationale,
                "source_references": safe_json_loads(d.source_references, []),
                "call_to_action": d.call_to_action,
                "status": d.status,
                "approved_by": d.approved_by,
                "approval_decision_at": d.approval_decision_at,
                "rejection_reason": d.rejection_reason,
                "simulated_sent_at": d.simulated_sent_at,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
                "lead_name": f"{lead.first_name} {lead.last_name}" if lead else "Unknown",
                "lead_company": lead.company if lead else "Unknown"
            })

        return results, total

    @staticmethod
    def create_draft(db: Session, draft_in: FollowUpDraftCreate) -> FollowUpDraft:
        # Check duplicate pending drafts for same lead
        existing = (
            db.query(FollowUpDraft)
            .filter(
                FollowUpDraft.lead_id == draft_in.lead_id,
                FollowUpDraft.status == "pending_approval"
            )
            .first()
        )
        if existing:
            # Update existing rather than creating duplicate
            existing.subject = draft_in.subject
            existing.body = draft_in.body
            existing.personalization_points = safe_json_dumps(draft_in.personalization_points)
            existing.rationale = draft_in.rationale
            existing.source_references = safe_json_dumps(draft_in.source_references)
            existing.call_to_action = draft_in.call_to_action
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing

        draft = FollowUpDraft(
            id=str(uuid.uuid4()),
            lead_id=draft_in.lead_id,
            agent_run_id=draft_in.agent_run_id,
            channel=draft_in.channel,
            subject=draft_in.subject,
            body=draft_in.body,
            personalization_points=safe_json_dumps(draft_in.personalization_points),
            rationale=draft_in.rationale,
            source_references=safe_json_dumps(draft_in.source_references),
            call_to_action=draft_in.call_to_action,
            status=draft_in.status
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft

    @staticmethod
    def update_draft(db: Session, draft_id: str, updates: FollowUpDraftUpdate) -> FollowUpDraft:
        draft = FollowUpService.get_draft_by_id(db, draft_id)
        if draft.status in ["simulated_sent"]:
            raise BusinessRuleViolationException("Cannot edit a draft that has already been dispatched.")

        data = updates.model_dump(exclude_unset=True)
        for k, v in data.items():
            if k == "personalization_points" and isinstance(v, list):
                draft.personalization_points = safe_json_dumps(v)
            else:
                setattr(draft, k, v)

        draft.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(draft)
        return draft

    @staticmethod
    def approve_draft(db: Session, draft_id: str, approved_by: str = "Sales Manager") -> FollowUpDraft:
        draft = FollowUpService.get_draft_by_id(db, draft_id)
        if draft.status == "simulated_sent":
            raise BusinessRuleViolationException("Draft has already been sent.")

        draft.status = "approved"
        draft.approved_by = approved_by
        draft.approval_decision_at = datetime.utcnow()
        draft.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(draft)
        return draft

    @staticmethod
    def reject_draft(db: Session, draft_id: str, reason: str) -> FollowUpDraft:
        draft = FollowUpService.get_draft_by_id(db, draft_id)
        draft.status = "rejected"
        draft.rejection_reason = reason
        draft.approval_decision_at = datetime.utcnow()
        draft.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(draft)
        return draft

    @staticmethod
    def simulate_send(db: Session, draft_id: str) -> Dict[str, Any]:
        draft = FollowUpService.get_draft_by_id(db, draft_id)
        if draft.status != "approved":
            raise BusinessRuleViolationException(
                f"Draft must be approved prior to dispatch. Current status: '{draft.status}'."
            )

        now = datetime.utcnow()
        draft.status = "simulated_sent"
        draft.simulated_sent_at = now
        draft.updated_at = now

        # Record interaction in lead timeline
        interaction = Interaction(
            id=str(uuid.uuid4()),
            lead_id=draft.lead_id,
            interaction_type="Email Sent" if draft.channel == "email" else "LinkedIn Message",
            direction="outbound",
            subject=draft.subject,
            content=draft.body,
            occurred_at=now,
            created_at=now
        )
        db.add(interaction)
        db.commit()
        db.refresh(draft)

        return {
            "success": True,
            "draft_id": draft.id,
            "simulated_sent_at": now.isoformat(),
            "interaction_id": interaction.id,
            "message": f"Dispatched {draft.channel} message to lead (Sandbox Simulation Mode)."
        }
