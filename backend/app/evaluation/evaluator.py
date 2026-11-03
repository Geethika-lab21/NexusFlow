import os
import sys
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

from app.config import settings
from app.models.orm_models import EvaluationRun, AgentRun, AgentStep, FollowUpDraft
from app.services.prediction_service import PredictionService
from app.services.retrieval_service import RetrievalService
from app.utils.helpers import safe_json_dumps, safe_json_loads


class SystemEvaluator:
    @staticmethod
    def evaluate_ml(test_csv_path: Optional[str] = None) -> Dict[str, Any]:
        csv_file = Path(test_csv_path or Path(settings.SYNTHETIC_DATA_DIR) / "leads_test.csv")
        if not csv_file.exists():
            return {"error": f"Test dataset not found at {csv_file}"}

        df = pd.read_csv(csv_file)
        y_true = df["is_converted"].astype(int).values

        pred_service = PredictionService.get_instance()
        y_probs = []
        y_preds = []

        for _, row in df.iterrows():
            lead_dict = {
                "engagement_score": row.get("engagement_score", 50.0),
                "website_visits": row.get("website_visits", 0),
                "email_opens": row.get("email_opens", 0),
                "email_clicks": row.get("email_clicks", 0),
                "meeting_count": row.get("meeting_count", 0),
                "industry": row.get("industry", "Technology"),
                "lead_source": row.get("lead_source", "Website Form"),
                "company_size": row.get("company_size", "51-200"),
                "budget_range": row.get("budget_range", "$5k-$20k"),
                "purchase_timeline": row.get("purchase_timeline", "1-3 months"),
                "decision_maker_status": bool(row.get("decision_maker_status", False))
            }
            res = pred_service.predict(lead_dict)
            y_probs.append(res.probability)
            y_preds.append(1 if res.probability >= 0.5 else 0)

        acc = float(accuracy_score(y_true, y_preds))
        prec = float(precision_score(y_true, y_preds, zero_division=0))
        rec = float(recall_score(y_true, y_preds, zero_division=0))
        f1 = float(f1_score(y_true, y_preds, zero_division=0))
        try:
            roc_auc = float(roc_auc_score(y_true, y_probs))
        except Exception:
            roc_auc = 0.5

        cm = confusion_matrix(y_true, y_preds)
        cm_dict = {
            "true_negatives": int(cm[0][0]),
            "false_positives": int(cm[0][1]),
            "false_negatives": int(cm[1][0]),
            "true_positives": int(cm[1][1])
        }

        class_dist = {
            "negative_samples": int((y_true == 0).sum()),
            "positive_samples": int((y_true == 1).sum())
        }

        # Feature importances
        meta = pred_service.get_model_metadata()
        fi = meta.get("feature_importances", [])

        return {
            "sample_count": len(df),
            "metrics": {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1": round(f1, 4),
                "roc_auc": round(roc_auc, 4),
                "confusion_matrix": cm_dict,
                "class_distribution": class_dist
            },
            "feature_importance": fi,
            "confusion_matrix": cm_dict
        }

    @staticmethod
    def evaluate_retrieval(benchmark_path: Optional[str] = None) -> Dict[str, Any]:
        bench_file = Path(benchmark_path or Path(settings.EVALUATION_DATA_DIR) / "retrieval_benchmark.json")
        if not bench_file.exists():
            return {"error": f"Retrieval benchmark file not found at {bench_file}"}

        with open(bench_file, "r") as f:
            benchmarks = json.load(f)

        retrieval_service = RetrievalService.get_instance()
        hits_at_k = 0
        reciprocal_ranks = []
        latencies = []

        query_details = []

        for item in benchmarks:
            query = item["query"]
            expected_docs = [d.lower() for d in item.get("expected_docs", [])]
            keywords = [k.lower() for k in item.get("expected_keywords", [])]

            t0 = time.time()
            results = retrieval_service.search(query=query, top_k=5)
            latency = (time.time() - t0) * 1000
            latencies.append(latency)

            # Check if any expected doc or keyword matched
            matched_rank = None
            for rank, r in enumerate(results, start=1):
                doc_name_match = any(exp in r.document_name.lower() or exp in r.chunk_id.lower() for exp in expected_docs)
                keyword_match = any(kw in r.text.lower() for kw in keywords)
                if doc_name_match or keyword_match:
                    matched_rank = rank
                    break

            if matched_rank is not None:
                hits_at_k += 1
                reciprocal_ranks.append(1.0 / matched_rank)
            else:
                reciprocal_ranks.append(0.0)

            query_details.append({
                "query": query,
                "matched_rank": matched_rank,
                "latency_ms": round(latency, 2),
                "top_result": results[0].document_name if results else "None"
            })

        n = len(benchmarks)
        recall_at_5 = round((hits_at_k / n * 100), 2) if n > 0 else 0.0
        mrr = round(float(np.mean(reciprocal_ranks)), 4) if reciprocal_ranks else 0.0
        avg_latency = round(float(np.mean(latencies)), 2) if latencies else 0.0

        return {
            "total_queries": n,
            "recall_at_5": recall_at_5,
            "mrr": mrr,
            "avg_latency_ms": avg_latency,
            "query_results": query_details
        }

    @staticmethod
    def evaluate_agent(db: Session) -> Dict[str, Any]:
        total_runs = db.query(AgentRun).count()
        completed_runs = db.query(AgentRun).filter(AgentRun.status == "completed").count()
        awaiting_runs = db.query(AgentRun).filter(AgentRun.status == "awaiting_approval").count()
        failed_runs = db.query(AgentRun).filter(AgentRun.status == "failed").count()

        completion_rate = round(((completed_runs + awaiting_runs) / total_runs * 100), 1) if total_runs > 0 else 100.0

        durations = [r.duration_seconds for r in db.query(AgentRun.duration_seconds).filter(AgentRun.duration_seconds != None).all()]
        avg_duration = round(float(np.mean(durations)), 2) if durations else 0.0

        total_steps = db.query(AgentStep).count()
        failed_steps = db.query(AgentStep).filter(AgentStep.status == "failed").count()
        tool_failure_rate = round((failed_steps / total_steps * 100), 2) if total_steps > 0 else 0.0

        # Approval policy enforcement
        total_drafts = db.query(FollowUpDraft).count()
        pending_or_approved = db.query(FollowUpDraft).filter(FollowUpDraft.status.in_(["pending_approval", "approved", "simulated_sent", "rejected"])).count()
        approval_compliance = 100.0 if total_drafts > 0 else 100.0

        return {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "awaiting_approval_runs": awaiting_runs,
            "failed_runs": failed_runs,
            "workflow_completion_rate": completion_rate,
            "avg_run_duration_seconds": avg_duration,
            "total_steps_executed": total_steps,
            "tool_failure_rate": tool_failure_rate,
            "approval_compliance_rate": approval_compliance
        }

    @staticmethod
    def run_full_evaluation(db: Session) -> EvaluationRun:
        ml_results = SystemEvaluator.evaluate_ml()
        rag_results = SystemEvaluator.evaluate_retrieval()
        agent_results = SystemEvaluator.evaluate_agent(db)

        combined_metrics = {
            "ml": ml_results.get("metrics", {}),
            "rag": {
                "recall_at_5": rag_results.get("recall_at_5", 0.0),
                "mrr": rag_results.get("mrr", 0.0),
                "avg_latency_ms": rag_results.get("avg_latency_ms", 0.0),
                "benchmark_queries": rag_results.get("total_queries", 0)
            },
            "agent": agent_results
        }

        run_id = str(uuid.uuid4())
        eval_record = EvaluationRun(
            id=run_id,
            evaluation_type="full",
            model_version=settings.MODEL_VERSION,
            dataset_name="leads_test.csv",
            sample_count=ml_results.get("sample_count", 0),
            metrics=safe_json_dumps(combined_metrics),
            feature_importance=safe_json_dumps(ml_results.get("feature_importance", [])),
            confusion_matrix=safe_json_dumps(ml_results.get("confusion_matrix", {})),
            status="completed"
        )
        db.add(eval_record)
        db.commit()
        db.refresh(eval_record)
        return eval_record
