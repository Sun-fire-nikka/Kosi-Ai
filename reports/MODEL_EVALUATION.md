# Model Evaluation — SYNTHETIC_DEVELOPMENT_ONLY

Command: `python scripts/train_development_model.py`

## Purpose

Validate preprocessing → training → serialization → inference on the 200-segment synthetic dataset. **These metrics do NOT represent real-world Kosi prediction accuracy.**

## Results (holdout 25%, seed 42, target = synthetic condition ∈ {poor})

| Model | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.0 | 0.0 | 0.0 | 0.444 | 0.152 |
| Random Forest | 0.0 | 0.0 | 0.0 | 0.494 | 0.189 |

## Interpretation (important)

The synthetic condition label was generated independently of the feature columns, so there is no learnable signal — ROC-AUC ≈ 0.5 is exactly what an honest pipeline should produce on noise. We deliberately report this rather than tuning until metrics look good: it demonstrates the pipeline computes real metrics and does not fabricate performance.

Feature importance is saved in `models/development/SYNTHETIC_DEVELOPMENT_ONLY_metrics.json` for pipeline validation of explainability output only.

## What would change at V1

Real supervised training requires event-linked labelled samples (breach / no-breach with pre-event hydrology), event-aware temporal validation splits — none of which exist today.
