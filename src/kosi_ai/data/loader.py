"""Data loading utilities for Kosi Embankment AI/ML pipeline."""

from kosi_ai.config import get_base_dir, get_synthetic_dir, get_data_dir, \
    settings
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
import logging

logger = logging.getLogger(__name__)


def load_synthetic_dataset(name: str = "default") -> pd.DataFrame:
    """Load the synthetic development dataset.

    Returns DataFrame with a metadata dict indicating dataset_status.
    The dataset is explicitly marked SYNTHETIC_DEVELOPMENT_ONLY.
    """
    synthetic_dir = Path(get_synthetic_dir())
    # Look for parquet or csv
    parquet_path = synthetic_dir / f"{name}.parquet"
    csv_path = synthetic_dir / f"{name}.csv"

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        logger.info(f"Loaded synthetic dataset from {parquet_path} "
                    f"({len(df)} rows)")
    elif csv_path.exists():
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded synthetic dataset from {csv_path} "
                    f"({len(df)} rows)")
    else:
        # Generate a minimal synthetic dataset if none exists
        logger.warning("No synthetic dataset found; generating minimal placeholder")
        df = _generate_minimal_synthetic()
        df.dataset_status = "SYNTHETIC_DEVELOPMENT_ONLY"
        return df

    # Mark as synthetic
    df.dataset_status = "SYNTHETIC_DEVELOPMENT_ONLY"
    return df


def _generate_minimal_synthetic(n_segments: int = 50) -> pd.DataFrame:
    """Generate a minimal synthetic dataset for pipeline testing."""
    np.random.seed(settings.default_seed)

    n = n_segments
    data = {
        "segment_id": [f"KOSI_EB_{i:03d}" for i in range(n)],
        "dataset_status": ["SYNTHETIC_DEVELOPMENT_ONLY"] * n,
        "latitude": np.random.uniform(25.0, 29.0, n),
        "longitude": np.random.uniform(86.0, 88.0, n),
        "river_level": np.random.uniform(15.0, 25.0, n),
        "embankment_height": np.random.uniform(8.0, 15.0, n),
        "freeboard": np.random.uniform(0.5, 6.0, n),
        "slope": np.random.uniform(0.1, 0.5, n),
        "condition": np.random.choice(["good", "fair", "poor"], n, p=[0.5, 0.35, 0.15]),
        "rainfall_24h": np.random.exponential(5.0, n),
        "rainfall_72h": np.random.exponential(15.0, n),
        "rainfall_7d": np.random.exponential(30.0, n),
        "discharge": np.random.uniform(500.0, 3000.0, n),
        "discharge_change": np.random.uniform(-200.0, 200.0, n),
        "water_level_change": np.random.uniform(-1.0, 3.0, n),
        "soil_type": np.random.choice(["clay", "silt", "sand", "loam"], n),
        "erosion_indicator": np.random.choice(["none", "minor", "major"], n, p=[0.7, 0.2, 0.1]),
        "sedimentation_indicator": np.random.choice(["none", "minor"], n, p=[0.8, 0.2]),
        "historical_failure_count": np.random.poisson(lam=0.5, size=n),
        "historical_breach_distance": np.random.exponential(2.0, n),
        "historical_flood_frequency": np.random.uniform(0.1, 1.0, n),
        "elevation": np.random.uniform(20.0, 30.0, n),
        "local_slope": np.random.uniform(0.05, 0.15, n),
        "river_width": np.random.uniform(100.0, 500.0, n),
        "river_curvature": np.random.uniform(0.0, 0.5, n),
        "distance_to_river": np.random.uniform(10.0, 1000.0, n),
    }

    df = pd.DataFrame(data)

    # Add derived features
    df["water_level_change"] = df["river_level"].diff().fillna(df["river_level"])
    # Ensure non-negative freeboard for some segments
    df["freeboard"] = df["embankment_height"] - df["river_level"]
    df["soil_moisture"] = np.random.uniform(0.1, 0.5, n)

    return df


def load_processed_data(name: str = "default") -> pd.DataFrame:
    """Load processed data from the processed directory."""
    processed_dir = Path(get_processed_dir())
    parquet_path = processed_dir / f"{name}.parquet"
    csv_path = processed_dir / f"{name}.csv"

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        logger.info(f"Loaded processed data from {parquet_path}")
    elif csv_path.exists():
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded processed data from {csv_path}")
    else:
        logger.warning(f"No processed data found at {processed_dir}")
        return pd.DataFrame()

    return df


def save_processed_data(df: pd.DataFrame, name: str = "default") -> None:
    """Save processed data to the processed directory."""
    processed_dir = Path(get_processed_dir())
    processed_dir.mkdir(parents=True, exist_ok=True)

    out_path = processed_dir / f"{name}.parquet"
    df.to_parquet(out_path, index=False)
    logger.info(f"Saved processed data to {out_path} ({len(df)} rows)")


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
        for feat in feature_registry.get("feature_registry", []) if feature_registry else []:
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
                # Check valid_range if specified
                if "valid_range" in feature_info and feature_info["valid_range"] != "N/A":
                    try:
                        valid_range = feature_info["valid_range"]
                        if " to " in valid_range:
                            parts = valid_range.split(" to ")
                            min_val, max_val = float(parts[0]), float(parts[1])
                            if isinstance(val, (int, float)):
                                if not (min_val <= val <= max_val):
                                    errors.append(f"{col}[{idx}]: value {val} outside valid range {valid_range}")
                    except (ValueError, TypeError):
                        pass

                # Check for negative physical metrics
                if feature_info.get("units") == "m" and isinstance(val, (int, float)):
                    if val < 0:
                        errors.append(f"{col}[{idx}]: negative value {val} not physically meaningful for metric in meters")

                if feature_info.get("units") == "mm" and isinstance(val, (int, float)):
                    if val < 0:
                        errors.append(f"{col}[{idx}]: negative value {val} not physically meaningful for metric in mm")

                if feature_info.get("units", "").startswith("ratio") and isinstance(val, (int, float)):
                    if val < 0:
                        errors.append(f"{col}[{idx}]: negative value {val} not physically meaningful")

                passed_checks += 1

    # Calculate data quality score
    data_quality = passed_checks / total_checks if total_checks > 0 else 0.0

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "data_quality": round(data_quality, 3)
    }