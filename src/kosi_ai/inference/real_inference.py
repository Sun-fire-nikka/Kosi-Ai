"""Real-data inference: station-level status + vulnerability + scenarios."""
from __future__ import annotations

import pandas as pd

from ..data import loaders
from ..features.hydrology import engineer_hydrology, feature_provenance_record
from ..vulnerability.engine import compute_vulnerability, load_config, scenario


def build_station_assessments() -> list[dict]:
    hydro = loaders.load_real_hydrology()
    warning = loaders.load_warning_levels()
    events = loaders.load_historical_events()
    cfg = load_config()

    df = engineer_hydrology(hydro, warning)

    assessments: list[dict] = []
    for _, row in df.iterrows():
        section = {
            "section_id": f"STATION-{str(row['station']).strip().upper().replace(' ', '-')}",
            "observed_water_level": None if pd.isna(row["observed_water_level"]) else float(row["observed_water_level"]),
            "warning_level": None if pd.isna(row.get("warning_level")) else float(row["warning_level"]),
            "danger_level": None if pd.isna(row.get("effective_danger_level")) else float(row["effective_danger_level"]),
            "HFL": None if pd.isna(row.get("effective_HFL")) else float(row["effective_HFL"]),
            "hydrological_stress": None if pd.isna(row.get("hydrological_stress")) else float(row["hydrological_stress"]),
            "reported_condition": None,   # no embankment inspection dataset exists
            "remarks": None,
            "_events": events,
            "historical_link_status": "UNAVAILABLE",
        }
        vuln = compute_vulnerability(section, cfg)
        prov = feature_provenance_record(row)
        assessments.append({
            "section_id": section["section_id"],
            **vuln,
            "station": str(row["station"]),
            "district": str(row.get("district", "")),
            "date": str(row.get("date", "")),
            "observed_features": {k: v for k, v in prov.items()
                                  if v["status"] == "OBSERVED"},
            "derived_features": {k: v for k, v in prov.items()
                                 if v["status"] == "DERIVED"},
            "unavailable_features": sorted(k for k, v in prov.items()
                                           if v["status"] == "UNAVAILABLE"),
            "simulated_features": [],
            "historical_evidence": {"link_status": "UNAVAILABLE",
                                    "note": ("no verified gauge-to-embankment-section "
                                             "mapping; historical records not assigned")},
        })
    return assessments


def run_scenario(station_id: str, delta: float) -> dict:
    assessments = build_station_assessments()
    match = [a for a in assessments if a["station"].lower() in station_id.lower()
             or a["section_id"].lower() == station_id.lower()]
    if not match:
        raise KeyError(f"unknown station '{station_id}'")
    a = match[0]
    section = {
        "observed_water_level": (a["observed_features"].get("observed_water_level", {}) or {}).get("value"),
        "warning_level": (a["observed_features"].get("warning_level", {}) or {}).get("value") or None,
        "danger_level": (a["observed_features"].get("danger_level", {}) or {}).get("value"),
        "HFL": (a["observed_features"].get("HFL", {}) or {}).get("value"),
        "reported_condition": None, "remarks": None,
        "_events": loaders.load_historical_events(),
        "historical_link_status": "UNAVAILABLE",
    }
    return scenario(section, delta)

