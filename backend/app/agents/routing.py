from app.agents.state import AgentState

def route_after_load(state: AgentState) -> str:
    if not state.get("lead") or state.get("errors"):
        return "complete_persist"
    return "gather_context"

def route_after_context(state: AgentState) -> str:
    if state.get("skip_reason"):
        return "complete_persist"
    return "analyze_intelligence"

def route_after_retrieval(state: AgentState) -> str:
    return "decide_next_action"

def route_after_validation(state: AgentState) -> str:
    if state.get("errors"):
        return "complete_persist"
    if state.get("requires_human_approval", True):
        return "human_approval"
    return "execute_action"

def route_after_approval(state: AgentState) -> str:
    return "complete_persist"

def route_after_execution(state: AgentState) -> str:
    return "complete_persist"
