"""Configuration settings for the Kosi Embankment AI/ML layer."""
import logging

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field, validator
from typing import List, Optional
import os


class Settings(BaseModel):
    """Application settings loaded from environment and config files."""

    # Paths
    base_dir: str = Field(default="", description="Base project directory")
    data_dir: str = Field(default="data", description="Data directory")
    synthetic_dir: str = Field(default="data/synthetic", description="Synthetic data directory")
    raw_dir: str = Field(default="data/raw", description="Raw data directory")
    processed_dir: str = Field(default="data/processed", description="Processed data directory")
    configs_dir: str = Field(default="configs", description="Configuration directory")
    models_dir: str = Field(default="models", description="Trained model directory")
    notebooks_dir: str = Field(default="notebooks", description="Notebooks directory")
    tests_dir: str = Field(default="tests", description="Tests directory")

    # Model settings
    default_seed: int = Field(default=42, description="Random seed for reproducibility")
    model_version: str = Field(default="engineering_index_v0.1", description="Current model version")
    model_status: str = Field(default="ENGINEERING_INDEX_V0.1", description="Current model status")

    # Vulnerability index settings
    vulnerability_score_thresholds: dict = Field(
        default={
            "LOW": 0.0,
            "MODERATE": 0.3,
            "HIGH": 0.6,
            "CRITICAL": 1.0,
        },
        description="Configurable thresholds for vulnerability classes",
    )

    # Feature registry
    feature_registry_path: str = Field(
        default="configs/feature_registry.yaml", description="Path to feature registry"
    )
    data_sources_path: str = Field(
        default="configs/data_sources.yaml", description="Path to data sources registry"
    )

    # Data quality settings
    min_data_completeness: float = Field(
        default=0.7, description="Minimum fraction of features required for prediction"
    )

    # API output settings
    output_vulnerability_schema: bool = Field(
        default=True, description="Use vulnerability schema for output"
    )
    output_risk_schema: bool = Field(
        default=False, description="Use risk schema for output (supervised mode)"
    )

    # Synthetic data flag
    synthetic_mode: bool = Field(
        default=True,
        description="If True, use synthetic development data with clear marking",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="structured", description="Log format (structured/json)"
    )

    @validator("base_dir", always=True)
    def set_base_dir(cls, v):
        """Auto-detect base directory if not provided."""
        if not v:
            # Use the directory where this config file lives, going up one level
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return v

    class Config:
        """Pydantic config."""

        arbitrary_types = True


# Singleton instance
settings = Settings()


def get_base_dir() -> str:
    """Return the base project directory."""
    return settings.base_dir


def get_data_dir() -> str:
    """Return the data directory path."""
    return os.path.join(get_base_dir(), settings.data_dir)


def get_synthetic_dir() -> str:
    """Return the synthetic data directory path."""
    return os.path.join(get_base_dir(), settings.synthetic_dir)


def get_processed_dir() -> str:
    """Return the processed data directory path."""
    return os.path.join(get_base_dir(), settings.processed_dir)


def get_configs_dir() -> str:
    """Return the configs directory path."""
    return os.path.join(get_base_dir(), settings.configs_dir)


def get_models_dir() -> str:
    """Return the models directory path."""
    return os.path.join(get_base_dir(), settings.models_dir)


# Convenience: vulnerability class thresholds
VULN_THRESHOLDS = settings.vulnerability_score_thresholds


def get_vulnerability_class(score: float) -> str:
    """Convert a vulnerability score (0-1) to a vulnerability class."""
    thresholds = VULN_THRESHOLDS
    if score <= thresholds["LOW"]:
        return "LOW"
    elif score <= thresholds["MODERATE"]:
        return "MODERATE"
    elif score <= thresholds["HIGH"]:
        return "HIGH"
    else:
        return "CRITICAL"


def load_feature_registry() -> dict:
    """Load the feature registry from YAML config."""
    import yaml
    from pathlib import Path
    path = Path(get_configs_dir()) / settings.feature_registry_path
    if path.exists():
        with open(path, "r") as f:
            return yaml.safe_load(f)
    else:
        logger.warning(f"Feature registry config not found at {path}")
        return {}


def load_data_sources() -> dict:
    """Load the data sources registry from YAML config."""
    import yaml
    from pathlib import Path
    path = Path(get_configs_dir()) / settings.data_sources_path
    if path.exists():
        with open(path, "r") as f:
            return yaml.safe_load(f)
    else:
        logger.warning(f"Data sources config not found at {path}")
        return {}