# Travel Time Analysis

Travel time estimation is carried out by `src/r/dashboard/run/02_ttm.R`. For each facility type, it computes the travel time from every populated grid cell to the closest facility along the road network.

## Before running

Ensure you have completed the data preparation step and the following output files exist:

- `data/boundaries/<country>_districts.geojson`
- `data/poi/<country>_healthcare_facilities.csv`
- `data/population/<iso3>_agesex_<year>/geodemographics.tif`

See [03 — Data preparation](03-data-preparation.md).

## What `02_ttm.R` does

The script runs these steps in order:

1. Load districts and healthcare facilities produced by `01_preprocess.R`.
2. Convert the population raster to points.
3. Assign each population point to a district using the method set in config.
4. Download the country OSM PBF file from Geofabrik (skipped if already present).
5. Build the r5r transport network from the OSM data.
6. For each facility type, compute the travel-time matrix and find the closest facility per population point.
7. Write the results as CSV and Parquet.

## Run the script

From an R session in the repository root, first load the local dashboard package:

```r
devtools::load_all(here::here("src", "r", "dashboard"), quiet = TRUE)
```

Then run the travel-time script:

```r
source(here::here("src", "r", "dashboard", "run", "02_ttm.R"))
```

Or non-interactively from the command line:

```bash
Rscript src/r/dashboard/run/02_ttm.R
```

To run the full pipeline end-to-end (preprocessing, travel-time, and dashboard), use `_run_all.R` from the repository root instead:

```r
source(here::here("src", "r", "dashboard", "_run_all.R"))
```

## Outputs

Results are written to `data/ttm/`:

- `data/ttm/<country>_closest_times.csv`
- `data/ttm/<country>_closest_times.parquet`

Each row represents a population point with its closest facility, travel time, and facility type. The Parquet file is used directly by the dashboard.

Output columns include:

| Column | Description |
| --- | --- |
| `id` | Population point identifier |
| `lon`, `lat` | Coordinates of the population point |
| `district` | Assigned district name |
| `population` | Population count at the grid cell |
| `facility_type` | Type of the closest facility |
| `from_id` | ID of the closest facility |
| `travel_time_p50` | Median travel time in minutes to the closest facility |

## Network build

The OSM road network is downloaded automatically from [Geofabrik](https://www.geofabrik.de/) and saved to `data/network/<country>/`. Subsequent runs reuse the existing file unless `overwrite = TRUE` is set in the `download_geofabrik_pbf()` call.

The r5r network is built from the PBF file each run. This step can take several minutes depending on country size.

## Common issues

- If the r5r network build fails with a Java memory error, increase `java.parameters` before running.
- If no travel times are returned for a facility type, check that facilities of that type have coordinates within the network extent.
- If the Geofabrik download fails, download the PBF manually from [download.geofabrik.de](https://download.geofabrik.de/) and place it in `data/network/<country>/`.

## Next step

→ [05 — Dashboard](05-dashboard.md)
