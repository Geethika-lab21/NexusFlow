import uuid
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes import (
    node_load_and_validate_lead,
    node_gather_context,
    node_analyze_intelligence,
    node_determine_retrieval_needs,
    node_retrieve_knowledge,
    node_decide_next_action,
    node_generate_draft,
    node_validate_output,
    node_human_approval,
    node_execute_action,
    node_complete_and_persist
)
from app.agents.routing import (
    route_after_load,
    route_after_context,
    route_after_retrieval,
    route_after_validation,
    route_after_approval,
    route_after_execution
)
from app.models.orm_models import AgentRun
from app.config import settings


def build_agent_graph(db: Session):
    workflow = StateGraph(AgentState)

    # 11 Nodes with DB context
    workflow.add_node("load_lead", lambda state: node_load_and_validate_lead(state, db))
    workflow.add_node("gather_context", lambda state: node_gather_context(state, db))
    workflow.add_node("analyze_intelligence", lambda state: node_analyze_intelligence(state, db))
    workflow.add_node("determine_retrieval_needs", lambda state: node_determine_retrieval_needs(state, db))
    workflow.add_node("retrieve_knowledge", lambda state: node_retrieve_knowledge(state, db))
    workflow.add_node("decide_next_action", lambda state: node_decide_next_action(state, db))
    workflow.add_node("generate_draft", lambda state: node_generate_draft(state, db))
    workflow.add_node("validate_output", lambda state: node_validate_output(state, db))
    workflow.add_node("human_approval", lambda state: node_human_approval(state, db))
    workflow.add_node("execute_action", lambda state: node_execute_action(state, db))
    workflow.add_node("complete_persist", lambda state: node_complete_and_persist(state, db))

    # Graph connectivity
    workflow.set_entry_point("load_lead")

    workflow.add_conditional_edges(
        "load_lead",
        route_after_load,
        {
            "complete_persist": "complete_persist",
            "gather_context": "gather_context"
        }
    )

    workflow.add_conditional_edges(
        "gather_context",
        route_after_context,
        {
            "complete_persist": "complete_persist",
            "analyze_intelligence": "analyze_intelligence"
        }
    )

    workflow.add_edge("analyze_intelligence", "determine_retrieval_needs")
    workflow.add_edge("determine_retrieval_needs", "retrieve_knowledge")

    workflow.add_conditional_edges(
        "retrieve_knowledge",
        route_after_retrieval,
        {
            "decide_next_action": "decide_next_action"
        }
    )

    workflow.add_edge("decide_next_action", "generate_draft")
    workflow.add_edge("generate_draft", "validate_output")

    workflow.add_conditional_edges(
        "validate_output",
        route_after_validation,
        {
            "complete_persist": "complete_persist",
            "human_approval": "human_approval",
            "execute_action": "execute_action"
        }
    )

    workflow.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "complete_persist": "complete_persist"
        }
    )

    workflow.add_conditional_edges(
        "execute_action",
        route_after_execution,
        {
            "complete_persist": "complete_persist"
        }
    )

    workflow.add_edge("complete_persist", END)

    return workflow.compile()


def run_agent_workflow(lead_id: str, run_id: str, db: Session, requested_by: str = "user") -> AgentState:
    now = datetime.utcnow()
    initial_state: AgentState = {
        "lead_id": lead_id,
        "run_id": run_id,
        "requested_by": requested_by,
        "lead": None,
        "interactions": [],
        "existing_analyses": [],
        "existing_drafts": [],
        "conversion_probability": None,
        "priority_score": None,
        "priority_category": None,
        "positive_indicators": [],
        "negative_indicators": [],
        "missing_information": [],
        "feature_contributions": [],
        "retrieval_query": None,
        "retrieved_chunks": [],
        "source_ids": [],
        "recommended_action": None,
        "action_rationale": None,
        "draft": None,
        "draft_id": None,
        "channel": "email",
        "current_node": "initialized",
        "errors": [],
        "warnings": [],
        "requires_human_approval": settings.REQUIRE_APPROVAL,
        "approval_status": None,
        "skip_reason": None,
        "retry_count": 0,
        "llm_mode": settings.LLM_PROVIDER,
        "started_at": now.isoformat(),
        "completed_at": None,
        "step_traces": []
    }

    # Ensure AgentRun record exists
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        run = AgentRun(
            id=run_id,
            lead_id=lead_id,
            requested_by=requested_by,
            status="running",
            current_node="initialized",
            started_at=now
        )
        db.add(run)
        db.commit()
    else:
        run.status = "running"
        db.commit()

    compiled_graph = build_agent_graph(db)
    final_state = compiled_graph.invoke(initial_state)

    return final_state
