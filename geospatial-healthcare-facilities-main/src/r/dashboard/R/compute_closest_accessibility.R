#' Compute closest travel time to each destination by facility type
#'
#' For each facility type, computes the travel time matrix and finds the closest facility for each destination.
#'
#' @param r5r_network An r5r network object
#' @param healthcare Tibble of healthcare facilities (must include id, lon, lat, type)
#' @param destinations Tibble of destination points (must include id, lon, lat)
#' @param mode Mode of transport (default: "BICYCLE")
#' @param max_travel_time Maximum travel time in minutes (default: 120).
#' @param n_threads Number of threads for parallel processing (default: 2)
#' @return A tibble with destination id, lon, lat, population, facility_type, from_id, travel_time_p50
#' @importFrom dplyr filter bind_rows group_by slice_min mutate left_join select
#' @importFrom purrr map_dfr
#' @export
compute_closest_accessibility <- function(
    r5r_network,
    healthcare,
    destinations,
    mode = "BICYCLE",
    max_travel_time = 167,
    n_threads = 2
) {
  if (!is.numeric(max_travel_time) || length(max_travel_time) != 1 || is.na(max_travel_time) || max_travel_time <= 0) {
    stop("max_travel_time must be a single positive number of minutes.")
  }

  if (!(mode %in% c("WALK", "BICYCLE"))) {
    stop("mode must be either 'WALK' or 'BICYCLE'")
  }

  max_walk_time <- max_travel_time
  max_trip_duration <- max_travel_time

  healthcare$type <- trimws(tolower(healthcare$type))
  healthcare$id <- as.character(healthcare$id)
  destinations$id <- as.character(destinations$id)
  facility_types <- unique(stats::na.omit(healthcare$type))
  results <- purrr::map_dfr(facility_types, function(ftype) {
    origins <- dplyr::filter(healthcare, type == ftype)
    origins_min <- origins |>
      dplyr::select(id, lon, lat) |>
      dplyr::distinct()
    destinations_min <- destinations |>
      dplyr::select(id, lon, lat) |>
      dplyr::distinct()
    ttm <- r5r::travel_time_matrix(
      r5r_network,
      origins = origins_min,
      destinations = destinations_min,
      mode = mode,
      max_walk_time = max_walk_time,
      max_trip_duration = max_trip_duration,
      max_lts = 4L,
      n_threads = n_threads
    )
    if (nrow(ttm) == 0) {
      warning(paste0("No travel times returned for facility type '", ftype, "'. Check network and coordinate coverage."))
      return(dplyr::left_join(destinations, ttm, by = c("id" = "to_id")))
    }
    closest <- ttm |>
      dplyr::mutate(from_id = as.character(from_id), to_id = as.character(to_id)) |>
      dplyr::group_by(to_id) |>
      dplyr::slice_min(travel_time_p50) |>
      dplyr::mutate(facility_type = ftype)
    dplyr::left_join(destinations, closest, by = c("id" = "to_id"))
  })
  return(results)
}
