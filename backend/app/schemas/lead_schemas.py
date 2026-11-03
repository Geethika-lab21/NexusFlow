from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class InteractionBase(BaseModel):
    interaction_type: str
    direction: str = "outbound"
    subject: Optional[str] = None
    content: str
    occurred_at: Optional[datetime] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionResponse(InteractionBase):
    id: str
    lead_id: str
    occurred_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class LeadBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    company: str = Field(..., min_length=1, max_length=150)
    title: str = Field(..., min_length=1, max_length=150)
    industry: str
    company_size: str
    country: str = "USA"
    lead_source: str = "Website Form"
    lead_status: str = "New"
    sales_stage: str = "Lead"
    budget_range: str = "$5k-$20k"
    purchase_timeline: str = "1-3 months"
    decision_maker_status: bool = False
    pain_points: Optional[str] = None
    product_interest: str = "NexusFlow Core Automation"
    business_need: Optional[str] = None
    engagement_score: float = Field(0.0, ge=0.0, le=100.0)
    website_visits: int = Field(0, ge=0)
    email_opens: int = Field(0, ge=0)
    email_clicks: int = Field(0, ge=0)
    meeting_count: int = Field(0, ge=0)
    is_converted: bool = False

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    country: Optional[str] = None
    lead_source: Optional[str] = None
    lead_status: Optional[str] = None
    sales_stage: Optional[str] = None
    budget_range: Optional[str] = None
    purchase_timeline: Optional[str] = None
    decision_maker_status: Optional[bool] = None
    pain_points: Optional[str] = None
    product_interest: Optional[str] = None
    business_need: Optional[str] = None
    engagement_score: Optional[float] = None
    website_visits: Optional[int] = None
    email_opens: Optional[int] = None
    email_clicks: Optional[int] = None
    meeting_count: Optional[int] = None
    is_converted: Optional[bool] = None

class LeadResponse(LeadBase):
    id: str
    created_at: datetime
    updated_at: datetime
    priority_score: Optional[float] = None
    priority_category: Optional[str] = None
    conversion_probability: Optional[float] = None

    class Config:
        from_attributes = True

class LeadDetailResponse(LeadResponse):
    interactions: List[InteractionResponse] = []

class PaginatedLeadsResponse(BaseModel):
    items: List[LeadResponse]
    total: int
    skip: int
    limit: int
