# Kosi Embankment Intelligence

Section-wise flood-risk and embankment-status intelligence for the Kosi River (Bihar, India) — combining real government hydrological observations, a verified historical breach-event database, an explainable engineering vulnerability engine, scenario simulation, and a development ML pipeline.

> **V0.1 — Prototype.** This system is an **engineering-informed embankment vulnerability and status intelligence** tool. It is **NOT a validated breach-prediction model**, and it never returns a breach probability.

## Problem

The Kosi embankments protect millions of people in Bihar, but failures (1954, 1963, 1968, 1971, 1980, 1984, 1987, 1991, 2008 Kusaha avulsion, 2024 Bhubhaul) have been catastrophic. There is no single operational tool that fuses official gauge observations, official threshold levels, historical failure evidence, and structural status into one explainable per-section risk view. Kosi AI builds that foundation honestly, labelling every data point as OBSERVED / DERIVED / SIMULATED / UNAVAILABLE.

## What the system does today

| Capability | Data | Status |
|---|---|---|
| Station water-level ingestion (23 gauges) | REAL — FMISC bulletin 2026-08-22 | ✅ Working |
| Official thresholds: danger level, HFL, warning level | REAL — FMISC bulletins | ✅ Working |
| Danger/HFL/warning margins + hydrological stress (0–100) | DERIVED from real obs | ✅ Working |
| Engineering vulnerability score & class (config-weighted, explainable) | REAL inputs | ✅ Working |
| Historical breach/flood event database (32 audited events, 1954–2025) | REAL evidence | ✅ Working (evidence only) |
| Scenario simulation (+0.5 … +2.0 m deltas) | DERIVED arithmetic | ✅ Working (`SCENARIO_SIMULATION` label) |
| Synthetic ML pipeline validation (LogReg + RF, metrics, artifacts) | SYNTHETIC_DEVELOPMENT_ONLY | ✅ Working |
| REST API (predict / scenario / sections / history / quality) | mixed | ✅ Working |
| Embankment section geometry, condition inspections, chainage | UNAVAILABLE | ❌ Not in repo |
| Supervised breach prediction | NOT SCIENTIFICALLY JUSTIFIED | ❌ Deliberately not built |
| Hourly forecasts (6h–72h) | UNAVAILABLE (source is date-based) | ❌ Never inferred |

## Architecture

```
Real sources (bulletins, reference levels, discharge, 32 events)
        ↓ ingestion + provenance            src/kosi_ai/data
Feature engineering (margins, stress)       src/kosi_ai/features
        ↓
┌ Hydrological engine ── Historical engine ── Vulnerability engine ─┐
│ (stress/margins)     (32-event DB, link    (YAML weights,         │
│                       gating)              explainable)           │
│              ML development (SYNTHETIC_DEVELOPMENT_ONLY)          │
│              Scenario engine (±delta re-evaluation)               │
└───────────────────────────────────────────────────────────────────┘
        ↓ inference                          src/kosi_ai/inference
FastAPI: /predict /scenario /sections /historical-events /model-info /data-quality
```

## Data sources (all local, all provenance-tracked)

| File | Records | Source |
|---|---|---|
| `data/processed/kosi_hydrology/kosi_bulletins.parquet` | 23 stations × 24 fields | FMISC Bihar *Daily Water Level & Flood Forecast* bulletin, 22-08-2026 |
| `data/raw/official/hydrology/kosi_warning_levels.xlsx` | 15 stations | WRD Bihar / FMISC Kosi Flood Bulletin (HFL, danger, warning levels) |
| `data/raw/official/hydrology/kosi_discharge_datasets.xlsx` | 17 records | NDMI (MHA, GoI) observations; FMISC Mike-11 Birpur forecasts |
| `data/raw/historical/Kosi_32_Verified_Historical_and_Flood_Records.xlsx` | 32 events | Multi-agency verified records (CWC, NRSC/ISRO, IMD, Parliament, research) |
| `src/data/synthetic/synthetic_development_v0.1.parquet` | 200 × 30 | **SYNTHETIC_DEVELOPMENT_ONLY** — pipeline validation exclusively |

FMISC ArcGIS BEAMS-KOSI MapServer was investigated: layer schemas verified, but the service exposes **zero observation records**; nothing was fabricated from it.

## Installation

```bash
git clone <repo-url>
cd kosi-ai
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Run the pipeline

```bash
# 1. Ingest + validate all datasets, build features
python scripts/ingest_data.py

# 2. Train synthetic development models (LR + RF)
python scripts/train_development_model.py

# 3. Real-data inference for all 23 stations (+ optional scenario delta)
python scripts/run_real_inference.py --delta 1.0

# 4. API
uvicorn src.kosi_ai.api.main:app --reload

# 5. Tests
pytest -q
```

## Example output (`run_real_inference.py`)

```
Station                WL(m)  DL(m) HFL(m) Stress Score Class
Baltara                34.37  33.85  36.40     43  42.8 MODERATE
Gandhighat             49.35  48.60  50.52     39  36.6 LOW
...
SCENARIO SIMULATION (Dheng bridge, +1.0 m):
  scenario_water_level 70.90 · danger_margin −0.10 m · labelled SCENARIO_SIMULATION
```

## Model evaluation — read this

`reports/MODEL_EVALUATION.md` contains precision/recall/F1/ROC-AUC/PR-AUC/confusion matrices for the synthetic models. **Synthetic metrics are not real-world Kosi accuracy.** The synthetic target has no learnable signal by construction; near-chance AUC is the honest result and demonstrates we do not fabricate performance.

## Scientific rules enforced in code

- No missing value is imputed or zero-filled.
- Danger level ≠ embankment height. Station names are identifiers, not features.
- Historical events attach to sections only with a CONFIRMED mapping; otherwise `UNAVAILABLE`.
- No endpoint returns breach probability (`GET /model-info` states this).
- Scenario outputs are always labelled as simulations, not forecasts.

## Roadmap

- **V1**: embankment-section dataset (chainage, crest, condition inspections) → full section-wise engine; gauge↔section mapping → historical evidence activation; hourly forecast ingestion; supervised breach baseline only if event-linked samples exist, validated event-aware/temporally.
- **V2**: rainfall/discharge fusion, multi-river generalisation.

## Documentation

`docs/` — SYSTEM_ARCHITECTURE · MODEL_LIMITATIONS · TRACEABILITY · DATA_PROVENANCE · HISTORICAL_BREACH_DATASET · PROJECT_STATUS · FEATURE_ENGINEERING · EXPERIMENTS
`reports/` — DATA_QUALITY_REPORT · MODEL_EVALUATION · REAL_DATA_INFERENCE

## License

MIT
