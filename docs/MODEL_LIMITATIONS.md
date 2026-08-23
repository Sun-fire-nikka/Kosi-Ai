# Model Limitations — Kosi AI V0.1

**V0.1 IS NOT A VALIDATED BREACH-PREDICTION MODEL.**

## Data limitations

- Only **23 real hydrological station observations** exist (single snapshot, 2026-08-22). No time series; rate-of-change features cannot be computed from real data.
- Embankment status observations are **not available at all**: no inspection dataset exists in the repository. The condition component of the vulnerability engine activates only when such data is supplied.
- **No verified breach/no-breach labelled training dataset exists.** The 32 historical records contain 9 breach-related events, but only 2–3 carry any measurement, and none are linked to pre-event hydrological observations.
- Historical breach records are sparse and heterogeneous (11 source organizations, mixed date precision: 11/32 year-only).
- No discharge linkage: barrage discharge data exists but covers Birpur only and cannot be joined to bulletin gauges.
- Missing entirely: rainfall time series, soil/geotechnical data, sediment data, embankment geometry observations (FMISC GIS exposes schema only — zero feature records), chainage/segment identifiers.

## Model limitations

- The vulnerability score is an **engineering-informed indicator (0–100)**, not a probability of failure.
- Danger level is an official river threshold — it is **not embankment height** and is never used as one.
- Station names are identifiers, never ML features.
- Synthetic data (`SYNTHETIC_DEVELOPMENT_ONLY`) is used only to validate the ML pipeline; synthetic metrics are never presented as Kosi accuracy.
- Scenario simulation is **NOT a validated flood forecast**; it is arithmetic re-evaluation of margins under a user-supplied water-level delta.
- Validation of any future supervised model must be event-aware/temporal; random row splits would leak samples from the same flood event across train/test.
