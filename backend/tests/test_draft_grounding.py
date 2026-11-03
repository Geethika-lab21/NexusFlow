import re

from app.agents.prompts import DemoLLMProvider, FOLLOW_UP_GENERATION_PROMPT


def make_lead(**overrides):
    lead = {
        "first_name": "Alex",
        "last_name": "Morgan",
        "company": "TechCorp Global",
        "title": "VP of Revenue Operations",
        "pain_points": "manual data entry bottlenecks sdr response latency",
        "business_need": "Automate sales qualification workflows and reduce customer response latency.",
    }
    lead.update(overrides)
    return lead


def make_chunk(text, **overrides):
    chunk = {
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "document_name": "07 Sales Objections",
        "category": "Objections",
        "text": text,
    }
    chunk.update(overrides)
    return chunk


def test_demo_draft_does_not_turn_document_name_into_outcome_claim():
    draft = DemoLLMProvider.generate_draft(
        make_lead(),
        {"action": "Schedule Technical Architecture Demo"},
        [make_chunk("This document explains how to prepare for a technical discussion.")],
    )

    assert "immediate operational velocity gains" not in draft["body"].lower()
    assert "34%" not in draft["body"]
    assert "in reviewing our" not in draft["body"].lower()


def test_demo_draft_cleans_malformed_crm_pain_point():
    raw_pain = "manual data entry bottlenecks sdr response latency"
    draft = DemoLLMProvider.generate_draft(
        make_lead(pain_points=raw_pain),
        {"action": "Schedule Technical Architecture Demo"},
        [],
    )

    assert raw_pain not in draft["body"]
    assert "You mentioned: Manual data entry is bottlenecking SDR response latency." in draft["body"]


def test_demo_draft_omits_unsupported_results_when_evidence_is_missing_or_irrelevant():
    irrelevant_chunk = make_chunk(
        "NexusFlow supports retrieval across product documentation.",
        document_name="13 Case Studies",
    )
    draft = DemoLLMProvider.generate_draft(
        make_lead(),
        {"action": "Share Case Study & Pricing Sheet"},
        [irrelevant_chunk],
    )

    assert not re.search(r"\b\d+(?:\.\d+)?%?\b", draft["body"])
    assert not re.search(r"\b(?:increased|improved|reduced|saved|gains?|ROI)\b", draft["body"], re.IGNORECASE)


def test_demo_draft_does_not_generalize_even_source_supported_case_study_results():
    case_study = make_chunk(
        "Krypton Commerce reduced response time from 48 hours to 18 minutes and saved "
        "32 SDR hours weekly across an 8-person team.",
        document_name="13 Case Studies",
        category="Case Studies",
    )
    draft = DemoLLMProvider.generate_draft(
        make_lead(),
        {"action": "Share Case Study & Pricing Sheet"},
        [case_study],
    )

    assert "48 hours" not in draft["body"]
    assert "18 minutes" not in draft["body"]
    assert "32 SDR hours" not in draft["body"]
    assert draft["source_references"][0]["excerpt"] == case_study["text"]
    assert draft["source_references"][0]["document_name"] == "13 Case Studies"
    assert draft["source_references"][0]["category"] == "Case Studies"
    assert draft["source_references"][0]["chunk_id"] == "chunk-1"


def test_follow_up_prompt_requires_chunk_text_and_contextualized_evidence():
    prompt = FOLLOW_UP_GENERATION_PROMPT.format(
        lead_name="Alex Morgan",
        lead_company="TechCorp Global",
        lead_title="VP of Revenue Operations",
        pain_points="Manual data entry is bottlenecking SDR response latency.",
        business_need="Automate sales qualification workflows.",
        action_decision="Schedule Technical Architecture Demo",
        retrieved_chunks='[{"document_name":"13 Case Studies","text":"Krypton Commerce reduced response time from 48 hours to 18 minutes."}]',
    )

    assert "Krypton Commerce reduced response time from 48 hours to 18 minutes." in prompt
    assert "document names and metadata as identifiers, never as evidence" in prompt
    assert "preserve the specific result and the customer/context" in prompt
    assert "operational velocity gains" not in prompt
