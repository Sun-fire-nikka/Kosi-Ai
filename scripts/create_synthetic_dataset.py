"""Synthetic development dataset for Kosi Embankment AI/ML pipeline testing.

IMPORTANT: This dataset is SYNTHETIC DEVELOPMENT ONLY.
It is NOT real Kosi River data and contains no verified historical breach labels.

This dataset exists solely to test data loading, preprocessing,
feature engineering, scoring, and model training mechanics.
Model metrics computed on this data have NO real-world predictive validity.

For production use, verified Kosi historical event data must replace
this synthetic dataset.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from kosi_ai.config import get_synthetic_dir, settings

# Ensure synthetic directory exists
synthetic_dir = Path(get_synthetic_dir())
synthetic_dir.mkdir(parents=True, exist_ok=True)

np.random.seed(settings.default_seed)

n_segments = 200

# --- Identification ---
segment_ids = [f"KOSI_EB_{i:03d}" for i in range(n_segments)]
latitudes = np.random.uniform(25.0, 29.0, n_segments)
longitudes = np.random.uniform(86.0, 88.0, n_segments)

# --- Hydrological ---
# River level in meters (typical Kosi range during monsoon)
river_levels = np.random.uniform(15.0, 25.0, n_segments)
# Discharge in m^3/s
discharges = np.random.uniform(500.0, 3500.0, n_segments)
# Water level change (m/day) - key stress indicator
water_level_changes = np.random.uniform(-1.0, 4.0, n_segments)
# Discharge change
discharge_changes = np.random.uniform(-300.0, 300.0, n_segments)

# --- Rainfall (mm) ---
rainfall_24h = np.random.exponential(8.0, n_segments)
rainfall_72h = np.random.exponential(20.0, n_segments)
rainfall_7d = np.random.exponential(50.0, n_segments)

# --- Embankment ---
embankment_heights = np.random.uniform(8.0, 16.0, n_segments)
# Freeboard = embankment_height - river_level (can be negative = overtopping risk)
freeboards = embankment_heights - river_levels
# Slope (ratio)
slopes = np.random.uniform(0.1, 0.5, n_segments)
# Material (categorical: earthen, concrete, stone-faced)
materials = np.random.choice(["earthen", "concrete", "stone-faced"], n_segments,
                             p=[0.6, 0.2, 0.2])
# Condition (categorical: good, fair, poor)
conditions = np.random.choice(["good", "fair", "poor"], n_segments,
                              p=[0.5, 0.35, 0.15])

# --- Geospatial ---
elevations = np.random.uniform(20.0, 32.0, n_segments)
local_slopes = np.random.uniform(0.03, 0.15, n_segments)
river_widths = np.random.uniform(200.0, 800.0, n_segments)
river_curvatures = np.random.uniform(0.0, 0.6, n_segments)
distance_to_rivers = np.random.uniform(50.0, 2000.0, n_segments)
floodplain_chars = np.random.choice(["narrow", "wide", "connected"], n_segments,
                                    p=[0.5, 0.3, 0.2])

# --- Soil ---
soil_types = np.random.choice(["clay", "silt", "sand", "loam"], n_segments,
                              p=[0.3, 0.25, 0.25, 0.2])
soil_moistures = np.random.uniform(0.1, 0.6, n_segments)

# --- Erosion/Sediment ---
erosion_indicators = np.random.choice(["none", "minor", "major"], n_segments,
                                      p=[0.7, 0.2, 0.1])
sedimentation_indicators = np.random.choice(["none", "minor"], n_segments,
                                            p=[0.85, 0.15])

# --- Historical ---
historical_failure_counts = np.random.poisson(lam=1.0, size=n_segments)
historical_breach_distances = np.random.exponential(3.0, n_segments)
historical_flood_frequencies = np.random.uniform(0.1, 2.0, n_segments)

# --- Derived / computed ---
water_level_changes = river_levels - np.roll(river_levels, 1, axis=0)
water_level_changes[0] = 0

# Create DataFrame
data = {
    # Identification
    "segment_id": segment_ids,
    "latitude": latitudes,
    "longitude": longitudes,
    "chainage": np.random.uniform(0.0, 100.0, n_segments),

    # Hydrological
    "river_level": river_levels,
    "discharge": discharges,
    "water_level_change": water_level_changes,
    "discharge_change": discharge_changes,
    "rainfall_24h": rainfall_24h,
    "rainfall_72h": rainfall_72h,
    "rainfall_7d": rainfall_7d,

    # Embankment
    "embankment_height": embankment_heights,
    "freeboard": freeboards,
    "slope": slopes,
    "material": materials,
    "condition": conditions,

    # Geospatial
    "elevation": elevations,
    "local_slope": local_slopes,
    "river_width": river_widths,
    "river_curvature": river_curvatures,
    "distance_to_river": distance_to_rivers,
    "floodplain_characteristics": floodplain_chars,

    # Soil
    "soil_type": soil_types,
    "soil_moisture": soil_moistures,

    # Erosion/Sediment
    "erosion_indicator": erosion_indicators,
    "sedimentation_indicator": sedimentation_indicators,

    # Historical
    "historical_failure_count": historical_failure_counts,
    "historical_breach_distance": historical_breach_distances,
    "historical_flood_frequency": historical_flood_frequencies,

    # Synthetic metadata
    "dataset_status": "SYNTHETIC_DEVELOPMENT_ONLY",
}

df = pd.DataFrame(data)

# Save synthetic dataset
synthetic_path = synthetic_dir / "synthetic_development_v0.1.parquet"
df.to_parquet(synthetic_path, index=False)

logger_msg = (
    f"Created synthetic development dataset: {len(df)} segments, "
    f"saved to {synthetic_path}\n"
    f"dataset_status = SYNTHETIC_DEVELOPMENT_ONLY\n"
    f"NOTE: Model metrics on this data have NO real-world predictive validity."
)
logger.info(logger_msg)

# Also save as CSV
df.to_csv(synthetic_dir / "synthetic_development_v0.1.csv", index=False)

print(logger_msg)
print(f"\nSynthetic dataset columns: {list(df.columns)}")
print(f"Sample data:\n{df.head(3).to_string()}")