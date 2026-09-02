# prepare_subnational_network.R
#
# OPTIONAL HELPER SCRIPT for subnational analysis workflows
#
# Run this script ONCE before 01_preprocess.R when preparing a regional network
# for a subnational area. This script helps create a cropped OSM PBF file to reduce
# memory usage for large countries like Argentina.
#
# This script:
#   1. Reads the ADM2 district polygons from districts_filepath in config
#   2. Unions them into a single ADM1 boundary
#   3. Buffers the ADM1 boundary by boundary_buffer_km
#   4. Downloads the country OSM PBF from Geofabrik (skipped if already present)
#   5. Clips the PBF to the buffered boundary using osmium
#
# Output: a clipped .osm.pbf file written to data/network/<area>/
# After running, set network_source_path in config.yaml to the path printed at the end.
#
# Requirements:
#   - osmium-tool must be installed and on PATH
#     Install via conda: conda install -c conda-forge osmium-tool

library(here)
library(sf)
devtools::load_all(here::here("src", "r", "dashboard"), quiet = TRUE)

config <- yaml::read_yaml(here::here("src", "r", "dashboard", "config", "config.yaml"))

# Set the network clipping buffer here (in kilometers).
# Keep this in the prep script to avoid coupling with the main workflow config.
boundary_buffer_km <- 10

if (is.null(config$subnational_area) || !nzchar(config$subnational_area)) {
  stop("subnational_area is not set in config.yaml. This script is only needed for subnational analyses.")
}

area_name <- clean_area_name(config$subnational_area)

# ── 1. Build ADM1 boundary by unioning ADM2 polygons ─────────────────────────

if (is.null(config$districts_filepath) || !nzchar(config$districts_filepath)) {
  stop("districts_filepath must be set in config.yaml to run a subnational analysis.")
}

message("Reading ADM2 boundaries from: ", config$districts_filepath)
adm2 <- sf::st_read(config$districts_filepath, quiet = TRUE)
message("Unioning ADM2 polygons into single ADM1 boundary...")
adm1 <- sf::st_union(adm2) |> sf::st_sf() |> sf::st_make_valid()

# ── 2. Buffer ADM1 boundary ───────────────────────────────────────────────────

if (boundary_buffer_km > 0) {
  message("Buffering ADM1 boundary by ", boundary_buffer_km, " km...")
  # Project to metres for accurate buffering, then back to WGS84 for osmium
  adm1_buffered <- adm1 |>
    sf::st_transform(crs = 3857) |>
    sf::st_buffer(dist = boundary_buffer_km * 1000) |>
    sf::st_transform(crs = 4326)
} else {
  message("No buffer applied (boundary_buffer_km = 0).")
  adm1_buffered <- sf::st_transform(adm1, crs = 4326)
}

boundary_dir <- here::here("data", "boundaries")
if (!dir.exists(boundary_dir)) dir.create(boundary_dir, recursive = TRUE)

boundary_path <- file.path(boundary_dir, paste0(area_name, "_adm1_buffered.geojson"))
sf::st_write(adm1_buffered, boundary_path, delete_dsn = TRUE)
message("Buffered ADM1 boundary written to: ", boundary_path)

# ── 3. Download country OSM PBF ───────────────────────────────────────────────

country_network_dir <- here::here("data", "network", tolower(config$country))
message("Downloading country OSM PBF for: ", config$country)
country_pbf_path <- download_geofabrik_pbf(
  country  = config$country,
  dest_dir = country_network_dir,
  overwrite    = FALSE,
  verify_md5   = TRUE
)
message("Country PBF available at: ", country_pbf_path)

# ── 4. Print osmium command (run manually in terminal) ──────────────────────

area_network_dir <- here::here("data", "network", area_name)
if (!dir.exists(area_network_dir)) dir.create(area_network_dir, recursive = TRUE)

output_pbf_path <- file.path(area_network_dir, paste0(area_name, ".osm.pbf"))

osmium_cmd <- paste(
  "osmium extract",
  "--polygon", shQuote(boundary_path),
  shQuote(country_pbf_path),
  "--output", shQuote(output_pbf_path),
  "--overwrite"
)

message("\n── Done ──────────────────────────────────────────────────────────────────")
message("Prepared inputs for subnational network clipping.")
message("\nRun this command in your terminal to create the clipped network file:")
message(osmium_cmd)
message("\nIf osmium is not available, install with:")
message("  conda install -c conda-forge osmium-tool")
message("\nExpected output file:")
message("  ", output_pbf_path)
message("\nAdd or update this line in config.yaml:")
message("  network_source_path: \"", output_pbf_path, "\"")
message("─────────────────────────────────────────────────────────────────────────")
