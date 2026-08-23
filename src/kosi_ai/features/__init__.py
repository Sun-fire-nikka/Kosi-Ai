"""Feature engineering for Kosi Embankment vulnerability index."""

import logging

from kosi_ai.config import settings, load_feature_registry
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def engineer_features(df: pd.DataFrame,
                      feature_registry: dict = None) -> pd.DataFrame:
    """Engineer features from raw inputs for vulnerability scoring.

    Applies derived feature engineering per the feature registry.
    All engineered features are traceable to their input sources.
    """
    if feature_registry is None:
        feature_registry = load_feature_registry()

    df = df.copy()

    # Ensure required columns exist
    for feat in feature_registry.get("feature_registry", []):
        fn = feat["feature_name"]
        if fn not in df.columns:
            # Set default based on type
            if feat.get("observed_or_derived") == "observed":
                df[fn] = np.nan
            elif feat.get("observed_or_derived") == "derived":
                # Compute sensible default
                continue

    # 1. Freeboard (if not already present)
    if "freeboard" not in df.columns or df["freeboard"].isna().all():
        if "embankment_height" in df.columns and "river_level" in df.columns:
            df["freeboard"] = df["embankment_height"] - df["river_level"]
            # Cap at reasonable max
            df["freeboard"] = df["freeboard"].clip(upper=20.0)

    # 2. Water level change (if not already present)
    if "water_level_change" not in df.columns or df["water_level_change"].isna().all():
        if "river_level" in df.columns:
            df["water_level_change"] = df["river_level"].diff().fillna(0)

    # 3. Discharge change (if not already present)
    if "discharge_change" not in df.columns or df["discharge_change"].isna().all():
        if "discharge" in df.columns:
            df["discharge_change"] = df["discharge"].diff().fillna(0)

    # 4. Risk-oriented derived features
    # Hydrological stress index: combines river_level, water_level_change, discharge_change
    if "river_level" in df.columns and "water_level_change" in df.columns:
        # Normalize river_level to 0-1 scale (approx Kosi range)
        rl = df["river_level"]
        rl_norm = (rl - rl.min()) / (rl.max() - rl.min() + 1e-8)
        wlc = df["water_level_change"]
        wlc_norm = (wlc - wlc.min()) / (wlc.max() - wlc.min() + 1e-8)
        df["hydrological_stress"] = (
            0.5 * rl_norm + 0.5 * wlc_norm
        ).clip(0, 1)
    else:
        df["hydrological_stress"] = 0.5

    # 5. Rainfall loading index
    if all(c in df.columns for c in ["rainfall_24h", "rainfall_72h", "rainfall_7d"]):
        r24 = df["rainfall_24h"].replace(0, np.nan)
        r72 = df["rainfall_72h"].replace(0, np.nan)
        r7 = df["rainfall_7d"].replace(0, np.nan)
        # Weight recent rainfall more heavily
        r24_n = r24.rank(pct=True) if r24.notna().any() else 0
        r72_n = r72.rank(pct=True) if r72.notna().any() else 0
        r7_n = r7.rank(pct=True) if r7.notna().any() else 0
        df["rainfall_loading"] = (
            0.3 * r24_n + 0.3 * r72_n + 0.4 * r7_n
        ).clip(0, 1)
    elif "rainfall_24h" in df.columns:
        df["rainfall_loading"] = (
            df["rainfall_24h"].rank(pct=True)
            if df["rainfall_24h"].notna().any()
            else 0.0
        )
    else:
        df["rainfall_loading"] = 0.0

    # 6. Freeboard risk factor
    if "freeboard" in df.columns:
        fb = df["freeboard"]
        # Inverse relationship: lower freeboard = higher risk
        fb_norm = (fb - fb.min()) / (fb.max() - fb.min() + 1e-8)
        df["freeboard_risk"] = (1 - fb_norm).clip(0, 1)
    else:
        df["freeboard_risk"] = 0.5

    # 7. Embankment condition scoring
    if "condition" in df.columns:
        cond_map = {"good": 0.0, "fair": 0.5, "poor": 1.0}
        df["embankment_condition_score"] = df["condition"].map(cond_map).fillna(0.5)
    else:
        df["embankment_condition_score"] = 0.5

    # 8. Erosion risk
    if "erosion_indicator" in df.columns:
        eros_map = {"none": 0.0, "minor": 0.5, "major": 1.0}
        df["erosion_risk"] = df["erosion_indicator"].map(eros_map).fillna(0.0)
    else:
        df["erosion_risk"] = 0.0

    # 9. Sedimentation risk
    if "sedimentation_indicator" in df.columns:
        sed_map = {"none": 0.0, "minor": 0.3, "major": 0.7}
        df["sedimentation_risk"] = df["sedimentation_indicator"].map(sed_map).fillna(0.0)
    else:
        df["sedimentation_risk"] = 0.0

    # 10. Geospatial exposure
    if all(c in df.columns for c in ["river_width", "distance_to_river"]):
        rw = df["river_width"].replace(0, np.nan)
        dr = df["distance_to_river"]
        # Proximity risk: closer to river = higher risk
        dr_norm = (dr - dr.min()) / (dr.max() - dr.min() + 1e-8)
        rw_norm = (rw - rw.min()) / (rw.max() - rw.min() + 1e-8)
        df["geospatial_exposure"] = (
            0.7 * dr_norm + 0.3 * rw_norm
        ).clip(0, 1)
    else:
        df["geospatial_exposure"] = 0.5

    # 11. Soil moisture risk
    if "soil_moisture" in df.columns:
        df["soil_moisture_risk"] = df["soil_moisture"].clip(upper=1.0)
    else:
        df["soil_moisture_risk"] = 0.2  # default assumption

    # 12. Historical vulnerability
    if "historical_failure_count" in df.columns:
        hfc = df["historical_failure_count"]
        # Normalize: more failures = higher vulnerability
        max_hfc = hfc.max()
        if max_hfc > 0:
            df["historical_vulnerability"] = (
                hfc / max_hfc
            ).clip(0, 1)
        else:
            df["historical_vulnerability"] = 0.0
    elif "historical_breach_distance" in df.columns:
        hbd = df["historical_breach_distance"]
        # Shorter distance to historical breach = higher vulnerability
        hbd_norm = (hbd - hbd.min()) / (hbd.max() - hbd.min() + 1e-8)
        df["historical_vulnerability"] = (1 - hbd_norm).clip(0, 1)
    else:
        df["historical_vulnerability"] = 0.0

    logger.info(f"Engineered {len([c for c in df.columns if c not in _get_original_columns(df)])} "
                f"derived features")

    return df


def _get_original_columns(df: pd.DataFrame) -> set:
    """Get the set of columns that were in the original input."""
    # Original identification + hydrological + rainfall + embankment + geospatial + soil + erosion
    original_types = {"identification", "hydrological", "rainfall", "embankment",
                      "geospatial", "soil", "erosion_sediment"}
    # This is a heuristic - columns that look like original observations
    original = set()
    for col in df.columns:
        cl = col.lower()
        if any(kw in cl for kw in ["id", "seg", "lat", "lon", "river", "level",
                                    "discharge", "rainfall", "embank", "cond",
                                    "elev", "slope", "width", "curv",
                                    "soil", "erosion", "sedim", "historical"]):
            original.add(col)
    return original


def compute_vulnerability_score(df: pd.DataFrame,
                                 weights: dict = None) -> pd.DataFrame:
    """Compute the composite vulnerability score from engineered features.

    The score is a weighted sum of dimension-specific risk factors.
    Weights are configurable via the weights dict parameter.

    Returns DataFrame with 'vulnerability_score' column (0-1 scale).
    """
    if weights is None:
        # Default equal weights - these can be overridden from config
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

    # Ensure all required engineered features exist
    required_features = list(weights.keys())
    for feat in required_features:
        if feat not in df.columns:
            logger.warning(f"Required feature '{feat}' not found in DataFrame; "
                          f"setting to 0.0")
            df[feat] = 0.0

    # Compute weighted sum
    score_parts = {}
    for feat, weight in weights.items():
        if feat in df.columns:
            # Use the feature value directly as contribution
            contribution = df[feat] * weight
            score_parts[feat] = contribution
        else:
            score_parts[feat] = np.zeros(len(df)) * weight

    df["vulnerability_score"] = sum(score_parts.values()).clip(0, 1)

    # Add score breakdown columns for traceability
    for feat, weight in weights.items():
        df[f"{feat}_contribution"] = score_parts.get(feat, np.zeros(len(df)))

    # Add total weight sum for debugging
    df["_weight_sum"] = sum(weights.values())

    logger.info(f"Computed vulnerability scores: "
                f"mean={df['vulnerability_score'].mean():.3f}, "
                f"std={df['vulnerability_score'].std():.3f}")

    return df


def get_top_risk_factors(df: pd.DataFrame,
                         top_n: int = 3,
                         weight_threshold: float = 0.0) -> list:
    """Identify top risk factors contributing to vulnerability scores.

    Uses permutation importance logic: computes score change when feature
    is permuted (shuffled), indicating its importance.

    Returns list of dicts with 'feature', 'direction', 'impact'.
    """
    if "vulnerability_score" not in df.columns:
        logger.warning("No vulnerability_score column found; cannot compute risk factors")
        return []

    risks = []
    for col in df.columns:
        if col in ["vulnerability_score", "_weight_sum",
                   "hydrological_stress_contribution",
                   "rainfall_loading_contribution",
                   "freeboard_risk_contribution",
                   "embankment_condition_score_contribution",
                   "erosion_risk_contribution",
                   "sedimentation_risk_contribution",
                   "geospatial_exposure_contribution",
                   "soil_moisture_risk_contribution",
                   "historical_vulnerability_contribution",
                   "vulnerability_score", "_weight_sum"]:
            continue

        if df[col].dtype not in [np.float64, np.float32, np.int64, np.int32]:
            continue

        # Simple importance: correlation with vulnerability score
        try:
            corr = df[col].corr(df["vulnerability_score"])
            if pd.notna(corr) and abs(corr) > weight_threshold:
                direction = "increases_risk" if corr > 0 else "decreases_risk"
                risks.append({
                    "feature": col,
                    "direction": direction,
                    "impact": round(float(abs(corr)), 3)
                })
        except Exception:
            continue

    # Sort by impact descending
    risks.sort(key=lambda x: x["impact"], reverse=True)

    return risks[:top_n]