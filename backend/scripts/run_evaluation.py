import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.evaluation.evaluator import SystemEvaluator
from app.utils.helpers import safe_json_loads


def main():
    init_db()
    db = SessionLocal()
    try:
        print("Running comprehensive system evaluation (ML, RAG, Agent)...")
        eval_run = SystemEvaluator.run_full_evaluation(db)
        print(f"\nEvaluation Run ID: {eval_run.id}")
        print(f"Status: {eval_run.status}")

        metrics = safe_json_loads(eval_run.metrics, {})
        ml_m = metrics.get("ml", {})
        rag_m = metrics.get("rag", {})
        agent_m = metrics.get("agent", {})

        print("\n--- ML Model Metrics ---")
        print(f"  Accuracy:  {ml_m.get('accuracy')}")
        print(f"  Precision: {ml_m.get('precision')}")
        print(f"  Recall:    {ml_m.get('recall')}")
        print(f"  F1-Score:  {ml_m.get('f1')}")
        print(f"  ROC-AUC:   {ml_m.get('roc_auc')}")

        print("\n--- RAG Retrieval Metrics ---")
        print(f"  Recall@5:  {rag_m.get('recall_at_5')}%")
        print(f"  MRR:       {rag_m.get('mrr')}")
        print(f"  Latency:   {rag_m.get('avg_latency_ms')} ms")

        print("\n--- Agent Workflow Metrics ---")
        print(f"  Total Runs:             {agent_m.get('total_runs')}")
        print(f"  Workflow Completion:    {agent_m.get('workflow_completion_rate')}%")
        print(f"  Approval Compliance:    {agent_m.get('approval_compliance_rate')}%")

        print("\nEvaluation successfully recorded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
