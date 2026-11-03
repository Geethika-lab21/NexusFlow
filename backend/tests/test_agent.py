import uuid
import pytest
from app.core.exceptions import BusinessRuleViolationException
from app.models.orm_models import AgentRun, FollowUpDraft, Lead
from app.services.followup_service import FollowUpService
from app.agents.graph import run_agent_workflow
from app.agents import nodes

def test_complete_agent_workflow(db_session, sample_lead_dict):
    # Create temporary lead in DB
    lead_id = str(uuid.uuid4())
    lead = Lead(id=lead_id, **sample_lead_dict)
    lead.email = f"agent_test_{uuid.uuid4().hex[:6]}@techcorp.com"
    db_session.add(lead)
    db_session.commit()

    run_id = str(uuid.uuid4())
    final_state = run_agent_workflow(
        lead_id=lead_id,
        run_id=run_id,
        db=db_session,
        requested_by="pytest_runner"
    )

    assert final_state["current_node"] in ["completed", "human_approval"]
    assert final_state["priority_score"] is not None
    assert final_state["conversion_probability"] is not None
    assert len(final_state["retrieved_chunks"]) > 0
    assert final_state["draft"] is not None
    assert len(final_state["step_traces"]) >= 8
    assert final_state["requires_human_approval"] is True
    assert final_state["approval_status"] == "awaiting_approval"
    assert "immediate operational velocity gains" not in final_state["draft"]["body"].lower()
    assert "Manual data entry is bottlenecking SDR response latency." in final_state["draft"]["body"]
    assert "manual data entry bottlenecks sdr response latency" not in final_state["draft"]["body"]

    persisted_run = db_session.query(AgentRun).filter(AgentRun.id == run_id).one()
    persisted_draft = db_session.query(FollowUpDraft).filter(FollowUpDraft.id == final_state["draft_id"]).one()
    assert persisted_run.status == "awaiting_approval"
    assert persisted_draft.agent_run_id == run_id
    assert persisted_draft.status == "pending_approval"
    assert persisted_draft.source_references

    with pytest.raises(BusinessRuleViolationException, match="must be approved"):
        FollowUpService.simulate_send(db_session, persisted_draft.id)

    FollowUpService.approve_draft(db_session, persisted_draft.id, approved_by="pytest")
    send_result = FollowUpService.simulate_send(db_session, persisted_draft.id)
    assert send_result["success"] is True
    assert persisted_draft.status == "simulated_sent"


def test_openai_draft_prompt_receives_all_retrieved_text_and_metadata(
    db_session,
    sample_lead_dict,
    monkeypatch,
):
    lead_id = str(uuid.uuid4())
    lead = Lead(id=lead_id, **sample_lead_dict)
    lead.email = f"prompt_test_{uuid.uuid4().hex[:6]}@techcorp.com"
    db_session.add(lead)
    db_session.commit()

    retrieved_chunks = [
        {
            "chunk_id": f"chunk-{index}",
            "document_id": f"doc-{index}",
            "document_name": f"Document {index}",
            "category": "Test evidence",
            "text": (
                "Krypton Commerce reduced response time from 48 hours to 18 minutes and "
                "saved 32 SDR hours weekly across an 8-person team."
                if index == 5
                else f"Exact retrieved source passage {index}."
            ),
            "rrf_score": 0.02,
            "retrieval_method": "hybrid_rrf",
        }
        for index in range(1, 6)
    ]
    prompts = []

    def capture_prompt(prompt):
        prompts.append(prompt)
        if "Retrieved knowledge chunks (" in prompt:
            return {
                "subject": "Immediate operational velocity gains",
                "body": (
                    "Hi Alex,\n\n"
                    "Companies tackling similar initiatives saw immediate operational velocity gains.\n\n"
                    "Krypton Commerce reduced response time from 48 hours to 18 minutes and "
                    "saved 32 SDR hours weekly across an 8-person team.\n\n"
                    "Would you be open to discussing this further?"
                ),
            }
        return {}

    monkeypatch.setattr(nodes.settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(nodes.settings, "OPENAI_API_KEY", "configured-for-test")
    monkeypatch.setattr(nodes, "call_llm_json", capture_prompt)
    monkeypatch.setattr(
        nodes,
        "search_knowledge_base",
        lambda query, top_k: retrieved_chunks,
    )

    run_id = str(uuid.uuid4())
    final_state = run_agent_workflow(
        lead_id=lead_id,
        run_id=run_id,
        db=db_session,
        requested_by="pytest_prompt",
    )

    draft_prompt = next(prompt for prompt in prompts if "Retrieved knowledge chunks" in prompt)
    assert "Krypton Commerce reduced response time from 48 hours to 18 minutes" in draft_prompt
    assert '"document_id": "doc-5"' in draft_prompt
    assert '"category": "Test evidence"' in draft_prompt
    assert final_state["draft"] is not None
    assert "immediate operational velocity gains" not in final_state["draft"]["body"].lower()
    assert final_state["draft"]["subject"] == f"NexusFlow follow-up for {lead.company}"
    assert (
        "Krypton Commerce reduced response time from 48 hours to 18 minutes and saved "
        "32 SDR hours weekly across an 8-person team."
    ) in final_state["draft"]["body"]
