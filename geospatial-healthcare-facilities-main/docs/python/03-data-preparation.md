# Data Preparation

The script `src/healthcare_accessibility/data_preparation.py` sources and processes all required input data into the correct format for travel time analysis. It automatically acquires OSM road data, WorldPop population grids, and administrative boundaries. Health facility data must be supplied manually.

## Before running

Ensure you have:

1. Activated the `hc-mapping` conda environment.
2. Set `country` and `analysis_crs` in `configs/config.yaml` (see [02 — Configuration](02-configuration.md)).
3. Placed health facility data at the expected path (see section 4 below).

## 1. OSM road network

OSM data is downloaded programmatically from [Geofabrik](https://www.geofabrik.de/) into `data/<country>/raw_data/`.

For new countries, the `country_continent_dict` in `src/healthcare_accessibility/data_preparation.py` must be updated with the country name and its continent before the download will work:

```python
country_continent_dict = {
    "Malawi": "africa",
    "Rwanda": "africa",
    "Switzerland": "europe",
    "Nepal": "asia",
    "Bangladesh": "asia",
}
```

## 2. Population data

The default WorldPop data downloaded is the `v1` release of `R2025A` for the year 2025. Release settings are controlled in `define_wp_release_version` inside `src/healthcare_accessibility/data_processing_funcs.py`.

To change the year or release, update the dictionary:

```python
wp_release_details = {
    "wp_population_data_year": "2026",
    "wp_data_release": "R2025A",
    "wp_data_version": "v1",
}
```

At the time of writing, R2025A v1 was the latest available for both [aggregate population counts](https://hub.worldpop.org/geodata/listing?id=136) and [age-sex population](https://hub.worldpop.org/geodata/listing?id=139). Newer releases may be available — check the WorldPop Hub before running.

If the automatic download fails, retrieve the files manually from the links above and place them in `data/<country>/raw_data/population_data/`.

![WorldPop file structure example](images/worldpop-file-structure.png)

## 3. Administrative boundaries

ADM1 and ADM2 boundaries are downloaded automatically from [geoBoundaries.org](https://www.geoboundaries.org).

If the download fails, retrieve them manually from the [country downloads page](https://www.geoboundaries.org/countryDownloads.html) and place the files in:

`data/<country>/raw_data/admin_boundary_geom/`

![Admin boundary file structure example](images/admin-boundary-file-structure.png)

## 4. Health facility data (manual step)

Automatic acquisition of health facility data is not supported. The file must be placed manually before running the script.

Expected path:

`data/<country-lower>/raw_data/health_facility_data/<country-lower>.geojson`

Example for Nepal:

`data/nepal/raw_data/health_facility_data/nepal.geojson`

### Flexible source — healthsites.io via HDX

The data landscape for health facility datasets varies from country to country. In many cases, a publicly available register maintained by the relevant authorities (e.g. a national Ministry of Health) is likely to provide the most reliable source.

In an effort to create a generalised tool, we have identified the data from [healthsites.io](https://healthsites.io/) as a reasonable data source to experiment with initially. The advantages are that data is available for most countries around the world and is publicly downloadable from the [Humanitarian Data Exchange (HDX)](https://data.humdata.org/) platform. The data can also be explored within [healthsites.io](https://healthsites.io/) to check for suitability before interacting with code.

**Steps to download:**

1. Visit [HDX](https://data.humdata.org/).
2. Search for `<country> healthsites`.
3. Select the dataset tagged "Global Healthsites Mapping Project" (see screenshots below).

![HDX search result example](images/hdx-healthsites-search-result.png)

4. Download the GeoJSON resource (e.g. `<country>-healthsites-geojson`).

![HDX GeoJSON download example](images/hdx-healthsites-geojson-download.png)

5. Copy it to the expected path above.

### Bespoke health facility datasets

If using a country-specific dataset, it will need to be processed into the format the pipeline expects.

**Required columns** (the presence of these two columns is essential for the pipeline to function):

- `id` — unique identifier for each facility
- `geometry` — point geometry (can be derived from lat/lon using geopandas `points_from_xy`)


**Recommended columns** (not required, but enable richer dashboard filtering):

- `facility_name` — e.g. "North-East Hospital"
- `facility_type` — e.g. "Hospital", "Clinic", "Pharmacy"
- `facility_ownership` — e.g. "Government", "Private"

These can provide interesting insight, but they are not essential for the pipeline to function.

### Data quality

**NOTE:** there is no standardised approach to quality assure the health facility data (regardless of source) within the codebase. The responsibility rests with the user to suitably quality assure any health facility data used for this analysis — preferably using local knowledge — and to understand its limitations, biases and implications. Known issues to look out for:

- Missing records
- Incorrectly located facilities
- Duplicate entries
- Implausible counts or distributions by type

## 5. Run the script

From the repository root:

```bash
python src/healthcare_accessibility/data_preparation.py
```

## Validate outputs

After the script completes, confirm these files exist:

- `data/<country>/raw_data/<country>-latest.osm.pbf`
- `data/<country>/processed_data/master_population_grid_data.gpkg`
- `data/<country>/processed_data/healthcare_facility_data.gpkg`
- `data/<country>/raw_data/admin_boundary_geom/<ISO3>_ADM1_geoboundaries.geojson`
- `data/<country>/raw_data/admin_boundary_geom/<ISO3>_ADM2_geoboundaries.geojson`

## Next step

→ [04 — Travel time analysis](04-travel-time-analysis.md)
