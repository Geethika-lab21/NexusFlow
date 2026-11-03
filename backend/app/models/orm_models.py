import enum
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class LeadStage(str, enum.Enum):
    LEAD = "Lead"
    PROSPECT = "Prospect"
    QUALIFIED = "Qualified"
    PROPOSAL = "Proposal"
    NEGOTIATION = "Negotiation"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"


class LeadStatus(str, enum.Enum):
    NEW = "New"
    CONTACTED = "Contacted"
    ENGAGED = "Engaged"
    QUALIFIED = "Qualified"
    UNQUALIFIED = "Unqualified"


class LeadSource(str, enum.Enum):
    WEBSITE_FORM = "Website Form"
    PRODUCT_DEMO = "Product Demo"
    WEBINAR = "Webinar"
    REFERRAL = "Referral"
    INBOUND_INQUIRY = "Inbound Inquiry"
    OUTBOUND_PROSPECTING = "Outbound Prospecting"
    LINKEDIN = "LinkedIn"
    CONFERENCE = "Conference"
    PARTNER = "Partner"


class InteractionType(str, enum.Enum):
    EMAIL_SENT = "Email Sent"
    EMAIL_RECEIVED = "Email Received"
    PHONE_CALL = "Phone Call"
    MEETING = "Meeting"
    DEMO = "Demo"
    LINKEDIN_MESSAGE = "LinkedIn Message"
    NOTE = "Note"


class DraftStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SIMULATED_SENT = "simulated_sent"


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    company_size: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(50), default="USA")
    lead_source: Mapped[str] = mapped_column(String(50), default=LeadSource.WEBSITE_FORM.value)
    lead_status: Mapped[str] = mapped_column(String(50), default=LeadStatus.NEW.value)
    sales_stage: Mapped[str] = mapped_column(String(50), default=LeadStage.LEAD.value)
    budget_range: Mapped[str] = mapped_column(String(50), default="$5k-$20k")
    purchase_timeline: Mapped[str] = mapped_column(String(50), default="1-3 months")
    decision_maker_status: Mapped[bool] = mapped_column(Boolean, default=False)
    pain_points: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_interest: Mapped[str] = mapped_column(String(150), default="NexusFlow Core Automation")
    business_need: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    website_visits: Mapped[int] = mapped_column(Integer, default=0)
    email_opens: Mapped[int] = mapped_column(Integer, default=0)
    email_clicks: Mapped[int] = mapped_column(Integer, default=0)
    meeting_count: Mapped[int] = mapped_column(Integer, default=0)
    is_converted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    interactions: Mapped[List["Interaction"]] = relationship("Interaction", back_populates="lead", cascade="all, delete-orphan", order_by="desc(Interaction.occurred_at)")
    analyses: Mapped[List["LeadAnalysis"]] = relationship("LeadAnalysis", back_populates="lead", cascade="all, delete-orphan", order_by="desc(LeadAnalysis.created_at)")
    drafts: Mapped[List["FollowUpDraft"]] = relationship("FollowUpDraft", back_populates="lead", cascade="all, delete-orphan", order_by="desc(FollowUpDraft.created_at)")
    agent_runs: Mapped[List["AgentRun"]] = relationship("AgentRun", back_populates="lead", cascade="all, delete-orphan", order_by="desc(AgentRun.started_at)")


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), default="outbound")
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lead: Mapped["Lead"] = relationship("Lead", back_populates="interactions")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="General", index=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LeadAnalysis(Base):
    __tablename__ = "lead_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    conversion_probability: Mapped[float] = mapped_column(Float, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    priority_category: Mapped[str] = mapped_column(String(20), nullable=False)
    positive_indicators: Mapped[str] = mapped_column(Text, default="[]")  # JSON string
    negative_indicators: Mapped[str] = mapped_column(Text, default="[]")  # JSON string
    missing_information: Mapped[str] = mapped_column(Text, default="[]")  # JSON string
    feature_contributions: Mapped[str] = mapped_column(Text, default="[]")  # JSON string
    recommended_action: Mapped[str] = mapped_column(String(100), nullable=False)
    action_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lead: Mapped["Lead"] = relationship("Lead", back_populates="analyses")


class FollowUpDraft(Base):
    __tablename__ = "follow_up_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_run_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(50), default="email")
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    personalization_points: Mapped[str] = mapped_column(Text, default="[]")  # JSON string
    rationale: Mapped[str] = mapped_column(Text, default="")
    source_references: Mapped[str] = mapped_column(Text, default="[]")  # JSON string
    call_to_action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=DraftStatus.PENDING_APPROVAL.value, index=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    approval_decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    simulated_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lead: Mapped["Lead"] = relationship("Lead", back_populates="drafts")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(100), default="system")
    status: Mapped[str] = mapped_column(String(30), default=RunStatus.PENDING.value, index=True)
    current_node: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    trigger_source: Mapped[str] = mapped_column(String(50), default="manual")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    skip_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    lead: Mapped["Lead"] = relationship("Lead", back_populates="agent_runs")
    steps: Mapped[List["AgentStep"]] = relationship("AgentStep", back_populates="run", cascade="all, delete-orphan", order_by="AgentStep.step_order")


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    node_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="success")
    input_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="steps")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_type: Mapped[str] = mapped_column(String(50), default="ml")  # ml, rag, agent, full
    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    dataset_name: Mapped[str] = mapped_column(String(100), default="leads_test.csv")
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    metrics: Mapped[str] = mapped_column(Text, default="{}")  # JSON string
    feature_importance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    confusion_matrix: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    status: Mapped[str] = mapped_column(String(30), default="completed")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AppSettings(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="general")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
