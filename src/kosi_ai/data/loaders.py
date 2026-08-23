"""Kosi AI - data loading for all real and synthetic datasets.

Provenance is mandatory: every loader returns a DataFrame plus dataset metadata.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]

HYDROLOGY_PARQUET = PROJECT_ROOT / "data/processed/kosi_hydrology/kosi_bulletins.parquet"
HISTORICAL_XLSX = PROJECT_ROOT / "data/raw/historical/Kosi_32_Verified_Historical_and_Flood_Records.xlsx"
DISCHARGE_XLSX = PROJECT_ROOT / "data/raw/official/hydrology/kosi_discharge_datasets.xlsx"
WARNING_LEVELS_XLSX = PROJECT_ROOT / "data/raw/official/hydrology/kosi_warning_levels.xlsx"
SYNTHETIC_PARQUET = PROJECT_ROOT / "src/data/synthetic/synthetic_development_v0.1.parquet"

PARSER_VERSION = "v0.1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_real_hydrology() -> pd.DataFrame:
    """23 real FMISC bulletin station observations (2026-08-22)."""
    df = pd.read_parquet(HYDROLOGY_PARQUET)
    return df


def load_warning_levels() -> pd.DataFrame:
    """15 official Kosi station reference levels: HFL, Danger, Warning (FMISC Kosi_Model_Result bulletin)."""
    df = pd.read_excel(WARNING_LEVELS_XLSX, sheet_name="Kosi Warning Levels")
    df = df.rename(columns={
        "Station": "station",
        "River/Basin": "river",
        "HFL / Highest Flood Level (m)": "HFL",
        "Danger Level (m)": "danger_level",
        "Warning Level (m)": "warning_level",
        "Source Date & Time": "reference_datetime",
        "Source URL": "source_url",
    })
    keep = ["station", "river", "HFL", "danger_level", "warning_level",
            "reference_datetime", "Government Source", "source_url"]
    return df[keep].copy()


def load_discharge() -> pd.DataFrame:
    """17 Kosi barrage discharge records (NDMI observations + FMISC Mike-11 forecasts)."""
    df = pd.read_excel(DISCHARGE_XLSX, sheet_name="10+ Kosi Discharge Datasets")
    df = df.rename(columns={
        "Date/Time": "datetime_text",
        "Station": "station",
        "Discharge (cusecs)": "discharge_cusecs",
        "Discharge (cumecs)": "discharge_cumecs",
        "Design Discharge (cusecs)": "design_discharge_cusecs",
        "Data Type": "data_type",
    })
    keep = ["datetime_text", "station", "river" if "river" in df.columns else "River",
            "data_type", "discharge_cusecs", "discharge_cumecs",
            "design_discharge_cusecs", "Trend"]
    keep = [c for c in keep if c in df.columns]
    return df[keep].copy()


def load_historical_events() -> pd.DataFrame:
    """32 verified historical Kosi flood/breach records. NOT ML training data."""
    df = pd.read_excel(HISTORICAL_XLSX, sheet_name="Kosi_32_Records")
    return df


def load_synthetic_development() -> pd.DataFrame:
    """200-segment synthetic dataset. SYNTHETIC_DEVELOPMENT_ONLY."""
    df = pd.read_parquet(SYNTHETIC_PARQUET)
    if "dataset_status" not in df.columns or not str(df["dataset_status"].iloc[0]) .startswith("SYNTHETIC"):
        raise ValueError("Synthetic dataset missing SYNTHETIC_DEVELOPMENT_ONLY marker")
    return df


def dataset_provenance(name: str) -> dict:
    provenance = {
        "real_hydrology": {
            "status": "OBSERVED", "records": 23,
            "source": "FMISC Bihar FMIS daily water level & FF bulletin",
            "url": "https://www.fmiscwrdbihar.gov.in/bulletin/fmis%20daily%20water%20level%20and%20FF%20data.pdf",
            "file": str(HYDROLOGY_PARQUET), "snapshot_date": "2026-08-22"},
        "warning_levels": {
            "status": "OBSERVED", "records": 15,
            "source": "WRD Bihar / FMISC Kosi Flood Bulletin (Kosi_Model_Result)",
            "url": "https://www.fmiscwrdbihar.gov.in/bulletin/Kosi_Model_Result.pdf",
            "file": str(WARNING_LEVELS_XLSX)},
        "discharge": {
            "status": "OBSERVED+FORECAST", "records": 17,
            "source": "NDMI (MHA, GoI) observations; FMISC Mike-11 forecasts",
            "urls": ["https://www.ndmindia.mha.gov.in/ndmi/viewUploadedDocument?uid=NEW2208",
                     "https://www.fmiscwrdbihar.gov.in/bulletin/Kosi_Model_Result.pdf"],
            "file": str(DISCHARGE_XLSX)},
        "historical_events": {
            "status": "OBSERVED", "records": 32,
            "source": "Verified historical Kosi records (multi-agency)",
            "file": str(HISTORICAL_XLSX),
            "usage_restriction": "historical evidence only; NOT supervised training data"},
        "synthetic_development": {
            "status": "SIMULATED", "records": 200,
            "label": "SYNTHETIC_DEVELOPMENT_ONLY",
            "file": str(SYNTHETIC_PARQUET),
            "usage_restriction": "ML pipeline validation only; never represents Kosi accuracy"},
    }
    entry = provenance.get(name)
    if entry is None:
        raise KeyError(f"Unknown dataset '{name}'")
    out = dict(entry)
    out["retrieval_timestamp"] = _now()
    out["parser_version"] = PARSER_VERSION
    return out
