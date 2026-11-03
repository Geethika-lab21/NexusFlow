from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.database import get_db
from app.services.lead_service import LeadService
from app.schemas.lead_schemas import (
    LeadCreate, LeadUpdate, LeadResponse, LeadDetailResponse, PaginatedLeadsResponse
)

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("", response_model=PaginatedLeadsResponse)
def get_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    industry: Optional[str] = None,
    sales_stage: Optional[str] = None,
    lead_source: Optional[str] = None,
    priority: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):
    items, total = LeadService.get_leads(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        industry=industry,
        sales_stage=sales_stage,
        lead_source=lead_source,
        priority_category=priority,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return PaginatedLeadsResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(lead_in: LeadCreate, db: Session = Depends(get_db)):
    lead = LeadService.create_lead(db, lead_in)
    return lead


@router.get("/{lead_id}", response_model=LeadDetailResponse)
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = LeadService.get_lead_detail_by_id(db, lead_id)
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: str, lead_in: LeadUpdate, db: Session = Depends(get_db)):
    lead = LeadService.update_lead(db, lead_id, lead_in)
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: str, db: Session = Depends(get_db)):
    LeadService.delete_lead(db, lead_id)
    return None


@router.post("/import-csv")
async def import_leads_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    csv_text = content.decode("utf-8", errors="ignore")
    res = LeadService.import_leads_csv(db, csv_text)
    return res
