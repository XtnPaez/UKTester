# 02_ttm.R
#
# This script computes the closest travel time to each population cell by facility type.
# Outputs are written to data/closest_times.csv (or .parquet)

library(countrycode)
library(curl)
library(here)
library(dplyr)
library(sf)
library(arrow)
library(terra)
devtools::load_all(here::here("src", "r", "dashboard"), quiet = TRUE)

# Read config file
config <- yaml::read_yaml(here::here("src", "r", "dashboard", "config", "config.yaml"))
config <- format_config(config)
validate_config(config)
area_name <- define_area_name(config)

# Load districts and healthcare facilities (written by 01_preprocess.R)
message(paste0("Loading districts for ", area_name, "..."))
districts <- load_districts(area_name)

message(paste0("Loading healthcare facilities for ", area_name, "..."))
healthcare <- load_healthcare(area_name)

# Get population points
message("Processing population raster...")
if (config$analysis_mode == "country") {
  country_folder <- paste0(
    tolower(countrycode::countrycode(config$country, "country.name", "iso3c")),
    "_agesex_",
    config$worldpop$year
  )
  population_raster_path <- here::here("data", "population", country_folder, "geodemographics.tif")
  message("Using country-level population raster: ", population_raster_path)
} else if (config$analysis_mode == "subnational") {
  area_folder <- paste0(area_name, "_agesex_", config$worldpop$year)
  population_raster_path <- here::here("data", "population", area_folder, "geodemographics.tif")
  message("Using country-level population raster: ", population_raster_path)
}
population <- get_population_points(population_raster_path)

t0 <- Sys.time()
if(config$boundary_assign_method == "raster") {
  message("Attaching district names to population points with raster...")
  population <- add_district_to_points_raster(
    population,
    districts,
    population_raster_path,
  )
} else if(config$boundary_assign_method == "zonal"){
  message("Attaching district names to population points using largest area overlap...")
  population <- add_district_to_points_zonal(
    population,
    districts,
    population_raster_path,
  )
} else {
  message("Attaching district names to population points using join...")
  population <- add_district_to_points(population, districts)
}
t1 <- Sys.time()
message(paste0("Time taken to attach districts to names: ", round(difftime(t1, t0, units = "secs"), 2), " seconds"))

# Increase Java memory
rJavaEnv::java_quick_install(version = 21)
rJavaEnv::java_check_version_rjava()
java_memory <- ifelse(is.null(config$r5r$java_memory), 2, config$r5r$java_memory)
options(java.parameters = java_memory)

# Build r5r network
# Use network_source_path if provided (e.g. a subnational PBF created by helpers/prepare_subnational_network.R)
network_source_path <- config$network_source_path
has_network_source <- !is.null(network_source_path)

if (has_network_source) {
  message("Using provided network source file: ", network_source_path)
  if (!file.exists(network_source_path)) {
    stop("Network source file not found: ", network_source_path)
  }
  network_path <- dirname(network_source_path)
} else {
  network_path <- here::here("data", "network", tolower(config$country))
  message("No network_source_path set; downloading country PBF for: ", config$country)
  download_geofabrik_pbf(
    country  = config$country,
    dest_dir = network_path,
    overwrite    = FALSE,
    verify_md5   = TRUE
  )
}
t2 <- Sys.time()
message("Building r5r network...")
r5r_network <- build_r5r_network_cached(network_path)
t3 <- Sys.time()
message(paste0("Time taken to build r5r network: ", round(difftime(t3, t2, units = "secs"), 2), " seconds"))

# Compute closest accessibility
t4 <- Sys.time()
message("Computing closest travel times by facility type...")
closest_times <- compute_closest_accessibility(
  r5r_network = r5r_network,
  healthcare = healthcare,
  destinations = population,
  mode = config$travel_time$mode,
  max_travel_time = config$travel_time$max_travel_time_mins,
  n_threads = config$r5r$n_threads
)
t5 <- Sys.time()
message(paste0("Time taken to compute closest accessibility: ", round(difftime(t5, t4, units = "secs"), 2), " seconds"))

# Write output — filenames include mode so WALK and BICYCLE results are kept separate
mode_suffix <- tolower(config$travel_time$mode)
write_output(closest_times, here::here("data", "ttm", paste0(area_name, "_closest_times_", mode_suffix, ".csv")), format = "csv")
write_output(closest_times, here::here("data", "ttm", paste0(area_name, "_closest_times_", mode_suffix, ".parquet")), format = "parquet")

# Clean up r5r
r5r::stop_r5(r5r_network)
rJava::.jgc(R.gc = TRUE)
