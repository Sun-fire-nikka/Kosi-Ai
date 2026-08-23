# Kosi Embankment Data Acquisition Plan

**Version:** 0.1.0  
**Status:** Development V0.1 — data gaps identified; acquisition prioritized.  
**Purpose:** Document exactly which real-world data is still required to transition from the engineering vulnerability index to a supervised machine-learning model.

---

## Current Data Status

The following data sources have been **identified** (known, accessible), but none have been **ingested** (loaded and validated into the system). All have `verification_status: NOT_YET_INGESTED` in `configs/data_sources.yaml`.

| Source | Organization | Dataset | Variables | Temporal Resolution | Spatial Resolution | Priority |
|---|---|---|---|---|---|---|
| **Bihar Water Resources Department FMISC** | Government of Bihar | Kosi Embankment Bulletin | river_level, discharge, water_level | daily | segment-level | **CRITICAL** |
| **India-WRIS** | Central Water Commission | Kosi Basin Flood and Sediment Management Master Plan | embankment_height, crest_elevation, freeboard | annual | segment-level | **CRITICAL** |
| **NRSC/Bhuvan** | Indian Space Research Organisation | Satellite imagery and flood maps | elevation, river_width, floodplain_characteristics | varies (satellite pass) | 30m - 10m | **HIGH** |
| **IMD** | India Meteorological Department | Rainfall data | rainfall_24h, rainfall_72h, rainfall_7d | daily | district-level | **HIGH** |
| **Kosi Embankment Asset Management System** | Government of Bihar | Embankment condition, material, slope | embankment_condition, material, slope, erosion_indicator | irregular | segment-level | **MEDIUM** |

**Key:** CRITICAL = essential for vulnerability index; HIGH = strongly improves model; MEDIUM = useful but not urgent.

---

## Data Gaps — What Is Still Required

To transition from the engineering vulnerability index to a supervised model (`failure_event_within_horizon`), the following data must be acquired and ingested:

### 1. Historical Breach / Failure Events (HIGHEST PRIORITY)

No currently identified source provides a verified, labeled dataset of historical embankment breaches or failures with segment-level granularity and dates.

**What is needed:**
- A dataset containing: `segment_id`, `failure_date`, `failure_type` (breach/overtopping/erosion), `failure_severity`
- Time range: Ideally back to 1950s; minimum 20 years of historical events
- Verification: Each event must be cross-checked against government bulletins, CWC reports, or NRSC satellite analysis

**Potential sources to investigate:**
- CWC (Central Water Commission) annual flood reports
- Bihar State Disaster Management Authority (SDMA) records
- NRSC satellite breach detection products
- Peer-reviewed literature on Kosi historical breaches (e.g., 2008 event)
- Old irrigation department archives

### 2. River-Level Time Series (HIGH PRIORITY)

Required for computing `water_level_change` (a key derived feature) and for supervised model features.

**What is needed:**
- Daily river level readings for the Kosi River at multiple segment locations
- Time span: At least 10-15 years (2010-2025 preferred)
- Verification: Cross-check between Bihar WMBS, CWC data, and FMISC bulletins

**Current status:** IMD rainfall data is identified; river level from Bihar WMBS is identified but not yet ingested.

### 3. Embankment Condition Surveys (MEDIUM PRIORITY)

Required for `embankment_height`, `slope`, `material`, and `condition` features.

**What is needed:**
- Ground-truthed embankment cross-section surveys
- Material typology (earthen/concrete/stone-faced)
- Slope measurements from design surveys or LiDAR
- Condition assessments (good/fair/poor) from visual inspections

**Current status:** Kosi Embankment Asset Management System is identified but not yet ingested.

### 4. Sediment / Erosion Monitoring (MEDIUM PRIORITY)

Required for `erosion_indicator` and `sedimentation_indicator` features.

**What is needed:**
- Field reports of active erosion/sedimentation
- Satellite-derived sediment plumes (from NRSC/Bhuvan)
- Sediment load measurements from CWC

**Current status:** Identified but not ingested.

### 5. Soil Moisture Data (LOWER PRIORITY)

Required for `soil_moisture` feature (currently rated `NOT_AVAILABLE`).

**What is needed:**
- SMAP satellite soil moisture data (global, available openly)
- Local sensor networks (if any exist in Bihar)
- Model-derived estimates from rainfall and soil type

**Current status:** No operational source identified yet.

---

## Data Acquisition Priorities & Timeline

| Priority | Action | Estimated Effort | Target Date |
|---|---|---|---|
| **1** | Obtain CWC flood reports and Bihar FMISC bulletins; parse river level and discharge data | 2-3 weeks (data parsing) | 2026-09-30 |
| **2** | Contact Bihar SDMA for historical breach records; verify segment IDs match Kosi asset management system | 4-6 weeks (records request) | 2026-10-31 |
| **3** | Acquire NRSC satellite imagery time series for flood extent and river width extraction | 4-8 weeks (image processing) | 2026-11-30 |
| **4** | Negotiate access to Kosi Embankment Asset Management System data | 6-8 weeks (administrative) | 2026-12-31 |
| **5** | Investigate SMAP soil moisture data for the Kosi basin; assess derivability | 2 weeks (feasibility) | 2026-09-15 |

---

## Provenance & License Guidance

**Rule:** Only use datasets whose provenance can be documented and whose license allows academic/research use.

- **Bihar FMISC bulletins:** Public access; cite as "Bihar Water Resources Department, Kosi Embankment Bulletin".
- **India-WRIS:** CWC data portal; may require registration; cite appropriately.
- **NRSC/Bhuvan:** ISRO data policy; free for research with attribution.
- **IMD rainfall:** Indian Government data, public domain; cite as "India Meteorological Department".
- **Never download random internet datasets** without verified provenance and license.

---

## Next Steps

1. **Immediate (2 weeks):** Write Python scripts to parse Bihar FMISC bulletin PDFs/Web pages for river level/discharge time series.
2. **Short-term (1 month):** Submit data request to Bihar SDMA for historical breach records.
3. **Medium-term (2 months):** Acquire NRSC Sentinel/SAR imagery for the Kosi basin; extract river width and floodplain characteristics.
4. **Long-term (6 months):** Once all identified data is ingested, re-classify features from `NOT_AVAILABLE`/`DERIVABLE` to `AVAILABLE`, and begin supervised model development with `failure_event_within_horizon` target.

---

## Contact & Provenance Tracking

All data acquisition efforts must record:
- Date of request/access
- Contact person/organization
- Reference number (if applicable)
- License or access agreement ID
- Last verified date

This information should be stored in `data/manifest.yaml` alongside the dataset metadata.