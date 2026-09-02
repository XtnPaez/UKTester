# config_validation.R
#
# Two functions for cleaning and checking config.yaml after yaml::read_yaml():
#
#   format_config(config)   -- normalises types, casing and whitespace; returns
#                              the cleaned list.
#   validate_config(config) -- checks required fields, allowed values and file
#                              paths; stops on hard errors, warns on soft issues.
#
# Typical usage in run scripts:
#   config <- yaml::read_yaml(...)
#   config <- format_config(config)
#   validate_config(config)

# Internal helper: trim a string; return NULL if blank or already NULL.
.tidy <- function(x) {
  if (is.null(x)) return(NULL)
  x <- trimws(as.character(x))
  if (!nzchar(x)) NULL else x
}

#' Format and normalise raw config values
#'
#' Trims whitespace, applies consistent casing, converts empty strings to NULL,
#' and coerces numeric / integer fields to the correct type. Call this immediately
#' after \code{yaml::read_yaml()} and before \code{validate_config()}.
#'
#' @param config Named list as returned by \code{yaml::read_yaml()}.
#' @return The same list with normalised values.
#' @export
format_config <- function(config) {

  # ── analysis_mode ----------------------------------------------------------
  # Accept "country", "subnational", "sub-national", "sub_national" etc.
  mode_raw <- .tidy(config$analysis_mode)
  if (!is.null(mode_raw)) {
    mode_norm <- tolower(gsub("[-_ ]+", "", mode_raw))
    config$analysis_mode <- if (grepl("^sub", mode_norm)) "subnational" else "country"
  } else {
    stop("analysis_mode must be set in config.yaml to 'country' or 'subnational'.")
  }

  # ── Plain string fields: trim + NULL-if-blank ------------------------------
  config$country                <- .tidy(config$country)
  config$districts_filepath     <- .tidy(config$districts_filepath)
  config$district_name_column   <- .tidy(config$district_name_column)
  config$subnational_area       <- .tidy(config$subnational_area)
  config$network_source_path    <- .tidy(config$network_source_path)
  config$facility_list_filepath <- .tidy(config$facility_list_filepath)
  config$facility_list_url      <- .tidy(config$facility_list_url)
  config$population_filepath    <- .tidy(config$population_filepath)

  # ── admin_level_name: lowercase --------------------------------------------
  if (!is.null(config$admin_level_name)) {
    config$admin_level_name <- tolower(trimws(config$admin_level_name))
  }

  # ── boundary_assign_method: lowercase -------------------------------------
  if (!is.null(config$boundary_assign_method)) {
    config$boundary_assign_method <- tolower(trimws(config$boundary_assign_method))
  }

  # ── Integer fields ---------------------------------------------------------
  if (!is.null(config$crs)) {
    config$crs <- as.integer(config$crs)
  }
  if (!is.null(config$admin_level)) {
    config$admin_level <- as.integer(config$admin_level)
  }

  # ── worldpop sub-list ------------------------------------------------------
  if (!is.null(config$worldpop)) {
    if (!is.null(config$worldpop$year)) {
      config$worldpop$year <- as.integer(config$worldpop$year)
    }
    if (!is.null(config$worldpop$release)) {
      config$worldpop$release <- toupper(trimws(config$worldpop$release))
    }
    if (!is.null(config$worldpop$version)) {
      config$worldpop$version <- tolower(trimws(config$worldpop$version))
    }
  }

  # ── travel_time sub-list ---------------------------------------------------
  if (!is.null(config$travel_time)) {
    if (!is.null(config$travel_time$mode)) {
      config$travel_time$mode <- toupper(trimws(config$travel_time$mode))
    }
    if (!is.null(config$travel_time$max_travel_time_mins)) {
      config$travel_time$max_travel_time_mins <-
        as.integer(config$travel_time$max_travel_time_mins)
    }
  }

  # ── r5r sub-list -----------------------------------------------------------
  if (!is.null(config$r5r)) {
    if (!is.null(config$r5r$n_threads)) {
      config$r5r$n_threads <- as.integer(config$r5r$n_threads)
    }
    if (!is.null(config$r5r$java_memory)) {
      config$r5r$java_memory <- as.numeric(config$r5r$java_memory)
    }
  }

  config
}


#' Validate a formatted config list
#'
#' Checks required fields, allowed values, and referenced file paths. Collects
#' all problems before reporting: hard errors are raised together via
#' \code{stop()}; soft issues are raised individually via \code{warning()}.
#'
#' Run \code{format_config()} before calling this function.
#'
#' @param config Named list, ideally already passed through \code{format_config()}.
#' @return Invisibly returns \code{TRUE} when all checks pass.
#' @importFrom countrycode countrycode
#' @export
validate_config <- function(config) {

  errors   <- character(0)
  warnings <- character(0)

  err  <- function(...) errors   <<- c(errors,   paste0(...))
  warn <- function(...) warnings <<- c(warnings, paste0(...))

  is_subnational <- identical(config$analysis_mode, "subnational")

  # ── analysis_mode ----------------------------------------------------------
  if (!config$analysis_mode %in% c("country", "subnational")) {
    err("analysis_mode must be 'country' or 'subnational'; got: '",
        config$analysis_mode, "'")
  }

  # ── country ----------------------------------------------------------------
  if (is.null(config$country) || !nzchar(config$country)) {
    if (is_subnational) {
      err("country must be set in subnational mode (needed for WorldPop and Geofabrik lookups).")
    } else {
      err("country must be set in config.yaml.")
    }
  } else {
    iso <- tryCatch(
      countrycode::countrycode(config$country, "country.name", "iso3c"),
      warning = function(w) NA_character_
    )
    if (is.na(iso)) {
      warn("country '", config$country, "' was not recognised by countrycode. ",
           "Check spelling — WorldPop and Geofabrik lookups may fail.")
    }
  }

  # ── subnational_area -------------------------------------------------------
  if (is_subnational && (is.null(config$subnational_area) || !nzchar(config$subnational_area))) {
    err("subnational_area must be set when analysis_mode is 'subnational'.")
  }
  if (!is_subnational &&
      !is.null(config$subnational_area) &&
      nzchar(config$subnational_area)) {
    warn("subnational_area is set ('", config$subnational_area, "') but analysis_mode is ",
         "'country'. Set analysis_mode: 'subnational' if a subnational run was intended.")
  }

  # ── crs -------------------------------------------------------------------
  if (is.null(config$crs) || is.na(config$crs) || config$crs <= 0L) {
    err("crs must be a positive integer EPSG code (e.g. 4326).")
  }

  # ── districts_filepath / admin_level --------------------------------------
  if (!is.null(config$districts_filepath)) {
    if (!file.exists(config$districts_filepath)) {
      err("districts_filepath does not exist: ", config$districts_filepath)
    }
  } else {
    if (is_subnational) {
      err("districts_filepath must be set when analysis_mode is 'subnational'.")
    }
    if (is.null(config$admin_level) || is.na(config$admin_level)) {
      err("admin_level must be set when districts_filepath is blank.")
    } else if (config$admin_level <= 2L) {
      warn("admin_level ", config$admin_level, " corresponds to national/continental ",
           "boundaries in OpenStreetMap. Use a value >= 3 for district-level units.")
    }
  }

  # ── Healthcare facility inputs --------------------------------------------
  if (!is.null(config$facility_list_filepath) &&
      !file.exists(config$facility_list_filepath)) {
    err("facility_list_filepath does not exist: ", config$facility_list_filepath)
  }
  if (is.null(config$facility_list_filepath) && is.null(config$facility_list_url)) {
    warn("Neither facility_list_filepath nor facility_list_url is set. ",
         "Healthcare facilities will be downloaded from Healthsites.io.")
  }

  # ── network_source_path ---------------------------------------------------
  if (!is.null(config$network_source_path)) {
    if (!file.exists(config$network_source_path)) {
      warn("network_source_path is set but the file does not yet exist: ",
           config$network_source_path,
           ". The file must be present before 02_ttm.R runs.")
    } else if (!grepl("\\.osm\\.pbf$", config$network_source_path, ignore.case = TRUE)) {
      warn("network_source_path does not end in .osm.pbf: ", config$network_source_path)
    }
  }

  # ── worldpop --------------------------------------------------------------
  if (!is.null(config$worldpop)) {
    yr <- config$worldpop$year
    if (is.null(yr) || is.na(yr) || yr < 2000L || yr > 2050L) {
      err("worldpop$year must be a 4-digit year between 2000 and 2050; got: ", yr)
    }
    rel <- config$worldpop$release
    if (!is.null(rel) && nzchar(rel) && !grepl("^R[0-9]{4}[A-Z]$", rel)) {
      warn("worldpop$release '", rel, "' does not match the expected pattern (e.g. 'R2025A').")
    }
  }

  # ── boundary_assign_method ------------------------------------------------
  if (!is.null(config$boundary_assign_method) &&
      !config$boundary_assign_method %in% c("raster", "zonal", "join")) {
    err("boundary_assign_method must be one of: 'raster', 'zonal', 'join'; got: '",
        config$boundary_assign_method, "'")
  }

  # ── travel_time -----------------------------------------------------------
  if (!is.null(config$travel_time)) {
    mode <- config$travel_time$mode
    if (!is.null(mode) && !mode %in% c("WALK", "BICYCLE")) {
      err("travel_time$mode must be 'WALK' or 'BICYCLE'; got: '", mode, "'")
    }
    tt <- config$travel_time$max_travel_time_mins
    if (!is.null(tt) && !is.na(tt) && tt <= 0L) {
      err("travel_time$max_travel_time_mins must be a positive integer.")
    }
  }

  # ── r5r -------------------------------------------------------------------
  if (!is.null(config$r5r)) {
    if (!is.null(config$r5r$n_threads) &&
        (is.na(config$r5r$n_threads) || config$r5r$n_threads < 1L)) {
      err("r5r$n_threads must be a positive integer.")
    }
    if (!is.null(config$r5r$java_memory) &&
        (is.na(config$r5r$java_memory) || config$r5r$java_memory <= 0)) {
      err("r5r$java_memory must be a positive number (GB).")
    }
  }

  # ── Emit all collected issues ---------------------------------------------
  if (length(warnings) > 0) {
    for (w in warnings) warning(w, call. = FALSE)
  }
  if (length(errors) > 0) {
    stop(
      "Config validation failed with ", length(errors), " error(s):\n",
      paste0("  [", seq_along(errors), "] ", errors, collapse = "\n"),
      call. = FALSE
    )
  }

  message("Config validation passed.")
  invisible(TRUE)
}
