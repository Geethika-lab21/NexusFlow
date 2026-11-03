import os
import sys
import uuid
import random
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Setup python path to include backend root
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import SessionLocal, engine
from app.db.init_db import init_db
from app.models.orm_models import Lead, Interaction

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa", "Edward", "Deborah",
    "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Laura", "Jeffrey", "Sharon",
    "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy", "Nicholas", "Shirley",
    "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna", "Larry", "Brenda",
    "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma", "Benjamin", "Samantha"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz"
]

COMPANIES = [
    "Acme Corp", "Apex Technologies", "BlueStar Logistics", "Catalyst Health",
    "DataPulse Analytics", "Elevate Cloud", "Falcon Global", "Genesis Media",
    "Hyperion Financial", "Innovate Retail", "Jupiter Robotics", "Krypton Labs",
    "Luminary Education", "Meridian Software", "Nexus Logistics", "OmniTech Solutions",
    "Pinnacle Real Estate", "Quantum Systems", "Radiant Digital", "Summit Healthcare",
    "Titan Capital", "Universal Manufacturing", "Vanguard AI", "Waveform Audio",
    "Xenon Energy", "Zenith Media", "Aegis BioTech", "Beacon Networks", "Cobalt Dynamics",
    "Delta Cloudworks", "Echo Commerce", "Frontier Health", "GridLogic", "Horizon Wealth",
    "Insignia Legal", "Javelin Software", "Kinetic Industrial", "Latitude Tech",
    "Matrix Global", "Nova BioLabs", "Optima Logistics", "Polaris Systems"
]

TITLES = [
    "VP of Sales", "Head of Operations", "Chief Technology Officer", "Director of IT",
    "Operations Manager", "Chief Executive Officer", "VP of Marketing", "Sales Operations Lead",
    "Procurement Director", "Product Manager", "Chief Operating Officer", "Digital Transformation Lead",
    "Automation Architect", "Enterprise Solutions Director", "Senior Workflow Specialist"
]

INDUSTRIES = [
    "Technology", "Healthcare", "Finance", "Manufacturing", "Retail",
    "Education", "Real Estate", "Logistics", "Professional Services", "Media"
]

COMPANY_SIZES = ["1-10", "11-50", "51-200", "201-500", "501-2000", "2001+"]

LEAD_SOURCES = [
    "Website Form", "Product Demo", "Webinar", "Referral", "Inbound Inquiry",
    "Outbound Prospecting", "LinkedIn", "Conference", "Partner"
]

SALES_STAGES = [
    "Lead", "Prospect", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost"
]

BUDGET_RANGES = ["Under $5k", "$5k-$20k", "$20k-$50k", "$50k-$100k", "$100k+"]
TIMELINES = ["Immediate", "1-3 months", "3-6 months", "6-12 months", "12+ months"]

PAIN_POINTS = [
    "Manual data entry slows down sales SDR workflows by 15 hours weekly.",
    "Lack of automated CRM synchronisation causes lost pipeline opportunities.",
    "Complex legacy integration overhead and brittle webhook integrations.",
    "Inefficient multi-step approval bottlenecks between sales managers and SDRs.",
    "Inability to prioritize high-value inbound leads with statistical confidence.",
    "Scattered knowledge base documentation and slow response times to customer inquiries.",
    "High onboarding friction for new revenue operations and sales team members."
]

BUSINESS_NEEDS = [
    "Automate sales qualification workflows and reduce customer response latency.",
    "Consolidate 12 disconnected SaaS tools into a single orchestration platform.",
    "Deploy autonomous AI SDR agents to streamline objection handling and drafting.",
    "Modernize legacy pipeline scoring with predictive machine learning models.",
    "Scale inbound lead triage without adding redundant sales headcount."
]

PRODUCT_INTERESTS = [
    "NexusFlow Core Automation",
    "NexusFlow AI Agent Orchestrator",
    "NexusFlow Enterprise Integration Suite",
    "NexusFlow Sales Intelligence Cloud"
]

INTERACTION_TYPES = [
    "Email Sent", "Email Received", "Phone Call", "Meeting", "Demo", "LinkedIn Message", "Note"
]

INTERACTION_SNIPPETS = {
    "Email Sent": [
        "Sent introduction overview covering NexusFlow enterprise workflow automation.",
        "Shared product demo link and technical feature comparison sheet.",
        "Followed up regarding budget approval and upcoming board review.",
        "Sent custom pricing proposal with annual enterprise volume discount."
    ],
    "Email Received": [
        "Customer asked about SOC 2 compliance and data residency safeguards.",
        "Lead inquired about pre-built Salesforce and HubSpot connector availability.",
        "Requested an updated demo for their European operations leadership team.",
        "Confirmed interest in running a two-week proof-of-concept trial."
    ],
    "Phone Call": [
        "Discussed current pain points regarding manual triage and SDR bottlenecks.",
        "Reviewed decision maker timeline and Q3 procurement review cycle.",
        "Quick sync regarding licensing tier differences between Pro and Enterprise.",
        "Unscheduled check-in call; lead requested follow-up next Tuesday."
    ],
    "Meeting": [
        "Conducted 45-minute discovery call covering RevOps requirements.",
        "Held architecture review with VP of Engineering and security auditor.",
        "Executive alignment session regarding 500-seat company-wide rollout.",
        "Sprint review demonstrating automated lead routing and RAG search."
    ],
    "Demo": [
        "Demonstrated NexusFlow hybrid RAG search against mock knowledge docs.",
        "Walkthrough of autonomous email drafting and human approval workflows.",
        "Live test simulating 100 concurrent webhook events into lead triage.",
        "End-to-end demo showing ML conversion probability scoring."
    ],
    "LinkedIn Message": [
        "Connected via LinkedIn; lead expressed interest after seeing our webinar.",
        "Sent direct message highlighting automated CRM synchronization benchmarks.",
        "Lead commented on our AI workflow automation post asking for details."
    ],
    "Note": [
        "Internal note: Lead mentioned competitor contract expires in 60 days.",
        "Internal note: Key stakeholder promoted to Chief Operating Officer.",
        "Internal note: High probability prospect; expedite technical evaluation.",
        "Internal note: Budget confirmed approved by CFO."
    ]
}


def generate_synthetic_dataset(num_leads: int = 700, seed: int = 42):
    np.random.seed(seed)
    random.seed(seed)
    
    budget_scores = {
        "Under $5k": 0.1,
        "$5k-$20k": 0.3,
        "$20k-$50k": 0.6,
        "$50k-$100k": 0.85,
        "$100k+": 1.0
    }
    
    timeline_scores = {
        "Immediate": 1.0,
        "1-3 months": 0.8,
        "3-6 months": 0.5,
        "6-12 months": 0.2,
        "12+ months": 0.05
    }
    
    stage_scores = {
        "Lead": 0.1,
        "Prospect": 0.25,
        "Qualified": 0.5,
        "Proposal": 0.75,
        "Negotiation": 0.9,
        "Closed Won": 1.0,
        "Closed Lost": 0.0
    }

    leads_data = []
    interactions_data = []
    now = datetime.utcnow()
    
    used_emails = set()

    for i in range(num_leads):
        lead_id = str(uuid.uuid4())
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        company_name = f"{random.choice(COMPANIES)} {random.choice(['Inc', 'LLC', 'Group', 'Solutions', 'Tech'])}"
        
        email_prefix = f"{fname.lower()}.{lname.lower()}{random.randint(1, 999)}"
        email_domain = company_name.lower().replace(" ", "").replace(",", "")[:10] + ".com"
        email = f"{email_prefix}@{email_domain}"
        
        while email in used_emails:
            email_prefix = f"{fname.lower()}.{lname.lower()}{random.randint(1000, 99999)}"
            email = f"{email_prefix}@{email_domain}"
        used_emails.add(email)

        phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        title = random.choice(TITLES)
        industry = random.choice(INDUSTRIES)
        company_size = random.choice(COMPANY_SIZES)
        lead_source = random.choice(LEAD_SOURCES)
        sales_stage = random.choice(SALES_STAGES)
        budget_range = random.choice(BUDGET_RANGES)
        purchase_timeline = random.choice(TIMELINES)
        decision_maker = bool(random.random() < 0.45)
        
        # Engagement attributes
        engagement_score = float(np.clip(np.random.normal(55, 22), 0, 100))
        website_visits = max(0, int(np.random.poisson(engagement_score / 10)))
        email_opens = max(0, int(np.random.poisson(engagement_score / 15)))
        email_clicks = max(0, int(np.random.poisson(email_opens * 0.4)))
        meeting_count = max(0, int(np.random.poisson(1.5 if sales_stage in ["Proposal", "Negotiation", "Closed Won"] else 0.5)))
        
        # Outcome generation per formula:
        b_score = budget_scores[budget_range]
        t_score = timeline_scores[purchase_timeline]
        s_score = stage_scores[sales_stage]
        dm_val = 1.0 if decision_maker else 0.0
        
        base_prob = (
            0.30 * (engagement_score / 100.0) +
            0.20 * dm_val +
            0.15 * b_score +
            0.15 * t_score +
            0.20 * s_score
        )
        
        noise = float(np.random.normal(0, 0.15))
        conversion_prob = float(np.clip(base_prob + noise, 0.0, 1.0))
        
        if sales_stage == "Closed Won":
            is_converted = True
        elif sales_stage == "Closed Lost":
            is_converted = False
        else:
            is_converted = bool(random.random() < conversion_prob)
            
        created_days_ago = random.randint(10, 180)
        created_at = now - timedelta(days=created_days_ago, hours=random.randint(1, 23))
        updated_at = created_at + timedelta(days=random.randint(0, created_days_ago))
        
        lead_status = "New"
        if sales_stage in ["Closed Won", "Closed Lost"]:
            lead_status = "Qualified" if is_converted else "Unqualified"
        elif meeting_count > 0 or email_clicks > 0:
            lead_status = "Engaged"
        elif email_opens > 0:
            lead_status = "Contacted"

        lead_row = {
            "id": lead_id,
            "first_name": fname,
            "last_name": lname,
            "email": email,
            "phone": phone,
            "company": company_name,
            "title": title,
            "industry": industry,
            "company_size": company_size,
            "country": "USA",
            "lead_source": lead_source,
            "lead_status": lead_status,
            "sales_stage": sales_stage,
            "budget_range": budget_range,
            "purchase_timeline": purchase_timeline,
            "decision_maker_status": decision_maker,
            "pain_points": random.choice(PAIN_POINTS),
            "product_interest": random.choice(PRODUCT_INTERESTS),
            "business_need": random.choice(BUSINESS_NEEDS),
            "engagement_score": round(engagement_score, 2),
            "website_visits": website_visits,
            "email_opens": email_opens,
            "email_clicks": email_clicks,
            "meeting_count": meeting_count,
            "is_converted": is_converted,
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat()
        }
        leads_data.append(lead_row)

        # Generate 2 to 8 interactions for this lead
        num_interactions = random.randint(2, 8)
        for j in range(num_interactions):
            itype = random.choice(INTERACTION_TYPES)
            direction = "inbound" if itype in ["Email Received"] else "outbound"
            if itype == "Note":
                direction = "internal"
            
            days_offset = random.randint(0, created_days_ago)
            occ_time = created_at + timedelta(days=days_offset, minutes=random.randint(10, 500))
            
            content_snippet = random.choice(INTERACTION_SNIPPETS[itype])
            
            interactions_data.append({
                "id": str(uuid.uuid4()),
                "lead_id": lead_id,
                "interaction_type": itype,
                "direction": direction,
                "subject": f"{itype} regarding {lead_row['company']}",
                "content": content_snippet,
                "occurred_at": occ_time.isoformat(),
                "created_at": occ_time.isoformat()
            })

    leads_df = pd.DataFrame(leads_data)
    interactions_df = pd.DataFrame(interactions_data)

    # 70% / 30% stratified split based on is_converted
    train_df, test_df = train_test_split(
        leads_df,
        test_size=0.30,
        random_state=seed,
        stratify=leads_df["is_converted"]
    )

    out_dir = PROJECT_DIR / "data" / "synthetic"
    out_dir.mkdir(parents=True, exist_ok=True)

    leads_df.to_csv(out_dir / "leads.csv", index=False)
    train_df.to_csv(out_dir / "leads_train.csv", index=False)
    test_df.to_csv(out_dir / "leads_test.csv", index=False)
    interactions_df.to_csv(out_dir / "interactions.csv", index=False)

    print(f"Generated {len(leads_df)} leads ({len(train_df)} train, {len(test_df)} test) and {len(interactions_df)} interactions.")
    return leads_df, interactions_df


def seed_database(db_session=None):
    from app.config import settings
    init_db()

    csv_path = Path(settings.SYNTHETIC_DATA_DIR) / "leads.csv"
    interactions_csv_path = Path(settings.SYNTHETIC_DATA_DIR) / "interactions.csv"

    if not csv_path.exists():
        print("Generating synthetic CSVs first...")
        generate_synthetic_dataset()

    leads_df = pd.read_csv(csv_path)
    interactions_df = pd.read_csv(interactions_csv_path)

    session_created = False
    if db_session is None:
        db_session = SessionLocal()
        session_created = True

    try:
        existing_emails = set(e[0] for e in db_session.query(Lead.email).all())
        leads_to_insert = []
        lead_id_map = {}

        for _, row in leads_df.iterrows():
            if row["email"] in existing_emails:
                continue
            
            lead_obj = Lead(
                id=str(row["id"]),
                first_name=str(row["first_name"]),
                last_name=str(row["last_name"]),
                email=str(row["email"]),
                phone=str(row["phone"]) if pd.notna(row["phone"]) else None,
                company=str(row["company"]),
                title=str(row["title"]),
                industry=str(row["industry"]),
                company_size=str(row["company_size"]),
                country=str(row.get("country", "USA")),
                lead_source=str(row["lead_source"]),
                lead_status=str(row["lead_status"]),
                sales_stage=str(row["sales_stage"]),
                budget_range=str(row["budget_range"]),
                purchase_timeline=str(row["purchase_timeline"]),
                decision_maker_status=bool(row["decision_maker_status"]),
                pain_points=str(row["pain_points"]) if pd.notna(row["pain_points"]) else None,
                product_interest=str(row["product_interest"]),
                business_need=str(row["business_need"]) if pd.notna(row["business_need"]) else None,
                engagement_score=float(row["engagement_score"]),
                website_visits=int(row["website_visits"]),
                email_opens=int(row["email_opens"]),
                email_clicks=int(row["email_clicks"]),
                meeting_count=int(row["meeting_count"]),
                is_converted=bool(row["is_converted"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )
            leads_to_insert.append(lead_obj)
            existing_emails.add(row["email"])

        if leads_to_insert:
            db_session.bulk_save_objects(leads_to_insert)
            db_session.commit()
            print(f"Inserted {len(leads_to_insert)} new leads into the database.")
        else:
            print("No new leads to insert (all existing).")

        # Insert interactions
        existing_interaction_ids = set(i[0] for i in db_session.query(Interaction.id).all())
        interactions_to_insert = []

        for _, row in interactions_df.iterrows():
            if str(row["id"]) in existing_interaction_ids:
                continue
            
            inter_obj = Interaction(
                id=str(row["id"]),
                lead_id=str(row["lead_id"]),
                interaction_type=str(row["interaction_type"]),
                direction=str(row["direction"]),
                subject=str(row["subject"]) if pd.notna(row["subject"]) else None,
                content=str(row["content"]),
                occurred_at=datetime.fromisoformat(row["occurred_at"]),
                created_at=datetime.fromisoformat(row["created_at"])
            )
            interactions_to_insert.append(inter_obj)
            existing_interaction_ids.add(str(row["id"]))

        if interactions_to_insert:
            db_session.bulk_save_objects(interactions_to_insert)
            db_session.commit()
            print(f"Inserted {len(interactions_to_insert)} new interactions into the database.")

    except Exception as e:
        db_session.rollback()
        raise e
    finally:
        if session_created:
            db_session.close()


if __name__ == "__main__":
    print("Step 1: Generating synthetic datasets...")
    generate_synthetic_dataset()
    print("Step 2: Seeding database...")
    seed_database()
    print("Database seeding completed successfully.")
