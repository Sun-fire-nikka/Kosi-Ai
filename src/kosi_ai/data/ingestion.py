"""Data ingestion pipeline for Kosi Embankment AI/ML layer.

Supports reading CSV, Excel, JSON, and Parquet files while preserving
source metadata. Designed to work with the SourceRegistry for variable
availability classification and the DataAudit system.

Key design principles:
- Preserve source metadata (origin, date, license, variables)
- Classify each variable as: AVAILABLE, DERIVABLE, NOT_AVAILABLE, UNKNOWN
- Do not assume data quality; report all metadata for audit
- Configuration-driven: variable expectations come from feature_registry.yaml
- Modular: each format has a dedicated reader function
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from kosi_ai.data.source_registry import get_registry, SourceMetadata, SourceStatus

logger = logging.getLogger(__name__)

# Canonical observation schema fields (from feature registry)
CANONICAL_SCHEMA_FIELDS = [
    "segment_id", "latitude", "longitude", "chainage",
    "river_level", "discharge", "water_level_change", "discharge_change",
    "rainfall_24h", "rainfall_72h", "rainfall_7d",
    "embankment_height", "crest_elevation", "freeboard", "slope", "material", "condition",
    "elevation", "local_slope", "river_width", "river_curvature", "distance_to_river",
    "floodplain_characteristics",
    "soil_type", "soil_moisture",
    "erosion_indicator", "sedimentation_indicator",
    "historical_failure_count", "historical_breach_distance", "historical_flood_frequency",
    "dataset_status"
]


def classify_variable_availability(var_name: str, source_registry) -> str:
    """Classify a variable's availability using the source registry.

    Returns one of:
    - AVAILABLE: Variable is in source data already ingested
    - DERIVABLE: Variable can be derived from available sources
    - NOT_AVAILABLE: No source provides this variable
    - UNKNOWN: Unclear status (no source info available)
    """
    registry = get_registry()
    providing_sources = registry.get_sources_by_variable(var_name)

    if not providing_sources:
        return "NOT_AVAILABLE"

    # Check if any source is ACTIVE (data ingested and validated)
    active_sources = [s for s in providing_sources if s.status == SourceStatus.ACTIVE]
    if active_sources:
        return "AVAILABLE"

    # Check if all sources are IDENTIFIED (known but not ingested)
    identified_sources = [s for s in providing_sources if s.status == SourceStatus.IDENTIFIED]
    if identified_sources:
        return "DERIVABLE"

    # Some sources provide it but status is PENDING or UNAVAILABLE
    return "DERIVABLE"


def infer_variable_units(var_name: str) -> str:
    """Infer the standard units for a variable name."""
    units_map = {
        "segment_id": "string",
        "latitude": "decimal degrees",
        "longitude": "decimal degrees",
        "chainage": "km",
        "river_level": "m",
        "discharge": "m^3/s",
        "water_level": "m",
        "water_level_change": "m/day",
        "discharge_change": "m^3/s/day",
        "rainfall_24h": "mm",
        "rainfall_72h": "mm",
        "rainfall_7d": "mm",
        "embankment_height": "m",
        "crest_elevation": "m",
        "freeboard": "m",
        "slope": "ratio (m/m)",
        "material": "categorical",
        "condition": "categorical",
        "elevation": "m",
        "local_slope": "ratio (m/m)",
        "river_width": "m",
        "river_curvature": "1/km",
        "distance_to_river": "m",
        "floodplain_characteristics": "categorical",
        "soil_type": "categorical",
        "soil_moisture": "volumetric water content",
        "erosion_indicator": "categorical",
        "sedimentation_indicator": "categorical",
        "historical_failure_count": "count",
        "historical_breach_distance": "km",
        "historical_flood_frequency": "events/year",
        "dataset_status": "string",
    }
    return units_map.get(var_name, "unknown")


def detect_date_columns(df: pd.DataFrame, possible_names: List[str] = None) -> Optional[pd.Series]:
    """Detect which columns contain date/time values.

    Returns a Series of datetime values if found, None otherwise.
    """
    if possible_names:
        for name in possible_names:
            if name in df.columns:
                try:
                    dates = pd.to_datetime(df[name], errors="coerce")
                    if dates.notna().sum() > len(df) * 0.5:
                        return dates
                except Exception:
                    continue

    # Try common date column names
    common_date_names = ["date", "datetime", "timestamp", "observation_date", "report_date"]
    for name in common_date_names:
        if name in df.columns:
            try:
                dates = pd.to_datetime(df[name], errors="coerce")
                if dates.notna().sum() > len(df) * 0.5:
                    return dates
            except Exception:
                continue

    # Try to detect date-like columns by sampling
    for col in df.columns:
        sample = df[col].dropna().head(10)
        if len(sample) == 0:
            continue
        try:
            parsed = pd.to_datetime(sample, errors="coerce")
            na_rate = parsed.isna().sum() / len(sample)
            if na_rate < 0.5:
                full_dates = pd.to_datetime(df[col], errors="coerce")
                if full_dates.notna().sum() > len(df) * 0.3:
                    return full_dates
        except Exception:
            continue

    return None


def infer_temporal_resolution(dates: pd.Series) -> str:
    """Infer the temporal resolution from a date series.

    Returns one of: daily, weekly, monthly, annual, irregular, static
    """
    if dates is None or len(dates) < 3:
        return "static"

    sorted_dates = sorted(dates.dropna())
    if len(sorted_dates) < 3:
        return "static"

    diffs = []
    for i in range(1, len(sorted_dates)):
        diff = (sorted_dates[i] - sorted_dates[i - 1]).days
        if diff > 0:
            diffs.append(diff)

    if not diffs:
        return "static"

    from collections import Counter
    diff_counts = Counter(diffs)
    most_common_diff = diff_counts.most_common(1)[0][0]

    if most_common_diff == 1:
        return "daily"
    elif most_common_diff == 7:
        return "weekly"
    elif most_common_diff == 30:
        return "monthly"
    elif most_common_diff > 30:
        return "annual"
    else:
        return "irregular"


def infer_spatial_resolution_from_coords(lat_col: np.ndarray, lon_col: np.ndarray) -> str:
    """Infer spatial resolution from coordinate data.

    Returns a description of the spatial granularity.
    """
    if lat_col is None or lon_col is None or len(lat_col) < 3:
        return "unknown"

    lat_diff = np.max(lat_col) - np.min(lat_col)
    lon_diff = np.max(lon_col) - np.min(lon_col)

    lat_km = lat_diff * 111.0
    lon_km = lon_diff * 111.0 * np.cos(np.mean(lat_col) * np.pi / 180.0) if len(lat_col) > 0 else 0

    if lat_km > 100 and lon_km > 100:
        return "regional (hundreds of km)"
    elif lat_km > 10 or lon_km > 10:
        return "district-level"
    elif lat_km > 1 or lon_km > 1:
        return "segment-level"
    else:
        return "local (meters to km)"


def read_csv_safe(filepath: Path, **kwargs) -> pd.DataFrame:
    """Read a CSV file with multiple encoding attempts."""
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]
    separators = [",", ";", "\t", "|"]

    last_error = None
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(filepath, sep=sep, encoding=encoding, dtype=str, **kwargs)
                if len(df) > 0 and len(df.columns) > 1:
                    return df
            except Exception as e:
                last_error = e
                continue

    logger.warning(f"Failed to read CSV with encoding/separator attempts: {last_error}")
    return pd.read_csv(filepath, dtype=str)


def read_excel_safe(filepath: Path, **kwargs) -> pd.DataFrame:
    """Read an Excel file with sheet name detection."""
    try:
        xl = pd.ExcelFile(filepath)
        sheet_names = xl.sheet_names[:3]

        for sheet in sheet_names:
            try:
                df = pd.read_excel(filepath, sheet_name=sheet, **kwargs)
                if len(df) > 0 and len(df.columns) > 1:
                    return df
            except Exception:
                continue

        df = pd.read_excel(filepath, sheet_name=0, **kwargs)
        return df
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        return pd.DataFrame()


def read_json_safe(filepath: Path, **kwargs) -> pd.DataFrame:
    """Read a JSON file with multiple format attempts."""
    try:
        try:
            df = pd.read_json(filepath, orient="records", **kwargs)
            if len(df) > 0:
                return df
        except Exception:
            pass

        try:
            df = pd.read_json(filepath, lines=True, **kwargs)
            if len(df) > 0:
                return df
        except Exception:
            pass

        df = pd.read_json(filepath, **kwargs)
        return df
    except Exception as e:
        logger.error(f"Failed to read JSON file: {e}")
        return pd.DataFrame()


def read_parquet_safe(filepath: Path, **kwargs) -> pd.DataFrame:
    """Read a Parquet file."""
    try:
        df = pd.read_parquet(filepath, **kwargs)
        if len(df) > 0:
            return df
    except Exception as e:
        logger.error(f"Failed to read Parquet file: {e}")
    return pd.DataFrame()


def detect_file_type(filepath: Path) -> str:
    """Detect the file type based on extension."""
    ext = filepath.suffix.lower()
    if ext == ".csv":
        return "csv"
    elif ext in [".xls", ".xlsx"]:
        return "excel"
    elif ext == ".json":
        return "json"
    elif ext == ".parquet":
        return "parquet"
    else:
        return "unknown"


def infer_missing_policy(col_series: pd.Series, feature_info: dict = None) -> str:
    """Infer the missing data policy for a column based on its values."""
    null_count = col_series.isna().sum()
    total_count = len(col_series)
    null_pct = null_count / total_count * 100 if total_count > 0 else 0

    if null_pct == 0:
        return "no_missing"
    elif null_pct < 5:
        return "interpolate_nearest"
    elif null_pct < 20:
        return "use_nearest_station"
    elif null_pct < 50:
        return "flag_for_review"
    else:
        return "assign_default"


def enrich_with_source_metadata(
    df: pd.DataFrame,
    source_name: str,
    source_url: str,
    download_date: str,
    variable_availability: Dict[str, str] = None
):
    """Enrich a DataFrame with source metadata columns.

    Adds columns:
    - source_name: Name of the data source
    - source_url: URL of the data source
    - download_date: Date the data was downloaded/ingested
    - variable_availability: Dict mapping variable name to availability status
    """
    df = df.copy()

    df["source_name"] = source_name
    df["source_url"] = source_url
    df["download_date"] = download_date

    if variable_availability:
        for var in variable_availability:
            if var in df.columns:
                df[f"{var}_availability"] = variable_availability[var]

    for field in CANONICAL_SCHEMA_FIELDS:
        if field in df.columns and field not in variable_availability:
            availability = classify_variable_availability(field, get_registry())
            df[f"{field}_availability"] = availability

    return df


def infer_data_quality_summary(df: pd.DataFrame, feature_registry: dict = None) -> dict:
    """Compute a summary of data quality for a DataFrame."""
    total_rows = len(df)
    total_cells = df.size
    missing_cells = df.isna().sum().sum()
    missing_pct = total_cells > 0 and (missing_cells / total_cells * 100) or 0

    duplicate_rows = df.duplicated().sum()

    missing_per_col = {}
    for col in df.columns:
        n_missing = df[col].isna().sum()
        pct_missing = n_missing / total_rows * 100 if total_rows > 0 else 0
        missing_per_col[col] = {
            "n_missing": int(n_missing),
            "pct_missing": round(pct_missing, 1)
        }

    type_summary = {}
    for col in df.columns:
        type_summary[col] = str(df[col].dtype)

    return {
        "total_rows": total_rows,
        "total_cells": total_cells,
        "missing_cells": int(missing_cells),
        "missing_pct": round(missing_pct, 1),
        "duplicate_rows": int(duplicate_rows),
        "missing_per_col": missing_per_col,
        "type_summary": type_summary
    }


def infer_geographic_coverage(df: pd.DataFrame, lat_col: str = "latitude", lon_col: str = "longitude") -> dict:
    """Infer geographic coverage from latitude/longitude columns."""
    if lat_col not in df.columns or lon_col not in df.columns:
        return {"bounding_box": None, "centroid": None, "notes": "Lat/lon columns not found"}

    try:
        lats = pd.to_numeric(df[lat_col], errors="coerce").dropna()
        lons = pd.to_numeric(df[lon_col], errors="coerce").dropna()

        if len(lats) == 0 or len(lons) == 0:
            return {"bounding_box": None, "centroid": None, "notes": "No valid lat/lon values"}

        min_lat, max_lat = lats.min(), lats.max()
        min_lon, max_lon = lons.min(), lons.max()

        centroid_lat = (min_lat + max_lat) / 2
        centroid_lon = (min_lon + max_lon) / 2

        bounding_box = {
            "min_lat": round(float(min_lat), 4),
            "max_lat": round(float(max_lat), 4),
            "min_lon": round(float(min_lon), 4),
            "max_lon": round(float(max_lon), 4)
        }

        centroid = {
            "lat": round(float(centroid_lat), 4),
            "lon": round(float(centroid_lon), 4)
        }

        return {
            "bounding_box": bounding_box,
            "centroid": centroid,
            "notes": f"Coverage based on {len(lats)} valid latitude/longitude pairs"
        }
    except Exception as e:
        return {"bounding_box": None, "centroid": None, "notes": f"Error: {str(e)}"}


def ingest_file(
    filepath: Path,
    source_name: str = "unknown",
    source_url: str = "",
    download_date: str = None,
    variable_availability: Dict[str, str] = None,
    **kwargs: Any
) -> dict:
    """Ingest a single data file and return a structured result."""
    file_type = detect_file_type(filepath)

    reader_map = {
        "csv": read_csv_safe,
        "excel": read_excel_safe,
        "json": read_json_safe,
        "parquet": read_parquet_safe,
    }

    reader = reader_map.get(file_type, read_csv_safe)

    df = None
    try:
        df = reader(filepath, **kwargs)
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        df = pd.DataFrame()

    if df is None or len(df) == 0:
        return {
            "success": False,
            "dataframe": pd.DataFrame(),
            "file_type": file_type,
            "error": f"Could not read file or file is empty: {filepath}",
            "quality_summary": {},
            "geographic_coverage": {"bounding_box": None, "centroid": None, "notes": "Empty dataframe"},
            "variable_availability": {},
            "source_metadata": None,
        }

    # Infer geographic coverage
    geo_coverage = infer_geographic_coverage(df)

    # Infer temporal coverage
    dates = detect_date_columns(df)
    temporal_info = {
        "has_date_column": dates is not None,
        "date_range": None,
        "temporal_resolution": "static",
    }
    if dates is not None:
        try:
            date_range = {
                "start": dates.min().strftime("%Y-%m-%d"),
                "end": dates.max().strftime("%Y-%m-%d"),
            }
            temporal_info["date_range"] = date_range
            temporal_info["temporal_resolution"] = infer_temporal_resolution(dates)
        except Exception:
            pass

    # Infer variable availability
    if variable_availability is None:
        variable_availability = {}
        for col in df.columns:
            var_availability = classify_variable_availability(col, get_registry())
            variable_availability[col] = var_availability
    else:
        for col in df.columns:
            if col not in variable_availability:
                variable_availability[col] = classify_variable_availability(col, get_registry())

    # Enrich with source metadata
    if download_date is None:
        download_date = datetime.now().strftime("%Y-%m-%d")

    df_enriched = enrich_with_source_metadata(
        df,
        source_name=source_name,
        source_url=source_url,
        download_date=download_date,
        variable_availability=variable_availability,
    )

    # Compute quality summary
    quality_summary = infer_data_quality_summary(df_enriched)

    # Get source metadata object
    from kosi_ai.data.source_registry import SourceMetadata
    source_meta = None
    if source_name != "unknown":
        source_meta = get_registry().get_source(source_name)
        if source_meta is None:
            source_meta = SourceMetadata({
                "source_name": source_name,
                "organization": "",
                "url": source_url,
                "dataset_name": filepath.stem,
                "variable": ", ".join(df.columns[:10]) if len(df.columns) > 0 else "",
                "status": "IDENTIFIED",
                "temporal_resolution": temporal_info.get("temporal_resolution", "unknown"),
                "spatial_resolution": "unknown",
                "license_or_access_notes": "",
                "verification_status": "NOT_YET_INGESTED",
            })

    return {
        "success": True,
        "dataframe": df_enriched,
        "file_type": file_type,
        "quality_summary": quality_summary,
        "geographic_coverage": geo_coverage,
        "temporal_info": temporal_info,
        "variable_availability": variable_availability,
        "source_metadata": source_meta,
        "error": None,
    }


def ingest_directory(
    directory: Path,
    source_name: str = "unknown",
    source_url: str = "",
    recursive: bool = True
) -> List[dict]:
    """Ingest all supported data files in a directory."""
    results = []

    patterns = ["*.csv", "*.xlsx", "*.xls", "*.json", "*.parquet"]
    files = []
    for pattern in patterns:
        files.extend(directory.glob(pattern))
    files = sorted(set(files))

    for filepath in files:
        result = ingest_file(
            filepath=filepath,
            source_name=source_name,
            source_url=source_url,
        )
        result["file_path"] = str(filepath)
        result["relative_path"] = str(filepath.relative_to(directory)) if directory.is_dir() else str(filepath)
        results.append(result)
        logger.info(f"Ingested {filepath.name}: {result['quality_summary']['total_rows']} rows, success={result['success']}")

    return results