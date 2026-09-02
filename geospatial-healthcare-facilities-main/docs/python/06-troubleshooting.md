# Troubleshooting

## Environment and installation

| Problem | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: healthcare_accessibility` | Local package not installed | Run `pip install -e .` from the repository root |
| `ModuleNotFoundError: r5py` or `osmnx` | Conda packages missing | Run `conda install -c conda-forge r5py osmnx` in your environment |
| `quarto: command not found` | Quarto not on PATH | Install Quarto from [quarto.org](https://quarto.org/docs/get-started/) and restart your shell |

## Data preparation

| Problem | Likely cause | Fix |
| --- | --- | --- |
| OSM download fails for a new country | Country not in `country_continent_dict` | Add the country and its continent to the dict in `data_preparation.py` |
| WorldPop download fails | Network issue or release no longer available | Manually download from [WorldPop Hub](https://hub.worldpop.org/geodata/listing?id=136) and place in `data/<country>/raw_data/population_data/` |
| Admin boundary download fails | geoBoundaries API unavailable | Manually download from [geoBoundaries country downloads](https://www.geoboundaries.org/countryDownloads.html) and place in `data/<country>/raw_data/admin_boundary_geom/` |
| `FileNotFoundError` for health facility GeoJSON | File not placed before running | Add `<country-lower>.geojson` to `data/<country-lower>/raw_data/health_facility_data/` |

## Travel time analysis

| Problem | Likely cause | Fix |
| --- | --- | --- |
| Memory allocation error during routing | Too many origin-destination pairs for available RAM | Reduce `max_travel_time_mins`, run one mode at a time, or segment analysis by ADM1 with a buffer (see [04 — Travel time analysis](04-travel-time-analysis.md)) |
| Output parquet files are missing | Script did not complete successfully | Check terminal output for errors and re-run |
| Very long runtime | Large country with dense population and road network | Expected — see runtime estimates in [04 — Travel time analysis](04-travel-time-analysis.md) |

## Dashboard

| Problem | Likely cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` on dashboard startup | Missing parquet or `.gpkg` file | Complete the full pipeline first; confirm `country` in `configs/config.yaml` matches your output folders |
| Dashboard loads but map is blank | Empty data or CRS mismatch | Verify processed data files contain rows for the configured country |
| Shiny server port conflict | Another process on the default port | Pass `--port <number>` to `shiny run`, e.g. `shiny run src/healthcare_accessibility/app.py --port 8081` |
| Unexpected behaviour after re-render | Stale cached asset files | Delete `hcf-dashboard-python_files/` and re-run render and `shiny run` |
