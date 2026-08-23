"""Feature engineering on real Kosi observations.

Only OBSERVED inputs are used; derived features record their formula.
Missing values are never fabricated and never converted to zero.
"""
from __future__ import annotations

import pandas as pd

FORECAST_FIELDS = [f"forecast_{h}h" for h in range(6, 73, 6)]


def engineer_hydrology(hydro: pd.DataFrame, warning: pd.DataFrame) -> pd.DataFrame:
    """Join real bulletin observations with official reference levels.

    The 2026-08-22 bulletin lacks warning_level for most stations; the official
    FMISC warning-level table provides HFL/danger/warning per station. Where a
    station name matches, we enrich; otherwise values stay null (never imputed).
    """
    df = hydro.copy()

    # Normalise station names for matching only (matching key is not an ML feature)
    def norm(s: str) -> str:
        return str(s).lower().strip()

    wl = warning.copy()
    wl["_key"] = wl["station"].map(norm)

    def _lookup(station: str, column: str):
        key = norm(station)
        row = wl[wl["_key"] == key]
        if len(row) == 0:
            # partial containment match (e.g. "Baltara Khagaria" vs "Baltara")
            cand = wl[wl["_key"].apply(lambda k: k in key or key in k)]
            if len(cand) > 0:
                row = cand.iloc[[0]]
            else:
                return None
        val = row.iloc[0][column]
        return None if pd.isna(val) else float(val)

    w_vals, d_vals, h_vals, status = [], [], [], []
    for _, row in df.iterrows():
        st = row["station"]
        w = _lookup(st, "warning_level")
        d = _lookup(st, "danger_level")
        h = _lookup(st, "HFL")
        w_vals.append(w)
        d_vals.append(d)
        h_vals.append(h)
        status.append("MATCHED" if any(v is not None for v in (w, d, h))
                      else "UNMATCHED")

    df["warning_level"] = pd.Series(w_vals, index=df.index, dtype="float64")
    df["danger_level_ref"] = pd.Series(d_vals, index=df.index, dtype="float64")
    df["HFL_ref"] = pd.Series(h_vals, index=df.index, dtype="float64")
    df["station_match_status"] = status

    # Use bulletin danger/HFL as primary; reference table fills gaps only.
    eff_dl = [dl if pd.notna(dl) else ref
              for dl, ref in zip(df["danger_level"], df["danger_level_ref"])]
    df["effective_danger_level"] = pd.Series(eff_dl, index=df.index, dtype="float64")

    eff_hfl = [h if pd.notna(h) else ref
               for h, ref in zip(df["HFL"], df["HFL_ref"])]
    df["effective_HFL"] = pd.Series(eff_hfl, index=df.index, dtype="float64")

    # Derived features (formulas recorded)
    def _sub(a, b):
        return [float(x - y) if pd.notna(x) and pd.notna(y) else None
                for x, y in zip(a, b)]

    ol = df["observed_water_level"]
    df["water_level_minus_warning"] = pd.Series(
        _sub(ol, df["warning_level"]), index=df.index, dtype="float64")
    df["water_level_minus_danger"] = pd.Series(
        _sub(ol, df["effective_danger_level"]), index=df.index, dtype="float64")
    df["water_level_minus_HFL"] = pd.Series(
        _sub(ol, df["effective_HFL"]), index=df.index, dtype="float64")

    df["HFL_margin"] = -df["water_level_minus_HFL"].astype("float64")
    df["danger_margin"] = -df["water_level_minus_danger"].astype("float64")

    # Exceedance ratio only where meaningful (denominator != 0)
    def ratio(row):
        dl = row["effective_danger_level"]
        ol = row["observed_water_level"]
        if pd.isna(dl) or pd.isna(ol) or dl == 0:
            return None
        return float(ol / dl)
    df["danger_exceedance_ratio"] = df.apply(ratio, axis=1)

    # Hydrological stress score (0-100), engineering-informed, explainable:
    #   0 at/under warning level, 100 at HFL. Linear interpolation between the two
    #   thresholds; above HFL saturates at 100; below warning -> 0.
    def stress(row):
        ol = row["observed_water_level"]
        wl_ = row["warning_level"] if pd.notna(row.get("warning_level")) else None
        dl = row["effective_danger_level"]
        hfl = row["effective_HFL"]
        low = wl_ if wl_ is not None else dl
        if any(pd.isna(v) for v in (ol, low, hfl)) or hfl <= low:
            return None
        s = (float(ol) - float(low)) / (float(hfl) - float(low)) * 100.0
        return round(min(max(s, 0.0), 100.0), 1)
    df["hydrological_stress"] = df.apply(stress, axis=1)

    return df


def feature_provenance_record(row: pd.Series) -> dict:
    """Return per-feature provenance dict for one observation."""
    def prov(name, value, status, **extra):
        rec = {"value": None if pd.isna(value) else value, "status": status}
        rec.update(extra)
        return rec

    out = {
        "observed_water_level": prov("observed_water_level", row.get("observed_water_level"),
                                     "OBSERVED", source="FMISC Bihar FMIS bulletin"),
        "warning_level": prov("warning_level", row.get("warning_level"),
                              "OBSERVED" if pd.notna(row.get("warning_level")) else "UNAVAILABLE",
                              source="FMISC Kosi Flood Bulletin reference table"),
        "danger_level": prov("danger_level", row.get("effective_danger_level"), "OBSERVED",
                             source="FMISC bulletin"),
        "HFL": prov("HFL", row.get("effective_HFL"), "OBSERVED", source="FMISC bulletin"),
    }
    derived = {
        "water_level_minus_warning": ("observed_water_level - warning_level",),
        "water_level_minus_danger": ("observed_water_level - danger_level",),
        "water_level_minus_HFL": ("observed_water_level - HFL",),
        "hydrological_stress": ("linear interpolation warning->HFL scaled to 0-100",),
    }
    for name, (formula,) in derived.items():
        v = row.get(name)
        out[name] = {"value": None if pd.isna(v) else v,
                     "status": "DERIVED" if pd.notna(v) else "UNAVAILABLE",
                     "formula": formula}
    for f in FORECAST_FIELDS:
        v = row.get(f)
        out[f] = {"value": None if pd.isna(v) else v,
                  "status": "UNAVAILABLE" if pd.isna(v) else "OBSERVED",
                  "note": "hour-based forecast not provided by source"}
    out["rainfall"] = {"value": None, "status": "UNAVAILABLE"}
    out["discharge"] = {"value": None, "status": "UNAVAILABLE",
                        "note": "barrage discharge exists in separate dataset without station linkage to this gauge"}
    return out
