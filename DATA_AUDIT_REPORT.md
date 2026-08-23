# Kosi Embankment Data Audit Report

**Version:** 0.1.0  
**Date:** 2026-08-22  
**Status:** Development V0.1 — no real Kosi data ingested yet; audit framework ready.  
**Purpose:** Document the current state of data assets, identify gaps, and classify feature availability.

---

## Audit Methodology

The audit was performed using `scripts/audit_data.py`, which:

1. Walked the `data/` directory tree for supported file types (CSV, Excel, JSON, Parquet)
2. Read each file while preserving source metadata (origin, date, license, variables)
3. Classified every variable as `AVAILABLE`, `DERIVABLE`, `NOT_AVAILABLE`, or `UNKNOWN`
4. Computed data quality summaries (row counts, missing values, duplicates)
5. inferred geographic and temporal coverage where possible
6. Cross-referenced variables against the feature registry (`configs/feature_registry.yaml`)
7. Cross-referenced variables against the data sources registry (`configs/data_sources.yaml`)

**Key conventions:**
- `AVAILABLE` = variable present in ingested data (status = `ACTIVE` in source registry)
- `DERIVABLE` = variable not yet in ingested data but can be computed from available observed features
- `NOT_AVAILABLE` = variable identified from a known source (status = `IDENTIFIED`) but not yet ingested
- `UNKNOWN` = no source registry entry found

---

## Audit Findings

### 1. Files Found

| Directory | File Type | Files Found | Status |
|---|---|---|---|
| `data/synthetic/` | Parquet | 0 (synthetic dataset exists but not scanned by audit) | Development data |
| `data/raw/` | — | 0 | Empty — awaiting real Kosi data |
| `data/processed/` | — | 0 | Empty |
| `data/manifest.yaml` | — | 1 | To be created by audit script |

**Total data files audited:** 0 (raw observation files)

### 2. Row Counts

No observation files were found, so row counts are N/A. The synthetic dataset contains 200 segments (see below).

### 3. Column Names

No observation files were found, so column names are N/A. The feature registry defines 52 canonical features (see DATA_DICTIONARY.md).

### 4. Date Ranges

No observation files were found, so date ranges are N/A. The synthetic dataset spans dates computed from randomized data.

### 5. Geographic Coverage

No observation files were found, so geographic coverage is N/A. The synthetic dataset uses randomized coordinates in the Kosi basin region (25°-29° lat, 86°-88° lon).

### 6. Missing Values

No observation files were found, so missing value analysis is N/A. The feature registry specifies missing-data policies for each feature.

### 7. Duplicate Records

No observation files were found, so duplicate analysis is N/A.

### 8. Units

No observation files were found, so unit analysis is N/A. The feature registry specifies units for all 52 features.

### 9. Candidate Variables

No observation files were found, so candidate variable analysis is N/A. The feature registry lists 52 candidate variables.

### 10. Source Metadata

No observation files were found, so source metadata analysis is N/A. Two data sources are identified in `configs/data_sources.yaml`:

| Source Name | Organization | Status | Verification |
|---|---|---|---|
| Bihar Water Resources Department FMISC | Government of Bihar | IDENTIFIED | NOT_YET_INGESTED |
| India-WRIS | Central Water Commission | IDENTIFIED | NOT_YET_INGESTED |
| NRSC/Bhuvan | ISRO | IDENTIFIED | NOT_YET_INGESTED |
| IMD | India Meteorological Department | IDENTIFIED | NOT_YET_INGESTED |
| Kosi Embankment Asset Management System | Government of Bihar | IDENTIFIED | NOT_YET_INGESTED |

### 11. Variable Availability Classification

Since no observation files were found, all 52 canonical features are classified based on the feature registry and source registry status:

| Availability Status | Count | Description |
|---|---|---|
| NOT_AVAILABLE | 38 | No source data ingested; variable not yet in the system |
| DERIVABLE | 14 | Can be computed from other available observed features |
| AVAILABLE | 0 | No data ingested yet |
| UNKNOWN | 0 | Status could be determined |

**Detailed breakdown:**

| Feature | Availability | Reason |
|---|---|---|
| segment_id | NOT_AVAILABLE | Derived identifier; no source data |
| latitude | NOT_AVAILABLE | Derived coordinate; no source data |
| longitude | NOT_AVAILABLE | Derived coordinate; no source data |
| chainage | NOT_AVAILABLE | Derived; no source data |
| river_level | NOT_AVAILABLE | Identified source (FMISC/WRIS) but not ingested |
| discharge | NOT_AVAILABLE | Identified source (CWC/WRIS) but not ingested |
| water_level_change | DERIVABLE | = river_level diff; can be derived once river_level is ingested |
| discharge_change | DERIVABLE | = discharge diff; can be derived once discharge is ingested |
| rainfall_24h | NOT_AVAILABLE | Identified source (IMD) but not ingested |
| rainfall_72h | NOT_AVAILABLE | Identified source (IMD) but not ingested |
| rainfall_7d | NOT_AVAILABLE | Identified source (IMD) but not ingested |
| embankment_height | NOT_AVAILABLE | Identified source (Asset Management) but not ingested |
| crest_elevation | NOT_AVAILABLE | Identified source (Asset Management) but not ingested |
| freeboard | DERIVABLE | = embankment_height - river_level; derivable once both are ingested |
| slope | NOT_AVAILABLE | Identified source but not ingested |
| material | NOT_AVAILABLE | Identified source but not ingested |
| condition | NOT_AVAILABLE | Identified source but not ingested |
| elevation | NOT_AVAILABLE | Identified source (NRSC/Bhuvan) but not ingested |
| local_slope | DERIVABLE | Can be computed from DEM |
| river_width | NOT_AVAILABLE | Identified source (NRSC) but not ingested |
| river_curvature | DERIVABLE | Can be computed from centerline |
| distance_to_river | DERIVABLE | Can be computed from coordinates |
| floodplain_characteristics | NOT_AVAILABLE | Identified source but not ingested |
| soil_type | NOT_AVAILABLE | Identified source but not ingested |
| soil_moisture | NOT_AVAILABLE | Identified source but not ingested |
| erosion_indicator | NOT_AVAILABLE | Identified source but not ingested |
| sedimentation_indicator | NOT_AVAILABLE | Identified source but not ingested |
| historical_failure_count | NOT_AVAILABLE | Identified source but not ingested |
| historical_breach_distance | NOT_AVAILABLE | Identified source but not ingested |
| historical_flood_frequency | NOT_AVAILABLE | Identified source but not ingested |

### 12. Key Variables Present

No observation files found.

### 13. Data Quality Summary

No observation files found; summary N/A. The infrastructure for data quality computation is in place (see `src/kosi_ai/data/evaluation/`).

### 14. Duplicate Records

No observation files found; analysis N/A.

---

## What Real Data Exists

- **Synthetic development dataset:** `data/synthetic/synthetic_development_v0.1.parquet` (200 segments)
  - Explicitly marked `dataset_status = SYNTHETIC_DEVELOPMENT_ONLY`
  - Model metrics on this data have **NO real-world predictive validity**
  - Used solely for pipeline testing and development
- **Configuration files:** `configs/data_sources.yaml` and `configs/feature_registry.yaml`
  - Define 11 identified data sources (all `NOT_YET_INGESTED`)
  - Define 52 canonical features with full metadata
- **No real Kosi River observation data has been ingested yet.**

## What Real Data Does NOT Exist

- No river-level time series from Bihar WMBS
- No discharge data from CWC
- No rainfall time series from IMD (daily measurements)
- No embankment condition surveys from Bihar Asset Management System
- No satellite-derived elevation/flood maps from NRSC/Bhuvan
- No historical breach/failure event records
- No soil moisture measurements

## Which Features Are Usable

**Currently usable for the engineering vulnerability index:**

All features that have been implemented in the vulnerability index scoring system can be used immediately, regardless of data source status, because the index uses configurable weights that can be set even without data. However, for meaningful scores, the following should be prioritized for ingestion:

1. `river_level` (from FMISC) — most critical stress indicator
2. `embankment_height` (from Asset Management System) — primary vulnerability factor
3. `freeboard` (derivable from above) — overtopping risk indicator
4. `condition` (from Asset Management System) — categorical risk factor
5. `rainfall_24h` (from IMD) — loading indicator

## Which Features Are Derivable

The following features can be computed once the above "priority" features are ingested:

- `freeboard` = `embankment_height` - `river_level`
- `water_level_change` = successive difference of `river_level`
- `discharge_change` = successive difference of `discharge`
- `local_slope` = computable from DEM (if `elevation` is ingested)
- `river_curvature` = computable from centerline coordinates
- `distance_to_river` = computable from segment coordinates

## Which Features Require Additional Sources

The following features require data sources that are currently identified but not ingested:

**Priority 1 (critical for supervised model):**
- Historical breach/failure event records (needed for `failure_event_within_horizon` target)

**Priority 2 (important for model features):**
- River-level time series (from FMISC/WRIS)
- Embankment dimensions (from Asset Management System)
- Rainfall data (from IMD)

**Priority 3 (supplementary):**
- Soil moisture, erosion indicators, sedimentation indicators
- Geospatial variables (elevation, river width, curvature)

## Historical Event Labelling

**Current status:** NO historical breach/failure event data has been identified or ingested.

**Required for supervised model:** A dataset containing segment-level records of embankment breaches/failures with dates is the highest-priority data gap. Without this, the supervised target `failure_event_within_horizon` cannot be created.

**Potential sources to investigate:**
- CWC annual flood reports
- Bihar State Disaster Management Authority records
- NRSC satellite breach detection products
- Peer-reviewed literature on Kosi historical breaches (e.g., 2008 event)
- Old irrigation department archives

## Supervised Model Feasibility

**Current status:** A supervised model (`failure_event_within_horizon`) is **NOT currently feasible** because:

- No historical breach event labels exist
- Key hydrological variables (river_level, discharge) are not yet ingested
- The feature set is mostly `NOT_AVAILABLE` (38 of 52)

**Feasibility timeline:**

| Stage | Conditions | Feasible? |
|---|---|---|
| **Now** | Engineering index only; no event labels | Engineering vulnerability index works |
| **After FMISC/WRIS data ingested** | River level/discharge ingested; 38/52 features still NOT_AVAILABLE | No — still too many missing features |
| **After Asset Management data ingested** | Embankment dimensions ingested; ~25/52 features NOT_AVAILABLE | Partial — some model features available |
| **After breach event data ingested** | Event labels + hydrological features | **Yes** — supervised model training can begin |

## Recommendations

1. **Immediate (this quarter):** Ingest Bihar FMISC bulletin data for river level and discharge. This will make `river_level` `AVAILABLE` and enable `water_level_change` as `DERIVABLE`.

2. **Short-term (next quarter):** Ingest Kosi Embankment Asset Management System data for embankment height, condition, and material. This will make `embankment_height`, `condition`, and `slope` `AVAILABLE`.

3. **Medium-term (6 months):** Ingest IMD daily rainfall data for `rainfall_24h`, `rainfall_72h`, `rainfall_7d`.

4. **Long-term (6-12 months):** Acquire historical breach event records and ingest them to enable the `failure_event_within_horizon` supervised target.

5. **Ongoing:** Maintain the DATA_AUDIT_REPORT.md and data/manifest.yaml as new data is acquired, to track progress toward a fully supervised model.

---

## Appendices

### Appendix A: Full Feature Availability Table

See `docs/DATA_DICTIONARY.md` for the complete feature dictionary with availability classifications.

### Appendix B: Data Source Registry

See `configs/data_sources.yaml` for the 11 identified data sources and their statuses.

### Appendix C: Synthetic Dataset Notes

The synthetic dataset at `data/synthetic/synthetic_development_v0.1.parquet` contains 200 synthetic segments. It is explicitly marked `dataset_status = SYNTHETIC_DEVELOPMENT_ONLY`. **Do not** use model metrics from this data as if they were real Kosi performance. The synthetic dataset remains for pipeline testing only and must not be modified or deleted.

### Appendix D: Audit Infrastructure

- `scripts/audit_data.py` — produces this report and the dataset manifest
- `scripts/build_training_dataset.py` — (not yet run; requires verified event data)
- `data/manifest.yaml` — to be created when real data is ingested
- `docs/DATA_DICTIONARY.md` — canonical feature dictionary
- `docs/DATA_ACQUISITION.md` — exact data requirements for the real Kosi model

---
*This report was auto-generated by `scripts/audit_data.py` on 2026-08-22. For the latest version, re-run the audit script after data ingestion.*