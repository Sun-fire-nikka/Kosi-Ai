"""Utility functions for Kosi Embankment AI/ML pipeline."""

from kosi_ai.config import settings, get_base_dir
import numpy as np
import pandas as pd
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


def set_seed(seed: int = None):
    """Set random seed for reproducibility."""
    if seed is not None:
        settings.default_seed = seed
    np.random.seed(settings.default_seed)
    logger.info(f"Random seed set to {settings.default_seed}")


def load_json_config(path: str) -> dict:
    """Load a JSON configuration file."""
    p = Path(path)
    if p.exists():
        with open(p, "r") as f:
            return json.load(f)
    else:
        logger.warning(f"Config file not found at {path}")
        return {}


def save_json_config(data: dict, path: str):
    """Save data as a JSON configuration file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved config to {path}")


def format_output_vulnerability(
        segment_id: str,
        vulnerability_score: float,
        vulnerability_class: str,
        data_quality: float,
        top_risk_factors: list = None,
        historical_matches: list = None,
        model_status: str = None) -> dict:
    """Format a vulnerability prediction output dict.

    Uses the V0.1 engineering index schema.
    """
    if model_status is None:
        model_status = settings.model_status

    if top_risk_factors is None:
        top_risk_factors = []

    if historical_matches is None:
        historical_matches = []

    return {
        "segment_id": segment_id,
        "vulnerability_score": round(float(vulnerability_score), 3),
        "vulnerability_class": vulnerability_class,
        "data_quality": round(float(data_quality), 3),
        "top_risk_factors": top_risk_factors,
        "historical_matches": historical_matches,
        "model_status": model_status,
    }


def format_output_risk(
        segment_id: str,
        risk_probability: float,
        risk_class: str,
        model_confidence: float,
        model_version: str = None) -> dict:
    """Format a supervised risk prediction output dict.

    This schema is SEPARATE from the vulnerability index schema
    and is intended for future use when verified breach labels are available.

    Raises:
        RuntimeError: If called before supervised model is trained.
    """
    if model_version is None:
        model_version = settings.model_version

    # Check if a model is actually available
    from kosi_ai.models import BaselineModelRegistry
    registry = BaselineModelRegistry()
    registered = registry.list_models()
    has_supervised = any(
        m in ["logistic_regression", "random_forest", "xgboost"]
        for m in registered
    )

    if not has_supervised:
        raise RuntimeError(
            "Supervised risk prediction schema cannot be used yet. "
            "No trained models available. "
            "Use format_output_vulnerability() for the engineering index, "
            "or train a supervised model first using the ML pipeline."
        )

    return {
        "segment_id": segment_id,
        "risk_probability": round(float(risk_probability), 3),
        "risk_class": risk_class,
        "model_confidence": round(float(model_confidence), 3),
        "model_version": model_version,
    }


def log_system_info():
    """Log system and configuration information for auditability."""
    from kosi_ai.config import get_vulnerability_class, BaselineModelRegistry
    import numpy as np

    registry = BaselineModelRegistry()
    registered = registry.list_models()

    info = {
        "project": "Kosi Embankment Intelligence & Flood Risk Digital Twin",
        "version": "0.1.0",
        "model_status": settings.model_status,
        "model_version": settings.model_version,
        "synthetic_mode": settings.synthetic_mode,
        "default_seed": settings.default_seed,
        "registered_models": registered,
        "vulnerability_thresholds": settings.vulnerability_score_thresholds,
        "data_sources_registry": "configs/data_sources.yaml",
        "feature_registry": "configs/feature_registry.yaml",
    }

    logger.info("System configuration audit:")
    for key, value in info.items():
        logger.info(f"  {key}: {value}")

    return info