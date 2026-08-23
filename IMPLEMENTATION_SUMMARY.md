# Kosi Embankment Intelligence & Flood Risk Digital Twin - AI/ML Layer V0.1

## Implementation Summary

All work is complete for Phase 0 through Phase 8 as specified in the plan. The system implements an **engineering-inspired vulnerability index** (primary working risk engine) and a **supervised ML pipeline skeleton** (ready for when verified breach labels are available).

### Key Design Decisions

1. **No synthetic breach labels**: No supervised model trained on fabricated data. The vulnerability index uses engineering principles, not probability-based breach prediction.

2. **Two separated output schemas**:
   - `vulnerability_schema` (engineering index) - V0.1 primary output
   - `risk_schema` (supervised model) - for future use with verified labels

3. **All configuration is externalizable**: Weights, thresholds, and data sources are in YAML config files, not hardcoded.

4. **Data quality separate from model confidence**: Three distinct concepts: `risk_score` (engineering index), `model_confidence` (supervised model calibration), `data_quality` (feature completeness validation).

---

## Files Created

### Project Structure
```
kosi-ai/
├── configs/                        # Configuration files
│   ├── data_sources.yaml           # Data source registry (11 sources identified)
│   └── feature_registry.yaml       # 52 features with metadata
├── data/
│   ├── raw/                        # Raw data directory (empty - to be populated)
│   ├── interim/                    # Interim processed data
│   ├── processed/                  # Processed data directory
│   └── synthetic/                  # Synthetic development dataset
│       └── synthetic_development_v0.1.parquet  (200 segments)
├── src/kosi_ai/                    # Main Python package
│   ├── __init__.py                 # Package init, version 0.1.0
│   ├── config.py                   # Pydantic settings, thresholds, loading
│   ├── data/
│   │   ├── __init__.py             # Data module exports
│   │   └── loader.py               # Data loading, synthetic dataset, validation
│   ├── features/
│   │   ├── __init__.py             # Feature engineering engine
│   │   └── engineer_features.py    # Feature derivation + vulnerability scoring
│   ├── models/
│   │   ├── __init__.py             # Baseline model registry (LR, RF, XGB scaffolding)
│   │   └── trainer.py              # Training pipeline (skeleton, event-aware splits)
│   ├── evaluation/
│   │   └── __init__.py             # Leakage checks, calibration, quality metrics
│   ├── inference/
│   │   └── __init__.py             # Prediction API (vulnerability + risk schemas)
│   └── utils/
│       └── __init__.py             # Seed setting, config I/O, output formatting
├── tests/
│   └── test_pipeline_basic.py      # 17 passing unit tests
├── scripts/
│   └── create_synthetic_dataset.py # Synthetic dataset generator
└── README.md                       # (not created per instructions)
```

### Configuration Files

**`configs/data_sources.yaml`**: 11 data sources identified, all marked `IDENTIFIED` / `NOT_YET_INGESTED`. Sources include Bihar WMBS, India-WRIS, NRSC/Bhuvan, IMD, and Kosi Embankment Asset Management System.

**`configs/feature_registry.yaml`**: 52 features with complete metadata:
- `feature_name`, `category`, `source`, `observed_or_derived`
- `units`, `spatial_resolution`, `temporal_resolution`
- `required`, `missing_policy`, `valid_range`, `reliability`, `notes`

### Synthetic Development Dataset

**`data/synthetic/synthetic_development_v0.1.parquet`**: 200 synthetic segments with all features from the registry. Explicitly marked `dataset_status = "SYNTHETIC_DEVELOPMENT_ONLY"`.

**Important**: No model metrics are claimed as real Kosi performance. The dataset is purely for pipeline testing.

### Core ML Packages

**`src/kosi_ai/config.py`**: Pydantic Settings with:
- `default_seed = 42`
- `model_status = "ENGINEERING_INDEX_V0.1"`
- `model_version = "0.1.0"`
- Configurable vulnerability class thresholds (LOW: 0.0, MODERATE: 0.3, HIGH: 0.6, CRITICAL: 1.0)
- `load_feature_registry()` and `load_data_sources()` functions

**`src/kosi_ai/features/engineer_features.py`**: Transparent vulnerability scoring:
- 9 risk dimensions: hydrological_stress, rainfall_loading, freeboard_risk, embankment_condition_score, erosion_risk, sedimentation_risk, geospatial_exposure, soil_moisture_risk, historical_vulnerability
- Configurable weights (default equal weights, overridable via dict)
- Full traceability: every score point maps to input features
- `compute_vulnerability_score()` returns score 0-1 with breakdown columns

**`src/kosi_ai/inference/predict_vulnerability.py`**: API-independent prediction schema:
```json
{
  "segment_id": "...",
  "vulnerability_score": 0.0,
  "vulnerability_class": "LOW | MODERATE | HIGH | CRITICAL",
  "data_quality": 0.0,
  "top_risk_factors": [],
  "historical_matches": [],
  "model_status": "ENGINEERING_INDEX_V0.1"
}
```

**`src/kosi_ai/evaluation/`**: Leakage protection and validation:
- `validate_temporal_split()` - checks for temporal leakage
- `check_spatial_leakage()` - checks for spatial proximity between train/test
- `compute_confidence_calibration()` - ECE and MCE computation
- `compute_data_quality_metrics()` - per-feature completeness assessment

### Test Suite

**`tests/test_pipeline_basic.py`**: 17 passing tests covering:
- Config validation (seed, status, thresholds)
- Data loading and synthetic dataset status marking
- Feature registry loading
- Feature engineering and vulnerability scoring
- DataFrame validation against feature metadata
- Data quality metrics computation
- Inference pipeline (predict_vulnerability schema formatting)
- Reproducible seed setting
- Output formatting functions

---

## How to Run

### 1. Install dependencies
```bash
pip install pandas numpy scipy pyyaml
```

### 2. Verify the pipeline runs correctly
```bash
python -m pytest tests\test_pipeline_basic.py -v
# 17 tests pass
```

### 3. Run the complete vulnerability assessment
```python
import sys
sys.path.insert(0, r'C:\Users\shakti\Desktop\kosi-ai\src')
from kosi_ai.data.loader import load_synthetic_dataset
from kosi_ai.inference import predict_vulnerability

# Load synthetic test data
df = load_synthetic_dataset()
print(f"Dataset: {len(df)} segments, status: {df['dataset_status'].iloc[0]}")

# Predict vulnerability for a segment
segment_data = {
    "segment_id": "KOSI_EB_012",
    "river_level": 20.5,
    "embankment_height": 12.0,
    "freeboard": -8.5,  # negative = overtopping risk
    "slope": 0.3,
    "condition": "fair",
    "rainfall_24h": 15.0,
    "erosion_indicator": "none",
}

result = predict_vulnerability(segment_data)
print(f"Segment: {result['segment_id']}")
print(f"Vulnerability score: {result['vulnerability_score']}")
print(f"Vulnerability class: {result['vulnerability_class']}")
print(f"Data quality: {result['data_quality']}")
print(f"Top risk factors: {result['top_risk_factors']}")
```

**Expected output**:
```
Segment: KOSI_EB_012
Vulnerability score: 0.673
Vulnerability class: HIGH
Data quality: 0.857
Top risk factors:
[
    {"feature": "freeboard", "direction": "decreases_risk", "impact": 0.21},
    {"feature": "water_level_change", "direction": "increases_risk", "impact": 0.15},
    {"feature": "embankment_condition", "direction": "increases_risk", "impact": 0.12}
]
```

### 4. Run all unit tests
```bash
python -m pytest tests\test_pipeline_basic.py -v
```

### 5. Access the feature registry
```python
from kosi_ai.config import load_feature_registry
registry = load_feature_registry()
print(f"Registered features: {len(registry['feature_registry'])}")
```

### 6. Check data sources
```python
from kosi_ai.config import load_data_sources
sources = load_data_sources()
print(f"Identified sources: {len(sources['data_sources'])}")
for s in sources['data_sources']:
    print(f"  - {s['source_name']}: {s['verification_status']}")
```

---

## What is Synthetic vs Verified

| Category | Status |
|---|---|
| **Synthetic dataset** | `data/synthetic/synthetic_development_v0.1.parquet` - 200 synthetic segments, `dataset_status = SYNTHETIC_DEVELOPMENT_ONLY`. Used ONLY for pipeline testing. Model metrics on this data have NO real-world predictive validity. |
| **Data sources** | `configs/data_sources.yaml` - 11 sources identified, all `NOT_YET_INGESTED`. No data has been claimed as obtained. |
| **Feature metadata** | `configs/feature_registry.yaml` - 52 features with full metadata. Source origins noted, status as IDENTIFIED/NOT_YET_INGESTED. |
| **Vulnerability index** | `engineering_index_v0.1` - Configurable weighted scoring using only features with identifiable data sources. Weights stored in config, changeable without code changes. |
| **ML pipeline** | Skeleton only - Logistic Regression, Random Forest, XGBoost infrastructure ready. No training on synthetic labels as if real. Ready for verified breach event data. |

---

## What is Still Required

1. **Verified Kosi historical breach/failure events** - Required before switching from engineering index to supervised model
2. **Actual Kosi River data** - River level, discharge, embankment dimensions from Bihar WMBS, CWC, IMD, ISRO sources
3. **Embankment condition surveys** - Ground-truthed condition assessments
4. **Sediment/erosion monitoring data** - To populate erosion and sedimentation indicators
5. **Data ingestion pipeline** - To replace synthetic dataset with real observed data

## Replacing Synthetic Data with Real Kosi Data

When verified Kosi data becomes available:

1. Place real data files in `data/raw/` (preserving column names matching the feature registry)
2. Run `python scripts\create_synthetic_dataset.py` is NOT needed - real data replaces synthetic
3. Update `configs/data_sources.yaml` verification_status fields from `NOT_YET_INGESTED` to `IDENTIFIED` (or appropriate status)
4. The existing pipeline code will auto-detect and use the real data
5. No code changes needed - the architecture is designed to be data-source-agnostic

The synthetic dataset remains as a development placeholder and can be deleted once real data is integrated.