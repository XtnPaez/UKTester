#' Download and clean Malawi Master Health Facility Register
#'
#' Downloads the latest register, filters for functional facilities with valid coordinates, and joins to districts.
#'
#' @param districts An sf object of Malawi districts (for spatial join)
#' @param url The URL to download the Excel file from
#' @param crs_out Output CRS for coordinates (default: 4326)
#' @return A tibble with columns: id, lon, lat, name, type, ownership, district
#' @importFrom httr GET write_disk
#' @importFrom readxl read_xlsx
#' @importFrom dplyr filter filter_at vars all_vars mutate rename_with select rename
#' @importFrom stringr str_replace_all
#' @importFrom sf st_as_sf st_transform st_intersection st_drop_geometry st_coordinates
#' @importFrom purrr map_dbl
#' @export
get_healthcare_facilities_malawi <- function(
    districts,
    url = "https://zipatala.health.gov.mw/api/facilities/download?data={%22where%22:{},%22format%22:%22excel%22}",
    crs_out = 4326
) {
  tmp <- tempfile(fileext = ".xlsx")
  httr::GET(url = url, httr::write_disk(tmp))
  healthcare <- readxl::read_xlsx(tmp, sheet = "Facilities") |>
    dplyr::filter(STATUS == "Functional") |>
    dplyr::mutate(LONGITUDE = stringr::str_replace_all(LONGITUDE, " ", ""),
                  LONGITUDE = as.numeric(LONGITUDE), LATITUDE = as.numeric(LATITUDE))

  n_missing <- sum(is.na(healthcare$LONGITUDE) | is.na(healthcare$LATITUDE))
  if (n_missing > 0) {
    warning(sprintf("Removed %d rows with missing longitude or latitude.", n_missing))
    healthcare <- dplyr::filter(healthcare, !is.na(LONGITUDE), !is.na(LATITUDE))
  }

  healthcare <- healthcare |>
    sf::st_as_sf(coords = c("LONGITUDE", "LATITUDE"), crs = 4326) |>
    dplyr::rename_with(tolower) |>
    dplyr::select(code, name, type, ownership) |>
    sf::st_transform(sf::st_crs(districts)) |>
    sf::st_intersection(districts["name"]) |>
    dplyr::rename(district = name.1) |>
    sf::st_transform(crs_out) |>
    dplyr::mutate(lon = purrr::map_dbl(geometry, ~sf::st_coordinates(.x)[[1]]),
                  lat = purrr::map_dbl(geometry, ~sf::st_coordinates(.x)[[2]])) |>
    sf::st_drop_geometry() |>
    dplyr::select(id = code, lon, lat, name, type, ownership, district)
  return(healthcare)
}


#' Download or load and clean healthcare facility data for any country
#'
#' @param districts An sf object of country districts (for spatial join)
#' @param filepath Optional: path to a local file (CSV, XLSX, GeoJSON, etc.)
#' @param url Optional: URL to download the file from
#' @param country Optional: country name (for country-specific cleaning)
#' @param crs_out Output CRS for coordinates (default: 4326)
#' @return A tibble with columns: id, lon, lat, name, type, ownership, district
#' @export
get_healthcare_facilities <- function(
  districts,
  filepath = NULL,
  url = NULL,
  country = NULL,
  crs_out = 4326
) {
  if (!is.null(filepath)) {
    ext <- tools::file_ext(filepath)
    healthcare <- load_file_by_extension(filepath, ext)
  } else if (!is.null(url)) {
    ext <- tools::file_ext(url)
    if (ext == "") ext <- "xlsx" # Default to xlsx if unknown
    tmp <- tempfile(fileext = paste0(".", ext))
    httr::GET(url = url, httr::write_disk(tmp))
    healthcare <- load_file_by_extension(tmp, ext)
  } else {
    stop("Either filepath or url must be provided.")
  }

  healthcare <- clean_healthcare_facilities(healthcare, country)
  
  n_missing <- sum(is.na(healthcare$lon) | is.na(healthcare$lat))
  if (n_missing > 0) {
    warning(sprintf("Removed %d rows with missing longitude or latitude.", n_missing))
    healthcare <- dplyr::filter(healthcare, !is.na(lon), !is.na(lat))
  }
  healthcare <- dplyr::filter(healthcare, !is.na(lon), !is.na(lat))

  healthcare_sf <- sf::st_as_sf(healthcare, coords = c("lon", "lat"), crs = 4326, remove = FALSE) |>
    dplyr::select(id, name, type, ownership) |>
    sf::st_transform(sf::st_crs(districts)) |>
    sf::st_intersection(districts["name"]) |>
    dplyr::rename(district = name.1) |>
    sf::st_transform(crs_out) |>
    dplyr::mutate(
      lon = purrr::map_dbl(geometry, ~sf::st_coordinates(.x)[[1]]),
      lat = purrr::map_dbl(geometry, ~sf::st_coordinates(.x)[[2]])
    ) |>
    sf::st_drop_geometry()
    

  return(healthcare_sf)
}


#' Clean healthcare facilities data
#'
#' @param df A data frame or tibble containing healthcare facilities data
#' @param country Optional: country name (for country-specific cleaning)
#' @return A cleaned data frame or tibble
#' @export
clean_healthcare_facilities <- function(df, country = NULL) {
  df <- dplyr::rename_with(df, tolower)

  # Healthsites CSV (HDX)
  if (all(c("x", "y", "osm_id") %in% names(df))) {
    df <- df |>
      dplyr::mutate(
        lon = as.numeric(x),
        lat = as.numeric(y),
        id = osm_id,
        type = amenity,
        ownership = operator
      ) |>
      dplyr::select(-x, -y, -osm_id, -amenity, -operator)
  } else if (!is.null(country) && tolower(country) == "malawi") {
    # Malawi-specific cleaning
    df <- df |>
      dplyr::filter(status == "Functional") |>
      dplyr::mutate(
        lon = as.numeric(stringr::str_replace_all(longitude, " ", "")),
        lat = as.numeric(latitude),
        id = code
      )
  } else if ("geometry" %in% names(df)) {
    # GeoJSON
    coords <- sf::st_coordinates(df)
    df$lon <- coords[, 1]
    df$lat <- coords[, 2]
    if (!"id" %in% names(df)) df$id <- seq_len(nrow(df))
  } else {
    # Generic
    if (!"lon" %in% names(df) && "longitude" %in% names(df)) df$lon <- as.numeric(df$longitude)
    if (!"lat" %in% names(df) && "latitude" %in% names(df)) df$lat <- as.numeric(df$latitude)
    if (!"id" %in% names(df)) df$id <- seq_len(nrow(df))
  }

  if (!"type" %in% names(df)) df$type <- "Not specified"
  df
}
