# Troubleshooting

## Environment and installation

| Problem | Likely cause | Fix |
| --- | --- | --- |
| `Error: object 'xxx' not found` when sourcing a script | Missing R package | Run `devtools::install_deps("src/r/dashboard", dependencies = TRUE)` and ensure all packages installed successfully |
| `install_deps()` or package install says `osmdata`/`r5r` version does not exist (often on R 4.5) | Mirror metadata issue | Install with `pak` using explicit versions: `install.packages("pak")`, `pak::pak("osmdata@0.3.0")`, `pak::pak("r5r@2.3.0")`; then retry the pipeline |
| `quarto: command not found` | Quarto not on PATH | Install Quarto from [quarto.org](https://quarto.org/docs/get-started/) and restart your terminal |
| Java-related error when loading r5r | rJavaEnv or Java not properly configured | Run `rJavaEnv::java_quick_install(version = 21)` and `rJavaEnv::java_check_version_rjava()` |

## Data preparation (01_preprocess.R)

| Problem | Likely cause | Fix |
| --- | --- | --- |
| `Error: could not find function "get_districts"` | R helper functions not sourced | Ensure you are running the full script `01_preprocess.R` from the repository root, which sources all required functions |
| Repeated `Waiting 60s for retry backoff` messages | Network issue or API rate limit | Check your internet connection. If using a VPN, try disabling it. If the issue persists, wait and try again later or consider downloading the file manually and set `facility_list_filepath` to the local file |
| OpenStreetMap boundary download fails | Overpass API timeout or unavailable | Set `filepath` in config to a local boundary file, or try again later. Increase timeout with `timeout_seconds` parameter in `get_osm_districts` |
| WorldPop download fails | Network issue or release no longer available | Manually download from [WorldPop Hub](https://hub.worldpop.org/geodata/listing?id=136) and set `population_filepath` in config to the local zip file |
| `FileNotFoundError` for facility file | File not found at the specified path | Verify `facility_list_filepath` is correct and points to an existing file, or check the URL in `facility_list_url` is accessible |
| Healthcare facilities CSV/Excel download fails | URL no longer valid or network issue | Download the file manually and set `facility_list_filepath` to the local file |
| `Warning: Removed X rows with missing longitude or latitude` | Some facilities have missing coordinates | Rows without coordinates are automatically dropped. Check data quality if the number is unexpectedly high |

## Travel time analysis (02_ttm.R)

| Problem | Likely cause | Fix |
| --- | --- | --- |
| `Error: java.lang.OutOfMemoryError` during network build | Insufficient Java heap memory | Increase Java memory: change `java.parameters = "-Xmx2G"` to a larger value like `"-Xmx4G"` or `"-Xmx8G"` depending on available RAM |
| `Error: Could not find OSM PBF file` | Geofabrik download failed or file missing | Check `data/network/<country>/` exists and contains a `.pbf` file. Re-run the download or manually place the PBF file there |
| `Internet connection not working properly.` (or automatic R5 jar download fails during `r5r::build_network`) | Network restrictions/firewall block automatic jar download from GitHub | Manually download `r5-v7.4-all.jar` from [Conveyal release v7.4](https://github.com/conveyal/r5/releases/download/v7.4/r5-v7.4-all.jar), then place it in your local r5r cache directory (run `r5r::r5r_cache(list_files = TRUE)` to print the cache location). Re-run `02_ttm.R` after placing the jar |
| Travel time matrix is empty for a facility type | Facilities of that type outside network extent or invalid coordinates | Verify facility coordinates are valid and within the country boundary. Check that facility `type` values are not empty or whitespace-only |
| Script takes very long to complete | Large country or high `max_walk_time` threshold | This is expected for large countries. Consider reducing `max_walk_time`, increasing `n_threads`, or segmenting by district |
| `Error: object 'facility_type' not found` | Column name mismatch in facility data | Ensure the preprocessing step correctly named the facility type column. Verify `data/poi/<country>_healthcare_facilities.csv` has the expected columns |

## Dashboard

| Problem | Likely cause | Fix |
| --- | --- | --- |
| `Error: cannot open file 'data/ttm/<country>_closest_times.parquet'` | TTM file missing or wrong country name | Complete the full pipeline first; verify `country` in `src/r/dashboard/config/config.yaml` matches output file names exactly |
| `Error: subscript out of bounds` on dashboard load | Empty or mismatched data | Check that `01_preprocess.R` and `02_ttm.R` both completed successfully and produced non-empty outputs |
| Dashboard loads but map is blank | No facilities match the current filters | Try changing facility type or district filters. Verify facilities were written to `data/poi/<country>_healthcare_facilities.csv` |
| `Error: invalid subscript` on district selector | Config country name invalid or data files missing | Verify the `country` in config is spelled correctly (e.g. "Malawi", not "malawi") |
| Shiny error: `object 'config' not found` | Dashboard `.qmd` setup chunk failed | Check that `src/r/dashboard/config/config.yaml` exists and is valid YAML. Try restarting the Shiny preview |
| Port already in use when previewing | Another R session on the same port | Stop other R/Shiny processes, or restart RStudio and try again |
| Dashboard shows old data after re-running pipeline | Cached data in R session | Stop Shiny (Ctrl+C), close R, and start fresh |

## Common data issues

| Problem | Likely cause | Fix |
| --- | --- | --- |
| Facility coordinates look wrong on map | CRS mismatch or incorrect parsing | Verify facility data has valid longitude/latitude columns. Check that coordinates are in WGS84 (lon/lat) before preprocessing |
| Districts named incorrectly | Wrong column used as district label | Set `district_name_column` in config to the correct column name from your boundary file |
| Inconsistent facility IDs across runs | No stable `id` column in original data | Provide a stable `id` column in facility input data. Auto-generated IDs are not persistent between runs |

