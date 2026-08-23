"""Data ingestion, validation, and preprocessing for Kosi Embankment AI/ML."""

from kosi_ai.config import get_base_dir, get_data_dir, get_synthetic_dir, \
    get_processed_dir, get_configs_dir, settings
from pathlib import Path
import yaml
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def load_data_sources() -> dict:
    """Load the data sources registry from YAML config."""
    path = Path(get_configs_dir()) / settings.data_sources_path
    if path.exists():
        with open(path, "r") as f:
            return yaml.safe_load(f)
    else:
        logger.warning(f"Data sources config not found at {path}")
        return {}


def load_feature_registry() -> dict:
    """Load the feature registry from YAML config."""
    path = Path(get_configs_dir()) / settings.feature_registry_path
    if path.exists():
        with open(path, "r") as f:
            return yaml.safe_load(f)
    else:
        logger.warning(f"Feature registry config not found at {path}")
        return {}


def check_feature_availability(required_features: List[str],
                               available_features: List[str]) -> dict:
    """Check which required features are available and which are missing.

    Returns dict with 'available', 'missing', and 'coverage_ratio'.
    """
    required_set = set(required_features)
    available_set = set(available_features)
    missing = required_set - available_set
    available = required_set & available_set
    coverage_ratio = len(available) / len(required_set) if required_set else 1.0

    return {
        "available": sorted(list(available)),
        "missing": sorted(list(missing)),
        "coverage_ratio": round(coverage_ratio, 3)
    }


def validate_feature_value(feature_name: str, value, feature_info: dict) -> bool:
    """Validate a single feature value against its registry metadata.

    Returns (is_valid, error_message).
    """
    if value is None or value == "":
        return True, "missing - will be handled by missing_policy"

    # Check valid_range if specified
    if "valid_range" in feature_info and feature_info["valid_range"] != "N/A":
        try:
            valid_range = feature_info["valid_range"]
            if " to " in valid_range:
                parts = valid_range.split(" to ")
                min_val, max_val = float(parts[0]), float(parts[1])
                if isinstance(value, (int, float)):
                    if not (min_val <= value <= max_val):
                        return False, f"{value} outside valid range {valid_range}"
        except (ValueError, TypeError):
            pass

    # Check units/range for common types
    if feature_info.get("units") == "m" and isinstance(value, (int, float)):
        if value < 0:
            return False, f"{feature_name}: negative value {value} not physically meaningful for metric in meters"

    if feature_info.get("units") == "mm" and isinstance(value, (int, float)):
        if value < 0:
            return False, f"{feature_name}: negative value {value} not physically meaningful for metric in mm"

    if feature_info.get("units") in ["ratio (m/m)", "1/km"] and isinstance(value, (int, float)):
        if value < 0:
            return False, f"{feature_name}: negative value {value} not physically meaningful"

    return True, "ok"


def validate_dataframe(df: pd.DataFrame,
                      feature_registry: dict) -> dict:
    """Validate a DataFrame against the feature registry.

    Returns dict with 'valid', 'errors', 'warnings', and 'data_quality_score'.
    """
    errors = []
    warnings = []
    total_checks = 0
    passed_checks = 0

    for col in df.columns:
        # Find feature in registry
        feature_info = None
        for feat in feature_registry.get("feature_registry", []):
            if feat["feature_name"] == col:
                feature_info = feat
                break

        if feature_info is None:
            warnings.append(f"Column '{col}' not in feature registry - no metadata available")
            total_checks += 1
            continue

        total_checks += 1

        # Check for required features
        if feature_info.get("required", False) and col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                missing_pct = null_count / len(df) * 100
                errors.append(f"{col}: {null_count}/{len(df)} missing values ({missing_pct:.1f}%)")
            else:
                passed_checks += 1

        # Validate each non-null value
        if col in df.columns:
            for idx, val in df[col].items():
                if pd.isna(val):
                    continue
                is_valid, msg = validate_feature_value(col, val, feature_info)
                total_checks += 1
                if is_valid:
                    passed_checks += 1
                else:
                    errors.append(f"{col}[{idx}]: {msg}")

    # Calculate data quality score
    data_quality = passed_checks / total_checks if total_checks > 0 else 0.0

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "data_quality": round(data_quality, 3)
    }