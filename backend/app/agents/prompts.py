import json
import logging
import re
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

_OUTCOME_CLAIM_RE = re.compile(
    r"(?<!\w)\d+(?:[,.]\d+)*(?:\s?%|\s+(?:percent|hours?|minutes?|days?|weeks?|months?|years?|times?|x)\b)?"
    r"|[$€£]\s?\d+"
    r"|\b(?:immediate(?:ly)?|velocity|increase[ds]?|decrease[ds]?|improv(?:e[ds]?|ement)|"
    r"reduc(?:e[ds]?|tion)|sav(?:e[ds]?|ed|ings)|gain(?:s|ed)?|grow(?:th|s|ing)?|"
    r"boost(?:s|ed)?|accelerat(?:e[ds]?|ion)|faster|quicker|speed(?:s|ed|ing)?|"
    r"roi|revenue lift|cut|lower(?:ed)?|higher|more efficient|efficien(?:cy|t)|"
    r"productiv(?:ity|e)|benefit(?:s|ed)?|successful(?:ly)?|success|impact(?:s|ed)?|"
    r"outperform|deliver(?:ed)?|streamlin(?:e|es|ed|ing)|optimiz(?:e|es|ed|ation)|"
    r"results?|outcomes?)\b",
    re.IGNORECASE,
)


def remove_unverified_outcome_claims(
    value: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> str:
    """Keep outcome or metric sentences only when the source text states them verbatim."""
    evidence = [
        re.sub(r"\s+", " ", str(chunk.get("text") or "")).strip().casefold()
        for chunk in retrieved_chunks
    ]
    sentences = re.split(r"(?<=[.!?])(?=\s)", value)
    verified_sentences = []

    for sentence in sentences:
        normalized = re.sub(r"\s+", " ", sentence).strip().casefold()
        if (
            _OUTCOME_CLAIM_RE.search(sentence)
            and not any(
                normalized and normalized in source
                for source in evidence
                if source
            )
        ):
            continue
        verified_sentences.append(sentence)

    return "".join(verified_sentences).strip()


LEAD_ANALYSIS_PROMPT = """You are an expert sales intelligence analyst for NexusFlow.
Analyze the following lead context and machine learning predictions:
Lead Profile: {lead_json}
ML Conversion Probability: {conversion_probability}
Priority Score: {priority_score} ({priority_category})

Return a strictly valid JSON object with the following schema:
{{
  "positive_indicators": ["list of positive signals like decision maker authority, strong engagement"],
  "negative_indicators": ["list of risk factors like budget mismatch or long timeline"],
  "missing_information": ["list of key information gaps needed to close"],
  "recommended_action": "recommended sales action (e.g. Schedule Discovery Demo, Send Technical Whitepaper)",
  "action_rationale": "strategic justification grounded in the data"
}}
"""

ACTION_DECISION_PROMPT = """You are a senior RevOps strategist.
Based on the lead analysis:
Analysis: {analysis_json}
Retrieved Knowledge Evidence: {retrieved_chunks}

Select the optimal next action from the allowed list:
- "Send Personalized Follow-Up Email"
- "Schedule Technical Architecture Demo"
- "Share Case Study & Pricing Sheet"
- "Address Competitor Comparison"
- "Enroll in Long-term Nurture"

Return a strictly valid JSON object:
{{
  "action": "exact action string",
  "rationale": "detailed explanation referencing retrieved evidence",
  "confidence": 0.95
}}
"""

FOLLOW_UP_GENERATION_PROMPT = """You are a top-performing Sales Development Representative at NexusFlow.
Generate a tailored follow-up communication grounded strictly in the supplied lead fields and retrieved evidence.
Lead Contact: {lead_name} at {lead_company}
Title: {lead_title}
Pain Points: {pain_points}
Business Need: {business_need}
Action Decision: {action_decision}
Retrieved knowledge chunks (each includes its document metadata and exact source text): {retrieved_chunks}

Rules:
1. Treat document names and metadata as identifiers, never as evidence. Use only the exact text of a retrieved chunk to support a knowledge-base claim.
2. Do not invent or generalize customer results, operational outcomes, statistics, company priorities, product features, availability, or meeting dates.
3. Include a numerical or customer-outcome claim only when the retrieved text explicitly supports it. If used, preserve the specific result and the customer/context stated in that same source. Otherwise omit the claim.
4. Use CRM pain points and business needs only as provided facts; clean grammar without changing their meaning.
5. Tone must be professional, consultative, and concise. Ask a neutral question for the call to action without inventing availability.

Return a strictly valid JSON object:
{{
  "channel": "email",
  "subject": "Compelling subject line under 45 chars",
  "body": "Personalized email body text...",
  "personalization_points": ["point 1", "point 2"],
  "rationale": "Rationale explaining how this copy addresses the lead's pain points",
  "source_references": [
    {{"document_name": "Document Name", "chunk_id": "chunk_id", "excerpt": "relevant snippet"}}
  ],
  "call_to_action": "Clear friction-free CTA"
}}
"""


def clean_crm_text(value: str) -> str:
    """Normalize common CRM fragments while preserving the original meaning."""
    text = re.sub(r"\s+", " ", value).strip(" \t\r\n.,;:")
    if not text:
        return ""

    bottleneck_match = re.fullmatch(r"(.+?)\s+bottlenecks?\s+(.+)", text, flags=re.IGNORECASE)
    if bottleneck_match:
        text = f"{bottleneck_match.group(1)} is bottlenecking {bottleneck_match.group(2)}"

    text = text[0].upper() + text[1:]
    text = re.sub(r"\b(sdr|crm|roi|api|ml|ai)\b", lambda match: match.group(1).upper(), text, flags=re.IGNORECASE)
    if text[-1] not in ".!?":
        text += "."
    return text


class DemoLLMProvider:
    """Deterministic LLM Provider generating structured outputs grounded in real lead data."""

    @staticmethod
    def analyze_lead(lead: Dict[str, Any], prob: float, score: float, category: str) -> Dict[str, Any]:
        pos = []
        neg = []
        missing = []

        if lead.get("decision_maker_status"):
            pos.append(f"Direct executive authority ({lead.get('title')}) with purchasing decision power.")
        else:
            neg.append(f"Contact is {lead.get('title')}; may require stakeholder escalation to C-level.")
            missing.append("Budget approval committee identification.")

        eng = lead.get("engagement_score", 0.0) or 0.0
        if eng >= 60:
            pos.append(f"Strong digital engagement velocity (score {eng}/100 with {lead.get('email_opens', 0)} email opens).")
        else:
            neg.append(f"Low engagement score ({eng}/100); requires high-relevance trigger content.")

        budget = str(lead.get("budget_range", ""))
        if budget in ["$50k-$100k", "$100k+"]:
            pos.append(f"High-tier enterprise budget commitment ({budget}).")
        elif budget == "Under $5k":
            neg.append(f"Constrained starter budget tier ({budget}).")

        timeline = str(lead.get("purchase_timeline", ""))
        if timeline in ["Immediate", "1-3 months"]:
            pos.append(f"Active buying cycle with urgent purchase timeline ({timeline}).")
        else:
            neg.append(f"Extended procurement timeline ({timeline}); risk of deal stalling.")

        if not lead.get("pain_points"):
            missing.append("Specific operational bottleneck details.")

        if prob >= 0.65:
            rec_action = "Schedule Technical Architecture Demo"
            rationale = f"High conversion probability ({prob * 100:.1f}%) and solid priority score ({score}). Lead shows strong momentum for a live demonstration."
        elif prob >= 0.40:
            rec_action = "Send Personalized Follow-Up Email"
            rationale = f"Moderate qualification score ({score}). Provide targeted proof points addressing {lead.get('pain_points', 'workflow efficiency')}."
        else:
            rec_action = "Share Case Study & Pricing Sheet"
            rationale = f"Earlier stage opportunity (score {score}). Focus on ROI benchmarks and self-service case studies before scheduling live calls."

        return {
            "positive_indicators": pos,
            "negative_indicators": neg,
            "missing_information": missing,
            "recommended_action": rec_action,
            "action_rationale": rationale
        }

    @staticmethod
    def decide_action(analysis: Dict[str, Any], retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        rec = analysis.get("recommended_action", "Send Personalized Follow-Up Email")
        evidence_summary = ""
        if retrieved_chunks:
            docs = set(c.get("document_name", "Collateral") for c in retrieved_chunks[:3])
            evidence_summary = f" Grounded with collateral from: {', '.join(docs)}."

        return {
            "action": rec,
            "rationale": f"{analysis.get('action_rationale', '')}{evidence_summary}",
            "confidence": 0.92
        }

    @staticmethod
    def generate_draft(
        lead: Dict[str, Any],
        action: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        fname = lead.get("first_name", "there")
        company = lead.get("company", "your team")
        pain = clean_crm_text(str(lead.get("pain_points") or ""))

        source_refs = []
        for c in retrieved_chunks[:2]:
            source_text = str(c.get("text") or "").strip()
            if not source_text:
                continue
            source_refs.append({
                "document_name": c.get("document_name", "NexusFlow Knowledge"),
                "chunk_id": c.get("chunk_id", ""),
                "document_id": c.get("document_id", ""),
                "category": c.get("category", "General"),
                "excerpt": source_text
            })

        action_name = str(action.get("action") or "").strip()
        body_parts = [f"Hi {fname},"]
        if pain:
            body_parts.append(f"You mentioned: {pain}")
        if action_name:
            body_parts.append(f"A possible next step is to {action_name[0].lower() + action_name[1:]}.")
        body_parts.extend([
            "Would you be open to discussing this further?",
            "Best regards,\nNexusFlow Sales Intelligence Team"
        ])
        body = "\n\n".join(body_parts)

        return {
            "channel": "email",
            "subject": f"NexusFlow follow-up for {company}",
            "body": body,
            "personalization_points": [f"Referenced CRM pain point: '{pain}'"] if pain else [],
            "rationale": f"Uses the selected next action ({action_name}) and lead information provided in CRM." if action_name else "Uses only the lead information provided in CRM.",
            "source_references": source_refs,
            "call_to_action": "Would you be open to discussing this further?"
        }


def call_llm_json(prompt: str, system_prompt: str = "") -> Dict[str, Any]:
    """Invokes OpenAI LLM if configured; otherwise logs and falls back to demo mode."""
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt or "You are a helpful sales AI assistant. Output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                timeout=settings.LLM_TIMEOUT
            )
            content = resp.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"OpenAI LLM call failed: {e}. Falling back to demo mode.")

    return {}
