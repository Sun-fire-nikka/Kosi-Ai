# Kosi Embankment Data Dictionary

**Version:** 0.1.0  
**Purpose:** Canonical machine-readable dictionary of all features used in the Kosi Embankment Intelligence system.  
**Status:** Development V0.1 — based on identified data sources; verification pending.  
**Living document:** Updated whenever new data sources are ingested or the feature registry is modified.

---

## How to Read This Table

| Column | Description |
|---|---|
| **feature** | Canonical feature name used in the system |
| **meaning** | Human-readable description of what the feature represents |
| **unit** | Standard unit of measurement (or "categorical"/"string" for non-numeric) |
| **source** | Primary data source(s) where this feature is obtained |
| **observed/or derived** | `observed` = directly measured/monitored; `derived` = computed from other data |
| **temporal resolution** | How frequently the value is updated (e.g., daily, hourly, static, irregular) |
| **spatial resolution** | Granularity of the spatial data (e.g., segment-level, district-level, 30m) |
| **availability** | `AVAILABLE` = in ingested data; `DERIVABLE` = can be computed from available data; `NOT_AVAILABLE` = no source yet; `UNKNOWN` = status unclear |
| **missing-data policy** | Strategy for handling missing values (e.g., `interpolate_nearest`, `flag_for_review`, `assign_default`) |

---

## Feature List

| feature | meaning | unit | source | observed/or derived | temporal resolution | spatial resolution | availability | missing-data policy |
|---|---|---|---|---|---|---|---|---|
| segment_id | Unique identifier for each river segment | string | derived | derived | static | segment-level | UNKNOWN | error |
| latitude | WGS84 latitude coordinate of segment | decimal degrees | derived | derived | static | segment-level | UNKNOWN | error |
| longitude | WGS84 longitude coordinate of segment | decimal degrees | derived | derived | static | segment-level | UNKNOWN | error |
| chainage | Distance along embankment from reference point | km | derived | derived | static | segment-level | UNKNOWN | fill_from_upstream |
| river_level | Water level at the segment reference point | m | identified | observed | daily | segment-level | NOT_AVAILABLE | interpolate_nearest |
| discharge | River discharge (flow rate) at segment | m^3/s | identified | observed | daily | segment-level | NOT_AVAILABLE | use_downstream_value |
| water_level_change | Rate of change in river level (m/day) | m/day | derived | derived | daily | segment-level | DERIVABLE | calculate_from_successive |
| discharge_change | Rate of change in discharge (m^3/s/day) | m^3/s/day | derived | derived | daily | segment-level | DERIVABLE | calculate_from_successive |
| rainfall_24h | Cumulative rainfall over past 24 hours | mm | identified | observed | daily | district-level | NOT_AVAILABLE | use_nearest_station |
| rainfall_72h | Cumulative rainfall over past 72 hours | mm | identified | observed | daily | district-level | NOT_AVAILABLE | use_nearest_station |
| rainfall_7d | Cumulative rainfall over past 7 days | mm | identified | observed | daily | district-level | NOT_AVAILABLE | use_nearest_station |
| embankment_height | Height of embankment crest above datum | m | identified | observed | irregular | segment-level | NOT_AVAILABLE | flag_for_review |
| crest_elevation | Elevation of crest relative to datum | m | identified | observed | irregular | segment-level | NOT_AVAILABLE | flag_for_review |
| freeboard | Embankment height minus river level (overtopping risk indicator) | m | derived | derived | daily | segment-level | DERIVABLE | calculate_from_river_level_and_embankment_height |
| slope | Side-slope gradient of embankment cross-section | ratio (m/m) | identified | observed | irregular | segment-level | NOT_AVAILABLE | flag_for_review |
| material | Embankment material type (earthen, concrete, stone-faced) | categorical | identified | observed | static | segment-level | NOT_AVAILABLE | categorize_as_unknown |
| condition | Embankment condition (good, fair, poor) | categorical | identified | observed | irregular | segment-level | NOT_AVAILABLE | assess_from_visuals |
| elevation | Ground elevation from SRTM or local surveys | m | identified | observed | static | 30m (SRTM) | NOT_AVAILABLE | use_DEM_interpolation |
| local_slope | Local terrain slope within segment | ratio (m/m) | derived | derived | static | segment-level | DERIVABLE | compute_from_DEM |
| river_width | Width of river channel at segment | m | identified | observed | irregular | segment-level | NOT_AVAILABLE | use_historical_average |
| river_curvature | Curvature of river centerline (1/km) | 1/km | derived | derived | static | segment-level | DERIVABLE | compute_from_centerline |
| distance_to_river | Horizontal distance from segment point to river centerline | m | derived | derived | static | segment-level | DERIVABLE | compute_from_coordinates |
| floodplain_characteristics | Width, land use, connectivity to floodplain | categorical | identified | observed | static | segment-level | NOT_AVAILABLE | classify_from_terrain |
| soil_type | Soil type (clay, silt, sand, loam) | categorical | identified | observed | static | segment-level | NOT_AVAILABLE | assign_default |
| soil_moisture | Volumetric water content of soil | volumetric water content | identified | observed | daily | segment-level | NOT_AVAILABLE | use_default_or_nearest |
| erosion_indicator | Active erosion observed (yes/no/uncertain) | categorical | identified | observed | irregular | segment-level | NOT_AVAILABLE | assign_zero |
| sedimentation_indicator | Accretion/sedimentation observed (yes/no) | categorical | identified | observed | irregular | segment-level | NOT_AVAILABLE | assign_zero |
| historical_failure_count | Number of documented breach/failure events at segment | count | identified | observed | cumulative | segment-level | NOT_AVAILABLE | zero_if_unknown |
| historical_breach_distance | Distance to nearest historical breach (km) | km | identified | observed | cumulative | segment-level | NOT_AVAILABLE | zero_if_unknown |
| historical_flood_frequency | Historical flood occurrence frequency (events/year) | events/year | identified | observed | cumulative | segment-level | NOT_AVAILABLE | zero_if_unknown |

---

## Availability Classification Rules

Each feature is classified as one of four states. These rules are enforced by the `source_registry.py` and `ingestion.py` modules:

| Classification | When it applies |
|---|---|
| **AVAILABLE** | The feature is present in data that has been successfully ingested and validated (status = `ACTIVE` in source registry). |
| **DERIVABLE** | The feature is not yet in the ingested data, but it can be computed from other available observed features (e.g., `freeboard` = `embankment_height` - `river_level`; `water_level_change` = difference in successive river level readings). |
| **NOT_AVAILABLE** | The feature is identified as coming from a known source (status = `IDENTIFIED` in source registry), but no data file has been ingested yet. Once the data is ingested, it will become `AVAILABLE`. |
| **UNKNOWN** | The feature has no source registry entry and its availability cannot be determined from current configuration. |

---

## Updating This Document

This data dictionary is a living document. To update it:

1. **Add a new data source:** Update `configs/data_sources.yaml`, then run `scripts/audit_data.py` to re-classify features.
2. **Add a new feature:** Add to `configs/feature_registry.yaml` with all metadata fields.
3. **Change availability:** Modify the `availability` column based on whether data has been ingested.
4. **Change missing-data policy:** Update the policy string to match the project's validation rules.

Please do not modify the `meaning` or `unit` columns without corresponding changes to the data schema and source configurations.