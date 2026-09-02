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

# Load districts and healthcare facilities (written by 01_preprocess.R)
message(paste0("Loading districts for ", config$country, "..."))
districts <- load_districts(config$country)

message(paste0("Loading healthcare facilities for ", config$country, "..."))
healthcare <- load_healthcare(config$country)

# Get population points
message("Processing population raster...")
folder_name <- paste0(
  tolower(countrycode::countrycode(config$country,"country.name", "iso3c")),
  "_agesex_",
  config$worldpop$year
)
population <- get_population_points(here::here("data", "population", folder_name, "geodemographics.tif"))

t0 <- Sys.time()
if(config$boundary_assign_method == "raster") {
  message("Attaching district names to population points with raster...")
  population <- add_district_to_points_raster(
    population,
    districts,
    here::here("data", "population", folder_name, "geodemographics.tif"),
  )
} else if(config$boundary_assign_method == "zonal"){
  message("Attaching district names to population points using largest area overlap...")
  population <- add_district_to_points_zonal(
    population,
    districts,
    here::here("data", "population", folder_name, "geodemographics.tif"),
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
network_path <- here::here("data", "network", tolower(config$country))
download_geofabrik_pbf(
  country = config$country,
  dest_dir = network_path,
  overwrite = FALSE,
  verify_md5 = TRUE
)
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

# Write output
output_dir_path <- here::here("data", "ttm")
if (!dir.exists(output_dir_path)) dir.create(output_dir_path)
write_output(closest_times, file.path(output_dir_path, paste0(tolower(config$country), "_closest_times.csv")), format = "csv")
write_output(closest_times, file.path(output_dir_path, paste0(tolower(config$country), "_closest_times.parquet")), format = "parquet")

# Clean up r5r
r5r::stop_r5(r5r_network)
rJava::.jgc(R.gc = TRUE)
