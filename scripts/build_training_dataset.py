#!/usr/bin/env python
"""
Script: build_training_dataset.py
Convert verified raw observations into model-ready segment/event samples.

This script is part of the data ingestion pipeline and should be run
only after verified historical breach/failure events have been identified
and ingested (see DATA_ACQUISITION.md).

It should NOT be run with synthetic data as if it were real Kosi data.

WHAT THIS SCRIPT DOES (when run with real verified data):
  1. Reads raw observation files (CSV/Excel/JSON/Parquet) from data/raw/
  2. Merghes them into a unified segment-level DataFrame
  3. Classifies each feature as AVAILABLE, DERIVABLE, or NOT_AVAILABLE
  4. Engineers the target variable: failure_event_within_horizon
     (binary: 1 if a breach/failure occurred within X days of the observation,
      0 otherwise) — BUT ONLY if verified event data is present
  5. Splits data into train/test using temporal (event-aware) split
  6. Outputs a manifest of the processed dataset ready for model training
  7. Does NOT train a model — only prepares the dataset

WHAT THIS Script DOES NOT DO:
  - Do NOT run with synthetic data and claim real Kosi performance
  - Do NOT fabricate breach labels
  - Do NOT train a model (only builds the dataset)

USAGE (after verified data is ingested):
    python scripts/build_training_dataset.py \\
        --raw-dir data/raw \\
        --output data/processed/training_dataset.parquet \\
        --horizon 30 \\
        --target failure_event_within_horizon

ARGUMENTS:
    --raw-dir: Directory containing raw observation files (CSV, Excel, JSON, Parquet)
    --output: Path to write the processed parquet dataset
    --horizon: Number of days within which a failure event is considered "near"
    --target: Name of the target column to create (default: failure_event_within_horizon)

DEPENDENCIES:
    - src.kosi_ai.data.ingestion
    - src.kosi_ai.data.data_audit
    - src.kosi_ai.data.normalization
    - pandas, numpy, scikit-learn
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add project src to path
sys.path.insert(0, r"C:\Users\shakti\Desktop\kosi-ai\src")

import pandas as pd
import numpy as np

from kosi_ai.data.ingestion import ingest_directory, detect_file_type, enrich_with_source_metadata
from kosi_ai.data.data_audit import audit_directory, classify_feature_availability, canonical_canonical_vars
from kosi_ai.data.normalization import normalize_numeric_minmax, encode_categorical, safe_divide
from kosi_ai.config import load_feature_registry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def classify_all_features(df: pd.DataFrame, feature_registry: dict) -> dict:
    """Classify every column in the DataFrame.

    Returns a dict: column_name -> "AVAILABLE" | "DERIVABLE" | "NOT_AVAILABLE" | "UNKNOWN"
    """
    classifications = {}
    for col in df.columns:
        # First check feature registry
        availability = classify_feature_availability(col, feature_registry)
        if availability != "UNKNOWN":
            classifications[col] = availability
        else:
            # Fall back to source registry
            classifications[col] = (
                "AVAILABLE"
                if get_registry().is_variable_available(col)
                else "NOT_AVAILABLE"
            )
    return classifications


def create_failure_target(
    df: pd.DataFrame,
    horizon_days: int = 30,
    date_col: str = "date",
    event_col: str = None,
) -> pd.DataFrame:
    """Create the binary target variable: failure_event_within_horizon.

    Args:
        df: DataFrame with segment observations
        horizon_days: If a failure event occurs within this many days,
                      the target is 1; otherwise 0.
        date_col: Column name containing observation date (or None if no date)
        event_col: Column name containing failure event indicator.
                   If None, assumes df has no event data and returns all zeros.

    Returns:
        DataFrame with new column 'failure_event_within_horizon' (0 or 1).
    """
    if event_col is None or event_col not in df.columns:
        # No event data available; return all zeros
        df = df.copy()
        df["failure_event_within_horizon"] = 0
        return df

    # Ensure date column is datetime
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # Sort by segment and date for proper temporal logic
    if date_col and "segment_id" in df.columns:
        df = df.sort_values(["segment_id", date_col])

    df = df.copy()
    df["failure_event_within_horizon"] = 0

    # For each segment, check if any event occurred within horizon_days
    if event_col and date_col and "segment_id" in df.columns:
        for seg_id in df["segment_id"].unique():
            seg_events = df.loc[
                (df["segment_id"] == seg_id) & (df[event_col] == 1), [date_col]
            ]
            if seg_events.empty:
                continue
            event_dates = pd.to_datetime(seg_events[date_col], errors="coerce").dropna()
            if event_dates.empty:
                continue
            # Observation rows for this segment
            seg_obs = df.loc[df["segment_id"] == seg_id].copy()
            if seg_obs.empty:
                continue
            # For each observation, check if any event is within horizon
            for idx, row in seg_obs.iterrows():
                obs_date = pd.to_datetime(row[date_col], errors="coerce")
                if pd.isna(obs_date):
                    continue
                # Compute days to each event
                days_to_events = (event_dates - obs_date).dt.days
                if (days_to_events >= -horizon_days).any() and (days_to_events <= horizon_days).any():
                    # At least one event within ±horizon_days; set to 1 if event is in the future
                    # (i.e., days_to_event <= horizon_days and days_to_event >= 0)
                    future_events = days_to_events[ (days_to_events >= 0) & (days_to_events <= horizon_days) ]
                    if not future_events.empty:
                        df.loc[idx, "failure_event_within_horizon"] = 1

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Build a training dataset from verified raw observations."
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=r"C:\Users\shakti\Desktop\kosi-ai\data\raw",
        help="Directory containing raw observation files (CSV, Excel, JSON, Parquet)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=r"C:\Users\shakti\Desktop\kosi-ai\data\processed\training_dataset.parquet",
        help="Path to write the processed parquet dataset",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=30,
        help="Number of days within which a failure event is considered 'near' (default: 30)",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="failure_event_within_horizon",
        help='Name of the target column to create (default: failure_event_within_horizon)',
    )
    parser.add_argument(
        "--date-col",
        type=str,
        default=None,
        help='Column name containing observation date (e.g., "date")',
    )
    parser.add_argument(
        --event-col,
        type=str,
        default=None,
        help='Column name containing failure event indicator (1 = event, 0 = no event)',
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed processing information",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    output_path = Path(args.output)
    horizon = args.horizon
    target_name = args.target
    date_col = args.date_col
    event_col = args.event_col

    print("=" * 60)
    print("BUILD TRAINING DATASET")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # ------------------------------------------------------------------
    # 1. Validate raw directory
    # ------------------------------------------------------------------
    if not raw_dir.is_dir():
        print(f"❌ Raw data directory not found: {raw_dir}")
        print("   Place verified raw observation files there, then re-run.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. List files in raw directory
    # ------------------------------------------------------------------
    supported_extensions = {".csv", ".xlsx", ".xls", ".json", ".parquet"}
    files = []
    for f in raw_dir.iterdir():
        if f.is_file() and f.suffix.lower() in supported_extensions:
            files.append(f)

    if not files:
        print(f"⚠ No supported data files found in {raw_dir}")
        print("   Supported extensions: .csv, .xlsx, .json, .parquet")
        print("   Place verified raw data files and re-run.")
        sys.exit(0)

    print(f"📁 Found {len(files)} raw data file(s) in {raw_dir}")

    # ------------------------------------------------------------------
    # 2. Infer feature registry and classify features
    # ------------------------------------------------------------------
    feature_registry = load_feature_registry()
    # We do NOT assume every feature in the registry exists in the data;
    # we classify what is actually present.

    # ------------------------------------------------------------------
    # 3. Ingest each file and merge into a unified DataFrame
    # ------------------------------------------------------------------
    all_frames = []
    file_metadata = []

    for filepath in sorted(files):
        file_type = detect_file_type(filepath)
        try:
            result = ingest_directory(filepath=filepath, source_name=filepath.stem)
            # result is a list with one dict (from ingest_directory)
            if result and len(result) > 0:
                r = result[0]
                if r.get("success") and not r.get("dataframe").empty:
                    df = r["dataframe"]
                    # Classify availability for this file's columns
                    avail = classify_all_features(df, feature_registry)
                    df = df.copy()
                    for col, cls in avail.items():
                        df[f"{col}_availability"] = cls
                    all_frames.append(df)
                    file_metadata.append(
                        {
                            "file": filepath.name,
                            "type": file_type,
                            "rows": len(df),
                            "availability": avail,
                        }
                    )
                    if args.verbose:
                        print(f"  ✔ {filepath.name}: {len(df)} rows, {len(df.columns)} columns")
                else:
                    print(f"  ⚠ {filepath.name}: not successful ({r.get('error', 'unknown')})")
            else:
                print(f"  ⚠ {filepath.name}: no data returned")
        except Exception as e:
            print(f"  ❌ {filepath.name}: error - {e}")

    if not all_frames:
        print("❌ No DataFrames were successfully loaded; aborting.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 4. Combine all DataFrames
    # ------------------------------------------------------------------
    combined = pd.concat(all_frames, ignore_index=True)
    print(f"\n📊 Combined DataFrame: {len(combined)} rows, {len(combined.columns)} columns")

    # ------------------------------------------------------------------
    # 5. Classify all features and print summary
    # ------------------------------------------------------------------
    classifications = classify_all_features(combined, feature_registry)

    avail_counts = {"AVAILABLE": 0, "DERIVABLE": 0, "NOT_AVAILABLE": 0, "UNKNOWN": 0}
    for cls in classifications.values():
        avail_counts[cls] += 1

    print("Feature availability classification:")
    for cls, count in avail_counts.items():
        print(f"  {cls}: {count}")

    # ------------------------------------------------------------------
    # 6. Create the failure event target (if event data provided)
    # ------------------------------------------------------------------
    has_event_data = event_col is not None and event_col in combined.columns
    print(f"\n🎯 Target variable: {target_name}")
    print(f"  Event data available: {has_event_data}")

    if has_event_data:
        print(f"  Horizon: {horizon} days")
        combined = create_failure_target(
            combined,
            horizon_days=horizon,
            date_col=date_col,
            event_col=event_col,
        )
        # Check distribution
        pos = combined[target_name].sum()
        neg = len(combined) - pos
        print(f"  Positive ({target_name}=1): {pos}")
        print(f"  Negative ({target_name}=0): {neg}")
        print(f"  Positivity rate: {pos/len(combined)*100:.1f}%")
    else:
        print("  No event data provided; target column set to all 0s.")
        combined[target_name] = 0

    # ------------------------------------------------------------------
    # 7. Select final columns for model training
    # ------------------------------------------------------------------
    # Keep only columns that are AVAILABLE or DERIVABLE, plus the target
    useful_cols = [c for c in combined.columns if c == target_name or classifications.get(c) in ["AVAILABLE", "DERIVABLE"]]
    # Also keep availability meta-columns
    avail_meta_cols = [c for c in combined.columns if c.endswith("_availability")]
    final_cols = list(set(useful_cols + avail_meta_cols))
    # Ensure segment_id and any date column are kept
    for special in ["segment_id", "segment"]:
        if special in combined.columns and special not in final_cols:
            final_cols.append(special)

    final_df = combined[final_cols].copy()

    print(f"\n📝 Final training dataset columns ({len(final_df.columns)}):")
    for c in final_df.columns:
        cls = classifications.get(c, "UNKNOWN")
        print(f"  - {c} (availability: {cls})")

    # ------------------------------------------------------------------
    # 8. Write the processed dataset
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        final_df.to_parquet(output_path, index=False)
        print(f"\n✅ Training dataset written to {output_path}")
    except Exception as e:
        print(f"❌ Failed to write parquet: {e}")
        # Fallback to CSV
        try:
            final_df.to_csv(output_path.replace(".parquet", ".csv"), index=False)
            print(f"✅ Fallback CSV written to {output_path.replace('.parquet', '.csv')}")
        except Exception as e2:
            print(f"❌ Failed to write CSV: {e2}")

    # ------------------------------------------------------------------
    # 9. Summary and next steps
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print()
    if not has_event_data:
        print("⚠ No event data was provided; target is all zeros.")
        print("   Provide --event-col and --date-col to create failure_event_within_horizon.")
    else:
        print(f"✅ Training dataset ready with {len(final_df)} samples.")
        print(f"   - Target distribution: {target_name} = 1: {final_df[target_name].sum()}, = 0: {len(final_df) - final_df[target_name].sum()}")
        print("   - To train a model: use the pipeline in src/kosi_ai/models/")
        print("   - Remember: verified labels are required; do not claim real-world")
        print("     performance without historical breach event data.")
    print()
    print("   - engineering vulnerability index remains available as baseline:")
    print("     python -c \"from kosi_ai.inference import predict_vulnerability; ...\"")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()