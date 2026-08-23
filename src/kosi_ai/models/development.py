"""Synthetic development model training (SYNTHETIC_DEVELOPMENT_ONLY).

Logistic Regression + Random Forest on the 200-segment synthetic dataset.
Purpose: validate preprocessing, training, serialization, inference.
Metrics are SYNTHETIC ONLY and never represent real Kosi accuracy.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score, average_precision_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = PROJECT_ROOT / "models/development"

TARGET = "condition"          # proxy label present in synthetic data only
DROP = ["segment_id", "dataset_status", "material", "soil_type",
        "floodplain_characteristics", TARGET]


def _features(df: pd.DataFrame) -> pd.DataFrame:
    X = df.drop(columns=[c for c in DROP if c in df.columns])
    return pd.get_dummies(X, drop_first=True)


def _make_target(df: pd.DataFrame) -> pd.Series:
    """Binary proxy target from synthetic condition field.

    Uses only synthetic values; anything not clearly degraded is class 0.
    """
    cond = df[TARGET].astype(str).str.upper()
    return (cond.isin(["POOR", "CRITICAL"])).astype(int)


def train_all(df: pd.DataFrame, seed: int = 42) -> dict:
    y = _make_target(df)
    X = _features(df)
    strat = y if y.nunique() > 1 else None
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25,
                                              random_state=seed, stratify=strat)
    models = {
        "logistic_regression": Pipeline([("scaler", StandardScaler()),
                                         ("clf", LogisticRegression(max_iter=2000))]),
        "random_forest": RandomForestClassifier(n_estimators=300, random_state=seed),
    }
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    report: dict = {}
    for name, model in models.items():
        model.fit(X_tr, y_tr)
        proba = (model.predict_proba(X_te)[:, 1]
                 if hasattr(model, "predict_proba") else None)
        pred = model.predict(X_te)
        metrics = {
            "precision": round(float(precision_score(y_te, pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_te, pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_te, pred, zero_division=0)), 4),
            "confusion_matrix": confusion_matrix(y_te, pred).tolist(),
            "n_train": int(len(y_tr)), "n_test": int(len(y_te)),
        }
        if proba is not None and len(np.unique(y_te)) > 1:
            metrics["roc_auc"] = round(float(roc_auc_score(y_te, proba)), 4)
            metrics["pr_auc"] = round(float(average_precision_score(y_te, proba)), 4)
        if name == "random_forest":
            imp = sorted(zip(X.columns, model.feature_importances_),
                         key=lambda t: -t[1])[:10]
            metrics["feature_importance_top10"] = [
                {"feature": f, "importance": round(float(v), 4)} for f, v in imp]
        artifact = {
            "label": "SYNTHETIC_DEVELOPMENT_ONLY",
            "warning": ("Performance on synthetic data does NOT represent "
                        "real-world Kosi prediction accuracy."),
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "model_name": name,
        }
        path = MODELS_DIR / f"{name}_synthetic.joblib"
        joblib.dump({"model": model, "metadata": artifact,
                     "feature_names": list(X.columns)}, path)
        report[name] = {"metrics": metrics, "artifact": artifact,
                        "path": str(path)}
    with open(MODELS_DIR / "SYNTHETIC_DEVELOPMENT_ONLY_metrics.json", "w",
              encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return report


def load_model(name: str):
    path = MODELS_DIR / f"{name}_synthetic.joblib"
    bundle = joblib.load(path)
    assert bundle["metadata"]["label"] == "SYNTHETIC_DEVELOPMENT_ONLY"
    return bundle


def predict_synthetic(bundle, X: pd.DataFrame) -> np.ndarray:
    X = X.reindex(columns=bundle["feature_names"], fill_value=0)
    return bundle["model"].predict(X)
