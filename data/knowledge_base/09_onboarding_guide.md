# NexusFlow Customer Onboarding Guide

## Implementation Timeline & Milestones

### Phase 1: Environment Setup & CRM Sync (Days 1–3)
- Connect CRM authentication (Salesforce OAuth or HubSpot API token).
- Configure initial webhook endpoints for inbound lead capture.
- Verify lead field mappings (Company, Industry, Engagement metrics, Stage).

### Phase 2: Knowledge Ingestion & Grounding (Days 4–6)
- Upload product collateral, pricing sheets, objection playbooks, and competitor matrices.
- Run automated hybrid indexing (BM25 + Semantic dense embeddings).
- Conduct test queries in the Knowledge Base interface to verify retrieval accuracy.

### Phase 3: Model Calibration & Scoring Customization (Days 7–10)
- Train the initial ML model using historical CRM lead export.
- Adjust heuristic priority scoring weights according to ICP criteria.
- Establish threshold boundaries for High (>=65), Medium (>=40), and Low (<40).

### Phase 4: SDR Team Enablement & Live Rollout (Days 11–14)
- Train SDRs and Account Executives on review queue navigation.
- Configure human approval policy rules (all drafts require manager signoff during initial 30 days).
- Begin automated daily batch triage and measure rep time savings.
