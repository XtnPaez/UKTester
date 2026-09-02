#' Load districts from OpenStreetMap or local file
#' 
#' @param country The name of the country to receive boundaries for
#' @param filepath Path to the boundary file
#' @param admin_level OSM admin level (default 4 for districts)
#' @param name_col Name of the column in the file to use as the district label
#' @param crs Coordinate Reference System to return (default: 4326)
#' @return An sf object of selected boundaries
get_districts <- function(
  country,
  filepath,
  name_col,
  admin_level = 4,
  crs = 4326,
  analysis_mode = "country"
) {
  if (!is.null(filepath)) {
    message(paste("Loading district boundaries from", filepath))
    districts <- get_file_districts(filepath, name_col, crs)
  } else if (!is.null(country) && nzchar(country)) {
    if (analysis_mode == "subnational") {
      stop("districts_filepath must be set in config.yaml to run a subnational analysis.")
    }
    message(paste0("Downloading '", country, "' districts from OpenStreetMap..."))
    districts <- get_osm_districts(country, admin_level, crs)
  } else {
    stop("districts_filepath or country must be provided in config.yaml")
  }
  return(districts)
}

#' Download and process district boundaries from OpenStreetMap
#'
#' @param country The name of the country to receive boundaries for
#' @param admin_level OSM admin level (default 4 for districts)
#' @param crs Coordinate Reference System to return (default: 4326)
#' @param timeout_seconds Overpass query timeout in seconds (default 120)
#' @param memsize_bytes Overpass memory limit in bytes (default 1073741824 = 1 GB)
#' @return An sf object of selected boundaries
#' @importFrom osmdata getbb opq add_osm_feature osmdata_sf
#' @importFrom dplyr filter select
#' @importFrom sf st_transform
#' @export
get_osm_districts <- function(
  country,
  admin_level = 4,
  crs = 4326,
  timeout_seconds = 300,
  memsize_bytes = 1073741824,
  max_retries = 3,
  retry_wait_seconds = 10
  ) {
  iso_prefix <- countrycode::countrycode(country, "country.name", "iso2c")
  country_name <- trimws(country)
  admin_level_num <- suppressWarnings(as.integer(admin_level))

  if (!is.na(admin_level_num) && admin_level_num <= 2) {
    stop(paste0(
      "admin_level=", admin_level_num, " in OpenStreetMap corresponds to national boundaries. ",
      "Use a subnational admin level in config.yaml or provide a local boundary file via districts_filepath."
    ))
  }

  # admin_level must be a character string for the Overpass feature tag
  admin_level <- as.character(admin_level)

  run_query <- function() {
    osmdata::getbb(country) |>
      osmdata::opq(timeout = timeout_seconds, memsize = memsize_bytes) |>
      osmdata::add_osm_feature(key = "boundary", value = "administrative") |>
      osmdata::add_osm_feature(key = "admin_level", value = admin_level) |>
      osmdata::osmdata_sf() |>
      with(osm_multipolygons)
  }

  districts <- NULL
  last_error <- NULL
  for (attempt in seq_len(max_retries)) {
    districts <- tryCatch(run_query(), error = function(e) {
      last_error <<- e
      NULL
    })
    if (!is.null(districts)) break
    if (attempt < max_retries) {
      message(paste0(
        "Overpass query attempt ", attempt, " of ", max_retries,
        " failed for '", country, "': ", conditionMessage(last_error),
        " — retrying in ", retry_wait_seconds, "s..."
      ))
      Sys.sleep(retry_wait_seconds)
    }
  }

  if (is.null(districts)) {
    stop(paste0(
      "Overpass query failed after ", max_retries, " attempts for '",
      country, "' (admin_level=", admin_level, "): ",
      conditionMessage(last_error),
      "\nConsider providing a local boundary file via districts_filepath in config.yaml "
    ))
  }

  if (nrow(districts) == 0) {
    stop(paste0(
      "No admin_level=", admin_level, " boundaries returned for '", country, "' from OpenStreetMap. ",
      "Check the admin_level value in config.yaml or provide a local boundary file via districts_filepath."
    ))
  }

  message(paste0("Downloaded boundaries for '", country, "' from OpenStreetMap."))

  # Filter to features tagged with the country ISO prefix, where the tag exists
  if ("ISO3166-2" %in% names(districts) & iso_prefix %in% districts[["ISO3166-2"]]) {
    iso_filter <- !is.na(districts[["ISO3166-2"]]) &
      stringr::str_detect(districts[["ISO3166-2"]], paste0("^", iso_prefix))
    districts <- districts[iso_filter, , drop = FALSE]
  }

  if (nrow(districts) == 0) {
    stop(paste0(
      "No features matched ISO3166-2 prefix '", iso_prefix, "' for '", country, "'. ",
      "Consider providing a local boundary file via districts_filepath in config.yaml."
    ))
  }

  districts <- dplyr::select(districts, name)
  districts <- sf::st_transform(districts, crs)
  return(districts)
}

#' Load district boundaries from a local file (shp, gpkg, geojson)
#'
#' @param filepath Path to the boundary file
#' @param name_col Name of the column in the file to use as the district label
#' @param crs Coordinate Reference System to return (default: 4326)
#' @return An sf object of selected boundaries
#' @export
get_file_districts <- function(filepath, name_col, crs = 4326) {
  ext <- tolower(tools::file_ext(filepath))
  if (ext == "shp") {
    districts <- sf::st_read(filepath, quiet = TRUE)
  } else if (ext == "gpkg") {
    districts <- sf::st_read(filepath, quiet = TRUE)
  } else if (ext %in% c("geojson", "json")) {
    districts <- sf::st_read(filepath, quiet = TRUE)
  } else {
    stop("Unsupported file type: ", ext)
  }
  districts <- sf::st_transform(districts, crs)

  if(is.null(name_col)) {
    name_col <- names(districts)[1]
    warning(paste("name_col not provided, defaulting to first column:", name_col))
  } else if (!name_col %in% names(districts)) {
    stop("name_col not found in districts: ", name_col)
  }
  districts <- districts |>
    dplyr::select(name = !!name_col)
  return(districts)
}
