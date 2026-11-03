import os
import sys
import json
import joblib
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
from sklearn.model_selection import cross_val_score, StratifiedKFold

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

COMPANY_SIZE_MAP = {
    "1-10": 1,
    "11-50": 2,
    "51-200": 3,
    "201-500": 4,
    "501-2000": 5,
    "2001+": 6
}

BUDGET_MAP = {
    "Under $5k": 1,
    "$5k-$20k": 2,
    "$20k-$50k": 3,
    "$50k-$100k": 4,
    "$100k+": 5
}

TIMELINE_MAP = {
    "Immediate": 5,
    "1-3 months": 4,
    "3-6 months": 3,
    "6-12 months": 2,
    "12+ months": 1
}


def preprocess_dataframe(df: pd.DataFrame, reference_date: datetime = None) -> pd.DataFrame:
    df_feat = df.copy()
    if reference_date is None:
        reference_date = datetime.utcnow()

    # Calculate days since created
    if "created_at" in df_feat.columns:
        created_dt = pd.to_datetime(df_feat["created_at"])
        df_feat["days_since_created"] = (reference_date - created_dt).dt.total_seconds() / 86400.0
    else:
        df_feat["days_since_created"] = 30.0

    # Ordinal mappings
    df_feat["company_size_encoded"] = df_feat["company_size"].map(COMPANY_SIZE_MAP).fillna(2)
    df_feat["budget_range_encoded"] = df_feat["budget_range"].map(BUDGET_MAP).fillna(2)
    df_feat["timeline_encoded"] = df_feat["purchase_timeline"].map(TIMELINE_MAP).fillna(3)
    df_feat["decision_maker_status"] = df_feat["decision_maker_status"].astype(int)

    return df_feat


def train_lead_scoring_models():
    synthetic_dir = PROJECT_DIR / "data" / "synthetic"
    artifacts_dir = PROJECT_DIR / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    train_path = synthetic_dir / "leads_train.csv"
    test_path = synthetic_dir / "leads_test.csv"

    if not train_path.exists() or not test_path.exists():
        from scripts.seed_data import generate_synthetic_dataset
        generate_synthetic_dataset()

    train_raw = pd.read_csv(train_path)
    test_raw = pd.read_csv(test_path)

    now = datetime.utcnow()
    train_df = preprocess_dataframe(train_raw, reference_date=now)
    test_df = preprocess_dataframe(test_raw, reference_date=now)

    numeric_features = [
        "engagement_score", "website_visits", "email_opens",
        "email_clicks", "meeting_count", "days_since_created"
    ]
    categorical_features = ["industry", "lead_source"]
    ordinal_features = [
        "company_size_encoded", "budget_range_encoded",
        "timeline_encoded", "decision_maker_status"
    ]

    feature_cols = numeric_features + categorical_features + ordinal_features

    X_train = train_df[feature_cols]
    y_train = train_df["is_converted"].astype(int)

    X_test = test_df[feature_cols]
    y_test = test_df["is_converted"].astype(int)

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler())
                ]),
                numeric_features
            ),
            (
                "cat",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
                ]),
                categorical_features
            ),
            (
                "ord",
                SimpleImputer(strategy="most_frequent"),
                ordinal_features
            ),
        ]
    )

    lr_pipeline = Pipeline([
        ("prep", preprocessor),
        ("clf", LogisticRegression(max_iter=1000, random_state=42))
    ])

    rf_pipeline = Pipeline([
        ("prep", preprocessor),
        ("clf", RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42))
    ])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    lr_cv_scores = cross_val_score(lr_pipeline, X_train, y_train, cv=cv, scoring="f1")
    rf_cv_scores = cross_val_score(rf_pipeline, X_train, y_train, cv=cv, scoring="f1")

    print(f"Logistic Regression 5-fold CV F1: {lr_cv_scores.mean():.4f} (+/- {lr_cv_scores.std():.4f})")
    print(f"Random Forest 5-fold CV F1: {rf_cv_scores.mean():.4f} (+/- {rf_cv_scores.std():.4f})")

    if rf_cv_scores.mean() >= lr_cv_scores.mean():
        selected_model_type = "RandomForest"
        best_pipeline = rf_pipeline
    else:
        selected_model_type = "LogisticRegression"
        best_pipeline = lr_pipeline

    best_pipeline.fit(X_train, y_train)

    y_pred = best_pipeline.predict(X_test)
    y_proba = best_pipeline.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_proba))
    cm = confusion_matrix(y_test, y_pred)

    cm_dict = {
        "true_negatives": int(cm[0][0]),
        "false_positives": int(cm[0][1]),
        "false_negatives": int(cm[1][0]),
        "true_positives": int(cm[1][1])
    }

    # Extract transformed feature names
    fitted_prep = best_pipeline.named_steps["prep"]
    cat_encoder = fitted_prep.named_transformers_["cat"].named_steps["encoder"]
    encoded_cat_names = list(cat_encoder.get_feature_names_out(categorical_features))
    all_feature_names = numeric_features + encoded_cat_names + ordinal_features

    feature_importances = []
    clf = best_pipeline.named_steps["clf"]
    if hasattr(clf, "feature_importances_"):
        raw_importances = clf.feature_importances_
        for name, imp in zip(all_feature_names, raw_importances):
            feature_importances.append({"feature": name, "importance": float(imp)})
    elif hasattr(clf, "coef_"):
        raw_coefs = clf.coef_[0]
        for name, coef in zip(all_feature_names, raw_coefs):
            feature_importances.append({"feature": name, "importance": float(abs(coef))})
    
    feature_importances.sort(key=lambda x: x["importance"], reverse=True)

    # Save model pipeline
    model_file = artifacts_dir / "lead_model.joblib"
    joblib.dump(best_pipeline, model_file)
    print(f"Saved trained {selected_model_type} pipeline to {model_file}")

    # Metadata & metrics
    meta = {
        "model_type": selected_model_type,
        "model_version": "1.0.0",
        "threshold": 0.5,
        "training_date": now.isoformat(),
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "features": {
            "numeric": numeric_features,
            "categorical": categorical_features,
            "ordinal": ordinal_features,
            "all_transformed": all_feature_names
        },
        "metrics": {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": roc_auc
        },
        "confusion_matrix": cm_dict,
        "feature_importances": feature_importances[:15]
    }

    with open(artifacts_dir / "preprocessor_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    with open(artifacts_dir / "confusion_matrix.json", "w") as f:
        json.dump(cm_dict, f, indent=2)

    with open(artifacts_dir / "feature_importance.json", "w") as f:
        json.dump(feature_importances, f, indent=2)

    print("Training complete! Test Metrics:")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    print(f"  ROC-AUC:   {roc_auc:.4f}")
    return meta


if __name__ == "__main__":
    train_lead_scoring_models()
