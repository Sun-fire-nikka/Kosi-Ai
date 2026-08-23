# Experiments Log

| # | Experiment | Data | Result | Artifact |
|---|---|---|---|---|
| 1 | FMISC ArcGIS MapServer extraction | 18 layer schemas | 0 observation records exposed | reports/FMISC_EXTRACTION_REPORT.md |
| 2 | Bulletin archive investigation (182 files) | /bulletin/ listing | 18 PDFs downloaded; only canonical bulletin parsed (23 obs) | docs/HISTORICAL_BULLETIN_INVESTIGATION.md |
| 3 | Historical event audit | 32 records | 9 breach, 6 major-flood, 10 flood, 4 high-water; supervised training NOT justified | docs/HISTORICAL_BREACH_DATASET.md |
| 4 | Synthetic LR/RF pipeline validation | SYNTHETIC_DEVELOPMENT_ONLY 200x30 | honest near-chance metrics; artifacts labelled | models/development/, reports/MODEL_EVALUATION.md |
| 5 | Real-data inference | 23 stations | all LOW/MODERATE on snapshot; max stress 43 (Baltara) | reports/REAL_DATA_INFERENCE.md |
