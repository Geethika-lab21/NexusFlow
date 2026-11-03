import io
import csv
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.models.orm_models import Lead, Interaction, LeadAnalysis, FollowUpDraft
from app.schemas.lead_schemas import LeadCreate, LeadUpdate
from app.services.scoring_service import ScoringService
from app.services.prediction_service import PredictionService
from app.core.exceptions import NotFoundException, BusinessRuleViolationException


class LeadService:
    @staticmethod
    def get_lead_by_id(db: Session, lead_id: str) -> Lead:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise NotFoundException(f"Lead with ID {lead_id} not found.")
        return lead

    @staticmethod
    def get_lead_detail_by_id(db: Session, lead_id: str) -> Lead:
        lead = LeadService.get_lead_by_id(db, lead_id)
        latest_analysis = (
            db.query(LeadAnalysis)
            .filter(LeadAnalysis.lead_id == lead.id)
            .order_by(desc(LeadAnalysis.created_at))
            .first()
        )

        if latest_analysis:
            lead.conversion_probability = latest_analysis.conversion_probability
            lead.priority_score = latest_analysis.priority_score
            lead.priority_category = latest_analysis.priority_category
            return lead

        score = ScoringService.calculate_priority_score(lead)
        lead.priority_score = score.score
        lead.priority_category = score.category

        prediction_input = {
            "engagement_score": lead.engagement_score,
            "website_visits": lead.website_visits,
            "email_opens": lead.email_opens,
            "email_clicks": lead.email_clicks,
            "meeting_count": lead.meeting_count,
            "industry": lead.industry,
            "lead_source": lead.lead_source,
            "company_size": lead.company_size,
            "budget_range": lead.budget_range,
            "purchase_timeline": lead.purchase_timeline,
            "decision_maker_status": lead.decision_maker_status,
        }
        prediction = PredictionService.get_instance().predict(prediction_input)
        lead.conversion_probability = (
            prediction.probability if prediction is not None else None
        )
        return lead

    @staticmethod
    def get_leads(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        sales_stage: Optional[str] = None,
        lead_source: Optional[str] = None,
        priority_category: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = db.query(Lead)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Lead.first_name.ilike(search_term),
                    Lead.last_name.ilike(search_term),
                    Lead.email.ilike(search_term),
                    Lead.company.ilike(search_term)
                )
            )

        if industry:
            query = query.filter(Lead.industry == industry)
        if sales_stage:
            query = query.filter(Lead.sales_stage == sales_stage)
        if lead_source:
            query = query.filter(Lead.lead_source == lead_source)

        total = query.count()

        # Sorting
        sort_col = getattr(Lead, sort_by, Lead.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        leads = query.offset(skip).limit(limit).all()

        pred_service = PredictionService.get_instance()
        lead_items = []
        for l in leads:
            score_res = ScoringService.calculate_priority_score(l)
            # Filter by priority category if requested
            if priority_category and score_res.category != priority_category.lower():
                continue

            lead_dict = {
                "id": l.id,
                "first_name": l.first_name,
                "last_name": l.last_name,
                "email": l.email,
                "phone": l.phone,
                "company": l.company,
                "title": l.title,
                "industry": l.industry,
                "company_size": l.company_size,
                "country": l.country,
                "lead_source": l.lead_source,
                "lead_status": l.lead_status,
                "sales_stage": l.sales_stage,
                "budget_range": l.budget_range,
                "purchase_timeline": l.purchase_timeline,
                "decision_maker_status": l.decision_maker_status,
                "pain_points": l.pain_points,
                "product_interest": l.product_interest,
                "business_need": l.business_need,
                "engagement_score": l.engagement_score,
                "website_visits": l.website_visits,
                "email_opens": l.email_opens,
                "email_clicks": l.email_clicks,
                "meeting_count": l.meeting_count,
                "is_converted": l.is_converted,
                "created_at": l.created_at,
                "updated_at": l.updated_at,
                "priority_score": score_res.score,
                "priority_category": score_res.category,
                "conversion_probability": None
            }

            # If there's an existing analysis, attach the conversion prob
            latest_analysis = (
                db.query(LeadAnalysis)
                .filter(LeadAnalysis.lead_id == l.id)
                .order_by(desc(LeadAnalysis.created_at))
                .first()
            )
            if latest_analysis:
                lead_dict["conversion_probability"] = latest_analysis.conversion_probability
            else:
                pred = pred_service.predict(lead_dict)
                lead_dict["conversion_probability"] = pred.probability

            lead_items.append(lead_dict)

        return lead_items, total

    @staticmethod
    def create_lead(db: Session, lead_in: LeadCreate) -> Lead:
        existing = db.query(Lead).filter(Lead.email == lead_in.email).first()
        if existing:
            raise BusinessRuleViolationException(f"Lead with email {lead_in.email} already exists.")

        lead = Lead(
            id=str(uuid.uuid4()),
            first_name=lead_in.first_name,
            last_name=lead_in.last_name,
            email=lead_in.email,
            phone=lead_in.phone,
            company=lead_in.company,
            title=lead_in.title,
            industry=lead_in.industry,
            company_size=lead_in.company_size,
            country=lead_in.country,
            lead_source=lead_in.lead_source,
            lead_status=lead_in.lead_status,
            sales_stage=lead_in.sales_stage,
            budget_range=lead_in.budget_range,
            purchase_timeline=lead_in.purchase_timeline,
            decision_maker_status=lead_in.decision_maker_status,
            pain_points=lead_in.pain_points,
            product_interest=lead_in.product_interest,
            business_need=lead_in.business_need,
            engagement_score=lead_in.engagement_score,
            website_visits=lead_in.website_visits,
            email_opens=lead_in.email_opens,
            email_clicks=lead_in.email_clicks,
            meeting_count=lead_in.meeting_count,
            is_converted=lead_in.is_converted
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def update_lead(db: Session, lead_id: str, lead_in: LeadUpdate) -> Lead:
        lead = LeadService.get_lead_by_id(db, lead_id)
        update_data = lead_in.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] != lead.email:
            existing = db.query(Lead).filter(Lead.email == update_data["email"]).first()
            if existing:
                raise BusinessRuleViolationException(f"Email {update_data['email']} is already taken.")

        for field, value in update_data.items():
            setattr(lead, field, value)

        lead.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    def delete_lead(db: Session, lead_id: str):
        lead = LeadService.get_lead_by_id(db, lead_id)
        db.delete(lead)
        db.commit()

    @staticmethod
    def import_leads_csv(db: Session, csv_content: str) -> Dict[str, Any]:
        reader = csv.DictReader(io.StringIO(csv_content))
        imported = 0
        skipped = 0
        errors = []

        existing_emails = set(e[0] for e in db.query(Lead.email).all())

        for row_idx, row in enumerate(reader, start=1):
            email = row.get("email", "").strip()
            if not email or email in existing_emails:
                skipped += 1
                continue

            try:
                lead = Lead(
                    id=str(uuid.uuid4()),
                    first_name=row.get("first_name", "Unknown").strip(),
                    last_name=row.get("last_name", "Lead").strip(),
                    email=email,
                    phone=row.get("phone", None),
                    company=row.get("company", "Company").strip(),
                    title=row.get("title", "Representative").strip(),
                    industry=row.get("industry", "Technology").strip(),
                    company_size=row.get("company_size", "51-200").strip(),
                    country=row.get("country", "USA").strip(),
                    lead_source=row.get("lead_source", "Website Form").strip(),
                    lead_status=row.get("lead_status", "New").strip(),
                    sales_stage=row.get("sales_stage", "Lead").strip(),
                    budget_range=row.get("budget_range", "$5k-$20k").strip(),
                    purchase_timeline=row.get("purchase_timeline", "1-3 months").strip(),
                    decision_maker_status=str(row.get("decision_maker_status", "")).lower() in ["true", "1", "yes"],
                    pain_points=row.get("pain_points", None),
                    product_interest=row.get("product_interest", "NexusFlow Core Automation").strip(),
                    business_need=row.get("business_need", None),
                    engagement_score=float(row.get("engagement_score", 50.0)),
                    website_visits=int(row.get("website_visits", 0)),
                    email_opens=int(row.get("email_opens", 0)),
                    email_clicks=int(row.get("email_clicks", 0)),
                    meeting_count=int(row.get("meeting_count", 0)),
                    is_converted=str(row.get("is_converted", "")).lower() in ["true", "1", "yes"]
                )
                db.add(lead)
                existing_emails.add(email)
                imported += 1
            except Exception as e:
                errors.append(f"Row {row_idx}: {str(e)}")

        db.commit()
        return {
            "imported_count": imported,
            "skipped_count": skipped,
            "errors": errors[:10]
        }
