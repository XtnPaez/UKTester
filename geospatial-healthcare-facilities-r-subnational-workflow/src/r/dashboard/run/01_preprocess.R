# 01_preprocess.R
#
# This script downloads and processes Malawi districts and healthcare facilities.
# Outputs are written to data/boundaries/districts.geojson and data/poi/healthcare_facilities.csv

library(countrycode)
library(curl)
library(dplyr)
library(here)
library(sf)
devtools::load_all(here::here("src", "r", "dashboard"), quiet = TRUE)

# Read config file
config <- yaml::read_yaml(here::here("src", "r", "dashboard", "config", "config.yaml"))
config <- format_config(config)
validate_config(config)
area_name <- define_area_name(config)

# Get districts
districts <- get_districts(
  country = config$country,
  filepath = config$districts_filepath,
  name_col = config$district_name_column,
  admin_level = config$admin_level,
  crs = config$crs,
  analysis_mode = config$analysis_mode
)
sf::st_write(
  districts,
  here::here("data", "boundaries", paste0(area_name, "_districts.geojson")),
  delete_dsn = TRUE
)

# Get healthcare facilities
message("Downloading and processing healthcare facilities...")
healthcare <- get_healthcare_facilities(
  districts,
  filepath = config$facility_list_filepath,
  url = config$facility_list_url,
  country = config$country,
  crs_out = config$crs
)
write_output(
  healthcare,
  here::here("data", "poi", paste0(area_name, "_healthcare_facilities.csv")),
  format = "csv"
)

# Get population sub-groups
message("Downloading population sub-groups from WorldPop...")
population_files_exist <- get_subgroup_population_files(
  country = config$country,
  filepath = config$population_filepath,
  year = config$worldpop$year,
  release = config$worldpop$release,
  version = config$worldpop$version
)

message("Creating sub-group population rasters...")
population_subgroup_raster <- create_population_subgroup_rasters(
  country = config$country,
  raw_dir = here::here("data", "raw"),
  filepath = population_files_exist,
  year = config$worldpop$year
)

# For subnational runs, clip population raster to the provided district boundaries.
if (config$analysis_mode == "subnational") {
  clip_population_to_districts(
    population_raster = population_subgroup_raster,
    districts         = districts,
    area_name         = area_name,
    year              = config$worldpop$year
  )
}
