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

# Get districts
districts <- get_districts(
  country = config$country,
  filepath = config$districts_filepath,
  name_col = config$district_name_column,
  admin_level = config$admin_level,
  crs = config$crs
)
output_dir_path <- here::here("data", "boundaries")
if (!dir.exists(output_dir_path)) dir.create(output_dir_path)
sf::st_write(
  districts,
  file.path(output_dir_path, paste0(tolower(config$country), "_districts.geojson")),
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
output_dir_path <- here::here("data", "poi")
if (!dir.exists(output_dir_path)) dir.create(output_dir_path)
write_output(
  healthcare,
  file.path(output_dir_path, paste0(tolower(config$country), "_healthcare_facilities.csv")),
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
