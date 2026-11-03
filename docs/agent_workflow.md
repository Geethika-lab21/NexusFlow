# NexusFlow Agent Workflow

## LangGraph StateGraph Architecture
The agent automates SDR lead qualification and follow-up generation using an 11-node directed graph.

```mermaid
graph TD
    Start([Start]) --> load_lead[Load and Validate Lead]
    load_lead -->|Valid| gather_context[Gather Context & History]
    load_lead -->|Invalid| End([End])
    
    gather_context -->|Proceed| analyze_intel[Analyze Intelligence ML & Heuristics]
    gather_context -->|Pending Follow-up| End
    
    analyze_intel --> determine_retrieval[Determine Knowledge Needs]
    determine_retrieval --> retrieve_kb[Retrieve Knowledge Chunks]
    retrieve_kb --> decide_action[Decide Next Action]
    decide_action --> generate_draft[Generate Follow-up Draft]
    generate_draft --> validate_output[Validate Draft & Contact Policy]
    
    validate_output -->|Requires Approval| human_approval[Await Human Approval]
    validate_output -->|Pre-Approved / Demo| execute_action[Execute Action & Simulation]
    
    human_approval --> complete_persist[Complete & Persist Run]
    execute_action --> complete_persist
    complete_persist --> End
```

## Node Responsibilities
1. `load_lead`: Queries lead database and validates current status.
2. `gather_context`: Collects past interactions, previous analyses, active drafts.
3. `analyze_intelligence`: Calculates priority score & conversion probability.
4. `determine_retrieval`: Extracts search queries from lead pain points.
5. `retrieve_kb`: Executes hybrid search against Knowledge Base.
6. `decide_action`: Recommends next sales action with clear rationale.
7. `generate_draft`: Crafts personalized email or LinkedIn draft grounded in RAG sources.
8. `validate_output`: Checks schema integrity, contact frequency policy, and approval flags.
9. `human_approval`: Gates sending behind sales manager confirmation.
10. `execute_action`: Logs interaction and updates draft state.
11. `complete_persist`: Computes run duration, records step traces, persists telemetry.
