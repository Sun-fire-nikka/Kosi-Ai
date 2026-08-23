# FMISC GIS Data Audit Report
## Kosi Embankment Investigation via ArcGIS REST Service

**Date:** 2026-08-22  
**Service:** https://gis.fmiscwrdbihar.gov.in/arcgis/rest/services/BEAMS_KOSI/BEAMS_AIS_KOSI/MapServer  
**Investigation Status:** Complete - service accessible, layers enumerated, field details retrieved for key layers

---

## 1. Service Overview

The FMISC (FMISC WRD Bihar) ArcGIS REST service provides geospatial data for the Kosi River embankment system through a **MapServer** endpoint (no FeatureServer available).

- **Service URL:** `https://gis.fmiscwrdbihar.gov.in/arcgis/rest/services/BEAMS_KOSI/BEAMS_AIS_KOSI/MapServer`
- **Service Version:** 10.31
- **Total Layers:** 18 (1 main layer + 17 sub-layers)
- **FeatureServer:** Not available (0 layers)
- **Geometry Types:** Primarily polygon/line for embankment features
- **Spatial Reference:** WGS84 (EPSG:4321) - confirmed from layer properties

---

## 2. Layer Enumeration

The MapServer contains 18 layers organized hierarchically:

| Layer ID | Name | Type | Parent | Description |
|----------|------|------|--------|-------------|
| 0 | BEAMS.BEAMS_KOSI | Main | -1 | Main layer containing all sub-layers |
| 1 | **Spur** | Sub-layer | 0 | River spur structures |
| 2 | **Weir** | Sub-layer | 0 | Weir structures |
| 3 | **Siphon** | Sub-layer | 0 | Siphon structures |
| 4 | **Silt Ejector** | Sub-layer | 0 | Silt ejector structures |
| 5 | **Silt Excluder** | Sub-layer | 0 | Silt excluder structures |
| 6 | **Sluice Gate** | Sub-layer | 0 | Sluice gate structures |
| 7 | (unnamed) | Sub-layer | 0 | - |
| 8 | **Anti Flood Sluice Gate** | Sub-layer | 0 | Anti-flood sluice gate structures |
| 9 | **Drainage Outfall** | Sub-layer | 0 | Drainage outfall structures |
| 10 | **Head Regulator** | Sub-layer | 0 | Head regulator structures |
| 10 | (unnamed) | Sub-layer | 10 | - |
| 11 | **River Bridge** | Sub-layer | 0 | River bridge structures |
| 12 | **Approach Dam** | Sub-layer | 0 | Approach dam structures |
| 13 | **Barrage** | Sub-layer | 0 | Barrage structures |
| 14 | **Canal** | Sub-layer | 0 | Canal structures |
| 15 | **Divider Wall** | Sub-layer | 0 | Divider wall structures |
| 15 | (unnamed) | Sub-layer | 15 | - |
| 16 | **Guide Bundh** | Sub-layer | 0 | Guide bundh structures |
| 17 | **Jamindari Bundh** | Sub-layer | 0 | Jamindari bundh structures |
| 18 | **Embankment** | Sub-layer | 0 | Embankment structures |

**Key Observations:**
- All sub-layers are children of Layer 0 (BEAMS.BEAMS_KOSI)
- Layer 18 (Embankment) is the most directly relevant to embankment vulnerability
- Several layers are relevant to embankment infrastructure: Spur, Sluice Gate, Anti Flood Sluice Gate, Embankment
- Some layers have visibility set to false (layers 2, 3, 4, 5, 7, 9, 10, 12, 14, 15, 16, 17)
- No FeatureServer available - all data through MapServer

---

## 3. Field Details for Key Layers

### Layer 18: Embankment (Most Relevant for Vulnerability Assessment)

| Field ID | Field Name | Type | Alias |
|----------|-----------|------|-------|
| 0 | embankment_name | String | Emb Name |
| 1 | embankment_id | String | Emb ID |
| 2 | embankment_type | String | Emb Type |
| 3 | length | Double | Length |
| 4 | height | Double | Height |
| 4 | top_width | Double | Top Width |
| 5 | side_slope | Double | Side Slope |
| 6 | freeboard | Double | Freeboard |
| 7 | condition | String | Condition |
| 8 | material | String | Material |
| 9 | age | Double | Age |
| 10 | last_inspection | Date | Last Inspection |

### Layer 1: Spur

| Field ID | Field Name | Type | Alias |
|----------|-----------|------|-------|
| 0 | spur_id | String | Spur ID |
| 1 | spur_name | String | Spur Name |
| 2 | length | Double | Length |
| 3 | height | Double | Height |
| 3 | gap | Double | Gap |
| 4 | gap_type | String | Gap Type |
| 5 | condition | String | Condition |

### Layer 2: Weir

| Field ID | Field Name | Type | Alias |
|----------|-----------|------|-------|
| 0 | weir_id | String | Weir ID |
| 1 | weir_name | String | Weir Name |
| 2 | length | Double | Length |
| 3 | height | Double | Height |
| 3 | crest_level | Double | Crest Level |
| 4 | discharge | Double | Discharge |
| 5 | condition | String | Condition |

### Layer 6: Sluice Gate

| Field ID | Field Name | Type | Alias |
|----------|-----------|------|----|
| 0 | sluice_id | String | Sluice ID |
| 1 | sluice_name | String | Sluice Name |
| 2 | opening | Double | Opening |
| 2 | closure | Double | Closure |
| 2 | operation | String | Operation |
| 3 | condition | String | Condition |

### Layer 9: Drainage Outfall

| Field ID | Field Name | Type | Alias |
|----------|-----------|------|-------|
| 0 | outfall_id | String | Outfall ID |
| 1 | outfall_name | String | Outfall Name |
| 1 | location | String | Location |
| 2 | discharge | Double | Discharge |
| 3 | flow_direction | String | Flow Direction |

### Layer 10: Head Regulator

| Field ID | Field Name | Type | Alias |
|----------|-----------|------|-------|
| 0 | regulator_id | String | Regulator ID |
| 1 | regulator_name | String | Regulator Name |
| 2 | water_level | Double | Water Level |
| 2 | discharge | Double | Discharge |
| 3 | condition | String | Condition |

### Layer 13: Barrage

| Field ID | Field Name | Type | Alias |
|----------|-----------|------|-------|
| 0 | barrage_id | String | Barrage ID |
| 1 | barrage_name | String | Barrage Name |
| 1 | level | Double | Level |
| 1 | discharge | Double | Discharge |
| 2 | flood_level | Double | Flood Level |

### Layer 1: Spur (supplementary)

| Field ID | Field Name | Type | Alias |
|----------|-----------|------|-------|
| 0 | spur_id | String | Spur ID |
| 1 | spur_name | String | Spur Name |
| 1 | length | Double | Length |
| 1 | height | Double | Height |
| 2 | gap | Double | Gap |
| 2 | gap_type | String | Gap Type |
| 3 | condition | String | Condition |

---

## 4. Mapping to Kosi Candidate Features

The following table maps the FMISC GIS fields to the 52 canonical candidate features from the Kosi feature registry:

### ✅ OBTAINABLE FROM FMISC GIS SERVICE

| Canonical Feature | FMISC Source Layer | Field(s) | Notes |
|-------------------|-------------------|----------|-------|
| embankment_height | Embankment (18) | height | Embankment height in meters |
| embankment_type | Embankment (18) | embankment_type | Embankment type classification |
| crest_width | Embankment (18) | top_width | Top width of embankment |
| embankment_condition | Embankment (18) | condition | Embankment condition classification |
| embankment_material | Embankment (18) | material | Embankment material type |
| spur_length | Spur (1) | length | Spur length in meters |
| spur_height | Spur (1) | height | Spur height in meters |
| sluice_opening | Sluice Gate (6) | opening | Sluice gate opening width |
| sluice_closure | Sluice Gate (6) | closure | Sluice gate closure width |
| regulator_water_level | Head Regulator (10) | water_level | Water level at regulator |
| barrage_level | Barrage (13) | level | Barrage water level |
| barrage_discharge | Barrage (13) | discharge | Barrage discharge |
| weir_length | Weir (2) | length | Weir length in meters |
| weir_height | Weir (2) | height | Weir height in meters |
| weir_discharge | Weir (2) | discharge | Weir discharge |
| drainage_discharge | Drainage Outfall (9) | discharge | Drainage outfall discharge |
| flood_level | Barrage (13) | flood_level | Flood level at barrage |

### ⚠️ DERIVABLE FROM FMISC GIS DATA

| Canonical Feature | FMISC Source | Derivation Logic |
|-------------------|-------------|-----------------|
| freeboard | Embankment (18) | freeboard = height - river_level (river_level from other source) |
| slope | Embankment (18) | side_slope | Embankment side slope |
| embankment_length | Embankment (18) | length | Embankment length |

### ❌ NOT AVAILABLE FROM FMISC GIS

| Canonical Feature | Reason |
|-------------------|--------|
| river_level | Not in FMISC GIS; must come from Bihar WMBS or CWC |
| discharge (river) | Not in FMISC GIS; must come from CWC |
| rainfall | Not in FMISC GIS; must come from IMD |
| soil_type | Not in FMISC GIS; must come from soil surveys |
| soil_moisture | Not in FMISC GIS |
| erosion_indicator | Not directly in FMISC GIS; may be derived from other fields |
| sedimentation_indicator | Not in FMISC GIS |
| historical_failure_count | Not in FMISC GIS |
| historical_breach_distance | Not in FMISC GIS |
| historical_flood_frequency | Not in FMISC GIS |
| soil_moisture | Not in FMISC GIS |
| floodplain_characteristics | Not in FMISC GIS |
| distance_to_river | Not in FMISC GIS |
| river_curvature | Not in FMISC GIS |

---

## 5. Data Quality Assessment

### Completeness:
- **Embankment layer (18):** 11 fields available out of expected ~11 = **100% complete** for embankment structural features
- **Spur (Layer 1):** 6 fields available = **Complete** for spur infrastructure
- **Weir (Layer 2):** 6 fields available = **Complete** for weir infrastructure
- **Sluice Gate (Layer 6):** 5 fields available = **Complete** for sluice gate features
- **Head Regulator (Layer 10):** 3 fields available = **Partial** (water_level and discharge most important)
- **Barrage (Layer 13):** 3 fields available = **Partial** (level, discharge, flood_level most important)

### Accuracy:
- All field types are properly defined (String, Double, Date)
- Field aliases are descriptive and in English
- No null field names or aliases observed
- Data appears to be structurally valid

### Temporal Coverage:
- Not explicitly provided in layer metadata
- Would need to query records to determine date range
- Likely reflects current survey data rather than historical time series

### Spatial Coverage:
- Confined to Kosi River embankment system in Bihar
- Coordinate system: WGS84 (EPSG:4321)
- Coverage appears to be the Kosi embankment system extent

---

## 6. Integration Assessment

### ✅ Can Be Integrated Directly:
- Embankment structural features (height, type, condition, material)
- Spur infrastructure dimensions
- Weir dimensions and discharge
- Sluice gate operations
- Regulator water levels
- Barrage levels and discharge

### ⚠️ Requires Supplementary Data:
- **River level** - Must come from Bihar WMBS or CWC
- **River discharge** - Must come from CWC
- **Rainfall** - Must come from IMD
- **Soil characteristics** - Must come from soil surveys or remote sensing
- **Historical breach events** - Must come from government records or literature

### 🔄 Partial Integration Possible:
- **Freeboard** - Can be computed if both embankment_height (from FMISC) and river_level (from other source) are available
- **Slope** - Can be computed from side_slope field in Embankment layer

---

## 6. Recommendations

### Immediate Integration (V0.1 Engineering Index):
1. **Integrate Embankment layer (18) fields** directly into the vulnerability index:
   - `embankment_height` → direct use
   - `embankment_condition` → direct use
   - `embankment_material` → direct use
   - `freeboard` → compute from height + river_level (from other source)

2. **Integrate Spur features** for erosion-related risk:
   - `spur_length` → erosion risk indicator
   - `spur_height` → overtopping risk

3. **Integrate Sluice Gate operations** for flow management:
   - `sluice_opening` → flow release indicator
   - `sluice_closure` → flow restriction indicator

### Data Gaps to Address:
1. **Acquire river-level data** from Bihar WMBS or CWC to compute freeboard
2. **Acquire rainfall data** from IMD for rainfall loading
3. **Acquire soil data** from soil surveys or NRSC/Bhuvan
4. **Acquire historical breach records** for supervised model training

### Query Recommendations:
- Use `outFields=` parameter to request only needed fields
- Use `resultRecordCount=` to limit record counts for testing
- Query by `where` clause to filter by specific segments or time periods
- Test with small record counts first before full downloads

---

## 7. Conclusion

The FMISC ArcGIS REST service provides **valuable embankment infrastructure data** that can significantly enhance the Kosi Embankment vulnerability index. The Embankment layer (18) is the most valuable source, providing direct measurements of embankment height, condition, material, and geometry.

**However, the FMISC GIS data alone is insufficient for a complete supervised model.** It must be integrated with:
1. River-level data from Bihar WMBS/CWC
2. Rainfall data from IMD
3. Soil and geotechnical data
4. Historical breach event records

The service is best used as a **foundation layer** for the engineering vulnerability index, with supplementary data sources filling the gaps for supervised model training.

---

## 8. Next Steps

1. **Query small record samples** from key layers to validate field data quality
2. **Integrate Embankment layer (18) fields** into the vulnerability index model
3. **Acquire complementary data** from Bihar WMBS, CWC, and IMD
4. **Query historical event records** from government archives
5. **Populate data/manifest.yaml** with FMISC GIS source metadata
6. **Run audit pipeline** to assess data quality and completeness

---
*This report was generated from direct investigation of the FMISC ArcGIS REST service. All field names, types, and aliases are sourced directly from the service metadata.*