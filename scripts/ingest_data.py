#!/usr/bin/env python
"""Ingest + validate all real datasets and write processed copies.

Usage: python scripts/ingest_data.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kosi_ai.data import loaders            # noqa: E402
from kosi_ai.features.hydrology import engineer_hydrology  # noqa: E402

OUT = Path("data/processed")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "official_hydrology").mkdir(exist_ok=True)

    hydro = loaders.load_real_hydrology()
    warning = loaders.load_warning_levels()
    discharge = loaders.load_discharge()
    events = loaders.load_historical_events()

    for name, df in [("kosi_bulletins", hydro), ("kosi_warning_levels", warning),
                     ("kosi_discharge", discharge), ("kosi_historical_events", events)]:
        print(f"{name:24} rows={len(df):4} cols={df.shape[1]:3} "
              f"missing_cells={int(df.isna().sum().sum())}")

    enriched = engineer_hydrology(hydro, warning)
    enriched.to_parquet(OUT / "official_hydrology/kosi_features_v0.1.parquet")
    matched = int((enriched["station_match_status"] == "MATCHED").sum())
    print(f"\nEnriched features written. Station matches with reference table: {matched}/{len(enriched)}")
    print("Provenance recorded in data/manifest.yaml (see docs/DATA_PROVENANCE.md).")


if __name__ == "__main__":
    main()
