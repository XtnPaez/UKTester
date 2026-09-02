# Data Preparation

The R preprocessing stage is handled by `src/r/dashboard/run/01_preprocess.R`.

This script prepares the three core inputs needed by the travel-time stage:

- district boundaries
- healthcare facilities
- WorldPop population subgroup rasters

## Before running

Ensure you have:

1. Installed the R dependencies described in [01 — Installation](01-installation.md).
2. Updated `src/r/dashboard/config/config.yaml` for your country and data sources.
3. Confirmed that any local boundary or facility files referenced in the config exist.

## What `01_preprocess.R` does

The preprocessing script runs these steps in order:

1. Read `src/r/dashboard/config/config.yaml`.
2. Load district boundaries from a local file or download them from OpenStreetMap.
3. Load healthcare facilities from a local file or download them from a configured URL.
4. Clean and standardise the facility data.
5. Download or reuse WorldPop age-sex population inputs.
6. Create subgroup rasters and a combined `geodemographics.tif` raster stack.

## Data requirements
There are four datasets required to run the pipeline:

|Name |Source |URL |Type |Licence |
|:-----|:-----|:-----|:-----|:-----|
|Administrative boundaries |[OpenStreetMap (OSM)](ttps://wiki.openstreetmap.org/wiki/Overpass_API) |[Link](https://overpass-api.de/) |`.GeoJSON`  |[ODbL](https://opendatacommons.org/licenses/odbl/) |
|Healthcare facilities |[healthsites.io](https://healthsites.io/) | [Link](https://data.humdata.org/dataset) |`.csv` |[Open Database License](https://opendatacommons.org/licenses/odbl/) |
|Population estimates |[WorldPop](https://www.worldpop.org/) | [Link](https://www.worldpop.org/datacatalog/) |`.tif` |[Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0) |
|Road network |[OpenStreetMap (OSM)](ttps://wiki.openstreetmap.org/wiki/Overpass_API) | [Link](https://overpass-api.de/) |`.pbf` |[ODbL](https://opendatacommons.org/licenses/odbl/) |


## 1. Administrative boundaries

Administrative boundaries are controlled by these config fields:

```yaml
districts_filepath:
district_name_column:
admin_level:
admin_level_name:
```

Two input modes are supported:

- Local file: set `districts_filepath` to a `.shp`, `.gpkg`, `.geojson`, or `.json` file.
- OpenStreetMap: leave `districts_filepath` blank and provide `country` plus a suitable `admin_level`.

If `district_name_column` is blank for a local file, the first column in the boundary layer is used as the administrative unit label.

The `admin_level_name` is used in the dashboard UI to label the administrative level (for example, `district`).

The script writes the processed boundaries to:

`data/boundaries/<country>_districts.geojson`

## 2. Healthcare facilities

Healthcare facilities are controlled by:

```yaml
facility_list_filepath:
facility_list_url:
```

Two input modes are supported:

- Local file: set `facility_list_filepath`.
- Remote file: leave `facility_list_filepath` blank and set `facility_list_url`.

Supported formats depend on the source loader and currently include:

- CSV
- Excel (`.xlsx`)

### Flexible source — healthsites.io via HDX

The data landscape for health facility datasets varies from country to country. In many cases, a publicly available register maintained by the relevant authorities, such as a Ministry of Health, is likely to provide the most reliable source.

A country-owned dataset should usually be the first choice where one is available and of reasonable quality. In practice, that means either:

- downloading the source file yourself and pointing `facility_list_filepath` at it, or
- setting `facility_list_url` to a direct downloadable file URL when a stable endpoint exists.

In an effort to create a generalised tool, we have identified the data from [healthsites.io](https://healthsites.io/) as a reasonable data source to experiment with initially. The advantages are that data is available for most countries around the world and is publicly downloadable from the [Humanitarian Data Exchange (HDX)](https://data.humdata.org/) platform. The data can also be explored within [healthsites.io](https://healthsites.io/) to check for suitability before interacting with code.

In the current R pipeline, Healthsites data is not fetched automatically. The typical approach is to download the file manually and set `facility_list_filepath` in `config.yaml`.

**Suggested steps:**

1. Visit the [Humanitarian Data Exchange](https://data.humdata.org/dataset) (HDX) website
2. Enter `<country> healthsites` in the search bar
3. Select the dataset called 'Global Healthsites Mapping Project'
4. Navigate to the bottom of the next page and select `<country>-healthsites-csv` to download the data.
5. Set `facility_list_filepath` to the downloaded file.

Healthsites-style CSV inputs are supported by the current R cleaning code when fields such as `x`, `y`, and `osm_id` are present.

### Bespoke health facility datasets

If using a country-specific dataset, it will need to be processed into the format the R pipeline expects.

**Required columns** (facilities without usable coordinates are silently dropped):

- `lon` and `lat`, or `longitude` and `latitude` columns — usable point coordinates for each facility.

**Recommended columns** (not required, but enable richer outputs and dashboard filtering):

- `id` — stable unique identifier for each facility. If absent, a sequential integer is generated automatically, but this will not be consistent across runs.
- `name` — e.g. "North-East Hospital"
- `type` — e.g. "Hospital", "Clinic", "Pharmacy"
- `ownership` — e.g. "Government", "Private"

These can provide useful additional context, but they are not essential for the pipeline to function.

The pipeline expects the following columns. Only lon/lat are required; all others are optional but recommended:
|Column |Description |Data type |Example |Required |
|:-----|:-----|:-----|:-----|:-----|
|id |Unique id |String |LL040529 |No |
|lon |Longitude |Double |33.78512 |Yes |
|lat |Latitude |Double |-13.97639 |Yes |
|name |Name of healthcare facility |String |Kamuzu Central hospital |No |
|type |Type of healthcare facility |String |Hospital |No |
|ownership |Ownership of healthcare facility |String |Government |No |

### Data quality

**NOTE:** there is no standardised approach to quality assure the health facility data (regardless of source) within the codebase. The responsibility rests with the user to suitably quality assure any health facility data used for this analysis — preferably using local knowledge — and to understand its limitations, biases and implications. Known issues to look out for:

- Missing records
- Incorrectly located facilities
- Duplicate entries
- Implausible counts or distributions by type

The script writes the processed facilities to:

`data/poi/<country>_healthcare_facilities.csv`

## 3. Population data

Population inputs are controlled by:

```yaml
population_filepath:
worldpop:
    year: 2025
    release: "R2025A"
    version: "v1"
```

Two modes are supported:

- Automatic download: leave `population_filepath` blank and the script will download the WorldPop zip file for the configured country, year, release, and version.
- Local zip file: set `population_filepath` to an existing WorldPop zip file.

Population estimates for different demographic groups can be downloaded from [WorldPop](https://hub.worldpop.org/geodata/listing?id=138). Enter the country of interest in the search bar and select a year. 

Click the corresponding 'Data & Resources' and download the `.zip` file from the green button on the subsequent page. The `.zip` file will contain population estimates for different demographic groups at 100m<sup>2</sup> resolution in `.tif` format. Please provide a link to the `.zip` file in the `config.yaml` file.

The preprocessing step then:

- extracts the WorldPop files into `data/raw/`
- creates subgroup rasters in `data/population/<iso3>_agesex_<year>/`
- creates a combined `geodemographics.tif` stack used later by `02_ttm.R`

Generated rasters include:

- `females.tif`
- `males.tif`
- `children_(0-14).tif`
- `working-age_adults_(15-64).tif`
- `older_people_(65+).tif`
- `women_of_reproductive_age_(15-49).tif`
- `total_population.tif`
- `geodemographics.tif`

## 4. Road network
Road network data is provided by [OpenStreetMap](https://wiki.openstreetmap.org/wiki/Map_features#Highway). The data is downloaded programatically in the pipeline so there is no requirement to download the data manually.


## 5. Run the script

From the repository root, first load the local dashboard package in your R session:

```r
devtools::load_all(here::here("src", "r", "dashboard"), quiet = TRUE)
```

Then run the preprocessing script:

```r
source(here::here("src", "r", "dashboard", "run", "01_preprocess.R"))
```

If you prefer to run it non-interactively from the command line, use:

```bash
Rscript src/r/dashboard/run/01_preprocess.R
```

To run the full pipeline end-to-end (preprocessing, travel-time, and dashboard), use `_run_all.R` from the repository root instead:

```r
source(here::here("src", "r", "dashboard", "_run_all.R"))
```

## Validate outputs

After the script completes, confirm these files exist:

- `data/boundaries/<country>_districts.geojson`
- `data/poi/<country>_healthcare_facilities.csv`
- `data/population/<iso3>_agesex_<year>/geodemographics.tif`

You should also expect to see extracted WorldPop source files under `data/raw/`.

## Common issues

- If boundary download fails, provide a local boundary file via `districts_filepath`.
- If facility download fails, download the file manually and point `facility_list_filepath` at it.
- If WorldPop download fails, provide the local zip file path via `population_filepath`.
- If the wrong district names are used from a local boundary file, set `district_name_column` explicitly.

This stage does not build the transport network yet. That happens in `02_ttm.R`.

## Next step

→ [04 — Travel time analysis](04-travel-time-analysis.md)
