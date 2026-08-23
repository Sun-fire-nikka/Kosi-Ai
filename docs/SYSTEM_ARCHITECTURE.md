# System Architecture — Kosi AI V0.1

```
DATA SOURCES (all local, provenance-tracked)
  FMISC bulletin PDF ──► data/processed/kosi_hydrology/kosi_bulletins.parquet   (23 real obs)   [IMPLEMENTED]
  FMISC warning-level bulletin ──► kosi_warning_levels.xlsx                     (15 stations)  [IMPLEMENTED]
  NDMI/FMISC discharge tables ──► kosi_discharge_datasets.xlsx                  (17 records)   [IMPLEMENTED]
  Verified historical records ──► Kosi_32_...xlsx                               (32 events)    [IMPLEMENTED]
  Synthetic development set ──► synthetic_development_v0.1.parquet              (200 segments) [IMPLEMENTED]
  FMISC ArcGIS MapServer schema ──► data/raw/fmisc_gis/*.json                   (schema only)  [VERIFIED, no records]
        │
        ▼
DATA INGESTION            src/kosi_ai/data/loaders.py                 [IMPLEMENTED + TESTED]
        ▼
VALIDATION + PROVENANCE   dataset_provenance(), feature status tags    [IMPLEMENTED]
        ▼
FEATURE ENGINEERING       src/kosi_ai/features/hydrology.py           [IMPLEMENTED + TESTED]
  water_level_minus_warning / _danger / _HFL, margins,
  danger_exceedance_ratio, hydrological_stress (warning→HFL scaled 0–100)
        ▼
┌───────────────────────────────────────────────────────────────┐
│ HYDROLOGICAL ENGINE      stress & margins          [IMPLEMENTED] │
│ HISTORICAL ENGINE        event DB + link gating    [IMPLEMENTED] │
│ VULNERABILITY ENGINE     config-weighted score     [IMPLEMENTED] │
│ ML DEVELOPMENT           LR + RF on SYNTHETIC ONLY [IMPLEMENTED] │
│ SCENARIO ENGINE          ±delta re-evaluation      [IMPLEMENTED] │
│ SUPERVISED BREACH MODEL  —                         [NOT JUSTIFIED]│
└───────────────────────────────────────────────────────────────┘
        ▼
INFERENCE LAYER           src/kosi_ai/inference/real_inference.py     [IMPLEMENTED + TESTED]
        ▼
API                       src/kosi_ai/api/main.py (FastAPI)
  POST /predict · POST /scenario · GET /model-info ·
  GET /data-quality · GET /sections · GET /historical-events   [IMPLEMENTED + TESTED]
        ▼
FRONTEND / VISUALIZATION  external repo — NOT modified in V0.1        [PLANNED INTEGRATION]
```

## Design rules enforced in code

1. Every feature carries a status: OBSERVED / DERIVED / ESTIMATED / SIMULATED / UNAVAILABLE.
2. Missing values propagate as `null`; never imputed, never zero-filled.
3. Historical events are linked to sections only with `CONFIRMED` mapping; otherwise `historical_link_status = "UNAVAILABLE"`.
4. No endpoint returns breach probability; `/model-info` states this explicitly.
5. Vulnerability weights live in `configs/model_config.yaml`, not hard-coded.
