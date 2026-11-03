"""Lead Priority Scoring Service.

This service implements a multi-criteria weighted scoring algorithm to determine
the operational priority of incoming and existing sales leads.

Scoring Formula:
----------------
Total Score = (w_eng * s_eng) + (w_budget * s_budget) + (w_timeline * s_timeline) +
              (w_dm * s_dm) + (w_fit * s_fit) + (w_activity * s_activity)

Where:
- s_eng: Engagement Score (0-100), based on direct website and marketing engagement.
- s_budget: Budget Fit Score (20-100), derived from target deal budget tier.
- s_timeline: Purchase Timeline Score (15-100), rewarding near-term purchase intent.
- s_dm: Decision Maker Score (30 or 100), rewarding C-level / direct authority.
- s_fit: Product Fit Score (50-95), evaluating pain-point alignment.
- s_activity: Recent Activity Score (0-100), aggregated from visits, opens, clicks, meetings.

Thresholds:
- High Priority: Score >= 65.0
- Medium Priority: Score >= 40.0
- Low Priority: Score < 40.0
"""

from typing import Dict, Any, Union
from app.config import settings
from app.schemas.analysis_schemas import ScoringResult

BUDGET_SCORES = {
    "Under $5k": 20.0,
    "$5k-$20k": 45.0,
    "$20k-$50k": 75.0,
    "$50k-$100k": 90.0,
    "$100k+": 100.0
}

TIMELINE_SCORES = {
    "Immediate": 100.0,
    "1-3 months": 80.0,
    "3-6 months": 55.0,
    "6-12 months": 30.0,
    "12+ months": 15.0
}


class ScoringService:
    @staticmethod
    def calculate_priority_score(
        lead: Any,
        custom_weights: Dict[str, float] = None,
        custom_thresholds: Dict[str, float] = None
    ) -> ScoringResult:
        """Calculate weighted heuristic priority score for a lead instance or dict."""
        weights = {
            "engagement": settings.WEIGHT_ENGAGEMENT,
            "budget_fit": settings.WEIGHT_BUDGET_FIT,
            "timeline": settings.WEIGHT_TIMELINE,
            "decision_maker": settings.WEIGHT_DECISION_MAKER,
            "product_fit": settings.WEIGHT_PRODUCT_FIT,
            "recent_activity": settings.WEIGHT_RECENT_ACTIVITY
        }
        if custom_weights:
            weights.update(custom_weights)

        high_thresh = settings.HIGH_PRIORITY_THRESHOLD
        med_thresh = settings.MEDIUM_PRIORITY_THRESHOLD
        if custom_thresholds:
            high_thresh = custom_thresholds.get("high", high_thresh)
            med_thresh = custom_thresholds.get("medium", med_thresh)

        # Helper to extract attribute from ORM or dict
        def get_val(key, default=None):
            if isinstance(lead, dict):
                return lead.get(key, default)
            return getattr(lead, key, default)

        # 1. Engagement
        raw_eng = get_val("engagement_score", 0.0)
        s_eng = min(100.0, max(0.0, float(raw_eng or 0.0)))

        # 2. Budget Fit
        budget_range = str(get_val("budget_range", "$5k-$20k"))
        s_budget = BUDGET_SCORES.get(budget_range, 45.0)

        # 3. Timeline
        timeline = str(get_val("purchase_timeline", "1-3 months"))
        s_timeline = TIMELINE_SCORES.get(timeline, 55.0)

        # 4. Decision Maker
        is_dm = bool(get_val("decision_maker_status", False))
        s_dm = 100.0 if is_dm else 30.0

        # 5. Product Fit
        pain = get_val("pain_points")
        need = get_val("business_need")
        if pain and need and len(str(pain)) > 10 and len(str(need)) > 10:
            s_fit = 95.0
        elif pain or need:
            s_fit = 75.0
        else:
            s_fit = 50.0

        # 6. Recent Activity
        visits = int(get_val("website_visits", 0) or 0)
        opens = int(get_val("email_opens", 0) or 0)
        clicks = int(get_val("email_clicks", 0) or 0)
        meetings = int(get_val("meeting_count", 0) or 0)

        activity_points = (visits * 5.0) + (opens * 10.0) + (clicks * 20.0) + (meetings * 35.0)
        s_activity = min(100.0, max(0.0, activity_points))

        breakdown = {
            "engagement": round(s_eng, 2),
            "budget_fit": round(s_budget, 2),
            "timeline": round(s_timeline, 2),
            "decision_maker": round(s_dm, 2),
            "product_fit": round(s_fit, 2),
            "recent_activity": round(s_activity, 2)
        }

        total_score = (
            weights["engagement"] * s_eng +
            weights["budget_fit"] * s_budget +
            weights["timeline"] * s_timeline +
            weights["decision_maker"] * s_dm +
            weights["product_fit"] * s_fit +
            weights["recent_activity"] * s_activity
        )
        total_score = round(min(100.0, max(0.0, total_score)), 2)

        if total_score >= high_thresh:
            category = "high"
        elif total_score >= med_thresh:
            category = "medium"
        else:
            category = "low"

        return ScoringResult(
            score=total_score,
            category=category,
            breakdown=breakdown,
            weights=weights
        )
