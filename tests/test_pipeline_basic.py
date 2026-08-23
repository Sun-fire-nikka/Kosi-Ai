"""Tests for the Kosi AI V0.1 pipeline."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kosi_ai.data import loaders                      # noqa: E402
from kosi_ai.features import hydrology as feat        # noqa: E402
from kosi_ai.vulnerability import engine as vuln      # noqa: E402
from kosi_ai.models import development                # noqa: E402
from kosi_ai.inference import real_inference          # noqa: E402


# ---------------- data loading ----------------

def test_load_real_hydrology():
    df = loaders.load_real_hydrology()
    assert len(df) == 23
    for col in ["station", "date", "observed_water_level", "danger_level", "HFL"]:
        assert col in df.columns


def test_load_warning_levels():
    df = loaders.load_warning_levels()
    assert len(df) == 15
    assert {"HFL", "danger_level", "warning_level"}.issubset(df.columns)


def test_load_discharge():
    df = loaders.load_discharge()
    assert len(df) == 17
    assert "discharge_cusecs" in df.columns


def test_load_historical_events():
    df = loaders.load_historical_events()
    assert len(df) == 32
    assert {"Year", "Event Type", "Location"}.issubset(df.columns)


def test_synthetic_marker():
    df = loaders.load_synthetic_development()
    assert (df["dataset_status"] == "SYNTHETIC_DEVELOPMENT_ONLY").all()


# ---------------- feature engineering ----------------

@pytest.fixture()
def enriched():
    return feat.engineer_hydrology(loaders.load_real_hydrology(),
                                   loaders.load_warning_levels())


def test_derived_margins(enriched):
    m = enriched["water_level_minus_danger"].notna()
    assert m.sum() > 0
    row = enriched[m].iloc[0]
    expected = row["observed_water_level"] - row["effective_danger_level"]
    assert row["water_level_minus_danger"] == pytest.approx(expected)


def test_stress_bounds(enriched):
    s = enriched["hydrological_stress"].dropna()
    assert ((s >= 0) & (s <= 100)).all()


def test_no_fabricated_warning_level(enriched):
    """Unmatched stations must keep warning_level null, never zero-filled."""
    unmatched = enriched[enriched["station_match_status"] == "UNMATCHED"]
    if len(unmatched):
        assert unmatched["warning_level"].isna().all()


def test_provenance_record(enriched):
    rec = feat.feature_provenance_record(enriched.iloc[0])
    assert rec["observed_water_level"]["status"] == "OBSERVED"
    assert "formula" in rec["water_level_minus_danger"]
    assert rec["rainfall"]["status"] == "UNAVAILABLE"


# ---------------- vulnerability engine ----------------

def _section(**over):
    base = dict(observed_water_level=70.0, warning_level=69.0,
                danger_level=71.0, HFL=73.5, reported_condition="POOR",
                remarks="Erosion on riverside slope, seepage observed",
                _events=None, historical_link_status="UNAVAILABLE")
    base.update(over)
    return base


def test_vulnerability_score_range():
    r = vuln.compute_vulnerability(_section())
    assert 0 <= r["vulnerability_score"] <= 100
    assert r["vulnerability_class"] in {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    assert r["model_status"].startswith("ENGINEERING_INFORMED")


def test_condition_remarks_raise_score():
    plain = vuln.compute_vulnerability(_section(remarks=None))
    bad = vuln.compute_vulnerability(_section())
    assert bad["vulnerability_score"] > plain["vulnerability_score"]


def test_historical_link_unavailable_by_default():
    r = vuln.compute_vulnerability(_section())
    assert r["components"]["historical_vulnerability"] is None
    assert any("UNAVAILABLE" in e for e in r["evidence"])


def test_scenario_simulation():
    sc = vuln.scenario(_section(), 1.0)
    assert sc["simulation_label"].startswith("SCENARIO_SIMULATION")
    assert sc["scenario_water_level"] == pytest.approx(71.0)
    assert sc["scenario_danger_margin"] == pytest.approx(0.0)


def test_class_boundaries():
    cfg = vuln.DEFAULT_CONFIG
    assert vuln.classify(30.0, cfg) == "LOW"
    assert vuln.classify(50.0, cfg) == "MODERATE"
    assert vuln.classify(70.0, cfg) == "HIGH"
    assert vuln.classify(90.0, cfg) == "CRITICAL"
    assert vuln.classify(None, cfg) == "UNKNOWN"


# ---------------- synthetic models ----------------

def test_training_and_serialization(tmp_path):
    df = loaders.load_synthetic_development()
    report = development.train_all(df)
    assert set(report) >= {"logistic_regression", "random_forest"}
    for name, r in report.items():
        assert r["artifact"]["label"] == "SYNTHETIC_DEVELOPMENT_ONLY"
        assert Path(r["path"]).exists()
        assert 0 <= r["metrics"]["precision"] <= 1


def test_model_loading_guard():
    bundle = development.load_model("random_forest")
    assert bundle["metadata"]["label"] == "SYNTHETIC_DEVELOPMENT_ONLY"


# ---------------- real inference & API ----------------

def test_real_inference():
    assessments = real_inference.build_station_assessments()
    assert len(assessments) > 0
    a = assessments[0]
    assert a["historical_evidence"]["link_status"] == "UNAVAILABLE"
    assert a["model_version"] == "V0.1"


def test_scenario_inference():
    assessments = real_inference.build_station_assessments()
    target = next(a["station"] for a in assessments
                  if a["components"].get("hydrological_stress") is not None)
    sc = real_inference.run_scenario(target, 1.0)
    assert sc["simulation_label"].startswith("SCENARIO_SIMULATION")


def test_api_import_and_contract():
    from kosi_ai.api.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    r = client.get("/model-info")
    assert r.status_code == 200
    info = r.json()
    assert info["breach_probability_returned"] is False

    r = client.get("/sections")
    assert r.status_code == 200
    units = r.json()["assessment_units"]
    assert len(units) > 0
    sid = units[0]["station"]
    r = client.post("/predict", json={"station_id": sid})
    assert r.status_code == 200
    body = r.json()
    for key in ["vulnerability_score", "vulnerability_class",
                "data_quality", "top_contributing_factors", "model_version"]:
        assert key in body

    r = client.post("/scenario", json={"station_id": sid, "water_level_delta": 1.0})
    assert r.status_code == 200
    assert r.json()["simulation_label"].startswith("SCENARIO_SIMULATION")

    r = client.get("/historical-events")
    assert r.status_code == 200
    assert r.json()["count"] == 32
