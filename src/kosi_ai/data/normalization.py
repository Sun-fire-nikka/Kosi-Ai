"""Normalization module for Kosi Embankment AI/ML layer.

Provides functions for normalizing/standardizing features,
handling different data types (numeric, categorical, temporal),
and preparing data for the engineering vulnerability index
or supervised machine learning models.

Normalization is applied separately for:
- Engineering index: configurable weights, no standard scaling needed
- Supervised models: min-max scaling or z-score as needed
- All normalization parameters are configurable, not hardcoded
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

from kosi_ai.config import settings

logger = logging.getLogger(__name__)


def normalize_numeric_minmax(
    series: pd.Series,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> Tuple[pd.Series, float, float]:
    """Normalize a numeric series to [0, 1] range using min-max scaling.

    Args:
        series: pandas Series with numeric values
        min_val: If provided, use this as min instead of computing from data
        max_val: If provided, use this as max instead of computing from data

    Returns:
        Tuple of (normalized_series, computed_min, computed_max)
    """
    # Convert to numeric, coercing errors
    numeric_series = pd.to_numeric(series, errors="coerce")
    
    if min_val is None:
        computed_min = float(numeric_series.min())
    else:
        computed_min = min_val
    
    if max_val is None:
        computed_max = float(numeric_series.max())
    else:
        computed_max = max_val
    
    # Avoid division by zero
    range_val = computed_max - computed_min
    if range_val == 0 or pd.isna(range_val):
        # All values are the same or NaN; return zeros
        normalized = pd.Series(
            np.zeros(len(numeric_series)), index=numeric_series.index, dtype=float
        )
        return normalized, computed_min, computed_max
    
    normalized = (numeric_series - computed_min) / range_val
    # Clip to [0, 1] range in case of floating point issues
    normalized = normalized.clip(lower=0.0, upper=1.0)
    
    return normalized, computed_min, computed_max


def normalize_numeric_zscore(
    series: pd.Series,
    mean: Optional[float] = None,
    std: Optional[float] = None,
) -> Tuple[pd.Series, float, float]:
    """Normalize a numeric series to z-score (mean=0, std=1).

    Args:
        series: pandas Series with numeric values
        mean: If provided, use this as mean instead of computing from data
        std: If provided, use this as std instead of computing from data

    Returns:
        Tuple of (normalized_series, computed_mean, computed_std)
    """
    numeric_series = pd.to_numeric(series, errors="coerce")
    
    if mean is None:
        computed_mean = float(numeric_series.mean(skipna=True))
    else:
        computed_mean = mean
    
    if std is None:
        computed_std = float(numeric_series.std(skipna=True))
        # If std is 0 or NaN, all values are the same
        if pd.isna(computed_std) or computed_std == 0:
            computed_std = 1.0  # Avoid division by zero; result will be all NaN → filled later
    else:
        # Use provided std; ensure it's not zero
        computed_std = max(std, 1e-8)
    
    normalized = (numeric_series - computed_mean) / computed_std
    
    return normalized, computed_mean, computed_std


def encode_categorical(
    series: pd.Series,
    encoding: str = "one-hot",
    categories: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Encode a categorical series using the specified method.

    Args:
        series: pandas Series with categorical values (strings)
        encoding: "one-hot" or "label"
        categories: Pre-defined category list; if None, inferred from data

    Returns:
        DataFrame with encoded columns
    """
    # Convert to string and fill NaN
    str_series = series.astype(str).fillna("unknown")
    
    if encoding == "label":
        # Label encoding: assign integer codes
        unique_vals = str_series.unique()
        category_map = {val: idx for idx, val in enumerate(unique_vals)}
        encoded = str_series.map(category_map)
        return pd.DataFrame({"encoded": encoded}, index=series.index), category_map
    
    elif encoding == "one-hot":
        # One-hot encoding
        dummies = pd.get_dummies(str_prefix=str_series, prefix="cat", dummy_na=True)
        # Rename columns to be more descriptive
        dummies.columns = [f"cat_{col}" for col in dummies.columns]
        return dummies, {}
    
    else:
        logger.warning(f"Unknown encoding method: {encoding}; returning original series")
        return pd.DataFrame({"original": str_series}), {}


def normalize_engineering_index_weights(
    weights: Dict[str, float],
    normalize: bool = True,
) -> Dict[str, float]:
    """Normalize engineering index weights so they sum to 1.

    Args:
        weights: Dict mapping feature names to weight values
        normalize: If True, scale weights to sum to 1.0

    Returns:
        Dict of weights (normalized if normalize=True)
    """
    if not weights:
        return weights
    
    if normalize:
        total = sum(weights.values())
        if total > 0:
            return {k: v / total for k, v in weights.items()}
        else:
            # All weights are zero; return equal weights
            n = len(weights)
            if n > 0:
                return {k: 1.0 / n for k in weights.keys()}
    
    return weights


def format_value_for_output(
    value: Any,
    feature_type: str = "numeric",
    precision: int = 3,
) -> Any:
    """Format a value for output in the API schema.

    Args:
        value: The value to format
        feature_type: "numeric", "categorical", "date"
        precision: Number of decimal places for numeric values

    Returns:
        Formatted value suitable for API output
    """
    if value is None or value == "" or value == "nan" or (isinstance(value, float) and pd.isna(value)):
        return None
    
    if feature_type == "numeric":
        if isinstance(value, float):
            return round(value, precision)
        return value
    
    elif feature_type == "categorical":
        if isinstance(value, str):
            return value
        return str(value)
    
    elif feature_type == "date":
        if isinstance(value, pd.Timestamp):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, str):
            # Try to parse and format
            try:
                dt = pd.to_datetime(value)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                return value
        return value
    
    return value


def safe_divide(
    numerator: float,
    denominator: float,
    default: float = np.nan,
) -> float:
    """Safe division that handles division by zero and NaN.

    Returns:
        numerator / denominator, or default if denominator is 0 or NaN
    """
    if denominator is None or (isinstance(denominator, float) and pd.isna(denominator)):
        return default
    if denominator == 0:
        return default
    result = numerator / denominator
    if pd.isna(result):
        return default
    return result


def clamp_value(
    value: float,
    min_val: float = 0.0,
    max_val: float = 1.0,
) -> float:
    """Clamp a value to a specified range [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def compute_percentile_rank(
    series: pd.Series,
    method: str = "average",
) -> pd.Series:
    """Compute percentile rank (0-1) for each value in a series.

    Args:
        series: pandas Series of numeric values
        method: Passed to pandas rank() method

    Returns:
        Series with values ranked 0-1
    """
    numeric = pd.to_numeric(series, errors="coerce")
    # rank() returns 1-based rank; convert to 0-1
    if numeric.notna().sum() == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    
    ranks = numeric.rank(method=method, na_option="bottom")
    normalized = (ranks - 1) / (len(numeric.dropna()) - 1) if len(numeric.dropna()) > 1 else pd.Series(
        np.zeros(len(numeric)), index=numeric.index
    )
    # Handle NaN values - they should get rank 0
    normalized[normalized.isna()] = 0.0
    # Clamp to [0, 1]
    normalized = normalized.clip(lower=0.0, upper=1.0)
    return normalized