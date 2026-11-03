# NexusFlow Evaluation Framework

## 1. Machine Learning Evaluation
- **Dataset**: Stratified 70/30 split of synthetic leads.
- **Metrics Tracked**:
  - Accuracy
  - Precision
  - Recall
  - F1-Score
  - ROC-AUC
  - Confusion Matrix (TP, FP, TN, FN)
  - Feature Importance (Permutation or tree-based coefficients)

## 2. RAG Retrieval Evaluation
- **Benchmark Suite**: Ground-truth query questions mapped to expected document IDs and key phrases.
- **Metrics**:
  - Recall@K ($K=5$)
  - Mean Reciprocal Rank (MRR)
  - Average Retrieval Latency (ms)

## 3. Agent Execution Telemetry
- Workflow completion rate
- Tool invocation success rate
- Step trace durations
- Human approval policy compliance
