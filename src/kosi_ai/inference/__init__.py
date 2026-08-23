"""Inference/ prediction API for Kosi Embankment vulnerability assessment.

Provides two prediction schemas:
1. Engineering vulnerability index (primary, V0.1)
2. Supervised model prediction (future, when labeled breach data available)

Schemas are kept separate as per design requirements.
"""

import logging

from kosi_ai.config import settings, load_feature_registry, get_vulnerability_class, get_base_dir
from kosi_ai.features import engineer_features, compute_vulnerability_score, \
    get_top_risk_factors
from kosi_ai.data.loader import load_synthetic_dataset
from pathlib import Path
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def predict_vulnerability(
        segment_data: dict,
        weights: dict = None,
        feature_registry: dict = None) -> dict:
    """Compute engineering vulnerability index for a single segment.

    This is the primary risk engine for V0.1 - uses an engineering-inspired
    scoring system, NOT a supervised breach-probability model.

    Args:
        segment_data: Dict with feature values for one segment
        weights: Optional dict of feature weights; if None, uses defaults
        feature_registry: Optional feature registry; loads default if None

    Returns:
        Dict matching the V0.1 output schema
    """
    if feature_registry is None:
        feature_registry = load_feature_registry()

    if weights is None:
        weights = {
            "hydrological_stress": 0.20,
            "rainfall_loading": 0.15,
            "freeboard_risk": 0.20,
            "embankment_condition_score": 0.15,
            "erosion_risk": 0.10,
            "sedimentation_risk": 0.05,
            "geospatial_exposure": 0.10,
            "soil_moisture_risk": 0.05,
            "historical_vulnerability": 0.05,
        }

    # Convert to DataFrame
    df = pd.DataFrame([segment_data])

    # Engineer features
    df = engineer_features(df, feature_registry)

    # Compute vulnerability score
    df = compute_vulnerability_score(df, weights)

    score = float(df["vulnerability_score"].iloc[0])
    vuln_class = get_vulnerability_class(score)

    # Get top risk factors
    top_factors = get_top_risk_factors(df, top_n=3)

    # Compute data quality
    from kosi_ai.evaluation import compute_data_quality_metrics
    qm = compute_data_quality_metrics(df, feature_registry)
    data_quality = qm["overall_data_quality"]

    # Build output schema (vulnerability index V0.1)
    result = {
        "segment_id": segment_data.get("segment_id", "UNKNOWN"),
        "vulnerability_score": round(score, 3),
        "vulnerability_class": vuln_class,
        "data_quality": round(data_quality, 3),
        "top_risk_factors": top_factors,
        "historical_matches": [],
        "model_status": settings.model_status,
    }

    logger.info(f"Vulnerability prediction for {result['segment_id']}: "
                f"score={score:.3f}, class={vuln_class}, "
                f"data_quality={data_quality:.3f}")

    return result


def predict_batch(
        data: list,
        weights: dict = None,
        feature_registry: dict = None) -> list:
    """Compute vulnerability scores for a batch of segments.

    Args:
        data: List of dicts, each with segment feature values
        weights: Optional weight dict
        feature_registry: Optional feature registry

    Returns:
        List of result dicts matching V0.1 schema
    """
    results = []
    for segment_data in data:
        result = predict_vulnerability(
            segment_data, weights=weights,
            feature_registry=feature_registry
        )
        results.append(result)
    return results


def load_synthetic_for_testing(name: str = "default") -> pd.DataFrame:
    """Load the synthetic development dataset for testing the pipeline.

    Returns DataFrame with dataset_status metadata clearly marked.
    """
    df = load_synthetic_dataset(name)
    return df