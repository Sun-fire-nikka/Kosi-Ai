#!/usr/bin/env python
"""
Script: audit_data.py
Produce a human-readable dataset audit report for the Kosi Embankment AI/ML pipeline.

This script walks the data directories, reads all supported files (CSV, Excel, JSON, Parquet),
and outputs a comprehensive audit report to stdout and optionally to a Markdown file.

It uses:
- src.kosi_ai.data.ingestion for reading files
- src.kosi_ai.data.data_audit for computing audit metrics
- src.kosi_ai.data.source_registry for variable availability classification
- src.kosi_ai.config for loading feature registry

The script explicitly uses the project root directory for config file paths.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project src to path
sys.path.insert(0, r"C:\Users\shakti\Desktop\kosi-ai\src")

# Use explicit project root for config file paths (avoids base_dir auto-detection issues)
PROJECT_ROOT = r"C:\Users\shakti\Desktop\kosi-ai"
FEATURE_REGISTRY_PATH = os.path.join(PROJECT_ROOT, "configs", "feature_registry.yaml")
DATA_SOURCES_PATH = os.path.join(PROJECT_ROOT, "configs", "data_sources.yaml")

# Now import after setting paths
import yaml

from kosi_ai.data.ingestion import ingest_directory, detect_file_type
from kosi_ai.data.data_audit import (
    audit_directory,
    generate_audit_report,
    canonical_canonical_vars,
    create_dataset_manifest,
)
from kosi_ai.data.source_registry import get_registry

# Load feature registry using explicit path
with open(FEATURE_REGISTRY_PATH, "r") as f:
    FEATURE_REGISTRY = yaml.safe_load(f)

# Load data sources using explicit path
with open(DATA_SOURCES_PATH, "r") as f:
    DATA_SOURCES_CONFIG = yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("KOSI EMBANKMENT DATASET AUDIT")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # ------------------------------------------------------------------
    # 1. Identify which directories to audit
    # ------------------------------------------------------------------
    directories_to_audit = []

    # Add synthetic directory (for development/demo; clearly marked)
    synthetic_dir = Path(r"C:\Users\shakti\Desktop\kosi-ai\data\synthetic")
    if synthetic_dir.is_dir():
        from kosi_ai.data.data_audit import audit_directory as audit_synthetic
        synthetic_audit = audit_synthetic(synthetic_dir, feature_registry=FEATURE_REGISTRY)
        for a in synthetic_audit:
            a["_marker"] = "SYNTHETIC_DEVELOPMENT_DATA - Model metrics have NO real-world predictive validity"
        directories_to_audit.append(("synthetic", synthetic_audit))
        print(f"Audited synthetic directory: {synthetic_dir} ({len(synthetic_audit)} files)")

    # Add real data directory if it exists and has files
    data_dir = Path(r"C:\Users\shakti\Desktop\kosi-ai\data")
    if data_dir.is_dir():
        from kosi_ai.data.data_audit import audit_directory as audit_real
        real_audit = audit_real(data_dir, feature_registry=FEATURE_REGISTRY)
        directories_to_audit.append(("real_data", real_audit))
        print(f"Audited real data directory: {data_dir} ({len(real_audit)} files)")

    # ------------------------------------------------------------------
    # 2. Generate the full audit report
    # ------------------------------------------------------------------
    all_results = []
    for label, results in directories_to_audit:
        all_results.extend(results)

    if not all_results:
        print("No data files found. Ensure data directories exist with CSV/Excel/JSON/Parquet files.")
        print("  - data/raw/    : for raw observations (currently empty)")
        print("  - data/synthetic/: for development testing (has synthetic data)")
        sys.exit(0)

    report = generate_audit_report(all_results, output_path=None)

    # ------------------------------------------------------------------
    # 3. Print the report to stdout
    # ------------------------------------------------------------------
    print(report)

    # ------------------------------------------------------------------
    # 4. Create dataset manifest (YAML)
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("CREATING DATASET MANIFEST")
    print("=" * 60)

    # Only create manifest from real (non-synthetic) data
    real_results = [r for r in all_results if not r.get("_marker", "").startswith("SYNTHETIC")]
    if real_results:
        manifest = create_dataset_manifest(Path(r"C:\Users\shakti\Desktop\kosi-ai\data"), Path(r"C:\Users\shakti\Desktop\kosi-ai\data\manifest.yaml"))
        print(f"Manifest written to {MANIFEST_OUTPUT}")
        print(f"  Datasets included: {len(manifest['datasets'])}")
    else:
        print("No real data files found; manifest not created.")
        import yaml
        empty_manifest = {"datasets": [], "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "total_files": 0}
        with open(Path(r"C:\Users\shakti\Desktop\kosi-ai\data\manifest.yaml"), "w") as f:
            yaml.dump(empty_manifest, f, default_flow_style=False, sort_keys=False)
        print(f"Empty manifest written to {Path(r'C:\Users\shakti\Desktop\kosi-ai\data\manifest.yaml')}")

    # ------------------------------------------------------------------
    # 5. Summary
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)
    print()
    print(f"  Total files audited: {len(all_results)}")
    successful = sum(1 for r in all_results if r.get("status") == "success")
    print(f"  Successful: {successful}")
    failed = sum(1 for r in all_results if r.get("status") == "failed")
    print(f"  Failed: {failed}")
    print()
    print(f"  Report written to stdout (use redirect to file if needed)")
    print(f"  Manifest written to: data/manifest.yaml")


if __name__ == "__main__":
    main()