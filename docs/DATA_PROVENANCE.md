# Data Provenance Matrix — Kosi AI V0.1

Statuses: OBSERVED (real measurement) · DERIVED (computed from observed) · ESTIMATED · SIMULATED (synthetic) · UNAVAILABLE.

| Feature | Source | Real/Synthetic | Type | Current Status | Confidence |
|---|---|---|---|---|---|
| observed_water_level | FMISC bulletin 2026-08-22 | Real | Observed | 23/23 stations | High |
| danger_level | FMISC bulletin + reference table | Real | Observed | 23/23 | High |
| HFL | FMISC bulletin + reference table | Real | Observed | 23/23 | High |
| warning_level | FMISC reference bulletin | Real | Observed | 3/23 matched; rest null | Medium |
| water_level_minus_warning | computed | Real | Derived | where inputs exist | High |
| water_level_minus_danger | computed | Real | Derived | 23/23 | High |
| water_level_minus_HFL / HFL_margin | computed | Real | Derived | 23/23 | High |
| hydrological_stress | computed (warning→HFL scale) | Real | Derived | where thresholds exist | High |
| discharge (barrage) | NDMI obs + FMISC forecast, Birpur only | Real | Observed | dataset loaded; NOT joined to gauges | Medium |
| design_discharge_cusecs | NDMI/FMISC | Real | Observed | 17/17 | Medium |
| historical_breach_event | verified records xlsx | Real | Observed | 9 breach events | High (as evidence) |
| historical measurements (discharge/dimensions) | same, 2–3 events | Real | Observed | sparse | Low coverage |
| embankment_height | — | — | — | UNAVAILABLE (FMISC GIS schema only, 0 records) | — |
| embankment_condition / inspection | — | — | — | UNAVAILABLE | — |
| crest_level, side_slope, top_width, freeboard | — | — | — | UNAVAILABLE | — |
| rainfall (any horizon) | — | — | — | UNAVAILABLE | — |
| gauge-level discharge linkage | — | — | — | UNAVAILABLE | — |
| soil / geotechnical | — | — | — | UNAVAILABLE | — |
| sediment / erosion observations | — | — | — | UNAVAILABLE | — |
| chainage / section geometry | — | — | — | UNAVAILABLE | — |
| forecast_6h…forecast_72h (hourly) | — | — | — | UNAVAILABLE (source is date-based; never inferred) | — |
| all 52-feature synthetic columns | synthetic_development_v0.1.parquet | Synthetic | Simulated | SYNTHETIC_DEVELOPMENT_ONLY pipeline validation | n/a |

## Rule

A feature may be labelled real **only** when a source file exists in this repository and the loader reads it. Nothing in this matrix is aspirational.
