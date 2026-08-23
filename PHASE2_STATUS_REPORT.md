# PHASE 2: REAL DATA → MODEL — Status Report

## Current Data Status

| Directory | Status | Notes |
|---|---|---|
| `data/raw/` | **EMPTY** | No real Kosi observation data ingested yet |
| `data/synthetic/` | Populated | 200-segment synthetic dataset (`SYNTHETIC_DEVELOPMENT_ONLY`) |
| `data/manifest.yaml` | Populated | Empty manifest (no real datasets) |
| `data/processed/` | Empty | No processed datasets yet |
| `configs/data_sources.yaml` | Populated | 5 sources, all `NOT_YET_INGESTED` |
| `configs/feature_registry.yaml` | Populated | 52 features with metadata |
| `docs/DATA_DICTIONARY.md` | Populated | 52 features with availability classifications |
| `docs/DATA_ACQUISITION.md` | Populated | Data gaps and acquisition priorities |
| `scripts/audit_data.py` | Created | Audit pipeline (produces report when data exists) |
| `scripts/build_training_dataset.py` | Created | Model dataset builder (requires verified events) |

## PHASE 2 STEP 1: REAL DATA INGESTION Tooling

**Created:** `phase2_toolkit.py`

**Functionality:**
- `ingest_real_dataset()` — Ingests a single dataset from `data/raw/`
  - Preserves original file
  - Creates metadata entry in `data/manifest.yaml`
  - Records: source, source URL, download date, coverage period, spatial coverage, variables, units, temporal resolution, verification status
  - Classifies variable availability (AVAILABLE/DERIVABLE/NOT_AVAILABLE/UNKNOWN)
  - Does **not** fabricate missing values or observations

- `run_audit_pipeline()` — Runs audit over real data in `data/`
  - Reports: records, date ranges, stations/segments, missingness, duplicates, units, distributions, geographic coverage
  - Candidate target variables and features
  - Data gaps identification

**Current output:** Since `data/raw/` is empty, the audit reports no real data found and instructs user to place datasets.

## Required Action for Data Ingestion

To proceed, place verified Kosi observation datasets in `data/raw/` with proper provenance. Each dataset should include:

- Original data file (CSV, Excel, JSON, or Parquet)
- Source name (e.g., "Bihar WMBS", "IMD", "NRSC/Bhuvan")
- Source URL or access path
- Download/access date
- Variables present with units
- Temporal coverage (start/end dates)
- Spatial coverage (station/segment locations)
- Verification status

## PHASE 2 STEP 2: DATA AUDIT

**Pipeline:** `phase2_toolkit.py` → `scripts/audit_data.py`

**Would produce:** `reports/DATA_AUDIT_REPORT.md` containing:
- Number of records per dataset
- Date ranges (start/end)
- Stations/segments count
- Missingness analysis (per-column, percentages)
- Duplicate record counts
- Units for each variable
- Distributions (for numeric variables)
- Geographic coverage (bounding boxes, centroids)
- Candidate target variables
- Candidate features
- Data gaps identification

**Current output:** No real data found — audit instructs user to place data in `data/raw/`.

## PHASE 2 STEP 3: DATA INTEGRATION

**Would build:** `data/processed/kosi_canonical.parquet`

**Rules:**
- Join only observations defensibly joinable (same segment_id, compatible timestamps)
- **Do NOT** force joins merely to increase row count
- Preserve: source provenance, timestamp, station/segment identity, spatial coordinates, event identity

**Current status:** Cannot run — no source data in `data/raw/`.

## PHASE 2 STEP 4: HISTORICAL EVENT MINING

**Would create:** `data/processed/kosi_events.parquet`

**Schema (only fields supported by source):**
- event_id, event_date, start_date, end_date
- location, segment_id, water_level, discharge, rainfall
- inundation, breach, breach_location, damage
- source

**Rule:** If a field is unavailable, leave it missing rather than inventing it.

**Current status:** No verified historical reports/data placed in `data/raw/`.

## PHASE 2 STEP 5: DEFINE THE SUPERVISED TARGET

**Requires inspection of:** Verified failure/breach events

**If insufficient positive examples:**
> "Insufficient verified failure labels for supervised breach prediction."
> Then use engineering vulnerability index + anomaly detection/historical similarity as V1.

**If sufficient verified events exist:**
> Define `failure_event_within_horizon` with explicitly documented prediction horizon.

**Current status:** No verified failure events have been placed in `data/raw/`. Insufficient for supervised model.

## PHASE 2 STEP 6: BUILD MODEL DATASET

**Would create:** `data/processed/kosi_training.parquet`

**With:**
- Features, target, timestamp, spatial identifier
- Event identifier, provenance

**Prevents:**
- Temporal leakage
- Spatial leakage
- Post-event leakage
- Duplicated event leakage

**Current status:** Cannot run without verified event data.

## PHASE 2 STEP 7: TRAIN BASELINES

**Only if target quality is sufficient.**

Trains:
1. Logistic Regression
2. Random Forest
3. XGBoost if justified

Reports: precision, recall, F1, PR-AUC, ROC-AUC, confusion matrix, calibration, threshold analysis

**Explicitly examines:** Recall for failure events (safety-oriented application)

**Current status:** Insufficient data — cannot train.

## PHASE 2 STEP 8: TEMPORAL VALIDATION

**Does NOT use:** Naive random train/test split

**Uses:** Chronological/event-aware validation

Documents:
- Training period
- Validation period
- Test period

**Current status:** N/A — no model trained yet.

## PHASE 2 STEP 9: EXPLAINABILITY

**Would produce:**
- Global feature importance
- Permutation importance
- SHAP if computationally justified

**Individual predictions:** top_risk_factors (only factors supported by model)

**Current status:** N/A — no model trained yet.

## PHASE 2 STEP 10: MODEL CARD

**Would create:** `docs/MODEL_CARD.md`

**Includes:**
- Model purpose, training data, features, target definition
- Validation strategy, metrics, limitations
- Known data gaps, intended use, non-intended use
- Model version, dataset version

**Current status:** N/A — no model trained yet.

## PHASE 2 STEP 11: MODEL ARTIFACT

**Would save:** `models/kosi_risk_v0.1/`

**With:**
- Model, preprocessing, feature list, configuration, metadata, evaluation results
- Must be reproducible from the repository

**Current status:** N/A — no model trained yet.

## PHASE 2 STEP 12: IMPORTANT

**Never report:** Synthetic-data performance as Kosi performance

**Never claim:** "X% probability of breach" unless model has validated probabilistic target

**Never:** Fabricate labels or Kosi observations

**Current status:** All policies in place; awaiting real data.

---

## ⚠ STATUS: REAL DATA INGESTION REQUIRED

**To proceed from PHASE 2 to a scientifically defensible Kosi ML model, the following is needed:**

1. **Place verified datasets in `data/raw/`** with proper provenance documentation
2. **Run the ingestion tooling** to create metadata entries in `data/manifest.yaml`
3. **Run the audit pipeline** to produce `reports/DATA_AUDIT_REPORT.md`
4. **Assess verified failure/breach event availability** for supervised target definition

**Without real data ingested, the pipeline cannot progress beyond the data ingestion and audit stages. The existing infrastructure (source registry, feature registry, audit tools, synthetic dataset) is ready and waiting for real Kosi observation data.**

## Next Steps

1. **Obtain verified Kosi River observation data** from:
   - Bihar Water Resources Department FMISC bulletins
   - Central Water Commission (CWC) data
   - India Meteorological Department (IMD) rainfall data
   - ISRO NRSC/Bhuvan satellite data
   - Bihar Embankment Asset Management System

2. **Place datasets in `data/raw/`** with proper file structure and metadata

3. **Re-run the PHASE 2 toolkit** to ingest, audit, and assess data quality

4. **Assess verified event availability** for supervised model feasibility

5. **Proceed to model training** if target quality is sufficient, or use engineering vulnerability index + anomaly detection as V1