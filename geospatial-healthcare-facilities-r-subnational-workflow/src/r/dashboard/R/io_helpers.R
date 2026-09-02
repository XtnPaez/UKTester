#' Load a healthcare facilities file based on its extension
#'
#' @param path The file path to load
#' @param ext The file extension (e.g., "csv", "xlsx", "geojson")
#' @return A data frame or sf object containing the healthcare facilities data
load_file_by_extension <- function(path, ext) {
  ext <- tolower(ext)
  if (ext %in% c("csv")) {
    readr::read_csv(path, show_col_types = FALSE)
  } else if (ext %in% c("xlsx", "xls")) {
    readxl::read_xlsx(path)
  } else if (ext %in% c("geojson", "json")) {
    sf::st_read(path, quiet = TRUE)
  } else {
    stop("Unsupported file extension: ", ext)
  }
}


#' Write a tibble or data.frame to a CSV or Parquet file
#'
#' @param x The data to write
#' @param path The file path to write to
#' @param format File format: 'csv' or 'parquet' (default: 'csv')
#' @importFrom readr write_csv
#' @importFrom arrow write_parquet
#' @export
write_output <- function(x, path, format = 'csv') {
  if (format == 'csv') {
    readr::write_csv(x, path)
  } else if (format == 'parquet') {
    arrow::write_parquet(x, path)
  } else {
    stop('Unsupported format')
  }
}


#' Load district boundaries previously written by 01_preprocess.R
#'
#' Reads the GeoJSON written to data/boundaries/ by the preprocessing pipeline.
#' The file is expected to have a `name` column (as produced by get_districts()).
#'
#' @param country Country name (matched to filename prefix, case-insensitive)
#' @return An sf object of district boundaries with a `name` column
#' @importFrom sf read_sf
#' @export
load_districts <- function(country) {
  path <- here::here("data", "boundaries", paste0(tolower(country), "_districts.geojson"))
  sf::read_sf(path)
}

#' Load and normalise healthcare facilities previously written by 01_preprocess.R
#'
#' Reads the CSV written to data/poi/ by the preprocessing pipeline, lower-cases
#' all column names, and normalises the `type` column (trimmed lowercase).
#'
#' @param country Country name (matched to filename prefix, case-insensitive)
#' @return A data frame with normalised column names and `type` values
#' @export
load_healthcare <- function(country) {
  path <- here::here("data", "poi", paste0(tolower(country), "_healthcare_facilities.csv"))
  hc <- load_file_by_extension(path = path, ext = "csv")
  hc <- dplyr::rename_with(hc, tolower)
  hc <- dplyr::mutate(hc, type = trimws(tolower(type)))
  hc
}

#' Load the travel time matrix (TTM) previously written by 02_ttm.R
#'
#' Reads the Parquet file written to data/ttm/, converts to data.table, and
#' normalises `facility_type` to trimmed lowercase.
#'
#' @param country Country name (matched to filename prefix, case-insensitive)
#' @param mode Transport mode used during TTM computation, e.g. "WALK" or
#'   "BICYCLE". Must match the mode used in 02_ttm.R.
#' @return A data.table with a normalised `facility_type` column
#' @importFrom arrow read_parquet
#' @importFrom data.table data.table
#' @export
load_ttm <- function(country, mode) {
  mode_suffix <- tolower(mode)
  path <- here::here("data", "ttm", paste0(tolower(country), "_closest_times_", mode_suffix, ".parquet"))
  ttm <- arrow::read_parquet(path)
  ttm <- data.table::data.table(ttm)
  ttm[, facility_type := trimws(tolower(facility_type))]
  ttm
}

#' Load the WorldPop geodemographics raster previously written by 01_preprocess.R
#'
#' Reads the geodemographics.tif stacked raster from data/population/.
#' Uses a subnational folder name directly when provided; otherwise derives
#' the ISO3 country code automatically via countrycode.
#'
#' @param area_name Country or subnational area name
#' @param year Integer WorldPop year (e.g., 2025)
#' @param analysis_mode Either "country" or "subnational" (default: "country")
#' @return A SpatRaster from terra
#' @importFrom terra rast
#' @export
load_population_raster <- function(area_name, year, analysis_mode = "country") {
  if (analysis_mode == "country") {
    iso3 <- tolower(countrycode::countrycode(area_name, "country.name", "iso3c"))
    folder <- paste0(iso3, "_agesex_", year)
  } else {
    folder <- paste0(area_name, "_agesex_", year)
  }

  terra::rast(here::here("data", "population", folder, "geodemographics.tif"))
}
