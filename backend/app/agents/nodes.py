import time
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.agents.state import AgentState
from app.agents.tools import (
    get_lead,
    get_interaction_history,
    search_knowledge_base,
    predict_conversion_probability,
    calculate_lead_priority,
    save_lead_analysis,
    create_follow_up_draft,
    check_contact_policy,
    simulate_email_send,
    log_interaction
)
from app.agents.prompts import (
    DemoLLMProvider,
    call_llm_json,
    LEAD_ANALYSIS_PROMPT,
    ACTION_DECISION_PROMPT,
    FOLLOW_UP_GENERATION_PROMPT,
    remove_unverified_outcome_claims
)
from app.models.orm_models import AgentRun, AgentStep, FollowUpDraft, LeadAnalysis
from app.config import settings
from app.utils.helpers import safe_json_dumps, safe_json_loads


def _record_trace(state: AgentState, node_name: str, tool_name: str, status: str, input_summary: str, output_summary: str, duration_ms: float, db: Session):
    order = len(state["step_traces"]) + 1
    trace = {
        "step_order": order,
        "node_name": node_name,
        "tool_name": tool_name,
        "status": status,
        "input_summary": input_summary[:200],
        "output_summary": output_summary[:200],
        "duration_ms": round(duration_ms, 2),
        "created_at": datetime.utcnow().isoformat()
    }
    state["step_traces"].append(trace)

    # Persist step to DB if run_id exists
    try:
        step_record = AgentStep(
            run_id=state["run_id"],
            step_order=order,
            node_name=node_name,
            tool_name=tool_name,
            status=status,
            input_summary=input_summary[:500],
            output_summary=output_summary[:500],
            duration_ms=round(duration_ms, 2)
        )
        db.add(step_record)
        db.commit()
    except Exception as e:
        db.rollback()


# Node 1: Load and Validate Lead
def node_load_and_validate_lead(state: AgentState, db: Session) -> AgentState:
    t0 = time.time()
    state["current_node"] = "load_lead"
    lead_id = state["lead_id"]

    lead = get_lead(lead_id, db)
    dur = (time.time() - t0) * 1000

    if not lead:
        state["skip_reason"] = f"Lead with ID {lead_id} not found."
        state["errors"].append(state["skip_reason"])
        state["current_node"] = "invalid_lead"
        _record_trace(state, "load_lead", "get_lead", "failed", f"lead_id={lead_id}", "Lead not found", dur, db)
        return state

    state["lead"] = lead
    _record_trace(state, "load_lead", "get_lead", "success", f"lead_id={lead_id}", f"Loaded lead {lead['company']}", dur, db)
    return state


# Node 2: Gather Context
def node_gather_context(state: AgentState, db: Session) -> AgentState:
    t0 = time.time()
    state["current_node"] = "gather_context"
    lead_id = state["lead_id"]

    interactions = get_interaction_history(lead_id, db, limit=10)
    state["interactions"] = interactions

    # Existing analyses & drafts
    existing_drafts = db.query(FollowUpDraft).filter(FollowUpDraft.lead_id == lead_id).all()
    state["existing_drafts"] = [
        {"id": d.id, "status": d.status, "subject": d.subject, "created_at": d.created_at.isoformat()}
        for d in existing_drafts
    ]

    existing_analyses = db.query(LeadAnalysis).filter(LeadAnalysis.lead_id == lead_id).all()
    state["existing_analyses"] = [
        {"id": a.id, "conversion_probability": a.conversion_probability, "priority_score": a.priority_score}
        for a in existing_analyses
    ]

    # Check if a pending draft already exists
    pending = [d for d in existing_drafts if d.status == "pending_approval"]
    if pending:
        state["warnings"].append(f"Lead already has {len(pending)} pending follow-up drafts.")

    dur = (time.time() - t0) * 1000
    _record_trace(state, "gather_context", "get_interaction_history", "success", f"lead_id={lead_id}", f"Found {len(interactions)} interactions, {len(existing_drafts)} drafts", dur, db)
    return state


# Node 3: Analyze Intelligence
def node_analyze_intelligence(state: AgentState, db: Session) -> AgentState:
    t0 = time.time()
    state["current_node"] = "analyze_intelligence"
    lead = state["lead"]

    # 1. ML Prediction
    pred_res = predict_conversion_probability(lead)
    state["conversion_probability"] = pred_res["probability"]
    state["feature_contributions"] = pred_res.get("feature_contributions", [])

    # 2. Priority Scoring
    score_res = calculate_lead_priority(lead)
    state["priority_score"] = score_res["score"]
    state["priority_category"] = score_res["category"]

    # 3. LLM or Demo Analysis
    analysis_dict = {}
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        prompt = LEAD_ANALYSIS_PROMPT.format(
            lead_json=safe_json_dumps(lead),
            conversion_probability=state["conversion_probability"],
            priority_score=state["priority_score"],
            priority_category=state["priority_category"]
        )
        analysis_dict = call_llm_json(prompt)

    if not analysis_dict:
        analysis_dict = DemoLLMProvider.analyze_lead(
            lead=lead,
            prob=state["conversion_probability"],
            score=state["priority_score"],
            category=state["priority_category"]
        )

    state["positive_indicators"] = analysis_dict.get("positive_indicators", [])
    state["negative_indicators"] = analysis_dict.get("negative_indicators", [])
    state["missing_information"] = analysis_dict.get("missing_information", [])
    state["recommended_action"] = analysis_dict.get("recommended_action", "Send Follow-up")
    state["action_rationale"] = analysis_dict.get("action_rationale", "")

    # Save to DB
    save_lead_analysis({
        "lead_id": lead["id"],
        "conversion_probability": state["conversion_probability"],
        "priority_score": state["priority_score"],
        "priority_category": state["priority_category"],
        "positive_indicators": state["positive_indicators"],
        "negative_indicators": state["negative_indicators"],
        "missing_information": state["missing_information"],
        "feature_contributions": state["feature_contributions"],
        "recommended_action": state["recommended_action"],
        "action_rationale": state["action_rationale"],
        "model_version": pred_res.get("model_version", "1.0.0")
    }, db)

    dur = (time.time() - t0) * 1000
    _record_trace(
        state, "analyze_intelligence", "predict_conversion_probability + calculate_lead_priority",
        "success", f"lead={lead['id']}", f"Prob={state['conversion_probability']}, Score={state['priority_score']} ({state['priority_category']})",
        dur, db
    )
    return state


# Node 4: Determine Retrieval Needs
def node_determine_retrieval_needs(state: AgentState, db: Session) -> AgentState:
    t0 = time.time()
    state["current_node"] = "determine_retrieval_needs"
    lead = state["lead"]

    pain = lead.get("pain_points") or ""
    need = lead.get("business_need") or ""
    product = lead.get("product_interest") or "workflow automation"

    query_parts = []
    if pain:
        query_parts.append(pain)
    if need:
        query_parts.append(need)
    if product:
        query_parts.append(product)

    query = " ".join(query_parts) if query_parts else "NexusFlow sales workflow automation"
    state["retrieval_query"] = query[:300]

    dur = (time.time() - t0) * 1000
    _record_trace(state, "determine_retrieval_needs", "query_builder", "success", "pain_points + need", f"Built query: {state['retrieval_query'][:80]}...", dur, db)
    return state


# Node 5: Retrieve Knowledge
def node_retrieve_knowledge(state: AgentState, db: Session) -> AgentState:
    t0 = time.time()
    state["current_node"] = "retrieve_knowledge"
    query = state.get("retrieval_query") or "NexusFlow sales workflow automation"

    chunks = search_knowledge_base(query, top_k=settings.TOP_K_FINAL)
    state["retrieved_chunks"] = chunks
    state["source_ids"] = [c.get("chunk_id", "") for c in chunks]

    if not chunks:
        state["warnings"].append("No knowledge base chunks retrieved for query.")

    dur = (time.time() - t0) * 1000
    _record_trace(state, "retrieve_knowledge", "search_knowledge_base", "success", query[:80], f"Retrieved {len(chunks)} chunks", dur, db)
    return state


# Node 6: Decide Next Action
def node_decide_next_action(state: AgentState, db: Session) -> AgentState:
    t0 = time.time()
    state["current_node"] = "decide_next_action"

    decision = {}
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        prompt = ACTION_DECISION_PROMPT.format(
            analysis_json=safe_json_dumps({
                "action": state["recommended_action"],
                "rationale": state["action_rationale"]
            }),
            retrieved_chunks=safe_json_dumps(state["retrieved_chunks"][:2])
        )
        decision = call_llm_json(prompt)

    if not decision:
        decision = DemoLLMProvider.decide_action(
            analysis={"recommended_action": state["recommended_action"], "action_rationale": state["action_rationale"]},
            retrieved_chunks=state["retrieved_chunks"]
        )

    state["recommended_action"] = decision.get("action", state["recommended_action"])
    state["action_rationale"] = decision.get("rationale", state["action_rationale"])

    dur = (time.time() - t0) * 1000
    _record_trace(state, "decide_next_action", "decision_engine", "success", state["recommended_action"], f"Decided action: {state['recommended_action']}", dur, db)
    return state


# Node 7: Generate Draft
def node_generate_draft(state: AgentState, db: Session) -> AgentState:
    t0 = time.time()
    state["current_node"] = "generate_draft"
    lead = state["lead"]

    draft_dict = {}
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        prompt = FOLLOW_UP_GENERATION_PROMPT.format(
            lead_name=f"{lead['first_name']} {lead['last_name']}",
            lead_company=lead["company"],
            lead_title=lead["title"],
            pain_points=lead.get("pain_points", ""),
            business_need=lead.get("business_need", ""),
            action_decision=state["recommended_action"],
            retrieved_chunks=safe_json_dumps(state["retrieved_chunks"])
        )
        draft_dict = call_llm_json(prompt)
        for field in ("subject", "body", "rationale", "call_to_action"):
            if isinstance(draft_dict.get(field), str):
                draft_dict[field] = remove_unverified_outcome_claims(
                    draft_dict[field],
                    state["retrieved_chunks"],
                )
        if isinstance(draft_dict.get("personalization_points"), list):
            draft_dict["personalization_points"] = [
                remove_unverified_outcome_claims(point, state["retrieved_chunks"])
                for point in draft_dict["personalization_points"]
                if isinstance(point, str)
            ]

    if not draft_dict:
        draft_dict = DemoLLMProvider.generate_draft(
            lead=lead,
            action={"action": state["recommended_action"]},
            retrieved_chunks=state["retrieved_chunks"]
        )
    elif not str(draft_dict.get("body") or "").strip():
        draft_dict = DemoLLMProvider.generate_draft(
            lead=lead,
            action={"action": state["recommended_action"]},
            retrieved_chunks=state["retrieved_chunks"]
        )
    if not str(draft_dict.get("subject") or "").strip():
        draft_dict["subject"] = f"NexusFlow follow-up for {lead['company']}"

    draft_data = {
        "lead_id": lead["id"],
        "agent_run_id": state["run_id"],
        "channel": draft_dict.get("channel", "email"),
        "subject": draft_dict.get("subject", "NexusFlow Follow-Up"),
        "body": draft_dict["body"],
        "personalization_points": draft_dict.get("personalization_points", []),
        "rationale": draft_dict.get("rationale", ""),
        "source_references": draft_dict.get("source_references", []),
        "call_to_action": draft_dict.get("call_to_action"),
        "status": "pending_approval"
    }

    draft_id = create_follow_up_draft(draft_data, db)
    draft_data["id"] = draft_id
    state["draft"] = draft_data
    state["draft_id"] = draft_id
    state["channel"] = draft_data["channel"]

    dur = (time.time() - t0) * 1000
    _record_trace(state, "generate_draft", "create_follow_up_draft", "success", f"lead={lead['id']}", f"Draft created {draft_id}", dur, db)
    return state


# Node 8: Validate Output
def node_validate_output(state: AgentState, db: Session) -> AgentState:
    t0 = time.time()
    state["current_node"] = "validate_output"
    lead_id = state["lead_id"]

    # Check contact policy
    policy_res = check_contact_policy(lead_id, db)
    if not policy_res["allowed"]:
        state["warnings"].append(policy_res["reason"])
        state["approval_status"] = "policy_restricted"

    # Check requirement for approval
    state["requires_human_approval"] = settings.REQUIRE_APPROVAL

    dur = (time.time() - t0) * 1000
    _record_trace(state, "validate_output", "check_contact_policy", "success", f"lead={lead_id}", f"Policy allowed={policy_res['allowed']}, ApprovalRequired={state['requires_human_approval']}", dur, db)
    return state


# Node 9: Human Approval
def node_human_approval(state: AgentState, db: Session) -> AgentState:
    t0 = time.time()
    state["current_node"] = "human_approval"
    state["approval_status"] = "awaiting_approval"

    # Update run status in DB
    run = db.query(AgentRun).filter(AgentRun.id == state["run_id"]).first()
    if run:
        run.status = "awaiting_approval"
        run.current_node = "human_approval"
        db.commit()

    dur = (time.time() - t0) * 1000
    _record_trace(state, "human_approval", "workflow_gate", "success", f"run={state['run_id']}", "Awaiting human review in follow-up center", dur, db)
    return state


# Node 10: Execute Action
def node_execute_action(state: AgentState, db: Session) -> AgentState:
    t0 = time.time()
    state["current_node"] = "execute_action"
    draft_id = state.get("draft_id")

    if draft_id:
        sim_res = simulate_email_send(draft_id, db)
        log_interaction({
            "lead_id": state["lead_id"],
            "interaction_type": "Email Sent",
            "direction": "outbound",
            "subject": state["draft"].get("subject"),
            "content": state["draft"].get("body", "")
        }, db)
        dur = (time.time() - t0) * 1000
        _record_trace(state, "execute_action", "simulate_email_send + log_interaction", "success", f"draft={draft_id}", sim_res.get("message", "Sent"), dur, db)
    else:
        dur = (time.time() - t0) * 1000
        _record_trace(state, "execute_action", "none", "skipped", "No draft to send", "Skipped", dur, db)

    return state


# Node 11: Complete and Persist
def node_complete_and_persist(state: AgentState, db: Session) -> AgentState:
    t0 = time.time()
    state["current_node"] = "completed"
    now_dt = datetime.utcnow()
    state["completed_at"] = now_dt.isoformat()

    start_dt = datetime.fromisoformat(state["started_at"]) if state["started_at"] else now_dt
    duration = (now_dt - start_dt).total_seconds()

    run = db.query(AgentRun).filter(AgentRun.id == state["run_id"]).first()
    if run:
        if state["requires_human_approval"] and state.get("approval_status") == "awaiting_approval":
            run.status = "awaiting_approval"
        elif state.get("errors"):
            run.status = "failed"
            run.error_message = "; ".join(state["errors"])
        elif state.get("skip_reason"):
            run.status = "skipped"
            run.skip_reason = state["skip_reason"]
        else:
            run.status = "completed"

        run.current_node = state["current_node"]
        run.completed_at = now_dt
        run.duration_seconds = round(duration, 2)
        run.metadata_json = safe_json_dumps({
            "priority_score": state.get("priority_score"),
            "conversion_probability": state.get("conversion_probability"),
            "warnings": state.get("warnings", []),
            "draft_id": state.get("draft_id")
        })
        db.commit()

    dur = (time.time() - t0) * 1000
    _record_trace(state, "completed", "agent_run_persistence", "success", f"run={state['run_id']}", f"Completed run in {duration:.2f}s", dur, db)
    return state
