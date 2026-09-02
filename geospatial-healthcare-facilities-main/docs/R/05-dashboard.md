# Dashboard

This guide explains how to render the Quarto dashboard (`hcf-dashboard.qmd`) and run it interactively via Shiny for R.

The dashboard visualises healthcare accessibility metrics interactively. It is built using a Quarto `.qmd` file backed by Shiny for R, and is served locally via `quarto preview` or `shiny::runApp()`.

## Prerequisites

### R environment

The dashboard requires the R dependencies from [01 — Installation](01-installation.md). Install them using:

```r
install.packages("devtools")
devtools::install_deps("src/r/dashboard", dependencies = TRUE)
```

### Quarto

Quarto must be installed on your system. Download the latest release from [quarto.org](https://quarto.org/docs/get-started/).

Verify your installation:

```bash
quarto --version
```

### Required data outputs

The dashboard reads pre-computed travel-time data and geospatial inputs. Before rendering, you must have completed the full analysis pipeline so that the following files exist for your configured country (e.g. `Malawi`):

```text
data/ttm/<country>_closest_times.parquet
data/boundaries/<country>_districts.geojson
data/poi/<country>_healthcare_facilities.csv
data/population/<iso3>_agesex_<year>/geodemographics.tif
```

Refer to [03 — Data preparation](03-data-preparation.md) and [04 — Travel time analysis](04-travel-time-analysis.md) for instructions on generating these files.

### Configuration

Open `src/r/dashboard/config/config.yaml` and confirm the `country` field matches the context you want to visualise:

```yaml
country: Malawi
```

All file paths in the dashboard are derived from this value. No changes to the `.qmd` file itself are required.

## Running the full pipeline with `_run_all.R`

If you have not yet run the preprocessing and travel-time stages, the simplest approach is to run the full pipeline end-to-end from the repository root:

```r
source(here::here("src", "r", "dashboard", "_run_all.R"))
```

This runs `01_preprocess.R`, `02_ttm.R`, and then launches the dashboard automatically. If the pipeline has already been run and you only want to launch the dashboard, follow the steps below.

## Step 1 — Render and preview the dashboard

From a terminal in the repository root, run the following Quarto command to render and preview the dashboard:

```bash
quarto preview src/r/dashboard/hcf-dashboard.qmd
```

This will:

- Render the Quarto dashboard file
- Start a local Shiny server
- Open the dashboard in your default browser

The dashboard is now running interactively and will hot-reload if you make changes to the `.qmd` file.

## Interacting with the dashboard

Once open in a browser, the dashboard provides controls to filter and explore healthcare accessibility metrics:

| Control | Description |
| --- | --- |
| District selector | Filter to a specific district or view the country level |
| Facility type filter | Select one or more healthcare facility types to restrict the map and summary statistics |
| Distance band (km) | Set the distance threshold (5, 8, or 10 km) used to classify population as "within reach" |
| Demographic selector | View accessibility metrics for the total population or specific demographic groups (male, female, age bands, reproductive age) |
| Show outside toggle | Include or exclude population beyond the selected distance |
| Map | Interactive Leaflet map that updates in response to filters, showing facility locations and population grid cells |

## Re-rendering after changes

If you modify `hcf-dashboard.qmd` or any helper function in `src/r/dashboard/R/`, simply save the file. When using `quarto preview`, changes are automatically hot-reloaded.

If changes are not reflected, try stopping the preview (Ctrl+C in terminal) and re-running `quarto preview`.

## Troubleshooting

Common dashboard-specific issues:

| Problem | Likely cause | Fix |
| --- | --- | --- |
| `Error: cannot open file 'data/ttm/<country>_closest_times.parquet'` | Missing TTM output file | Run the full pipeline first; check `src/r/dashboard/config/config.yaml` `country` value |
| `Error: package 'xxx' is not installed` | Missing R dependency | Run `devtools::install_deps("src/r/dashboard", dependencies = TRUE)` |
| `quarto: command not found` | Quarto not on PATH | Install Quarto from [quarto.org](https://quarto.org/docs/get-started/) and restart your shell |
| Dashboard loads but map is blank | CRS mismatch or no facilities match filters | Verify output files have data for the configured country |
| Shiny error on district selector | Invalid config country name | Check `country` is spelled correctly and matches the data file names |
| Port already in use | Another process on the default Shiny port | Stop other R sessions or use a different port |

See [06 — Troubleshooting](06-troubleshooting.md) for errors relating to earlier pipeline stages.
