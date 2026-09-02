#' Convert a population raster to a points tibble
#'
#' Reads a population raster and returns a tibble of points with lon, lat, and population.
#'
#' @param tif_path Path to the population raster (GeoTIFF)
#' @param crs_out Output CRS for coordinates (default: 4326)
#' @return A tibble with columns: id, lon, lat, population
#' @importFrom terra rast as.points
#' @importFrom sf st_as_sf st_drop_geometry st_coordinates
#' @importFrom dplyr select mutate
#' @importFrom purrr map_dbl
#' @export
get_population_points <- function(tif_path, crs_out = 4326) {
  pop_pts <- terra::rast(tif_path) |>
    terra::as.points() |>
    sf::st_as_sf() |>
    sf::st_transform(crs_out) |>
    dplyr::mutate(id = dplyr::row_number(),
                  lon = purrr::map_dbl(geometry, ~sf::st_coordinates(.x)[[1]]),
                  lat = purrr::map_dbl(geometry, ~sf::st_coordinates(.x)[[2]])) |>
    sf::st_drop_geometry()
  return(pop_pts)
}
