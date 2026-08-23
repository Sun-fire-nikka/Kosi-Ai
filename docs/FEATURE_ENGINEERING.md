# Feature Engineering — V0.1

## Real observed inputs
observed_water_level · danger_level · HFL · warning_level (3/23 matched) · station/date identifiers

## Derived (formulas recorded per record)
- water_level_minus_warning = observed_water_level - warning_level
- water_level_minus_danger = observed_water_level - danger_level
- water_level_minus_HFL = observed_water_level - HFL
- danger_margin = -water_level_minus_danger ; HFL_margin analogous
- danger_exceedance_ratio = observed/danger (undefined when danger==0)
- hydrological_stress = clip((WL - low)/(HFL - low),0,1)*100, low=warning||danger [DERIVED]

## Explicitly NOT features
station names (identifiers only); danger level is a river threshold, never embankment height.

## Unavailable (never imputed)
rainfall, gauge-linked discharge, soil, sediment, embankment geometry/condition, hourly forecasts.

## Synthetic-only columns (pipeline validation)
52-feature conceptual schema realised as 30-column synthetic parquet: hydrology, geometry, soil, historical-count fields — SIMULATED status, never mixed with real observations.
