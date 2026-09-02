# Configuration

All R pipeline settings are read from `src/r/dashboard/config/config.yaml`.

Update this file before running:

- `src/r/dashboard/run/01_preprocess.R`
- `src/r/dashboard/run/02_ttm.R`

## Required settings

### Country name

Set `country` to the full English name of your target country:

```yaml
country: Malawi
```

This value is used to:

- resolve country codes for WorldPop and Geofabrik downloads
- name output files such as `<country>_districts.geojson` and `<country>_closest_times.csv`

### Coordinate reference system

Set `crs` to the output CRS used for point coordinates and saved boundary layers.

```yaml
crs: 4326
```

`4326` (WGS84 lon/lat) is the default and is recommended unless you have a specific reason to export in another CRS.

## Input settings

### District boundaries

You can provide local boundaries or download them from OpenStreetMap.

```yaml
## Boundaries
### Local filepath to the boundary file for the country
districts_filepath:
district_name_column:

### If no boundary files added boundaries are pulled from OpenStreetMap
admin_level:
admin_level_name:
```

How these fields behave:

- `districts_filepath`: if set, boundaries are read from this local file.
- `district_name_column`: optional when using a local file. If left blank, the first column is used for the area names.
- `admin_level`: used only when `districts_filepath` is not provided and boundaries are downloaded from OpenStreetMap. OpenStreetMap admin levels vary by country. For help selecting the correct admin level see the [OpenStreetMap wiki](https://wiki.openstreetmap.org/wiki/Key:admin_level).
- `admin_level_name`: display label used in the dashboard UI (for example, `district`).

### Healthcare facilities

Provide either a local file path or a URL.

```yaml
facility_list_filepath:
facility_list_url: "https://..."
```

Behavior:

- If `facility_list_filepath` is set, that file is used.
- Otherwise, if `facility_list_url` is set, the file is downloaded and processed.
- If both are empty, preprocessing will fail.

> For guidance on sourcing and downloading facility data, including expected column structure, see [03 — Data preparation: Healthcare facilities](03-data-preparation.md#2-healthcare-facilities).

### Population input (WorldPop)

If `population_filepath` is blank, the pipeline will download WorldPop data using the `worldpop` settings.

```yaml
population_filepath:
worldpop:
  year: 2025
  release: "R2025A"
  version: "v1"
```

Notes:

- `release` and `version` must match an available WorldPop directory layout.
- If you already have the WorldPop zip file, set `population_filepath` to skip download.

> For guidance on downloading WorldPop data, see [03 — Data preparation: Population data](03-data-preparation.md#3-population-data).

## Processing settings

### District assignment method

`02_ttm.R` assigns a district to each population grid cell before travel-time analysis.

As some grid cells may overlap multiple districts, you can choose how to resolve ambiguous assignments.

```yaml
boundary_assign_method: "zonal"
```

Supported options:

- `zonal`: Recommended. Resolves ambiguous boundary cells by assigning them to the district with the largest area overlap.
- `raster`: Resolves ambiguous boundary cells by assigning them to the district that contains the centroid of the grid cell. This is faster than `zonal` but may produce less accurate results so is only recommended to be used for testing.
- any other value falls back to a direct spatial join method.

### Transport mode

Default is `"BICYCLE"`. Set this in `src/r/dashboard/config/config.yaml`:

```yaml
travel_time:
	mode: "BICYCLE"
```

This tool currently only supports `"WALK"` and `"BICYCLE"` modes.

### `max_travel_time`

Sets the upper limit at which travel times are returned. Any routes beyond this threshold are excluded. Default is `167` minutes.

- Increasing this value captures more origin-destination pairs but increases runtime and output file size.
- Decreasing it risks excluding journeys that fall within accessibility thresholds of interest.

At 167 minutes, approximate maximum travel distances are:

- Bicycle: ~33 km
- Walking: ~10 km

### `n_threads`

The number of parallel threads used by r5r for travel-time computation. Set to `4` as default. Adjust based on available CPU cores.

### Java memory

The script sets Java heap memory to 2 GB before building the network:

```yaml
r5r:
  java_memory: 2  # Java memory allocation for r5r. Defaults to 2GB
```

Increase this if the network build fails with an out-of-memory error.

## Example config

```yaml
country: "Malawi"
crs: 4326

districts_filepath: "path/to/malawi_boundaries.geojson"
district_name_column:
admin_level:
admin_level_name:

facility_list_filepath: "path/to/malawi_facilities.geojson"
facility_list_url:

population_filepath:
worldpop:
  year: 2025
  release: "R2025A"
  version: "v1"

boundary_assign_method: "zonal"

travel_time:
  mode: "BICYCLE"
  max_travel_time_mins: 167

r5r:
  n_threads: 4
  java_memory: 2
```

## Next step

→ [03 — Data preparation](03-data-preparation.md)
