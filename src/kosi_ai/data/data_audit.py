"""Data audit module for Kosi Embankment AI/ML layer.

Produces comprehensive audit reports on data files, including:
- Files found and their types
- Row counts, column names
- Date ranges and geographic coverage
- Missing values and duplicate records
- Units and candidate variables
- Source metadata classification (AVAILABLE/DERIVABLE/NOT_AVAILABLE/UNKNOWN)

This module works in conjunction with source_registry.py and ingestion.py
to provide a complete picture of the data landscape before any modeling.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from kosi_ai.data.ingestion import (
    detect_file_type, read_csv_safe, read_excel_safe, read_json_safe,
    read_parquet_safe, classify_variable_availability, infer_variable_units,
    detect_date_columns, infer_temporal_resolution, infer_geographic_coverage,
    enrich_with_source_metadata, infer_data_quality_summary, infer_temporal_resolution,
    detect_file_type
)
from kosi_ai.data.source_registry import get_registry, SourceMetadata, SourceStatus
from kosi_ai.config import load_feature_registry

logger = logging.getLogger(__name__)


def classify_feature_availability(feature_name: str, feature_registry: dict = None) -> str:
    """Classify a feature's availability status.
    
    Returns one of:
    - AVAILABLE: Feature is in ingested source data
    - DERIVABLE: Feature can be derived from available sources
    - NOT_AVAILABLE: No source provides this feature
    - UNKNOWN: Status cannot be determined
    """
    if feature_registry is None:
        feature_registry = load_feature_registry()
    
    # Check feature registry
    for feat in feature_registry.get("feature_registry", []):
        if feat["feature_name"] == feature_name:
            # If observed and from identified source, it's available once ingested
            if feat.get("observed_or_derived") == "observed":
                return "AVAILABLE"  # Will be AVAILABLE once data is ingested
            elif feat.get("observed_or_derived") == "derived":
                return "DERIVABLE"
    
    # Check source registry
    registry = get_registry()
    providing_sources = registry.get_sources_by_variable(feature_name)
    
    if not providing_sources:
        return "NOT_AVAILABLE"
    
    # If any source is ACTIVE
    active_sources = [s for s in providing_sources if s.status == SourceStatus.ACTIVE]
    if active_sources:
        return "AVAILABLE"
    
    # If only IDENTIFIED sources
    identified_sources = [s for s in providing_sources if s.status == SourceStatus.IDENTIFIED]
    if identified_sources:
        return "DERIVABLE"  # Known but not yet ingested; can be derived from other data
    
    return "UNKNOWN"


def audit_single_file(
    filepath: Path,
    feature_registry: dict = None
) -> dict:
    """Perform a complete audit of a single data file.
    
    Returns a dict with comprehensive audit findings.
    """
    file_type = detect_file_type(filepath)
    
    # Read the file
    from kosi_ai.data.ingestion import ingest_file
    result = ingest_file(
        filepath=filepath,
        source_name=filepath.stem,  # Use filename as source name if unknown
        source_url="",
        download_date=datetime.now().strftime("%Y-%m-%d"),
    )
    
    if not result["success"] or result["dataframe"].empty:
        return {
            "file_path": str(filepath),
            "file_type": file_type,
            "error": result.get("error", "Unknown error"),
            "status": "failed",
        }
    
    df = result["dataframe"]
    
    # Basic info
    audit = {
        "file_path": str(filepath),
        "file_type": file_type,
        "status": "success",
        
        # File metadata
        "file_size_bytes": filepath.stat().st_size if filepath.exists() else None,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        
        # Data quality
        "quality_summary": result.get("quality_summary", {}),
        
        # Variable availability classification
        "variable_availability": result.get("variable_availability", {}),
        "availability_summary": _compute_availability_summary(
            result.get("variable_availability", {}), feature_registry
        ),
        
        # Geographic coverage
        "geographic_coverage": result.get("geographic_coverage", {}),
        
        # Temporal information
        "temporal_info": result.get("temporal_info", {}),
        
        # Source metadata
        "source_metadata": result.get("source_metadata", {}).__dict__ if result.get("source_metadata") else {},
        
        # Duplicate records
        "duplicate_records": {
            "count": int(df.duplicated().sum()),
            "pct": round(df.duplicated().mean() * 100, 1) if len(df) > 0 else 0,
        },
        
        # Key variables present
        "key_variables_present": _get_key_variables_present(df),
        
        # Notes
        "notes": [],
    }
    
    # Add any errors from the ingestion
    if result.get("error"):
        audit["notes"].append(f"Ingestion error: {result['error']}")
    
    return audit


def _compute_availability_summary(
    variable_availability: dict,
    feature_registry: dict = None
) -> dict:
    """Compute a summary of variable availability classifications."""
    if feature_registry is None:
        feature_registry = load_feature_registry()
    
    summary = {
        "AVAILABLE": 0,
        "DERIVABLE": 0,
        "NOT_AVAILABLE": 0,
        "UNKNOWN": 0,
        "total_checked": 0,
    }
    
    for var_name, classification in variable_availability.items():
        summary["total_checked"] += 1
        if classification in summary:
            summary[classification] += 1
        else:
            summary["UNKNOWN"] += 1
    
    return summary


def _get_key_variables_present(df: pd.DataFrame) -> List[str]:
    """Get a list of key canonical variables that are present in the DataFrame."""
    canonical = [
        "segment_id", "river_level", "embankment_height", "freeboard",
        "condition", "rainfall_24h", "erosion_indicator"
    ]
    present = []
    for var in canonical:
        if var in df.columns:
            present.append(var)
    return present


def audit_directory(
    directory: Path,
    feature_registry: dict = None,
    recursive: bool = True
) -> List[dict]:
    """Audit all data files in a directory.
    
    Returns a list of audit dicts, one per file.
    """
    if feature_registry is None:
        feature_registry = load_feature_registry()
    
    results = []
    
    # Find all supported files
    patterns = ["*.csv", "*.xlsx", "*.xls", "*.json", "*.parquet"]
    files = []
    for pattern in patterns:
        files.extend(directory.glob(pattern))
    files = sorted(set(files))
    
    for filepath in files:
        audit = audit_single_file(filepath, feature_registry)
        audit["file_relative_path"] = str(filepath.relative_to(directory)) if directory.is_dir() else str(filepath)
        results.append(audit)
    
    return results


def generate_audit_report(
    audit_results: List[dict],
    output_path: Path = None
) -> str:
    """Generate a human-readable dataset audit report from audit results.
    
    Args:
        audit_results: List of audit dicts from audit_directory()
        output_path: If provided, write the report to this path
    
    Returns:
        The report as a string
    """
    if not audit_results:
        return "No audit results provided."
    
    # Summary statistics
    total_files = len(audit_results)
    successful_files = sum(1 for r in audit_results if r.get("status") == "success")
    failed_files = sum(1 for r in audit_results if r.get("status") == "failed")
    
    total_rows = sum(r.get("rows", 0) for r in audit_results if r.get("status") == "success")
    total_columns = set()
    all_availability = {"AVAILABLE": 0, "DERIVABLE": 0, "NOT_AVAILABLE": 0, "UNKNOWN": 0}
    key_variables_found = set()
    geographic_coverage_notes = []
    
    for audit in audit_results:
        if audit.get("status") == "success":
            total_columns.update(audit.get("column_names", []))
            
            # Aggregate availability
            avail = audit.get("availability_summary", {})
            for key in all_availability:
                all_availability[key] += avail.get(key, 0)
            
            # Key variables
            for var in audit.get("key_variables_present", []):
                key_variables_found.add(var)
            
            # Geographic notes
            geo_note = audit.get("geographic_coverage", {}).get("notes", "")
            if geo_note:
                geographic_coverage_notes.append(geo_note)
    
    # Build the report
    lines = []
    lines.append("=" * 70)
    lines.append("KOSI EMBANKMENT DATA AUDIT REPORT")
    lines.append("=" * 70)
    lines.append("")
    
    # Section 1: Overview
    lines.append("SECTION 1: OVERVIEW")
    lines.append("-" * 70)
    lines.append(f"Total files audited: {total_files}")
    lines.append(f"  Successful: {successful_files}")
    lines.append(f"  Failed: {failed_files}")
    lines.append(f"  Total rows across all files: {total_rows}")
    lines.append(f"  Unique column names found: {len(total_columns)}")
    lines.append("")
    
    # Section 2: Variable Availability
    lines.append("SECTION 2: VARIABLE AVAILABILITY CLASSIFICATION")
    lines.append("-" * 70)
    lines.append(f"  AVAILABLE: {all_availability['AVAILABLE']} variables")
    lines.append(f"  DERIVABLE: {all_availability['DERIVABLE']} variables")
    lines.append(f"  NOT_AVAILABLE: {all_availability['NOT_AVAILABLE']} variables")
    lines.append(f"  UNKNOWN: {all_availability['UNKNOWN']} variables")
    lines.append("")
    
    # Section 3: Key Variables
    lines.append("SECTION 3: KEY VARIABLES PRESENT")
    lines.append("-" * 70)
    for var in sorted(key_variables_found):
        lines.append(f"  - {var}")
    lines.append(f"  (of {len(canonical_canonical_vars())} canonical variables checked)")
    lines.append("")
    
    # Section 4: File-level Details
    lines.append("SECTION 4: FILE-LEVEL DETAILS")
    lines.append("-" * 70)
    for i, audit in enumerate(audit_results):
        if audit.get("status") == "success":
            lines.append(f"  File {i+1}: {audit.get('file_relative_path', 'unknown')}")
            lines.append(f"    Type: {audit.get('file_type', 'unknown')}")
            lines.append(f"    Rows: {audit.get('rows', 'unknown')}")
            lines.append(f"    Columns: {audit.get('columns', 'unknown')}")
            lines.append(f"    Availability: AVAILABLE={audit.get('availability_summary', {}).get('AVAILABLE', 0)}, "
                         f"DERIVABLE={audit.get('availability_summary', {}).get('DERIVABLE', 0)}, "
                         f"NOT_AVAILABLE={audit.get('availability_summary', {}).get('NOT_AVAILABLE', 0)}")
            lines.append(f"    Duplicates: {audit.get('duplicate_records', {}).get('count', 0)} "
                         f"({audit.get('duplicate_records', {}).get('pct', 0)}%)")
            lines.append("")
    
    # Section 5: Geographic Coverage
    lines.append("SECTION 5: GEOGRAPHIC COVERAGE")
    lines.append("-" * 70)
    for note in geographic_coverage_notes:
        lines.append(f"  - {note}")
    lines.append("")
    
    # Section 6: Temporal Coverage
    lines.append("SECTION 6: TEMPORAL COVERAGE")
    lines.append("-" * 70)
    for audit in audit_results:
        if audit.get("status") == "success":
            ti = audit.get("temporal_info", {})
            if ti.get("date_range"):
                lines.append(f"  {audit.get('file_relative_path', 'unknown')}: "
                             f"{ti['date_range']['start']} to {ti['date_range']['end']}, "
                             f"resolution: {ti.get('temporal_resolution', 'unknown')}")
    lines.append("")
    
    # Section 7: Summary and Recommendations
    lines.append("SECTION 7: SUMMARY AND RECOMMENDATIONS")
    lines.append("-" * 70)
    
    # Check if supervised model is feasible
    available_vars = all_availability['AVAILABLE']
    derivable_vars = all_availability['DERIVABLE']
    not_available = all_availability['NOT_AVAILABLE']
    
    lines.append(f"  Variables AVAILABLE: {available_vars}")
    lines.append(f"  Variables DERIVABLE: {derivable_vars}")
    lines.append(f"  Variables NOT_AVAILABLE: {not_available}")
    lines.append("")
    
    if available_vars >= 15:
        lines.append("  -> Supervised model training may be feasible with current data.")
    elif available_vars >= 10:
        lines.append("  -> Supervised model training possible with feature engineering (derivable features).")
    elif available_vars > 0:
        lines.append("  -> Limited supervised model training; engineering vulnerability index recommended as baseline.")
    else:
        lines.append("  -> Insufficient data for supervised model; engineering index is primary tool.")
    
    lines.append("")
    lines.append("  -> Engineering vulnerability index can be computed immediately using available features.")
    lines.append("  -> Data acquisition prioritized for: " + 
                 ", ".join([v for v, c in all_availability.items() if c > 0 and c < 3] or ["none identified"]))
    lines.append("")
    
    lines.append("=" * 70)
    
    # Write to file if output_path specified
    if output_path:
        try:
            with open(output_path, "w") as f:
                f.write("\n".join(lines))
            logger.info(f"Audit report written to {output_path}")
        except Exception as e:
            logger.error(f"Failed to write audit report: {e}")
    
    return "\n".join(lines)


def canonical_canonical_vars() -> List[str]:
    """Return the list of canonical variable names from the feature registry."""
    import yaml
    try:
        fr = load_feature_registry()
        return [feat["feature_name"] for feat in fr.get("feature_registry", [])]
    except Exception:
        return [
            "segment_id", "latitude", "longitude", "chainage",
            "river_level", "discharge", "water_level_change", "discharge_change",
            "rainfall_24h", "rainfall_72h", "rainfall_7d",
            "embankment_height", "crest_elevation", "freeboard", "slope", "material", "condition",
            "elevation", "local_slope", "river_width", "river_curvature", "distance_to_river",
            "floodplain_characteristics",
            "soil_type", "soil_moisture",
            "erosion_indicator", "sedimentation_indicator",
            "historical_failure_count", "historical_breach_distance", "historical_flood_frequency",
        ]


def create_dataset_manifest(
    directory: Path,
    output_path: Path
) -> dict:
    """Create a dataset manifest YAML file from audited data files.
    
    Each real dataset in the manifest contains:
    - dataset_name
    - source
    - source_url
    - download_date
    - coverage_start
    - coverage_end
    - variables
    - spatial_coverage
    - temporal_resolution
    - license_or_usage_notes
    - verification_status
    """
    import yaml
    
    audit_results = audit_directory(directory)
    
    manifest = {
        "datasets": [],
        "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_files": len(audit_results),
    }
    
    for audit in audit_results:
        if audit.get("status") != "success":
            continue
        
        df = audit.get("dataframe")
        if df is None or df.empty:
            continue
        
        # Extract manifest fields
        file_path = Path(audit.get("file_path", ""))
        
        # Try to get source info from the dataframe metadata
        source_name = audit.get("source_metadata", {}).get("source_name", file_path.stem)
        source_url = audit.get("source_metadata", {}).get("source_url", "")
        download_date = audit.get("source_metadata", {}).get("download_date", datetime.now().strftime("%Y-%m-%d"))
        
        # Temporal coverage
        temporal_info = audit.get("temporal_info", {})
        coverage_start = temporal_info.get("date_range", {}).get("start", "")
        coverage_end = temporal_info.get("date_range", {}).get("end", "")
        temporal_resolution = temporal_info.get("temporal_resolution", "unknown")
        
        # Geographic coverage
        geo = audit.get("geographic_coverage", {})
        bbox = geo.get("bounding_box", {})
        if bbox:
            spatial_coverage = f"Lat: {bbox.get('min_lat', '-')} to {bbox.get('max_lat', '-')}, "
            spatial_coverage += f"Lon: {bbox.get('min_lon', '-')} to {bbox.get('max_lon', '-')}"
        else:
            spatial_coverage = "unknown"
        
        # Variables present
        var_avail = audit.get("variable_availability", {})
        variables = []
        for var, classification in var_avail.items():
            if classification in ["AVAILABLE", "DERIVABLE"]:
                variables.append(var)
        
        # License/usage notes from source metadata
        license_notes = audit.get("source_metadata", {}).get("license_or_access_notes", "")
        
        # Verification status
        verification_status = audit.get("source_metadata", {}).get("verification_status", "NOT_YET_INGESTED")
        
        dataset_entry = {
            "dataset_name": file_path.stem,
            "source": source_name,
            "source_url": source_url,
            "download_date": download_date,
            "coverage_start": coverage_start,
            "coverage_end": coverage_end,
            "variables": variables,
            "spatial_coverage": spatial_coverage,
            "temporal_resolution": temporal_resolution,
            "license_or_usage_notes": license_notes,
            "verification_status": verification_status,
        }
        
        manifest["datasets"].append(dataset_entry)
    
    # Write manifest
    try:
        with open(output_path, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Dataset manifest written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write dataset manifest: {e}")
    
    return manifest