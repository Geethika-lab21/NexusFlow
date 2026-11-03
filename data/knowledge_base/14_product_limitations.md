# NexusFlow Product Limitations & Unsupported Use Cases

## Unsupported Scenarios & Architectural Boundaries

### 1. High-Frequency Real-Time Telemetry & IoT
- NexusFlow is optimized for B2B sales operations where data updates occur in polling intervals or batch runs (typically 1 to 5 minutes).
- It is **not** designed for sub-second algorithmic trading, real-time industrial SCADA systems, or high-throughput IoT sensor telemetry.

### 2. Autonomous Outbound Voice Calling
- While NexusFlow generates comprehensive phone discovery scripts, talk tracks, and battlecard notes, it does **not** feature automated voice synthesizers or cold-calling telephony dialers.

### 3. Unsupervised Fully Autonomous Sending Without Guardrails
- NexusFlow enforces governance policies (such as human approval gates) to safeguard company brand reputation and prevent compliance violations. Autonomous bulk spam blasts are strictly unsupported and restricted by system policies.

### 4. Non-Structured Non-Text Binary Media Analysis
- NexusFlow processes structured tabular CRM records and textual knowledge collateral (PDF, DOCX, TXT, Markdown). It does not analyze raw video footage, 3D CAD models, or binary executable blobs.
