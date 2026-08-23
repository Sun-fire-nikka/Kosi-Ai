"""Source registry for Kosi Embankment data ingestion.

Loads and manages the data sources configuration from configs/data_sources.yaml.
Provides metadata lookup, availability classification, and source registry
operations for the data ingestion pipeline.

Classifies each data source as:
- ACTIVE: Data has been successfully ingested and validated
- IDENTIFIED: Source known but not yet ingested
- PENDING: Source under review/contract negotiation
- UNAVAILABLE: Source cannot be accessed or licensed
"""

import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

from kosi_ai.config import get_base_dir, get_configs_dir

logger = logging.getLogger(__name__)


class SourceStatus:
    """Status enumeration for data sources."""
    ACTIVE = "ACTIVE"
    IDENTIFIED = "IDENTIFIED"
    PENDING = "PENDING"
    UNAVAILABLE = "UNAVAILABLE"


class SourceMetadata:
    """Metadata container for a single data source."""
    
    def __init__(self, source_data: dict):
        self.source_name = source_data.get("source_name", "unknown")
        self.organization = source_data.get("organization", "")
        self.url = source_data.get("url", "")
        self.dataset_name = source_data.get("dataset_name", "")
        self.variables = source_data.get("variable", "").split(", ")
        self.status = source_data.get("status", "UNKNOWN")
        self.temporal_resolution = source_data.get("temporal_resolution", "")
        self.spatial_resolution = source_data.get("spatial_resolution", "")
        self.license_or_access_notes = source_data.get("license_or_access_notes", "")
        self.verification_status = source_data.get("verification_status", "NOT_YET_INGESTED")
        
        # Derived fields
        self._available_variables = [v.strip() for v in self.variables] if self.variables else []
        self._variable_set = set(self._available_variables)
    
    def is_variable_available(self, var_name: str) -> bool:
        """Check if a variable is in this source's variable list."""
        return var_name in self._variable_set
    
    def get_variable_info(self, var_name: str) -> Optional[dict]:
        """Get info about a specific variable from this source."""
        # Return basic info; detailed metadata comes from feature registry
        return {
            "variable": var_name,
            "source": self.source_name,
            "units": self._guess_units(var_name),
            "observed_or_derived": "observed",  # Sources provide observed data
        }
    
    def _guess_units(self, var_name: str) -> str:
        """Guess units based on variable name."""
        units_map = {
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
            "elevation": "m",
            "river_width": "m",
            "river_curvature": "1/km",
            "distance_to_river": "m",
            "soil_moisture": "volumetric water content",
            "historical_failure_count": "count",
            "historical_breach_distance": "km",
            "historical_flood_frequency": "events/year",
        }
        return units_map.get(var_name, "unknown")
    
    def __repr__(self) -> str:
        return f"SourceMetadata({self.source_name}, status={self.status})"


class SourceRegistry:
    """Registry managing all identified data sources for the Kosi Embankment project.
    
    Loads from configs/data_sources.yaml and provides:
    - Source metadata lookup
    - Variable availability classification
    - Status tracking
    - Geographic/temporal coverage info
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the source registry.
        
        Args:
            config_path: Path to data_sources.yaml. If None, uses default location.
        """
        if config_path is None:
            self.config_path = Path(get_configs_dir()) / "data_sources.yaml"
        else:
            self.config_path = Path(config_path)
        
        self._sources: Dict[str, SourceMetadata] = {}
        self._by_variable: Dict[str, List[str]] = {}  # var_name -> [source_names]
        self._load_sources()
    
    def _load_sources(self) -> None:
        """Load data sources from YAML config file."""
        if not self.config_path.exists():
            logger.warning(f"Source config not found at {self.config_path}")
            return
        
        try:
            with open(self.config_path, "r") as f:
                raw_config = yaml.safe_load(f)
            
            sources_list = raw_config.get("data_sources", [])
            
            for source_data in sources_list:
                metadata = SourceMetadata(source_data)
                source_name = metadata.source_name
                self._sources[source_name] = metadata
                
                # Index variables by source
                for var in metadata._available_variables:
                    if var not in self._by_variable:
                        self._by_variable[var] = []
                    self._by_variable[var].append(source_name)
            
            logger.info(f"Loaded {len(self._sources)} data sources from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error loading source config: {e}")
    
    def get_source(self, source_name: str) -> Optional[SourceMetadata]:
        """Get metadata for a specific source by name."""
        return self._sources.get(source_name)
    
    def list_sources(self) -> List[SourceMetadata]:
        """List all loaded source metadata."""
        return list(self._sources.values())
    
    def list_active_sources(self) -> List[SourceMetadata]:
        """List sources with ACTIVE or IDENTIFIED status."""
        return [
            s for s in self._sources.values() 
            if s.status in [SourceStatus.ACTIVE, SourceStatus.IDENTIFIED]
        ]
    
    def get_sources_by_variable(self, var_name: str) -> List[SourceMetadata]:
        """Get all sources that provide a specific variable."""
        source_names = self._by_variable.get(var_name, [])
        return [self._sources[name] for name in source_names if name in self._sources]
    
    def classify_variable_availability(self, var_name: str) -> str:
        """Classify variable availability.
        
        Returns one of:
        - 'available': Source has this variable and it's ingested
        - 'derivable': Variable can be derived from available sources
        - 'unknown': Unclear if variable is available
        - 'not_available': No source provides this variable
        """
        providing_sources = self.get_sources_by_variable(var_name)
        
        if not providing_sources:
            return "not_available"
        
        # Check if any source is ACTIVE (data already ingested)
        active_sources = [s for s in providing_sources if s.status == SourceStatus.ACTIVE]
        if active_sources:
            return "available"
        
        # Check if all identified sources (no ACTIVE, but IDENTIFIED)
        identified_sources = [s for s in providing_sources if s.status == SourceStatus.IDENTIFIED]
        if identified_sources and not active_sources:
            # Variable is identified but not yet ingested - could be derivable
            # if feature registry shows it's derivable from other data
            return "derivable"
        
        # Some IDENTIFIED sources provide it
        return "derivable"
    
    def get_coverage_info(self) -> dict:
        """Get geographic and temporal coverage overview."""
        if not self._sources:
            return {}
        
        # Collect temporal ranges
        temporal_terms = set()
        spatial_terms = set()
        
        for source in self._sources.values():
            if source.temporal_resolution:
                temporal_terms.add(source.temporal_resolution)
            if source.spatial_resolution:
                spatial_terms.add(source.spatial_resolution)
        
        return {
            "sources_count": len(self._sources),
            "active_sources": sum(1 for s in self._sources.values() if s.status == SourceStatus.ACTIVE),
            "identified_sources": sum(1 for s in self._sources.values() if s.status == SourceStatus.IDENTIFIED),
            "temporal_resolutions": list(temporal_terms),
            "spatial_resolutions": list(spatial_terms),
            "total_variables": len(self._by_variable),
            "variables_with_sources": {var: len(sources) for var, sources in self._by_variable.items()}
        }
    
    def __repr__(self) -> str:
        return f"SourceRegistry(sources={len(self._sources)})"


# Singleton instance - will be lazy-loaded
_registry: Optional[SourceRegistry] = None


def get_registry() -> SourceRegistry:
    """Get the singleton SourceRegistry instance."""
    global _registry
    if _registry is None:
        _registry = SourceRegistry()
    return _registry


def reload_registry() -> SourceRegistry:
    """Force reload of the source registry."""
    global _registry
    _registry = SourceRegistry()
    return _registry