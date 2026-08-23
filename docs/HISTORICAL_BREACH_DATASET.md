# Historical Breach Dataset Documentation

## Dataset Overview

- **Total records audited**: 32
- **Unique breach events**: 9 (8 breach + 1 major breach)
- **Unique major flood events**: 6 (year-only dates)
- **Unique flood events**: 10 (date ranges 2009-2022)
- **High water events**: 4 (2008 CGC gauge readings)
- **Embankment failure events**: 1 (1971)
- **Other events**: 2 (2008 Kusaha major breach, 2025 Sup-Sarahsa-Madhepura flood)

### Event Type Distribution

| Event Type | Count | Percentage |
|---|---|---|
| Breach | 8 | 25.0% |
| Major Breach | 1 | 3.1% |
| Embankment Failure | 1 | 3.1% |
| High Water / High Flood | 4 | 12.5% |
| Major Flood | 6 | 18.8% |
| Flood | 10 | 31.3% |
| Other | 2 | 6.3% |

### Date Coverage

| Date Precision | Count | Percentage |
|---|---|---|
| Exact date (day/month) | 21 | 65.6% |
| Year only | 11 | 34.4% |
| Date range (start-end) | 14 | 43.8%* |
| **Note**: Some records have both exact dates and ranges |

### Location Coverage

| Location Precision | Count | Percentage |
|---|---|---|
| Specific village/town | 10 | 31.3% |
| Kosi basin / Bihar | 14 | 43.8% |
| No specific location | 8 | 25.0% |

### Hydrological Measurements

| Measurement Type | Count | Percentage |
|---|---|---|
| Peak discharge (m³/s) | 1 | 3.1% |
| Embankment length (km) | 1 | 3.1% |
| Repair cost (₹ crore) | 1 | 3.1% |
| Water level (m) | 3 | 9.4% |
| No measurements | 28 | 87.5% |

### Source Organizations

| Organization | Records | Percentage |
|---|---|---|
| NRSC/ISRO Flood-Affected Area Atlas | 6 | 18.8% |
| CWC Flood Forecasting Reports | 3 | 9.4% |
| Research literature | 3 | 9.4% |
| IMD/NRSC | 1 | 3.1% |
| Parliament/CWC record | 1 | 3.1% |
| Research/WRD | 2 | 6.3% |
| Lok Sabha answer / Bihar Govt | 1 | 3.1% |
| Ministry of Jal Shakti | 1 | 3.1% |
| NRSC/ISRO rapid mapping | 1 | 3.1% |
| Historical breach timeline | 1 | 3.1% |
| Historical breach timeline (MDPI) | 1 | 3.1% |

### Duplicate / Related Records

- **ID 1 (1963 Dalwa) and ID 11 (1963 Kosi basin)**: Both reference the 1963 breach event; ID 11 is a basin-level associated record
- **ID 3 (1968 Jamalpur) and ID 13 (1984 Kosi basin)**: Both reference breach events; ID 13 is a associated flood-year record
- **IDs 10-16 (1954-1995 Major Floods)**: All are "Major flood" year-only events; likely related Kosi flood years
- **IDs 20-30 (2009-2022 Floods)**: All NRSC Flood-Affected Area Atlas records; spatially overlapping Kosi basin floods
- **IDs 17-19 (2008 High Water)**: All 2008 CWC gauge readings; same flood season, different locations (Basua/Balua/Kursela)
- **ID 31 (2024 Bhubhaul) and ID 32 (2025 Sup-Sarahsa-Madhepura)**: Consecutive years, both Kosi region, different event types (breach vs flood)

### Exact-Date Events

21 records have exact day/month dates (e.g., 20-Aug, 06-Oct, 12-Aug):
- Most common month: August (10 events)
- Most common day: 20th (5 events: IDs 1, 4, 5, 19, 31)
- Monsoon season concentration: June through October

### Usable Locations

10 events have specific village/town locations:
- Dalwa, Nepal (1963)
- Kunauli, Bihar/Nepal border area (1967)
- Jamalpur, Darbhanga (1968)
- Bhatania, near Supaul (1971)
- Bahuarawa, Saharsa (1980)
- Ghoghepur / Gandaul-Samani, Saharsa (1987)
- Joginia, Nepal (1991)
- Hempur/Navhatta, Saharsa (1984)
- Bhubhaul, Kiratpur, Darbhanga (2024)
- Kusaha, Nepal (2008, major breach)

### Events with Hydrological Information

Only 3 of 32 records (9.4%) contain hydrological measurements:
- **ID 3 (1968 Jamalpur)**: peak discharge ~25,853-25,900 m³/s
- **ID 5 (1980 Bahuarawa)**: embankment eroded over ~2 km
- **ID 31 (2024 Bhubhaul)**: 220 m embankment damaged, ₹40.2235 crore repair cost

### Can Supervised Breach Model Be Trained?

**CAN_SUPERVISED_BREACH_MODEL_BE_TRAINED = NO**

Justification:
1. **Insufficient event-linked hydrological data**: Only 2 of 9 breach events (22%) have any hydrological measurements (discharge, embankment dimensions, water levels)
2. **No consecutive observations**: No dataset provides before/after or pre/post-breach water level series for the same location
3. **Sparse location coverage**: Only 10/32 records (31%) have specific village/town locations; the rest use "Kosi basin / Bihar" as a generic location
4. **Date precision limitation**: 11/32 records (34%) have year-only dates; 21/32 (66%) have exact dates but from different years spanning 71 years
5. **Heterogeneous source types**: Records come from 11 different source organizations with varying quality and formats
6. **No standardized breach definition**: Events are classified as breach, major breach, flood, high water, etc. with no unified metric
7. **No ground truth for model validation**: No verified breach/no-breach pairs with associated hydrological conditions suitable for supervised training

**Conclusion**: The dataset is scientifically useful for:
- Engineering vulnerability scoring
- Historical event similarity analysis
- Anomaly detection framework design
- Scenario simulation parameter ranges
- But NOT for supervised breach prediction model training

**Recommendation**: Use for engineering-informed vulnerability model (V0.1), not as training data for a supervised breach classifier. The dataset should be used for event reconstruction interfaces and historical evidence collection, with the explicit understanding that reconstructed samples cannot be inserted into a supervised pipeline without additional event-linked hydrological data.

## Data Artifacts Created

- `data/processed/historical_events/kosi_historical_events.parquet` - Full 32-record audit
- `data/processed/historical_events/kosi_breach_events.parquet` - 9 breach events
- `data/processed/historical_events/kosi_flood_events.parquet` - 16 flood events (major + flood)
- `data/manifest.yaml` - Updated provenance for historical event dataset

## Key Limitations (for MODEL_LIMITATIONS.md)

1. Only 2 of 9 breach events (22%) have hydrological measurements suitable for model features
2. 11 of 32 records (34%) have year-only dates, preventing precise event timing
3. 8 of 32 records (25%) lack specific locations, limiting spatial modeling
4. No consecutive observation pairs exist for rate-of-change calculations
5. 71-year span (1954-2025) with evolving embankment standards and flood management practices
6. No verified breach/no-breach pairs with associated hydrological thresholds
7. Dataset should be used for engineering vulnerability assessment, not supervised breach prediction