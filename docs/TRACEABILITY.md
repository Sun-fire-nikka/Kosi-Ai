# Data → Feature → Model Traceability

## 1. Station hydrological status (real data)

```
FMISC bulletin PDF (23 stations, 2026-08-22)          [OBSERVED]
        ↓ pdfplumber parse (Phase 3)
kosi_bulletins.parquet: observed_water_level, danger_level, HFL
        +
FMISC warning-level bulletin (15 stations)             [OBSERVED]
        ↓ station-name join (3/23 matched; gaps stay null)
warning_level, effective_danger_level, effective_HFL
        ↓ arithmetic
water_level_minus_warning / _danger / _HFL             [DERIVED, formula recorded]
danger_margin, HFL_margin, danger_exceedance_ratio     [DERIVED]
        ↓ linear interpolation warning→HFL scaled to 0–100
hydrological_stress                                    [DERIVED]
        ↓ config-weighted combination (configs/model_config.yaml)
vulnerability_score + vulnerability_class              [ENGINEERING-INFORMED INDICATOR]
```

## 2. Embankment condition component

```
Embankment inspection dataset          [UNAVAILABLE — no file exists in repo]
        ↓ (when supplied)
reported_condition → base score (GOOD 20 / FAIR 45 / POOR 75 / CRITICAL 95)
inspection remarks → keyword evidence (erosion, seepage, piping, cracks…)
        ↓
condition component of vulnerability score
```
Currently inactive for all real stations because the input dataset does not exist. The engine renormalises weights over active components only.

## 3. Historical vulnerability component

```
Kosi_32_Verified_Historical_and_Flood_Records.xlsx      [OBSERVED, 32 events]
        ↓ audit/classification (docs/HISTORICAL_BREACH_DATASET.md)
9 breach · 6 major-flood · 10 flood · 4 high-water · 1 failure · 2 other
        ↓ spatial/section link required
historical_link_status = CONFIRMED ? indicator : UNAVAILABLE   [always UNAVAILABLE in V0.1 — no verified mapping exists]
```

## 4. Scenario engine

```
station observation (real) + user water_level_delta (+0.5 … +2.0 m)
        ↓ arithmetic
scenario_water_level, scenario_danger_margin, scenario_HFL_margin,
scenario_hydrological_stress, scenario_vulnerability_score
        ↓ label attached
SCENARIO_SIMULATION_NOT_A_VALIDATED_FLOOD_FORECAST
```

## 5. Synthetic ML pipeline (development validation only)

```
synthetic_development_v0.1.parquet (200×30)            [SIMULATED]
        ↓ one-hot + drop identifiers, stratified 75/25 split
Logistic Regression & Random Forest                    [SYNTHETIC_DEVELOPMENT_ONLY]
        ↓
precision/recall/F1/ROC-AUC/PR-AUC/confusion matrix/feature importance
        ↓ serialised with mandatory label
models/development/*_synthetic.joblib
```
Synthetic label has no learnable signal by construction; near-chance metrics confirm honest evaluation (reports/MODEL_EVALUATION.md).
