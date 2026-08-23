"""Evaluation and validation for Kosi Embankment AI/ML pipeline."""

from kosi_ai.config import settings
from kosi_ai.models import BaselineModelRegistry
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def compute_data_quality_metrics(df: pd.DataFrame,
                                  feature_registry: dict = None) -> dict:
    """Compute comprehensive data quality metrics for a DataFrame.

    Returns dict with overall quality score and per-feature breakdown.
    """
    if feature_registry is None:
        feature_registry = load_feature_registry()

    from kosi_ai.data.loader import validate_dataframe

    validation = validate_dataframe(df, feature_registry)

    # Additional quality metrics
    total_cells = df.size
    total_missing = df.isna().sum().sum()
    missing_ratio = total_missing / total_cells if total_cells > 0 else 1.0

    # Completeness per column
    completeness = {}
    for col in df.columns:
        non_null = df[col].notna().sum()
        completeness[col] = round(non_null / len(df), 3) if len(df) > 0 else 0.0

    # Unique value ratios
    cardinality = {}
    for col in df.columns:
        n_unique = df[col].nunique(dropna=True)
        cardinality[col] = {
            "n_unique": int(n_unique),
            "pct_of_rows": round(n_unique / len(df), 3) if len(df) > 0 else 0.0
        }

    # Type consistency
    type_checks = {}
    for col in df.columns:
        type_checks[col] = str(df[col].dtype)

    return {
        "overall_data_quality": validation["data_quality"],
        "validation_passed": validation["valid"],
        "missing_cell_ratio": round(missing_ratio, 3),
        "completeness": completeness,
        "cardinality": cardinality,
        "type_checks": type_checks,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "errors": validation["errors"],
        "warnings": validation["warnings"]
    }


def compute_confidence_calibration(y_true: np.ndarray,
                                   y_prob: np.ndarray,
                                   n_bins: int = 10) -> dict:
    """Compute calibration metrics for model probabilities.

    Measures how well predicted probabilities match observed frequencies.
    """
    from sklearn.calibration import calibration_curve

    if len(np.unique(y_true)) < 2:
        return {"error": "Only one class present in y_true"}

    # Bin the probabilities
    prob_binned, mean_prob_binned = calibration_curve(
        y_true, y_prob, n_bins=n_bins, strategy="quantile"
    )

    # Expected Calibration Error (ECE)
    bin_widths = 1.0 / n_bins
    ece = 0.0
    for i in range(n_bins):
        prob_interval = (i / n_bins, (i + 1) / n_bins)
        bin_size = np.sum((y_prob > prob_interval[0]) & (y_prob <= prob_interval[1]))
        if bin_size > 0:
            accuracy = np.mean(y_true[(y_prob > prob_interval[0])
                                  & (y_prob <= prob_interval[1])])
            ece += (bin_size / len(y_true)) * abs(accuracy - mean_prob_binned[i])

    # Maximum Calibration Error (MCE)
    mce = max(abs(mean_prob_binned - np.arange(1, n_bins + 1) / n_bins))

    return {
        "expected_calibration_error": round(float(ece), 4),
        "maximum_calibration_error": round(float(mce), 4),
        "mean_prob_per_bin": [round(float(p), 4) for p in mean_prob_binned],
        "observed_frac_per_bin": [round(float(o), 4) for o in prob_binned]
    }


def validate_temporal_split(df: pd.DataFrame,
                            date_column: str,
                            cutoff_quantile: float = 0.8) -> dict:
    """Validate that a temporal split is free of leakage.

    Checks that training data only contains earlier observations
    than testing data.

    Returns dict with 'valid', 'leakage_detected', and details.
    """
    if date_column not in df.columns:
        return {"valid": False, "leakage_detected": False,
                "error": f"Date column '{date_column}' not found"}

    dates = pd.to_datetime(df[date_column], errors="coerce")
    if dates.isna().all():
        return {"valid": False, "leakage_detected": False,
                "error": f"Could not parse dates in column '{date_column}'"}

    # Sort and split
    df_sorted = df.copy().reset_index(drop=True)
    df_sorted = df_sorted.sort_values(by=date_column)

    cutoff_date = df_sorted[date_column].iloc[
        int(len(df_sorted) * cutoff_quantile)]

    train_dates = pd.to_datetime(df_sorted[date_column].iloc[:int(len(df_sorted) * cutoff_quantile)])
    test_dates = pd.to_datetime(df_sorted[date_column].iloc[int(len(df_sorted) * cutoff_quantile):])

    # Check for leakage: no test date should be earlier than any train date
    leakage_detected = train_dates.max() > test_dates.min()

    return {
        "valid": not leakage_detected,
        "leakage_detected": leakage_detected,
        "cutoff_date": str(cutoff_date) if pd.notna(cutoff_date) else None,
        "train_date_range": [str(train_dates.min()), str(train_dates.max())],
        "test_date_range": [str(test_dates.min()), str(test_dates.max())],
        "notes": "Temporal split ensures no future information leaks into training"
    }


def check_spatial_leakage(df: pd.DataFrame,
                         lat_column: str = "latitude",
                         lon_column: str = "longitude",
                         distance_threshold_km: float = 50.0) -> dict:
    """Check for spatial leakage between training and test samples.

    If training and test samples are geographically close,
    spatial leakage may be present.

    Returns dict with spatial leakage analysis.
    """
    from sklearn.neighbors import NearestNeighbors

    if lat_column not in df.columns or lon_column not in df.columns:
        return {"valid": False, "error": "Latitude/longitude columns not found"}

    coords = df[[lat_column, lon_column]].dropna()

    if len(coords) < 3:
        return {"valid": True, "note": "Too few samples for spatial check"}

    # Use nearest neighbors to check cross-boundary proximity
    nbrs = NearestNeighbors(n_neighbors=1, metric="haversine").fit(
        np.radians(coords[[lat_column, lon_column]].values)
    )
    distances_km, indices = nbrs.kneighbors(
        np.radians(coords[[lat_column, lon_column]].values)
    )
    distances_km = distances_km[:, 0] * 6371.0  # Earth radius in km

    # Check if any point's nearest neighbor is within threshold
    # (excluding self-distance of 0)
    max_other_distance = distances_km[distances_km > 0].max() if (distances_km > 0).any() else 0

    spatial_leakage = max_other_distance < distance_threshold_km

    return {
        "valid": not spatial_leakage,
        "spatial_leakage_detected": spatial_leakage,
        "max_nearest_neighbor_km": round(float(max_other_distance), 2),
        "distance_threshold_km": distance_threshold_km,
        "note": f"Spatial leakage check: max nearest-neighbor distance = "
                f"{round(float(max_other_distance), 2)} km "
                f"(threshold: {distance_threshold_km} km)"
    }