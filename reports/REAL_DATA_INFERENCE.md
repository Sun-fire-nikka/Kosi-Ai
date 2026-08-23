# Real-Data Inference — V0.1

Command: `python scripts/run_real_inference.py --delta 1.0`

23 station assessments computed from REAL FMISC bulletin observations (2026-08-22) joined with official FMISC reference levels.

## Summary

- All stations below danger level on the snapshot date; hydrological stress 0 at 15/23 stations (observed ≤ warning/danger threshold), up to **43/100 at Baltara** (34.37 m vs DL 33.85 m, HFL 36.40 m).
- Highest vulnerability class on snapshot: **MODERATE (Baltara, score 42.8)**; Gandhighat 36.6 LOW; Kursela 31.0 LOW.
- No embankment inspection dataset exists → `reported_condition` component inactive for all stations (weights renormalised over active components only).
- Historical link status: **UNAVAILABLE** for all stations (no verified gauge→embankment-section mapping). Historical events are exposed via `/historical-events` but never auto-assigned.

## Scenario example (+1.0 m at Dheng bridge)

| Field | Base | Scenario |
|---|---|---|
| Water level | 69.90 m | 70.90 m |
| Danger margin | −1.10 m | −0.10 m |
| HFL margin | 3.57 m | 2.57 m |

Labelled `SCENARIO_SIMULATION_NOT_A_VALIDATED_FLOOD_FORECAST`.

## Explicit non-claims

- These are engineering-informed vulnerability indicators, not probabilities of failure.
- No breach probability is produced anywhere in V0.1.
