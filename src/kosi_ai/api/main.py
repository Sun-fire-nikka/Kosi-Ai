"""FastAPI application for Kosi AI V0.1.

Endpoints:
  POST /predict           {station_id} -> station vulnerability assessment
  POST /scenario          {station_id, water_level_delta}
  GET  /model-info
  GET  /data-quality
  GET  /sections
  GET  /historical-events
"""
from __future__ import annotations

from pathlib import Path
import json

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..data import loaders
from ..inference.real_inference import build_station_assessments, run_scenario
from ..vulnerability.engine import load_config

app = FastAPI(title="Kosi Embankment Intelligence API", version="V0.1")


class PredictRequest(BaseModel):
    station_id: str


class ScenarioRequest(BaseModel):
    station_id: str
    water_level_delta: float


@app.post("/predict")
def predict(req: PredictRequest):
    assessments = build_station_assessments()
    for a in assessments:
        if (a["section_id"].lower() == req.station_id.lower()
                or a["station"].lower() == req.station_id.lower()):
            return a
    raise HTTPException(404, f"unknown station '{req.station_id}'")


@app.post("/scenario")
def scenario_api(req: ScenarioRequest):
    try:
        return run_scenario(req.station_id, req.water_level_delta)
    except KeyError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/model-info")
def model_info():
    cfg = load_config()
    metrics_path = Path("models/development/SYNTHETIC_DEVELOPMENT_ONLY_metrics.json")
    synthetic_metrics = None
    if metrics_path.exists():
        with open(metrics_path, encoding="utf-8") as f:
            synthetic_metrics = json.load(f)
    return {
        "model_version": "V0.1",
        "model_status": ("ENGINEERING-INFORMED VULNERABILITY MODEL - "
                         "NOT A VALIDATED BREACH-PREDICTION MODEL"),
        "breach_probability_returned": False,
        "note": ("If breach probability is not scientifically supported, "
                 "no fake breach probability is returned."),
        "synthetic_development_models": {
            "label": "SYNTHETIC_DEVELOPMENT_ONLY",
            "warning": ("Synthetic metrics do NOT represent real-world "
                        "Kosi prediction accuracy."),
            "metrics": synthetic_metrics,
        },
        "config_weights": cfg.get("model", {}).get("weights", {}),
    }


@app.get("/data-quality")
def data_quality():
    out = {}
    for name in ["real_hydrology", "warning_levels", "discharge",
                 "historical_events", "synthetic_development"]:
        try:
            df_map = {
                "real_hydrology": loaders.load_real_hydrology,
                "warning_levels": loaders.load_warning_levels,
                "discharge": loaders.load_discharge,
                "historical_events": loaders.load_historical_events,
                "synthetic_development": loaders.load_synthetic_development,
            }
            df = df_map[name]()
            prov = loaders.dataset_provenance(name)
            out[name] = {
                **prov,
                "rows": int(len(df)),
                "columns": int(df.shape[1]),
                "missing_cells": int(df.isna().sum().sum()),
                "duplicate_rows": int(df.duplicated().sum()),
            }
        except Exception as e:  # pragma: no cover
            out[name] = {"error": str(e)}
    return out


@app.get("/sections")
def sections():
    return {"assessment_units": build_station_assessments(),
            "note": ("No verified embankment-section dataset exists; units are "
                     "hydrological stations.")}


@app.get("/historical-events")
def historical_events():
    import math
    df = loaders.load_historical_events()

    def clean(v):
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        if isinstance(v, pd.Timestamp):
            return v.isoformat()
        return v

    records = [{k: clean(v) for k, v in rec.items()}
               for rec in df.to_dict(orient="records")]
    return {"count": len(records), "events": records,
            "usage_restriction": ("historical evidence only; NOT supervised "
                                  "training data")}
