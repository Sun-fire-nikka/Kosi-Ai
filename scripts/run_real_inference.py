#!/usr/bin/env python
"""Real-data inference: station-level vulnerability assessment.

Usage: python scripts/run_real_inference.py [--delta 1.0]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kosi_ai.inference.real_inference import build_station_assessments, run_scenario  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delta", type=float, default=None,
                    help="optional scenario water_level_delta in metres")
    args = ap.parse_args()

    assessments = build_station_assessments()
    print(f"REAL-DATA INFERENCE: {len(assessments)} station assessments")
    print(f"{'Station':28} {'WL(m)':>7} {'DL(m)':>7} {'HFL(m)':>7} "
          f"{'Stress':>7} {'Score':>6} Class")
    for a in assessments:
        wl = (a["observed_features"].get("observed_water_level") or {}).get("value")
        dl = (a["observed_features"].get("danger_level") or {}).get("value")
        hfl = (a["observed_features"].get("HFL") or {}).get("value")
        hs = a["components"].get("hydrological_stress")
        fmt = lambda v: f"{v:.2f}" if isinstance(v, float) else "  n/a"
        print(f"{a['station'][:27]:28} {fmt(wl):>7} {fmt(dl):>7} {fmt(hfl):>7} "
              f"{(f'{hs:.0f}' if hs is not None else 'n/a'):>7} "
              f"{(f'{a['vulnerability_score']:.1f}' if a['vulnerability_score'] is not None else 'n/a'):>6} "
              f"{a['vulnerability_class']}")

    if args.delta is not None:
        target = assessments[0]["station"]
        sc = run_scenario(target, args.delta)
        print(f"\nSCENARIO SIMULATION ({target}, delta={args.delta:+.1f} m)")
        print(json.dumps({k: sc[k] for k in [
            "simulation_label", "base_water_level", "scenario_water_level",
            "scenario_danger_margin", "scenario_HFL_margin",
            "vulnerability_score", "vulnerability_class"]}, indent=2))


if __name__ == "__main__":
    main()
