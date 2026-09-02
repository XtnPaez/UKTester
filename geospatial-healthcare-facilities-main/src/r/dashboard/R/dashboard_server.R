#' Build district dropdown choices for a selectInput
#'
#' @param district An sf object with a `name` column
#' @param all_district_value Sentinel string representing "all areas"
#' @return A named character vector suitable for use in selectInput choices
#' @export
get_district_choices <- function(district, all_district_value) {
  district_names <- sort(unique(district$name))
  c(
    stats::setNames(all_district_value, "All areas"),
    stats::setNames(district_names, district_names)
  )
}


#' Filter district sf object to a single area or return all
#'
#' @param district An sf object with a `name` column
#' @param selected_district The currently selected district value from the UI
#' @param all_district_value Sentinel string representing "all areas"
#' @return An sf object: the full dataset or a single-district subset
filter_district_sf <- function(district, selected_district, all_district_value) {
  if (selected_district == all_district_value) {
    district
  } else {
    subset(district, name == selected_district)
  }
}

#' Filter healthcare data frame by district and facility type
#'
#' @param healthcare A data frame with at minimum columns `type` and optionally `district`
#' @param selected_district The currently selected district value from the UI
#' @param facility_types Character vector of selected facility types
#' @param has_district_col Logical; TRUE if the healthcare data has a `district` column
#' @param all_district_value Sentinel string representing "all areas"
#' @return A filtered data frame
filter_healthcare_df <- function(healthcare, selected_district, facility_types,
                                  has_district_col, all_district_value) {
  if (selected_district == all_district_value) {
    dplyr::filter(healthcare, .data$type %in% facility_types)
  } else if (has_district_col) {
    dplyr::filter(
      healthcare,
      .data$district == selected_district & .data$type %in% facility_types
    )
  } else {
    dplyr::filter(healthcare, .data$type %in% facility_types)
  }
}

#' Add a popup HTML column to a healthcare data frame and convert to sf
#'
#' Columns `id`, `lon`, and `lat` are excluded from the popup body; `name`
#' is displayed as a bold heading.
#'
#' @param df A data frame with at minimum columns `name`, `lon`, and `lat`
#' @return An sf point object (CRS 4326) with an additional `popup` column
build_healthcare_sf <- function(df) {
  popup_cols <- setdiff(names(df), c("id", "lon", "lat"))

  df$popup <- apply(df[, popup_cols, drop = FALSE], 1, function(row) {
    other_cols <- names(row)[names(row) != "name"]
    paste0(
      "<b>", row["name"], "</b><br>",
      paste0(other_cols, ": ", row[other_cols], collapse = "<br>")
    )
  })

  sf::st_as_sf(df, coords = c("lon", "lat"), crs = 4326)
}

#' Convert a distance in km to a travel time threshold in minutes
#'
#' Uses mode-specific speeds:
#' - WALK: 3.6 km/h
#' - BICYCLE: 12 km/h
#'
#' @param distance_band_km Numeric distance in kilometres
#' @param mode Character travel mode. Supported values: "WALK", "BICYCLE"
#' @return Numeric travel time in minutes
travel_time_threshold_from_km <- function(distance_band_km, mode = "WALK") {
  mode_norm <- toupper(as.character(mode)[1])

  speed_kmh <- dplyr::case_when(
    mode_norm == "WALK" ~ 3.6,
    mode_norm == "BICYCLE" ~ 12,
    TRUE ~ NA_real_
  )

  if (is.na(speed_kmh)) {
    stop("mode must be either 'WALK' or 'BICYCLE'", call. = FALSE)
  }

  as.numeric(distance_band_km) * 60 / speed_kmh
}

#' Filter TTM data.table by district and facility type
#'
#' @param ttm A data.table with columns `district` and `facility_type`
#' @param selected_district The currently selected district value from the UI
#' @param facility_types Character vector of selected facility types
#' @param all_district_value Sentinel string representing "all areas"
#' @return A filtered data.table
filter_ttm_data <- function(ttm, selected_district, facility_types, all_district_value) {
  if (selected_district == all_district_value) {
    ttm[is.na(facility_type) | facility_type %in% facility_types]
  } else {
    ttm[
      (is.na(district) | district == selected_district) &
        (is.na(facility_type) | facility_type %in% facility_types)
    ]
  }
}

#' Compute a population raster for the map from filtered TTM data
#'
#' Groups by population cell, finds the minimum travel time, applies the
#' within/outside distance filter, and rasterizes the result onto the
#' population raster template. Returns an all-NA raster if no cells match.
#'
#' @param ttm_filtered A filtered data.table (output of filter_ttm_data)
#' @param demographic Column name for the demographic group (character)
#' @param travel_time_threshold Numeric travel time threshold in minutes
#' @param show_outside Logical; if TRUE show cells *outside* the threshold
#' @param pop_rast A SpatRaster template used for extent and resolution
#' @return A SpatRaster
compute_ttm_raster <- function(ttm_filtered, demographic, travel_time_threshold,
                                show_outside, pop_rast) {
  safe_min <- function(x) if (all(is.na(x))) NA_real_ else min(x, na.rm = TRUE)

  ttm_min <- ttm_filtered |>
    dplyr::group_by(id, lon, lat, !!rlang::sym(demographic)) |>
    dplyr::summarise(travel_time_p50 = safe_min(travel_time_p50), .groups = "drop") |>
    dplyr::mutate(travel_time_p50 = ifelse(is.infinite(travel_time_p50), NA, travel_time_p50))

  if (show_outside) {
    ttm_min <- dplyr::filter(
      ttm_min, is.na(travel_time_p50) | travel_time_p50 > travel_time_threshold
    )
  } else {
    ttm_min <- dplyr::filter(
      ttm_min, !is.na(travel_time_p50) & travel_time_p50 <= travel_time_threshold
    )
  }

  valid_coords <- dplyr::filter(ttm_min, !is.na(lon) & !is.na(lat))
  if (nrow(valid_coords) == 0) {
    na_rast <- pop_rast
    terra::values(na_rast) <- NA
    return(na_rast)
  }

  valid_coords |>
    sf::st_as_sf(coords = c("lon", "lat"), crs = 4326) |>
    terra::rasterize(pop_rast, field = demographic)
}

#' Compute population summary (within / outside a distance band)
#'
#' Combines rows with valid facility TTM data with rows that have no matching
#' facility (NA facility_type), then classifies each population cell as within
#' or outside the chosen distance band.
#'
#' @param ttm A data.table with the full TTM dataset
#' @param selected_district The currently selected district value from the UI
#' @param facility_types Character vector of selected facility types
#' @param all_district_value Sentinel string representing "all areas"
#' @param demo_col Column name for the demographic group (character)
#' @param travel_time_threshold Numeric travel time threshold in minutes
#' @param distance_band_km Numeric distance in km (used for distance labels)
#' @return A data frame with columns: distance, population, percent
compute_pop_summary <- function(ttm, selected_district, facility_types,
                                 all_district_value, demo_col,
                                 travel_time_threshold, distance_band_km) {
  if (selected_district == all_district_value) {
    filtered_ttm <- ttm[is.na(facility_type) | facility_type %in% facility_types] |>
      dplyr::distinct()
  } else {
    filtered_ttm <- ttm[
      district == selected_district &
        (is.na(facility_type) | facility_type %in% facility_types)
    ]
  }

  valid_facility_ttm <- suppressWarnings(
    filtered_ttm |>
      dplyr::filter(!is.na(facility_type)) |>
      dplyr::select(id, !!rlang::sym(demo_col), travel_time_p50) |>
      dplyr::group_by(id) |>
      dplyr::summarise(
        population = dplyr::first(!!rlang::sym(demo_col)),
        travel_time_p50 = min(travel_time_p50, na.rm = TRUE),
        .groups = "drop"
      )
  )

  na_facility_ttm <- filtered_ttm |>
    dplyr::filter(is.na(facility_type) & !(id %in% valid_facility_ttm$id)) |>
    dplyr::distinct() |>
    dplyr::select(id, !!rlang::sym(demo_col), travel_time_p50) |>
    dplyr::rename(population = !!rlang::sym(demo_col))

  summary_df <- dplyr::bind_rows(na_facility_ttm, valid_facility_ttm) |>
    dplyr::mutate(
      travel_time_p50 = ifelse(is.infinite(travel_time_p50), NA, travel_time_p50),
      distance = dplyr::case_when(
        !is.na(travel_time_p50) & travel_time_p50 <= travel_time_threshold ~
          paste0("Within ", distance_band_km, "km"),
        TRUE ~ paste0("Outside ", distance_band_km, "km")
      )
    ) |>
    dplyr::group_by(distance) |>
    dplyr::summarise(population = sum(population, na.rm = TRUE), .groups = "drop")

  # Always return both labels so dashboard value boxes can safely pull either row.
  label_df <- data.frame(
    distance = c(
      paste0("Within ", distance_band_km, "km"),
      paste0("Outside ", distance_band_km, "km")
    ),
    stringsAsFactors = FALSE
  )

  summary_df <- dplyr::left_join(label_df, summary_df, by = "distance") |>
    dplyr::mutate(population = ifelse(is.na(population), 0, population))

  total_population <- sum(summary_df$population, na.rm = TRUE)
  summary_df |>
    dplyr::mutate(
      percent = if (total_population > 0) {
        round(population / total_population * 100, 1)
      } else {
        0
      }
    )
}

#' Count healthcare facilities by type
#'
#' Wraps filter_healthcare_df and returns a count table sorted by descending n.
#'
#' @param healthcare A data frame with at minimum a `type` column
#' @param selected_district The currently selected district value from the UI
#' @param facility_types Character vector of selected facility types
#' @param has_district_col Logical; TRUE if the data has a `district` column
#' @param all_district_value Sentinel string representing "all areas"
#' @return A data frame with columns `type` and `n`, sorted by descending n
compute_facility_counts <- function(healthcare, selected_district, facility_types,
                                     has_district_col, all_district_value) {
  filter_healthcare_df(
    healthcare, selected_district, facility_types, has_district_col, all_district_value
  ) |>
    dplyr::count(type) |>
    dplyr::arrange(dplyr::desc(n))
}

#' Build a summary text snippet for n_health_facilities value box
#'
#' Shows the top two facility types with their counts; appends "+N more" when
#' there are additional types. Returns a full tooltip string as an attribute.
#'
#' @param n_tbl A data frame with columns `type` and `n` (from compute_facility_counts)
#' @param n_show Integer; number of types to show before truncating (default 2)
#' @return A list with elements `summary_txt` (for display) and `full_txt` (for tooltip)
build_facility_summary_text <- function(n_tbl, n_show = 2L) {
  if (nrow(n_tbl) == 0) {
    return(list(summary_txt = "None selected", full_txt = "None selected"))
  }

  rows_shown <- min(n_show, nrow(n_tbl))
  shown <- paste0(n_tbl$type[seq_len(rows_shown)], ": ", n_tbl$n[seq_len(rows_shown)], collapse = " | ")
  summary_txt <- if (nrow(n_tbl) > n_show) {
    paste0(shown, " | +", nrow(n_tbl) - n_show, " more")
  } else {
    shown
  }

  full_txt <- paste0(n_tbl$type, ": ", n_tbl$n, collapse = " | ")
  list(summary_txt = summary_txt, full_txt = full_txt)
}
