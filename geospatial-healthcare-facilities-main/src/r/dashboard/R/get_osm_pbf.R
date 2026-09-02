#' Fetch Geofabrik index as a data frame
#'
#' @param index_url URL to Geofabrik GeoJSON index
#' @return A data frame with Geofabrik extracts metadata
#' @importFrom jsonlite fromJSON
get_geofabrik_index <- function(index_url = "https://download.geofabrik.de/index-v1.json") {
  tmp <- tempfile(fileext = ".json")
  on.exit(unlink(tmp), add = TRUE)

  # Avoid GDAL remote reads to bypass platform-specific TLS trust issues.
  curl::curl_download(url = index_url, destfile = tmp, mode = "wb", quiet = TRUE)
  index_json <- jsonlite::fromJSON(tmp, simplifyVector = FALSE)

  if (is.null(index_json$features) || length(index_json$features) == 0) {
    stop("Geofabrik index has no features: ", index_url)
  }

  value_or_na <- function(x) {
    if (is.null(x) || length(x) == 0) return(NA_character_)
    as.character(x[[1]])
  }

  rows <- lapply(index_json$features, function(f) {
    p <- f$properties
    data.frame(
      id = value_or_na(p$id),
      name = value_or_na(p$name),
      `iso3166-1:alpha2` = value_or_na(p[["iso3166-1:alpha2"]]),
      pbf_url = value_or_na(p$urls$pbf),
      stringsAsFactors = FALSE,
      check.names = FALSE
    )
  })

  do.call(rbind, rows)
}


#' Resolve Geofabrik PBF URL for a country
#'
#' @param country Country name (e.g., "Nepal")
#' @param index Optional pre-loaded Geofabrik index from get_geofabrik_index()
#' @return A list with url, id, and name of the selected Geofabrik extract
#' @importFrom countrycode countrycode
#' @importFrom dplyr filter mutate arrange slice
resolve_geofabrik_pbf_url <- function(country, index = NULL) {
  if (is.null(index)) {
    index <- get_geofabrik_index()
  }

  iso2 <- countrycode::countrycode(country, "country.name", "iso2c")
  if (is.na(iso2) || is.null(iso2)) {
    stop("Could not map country name to ISO2 code: ", country)
  }

  # Prioritize rows that explicitly match the country's ISO2 code and have a PBF URL.
  candidates <- index |>
    dplyr::filter(
      !is.na(pbf_url),
      !is.na(`iso3166-1:alpha2`),
      toupper(`iso3166-1:alpha2`) == toupper(iso2)
    ) |>
    dplyr::mutate(
      name_lc = tolower(name),
      country_lc = tolower(country),
      exact_name = name_lc == country_lc
    ) |>
    dplyr::filter(!is.na(pbf_url), nzchar(pbf_url)) |>
    dplyr::arrange(dplyr::desc(exact_name), id)

  if (nrow(candidates) == 0) {
    stop("No Geofabrik PBF extract found for country: ", country)
  }

  selected <- dplyr::slice(candidates, 1)
  list(
    url = selected$pbf_url[[1]],
    id = selected$id[[1]],
    name = selected$name[[1]]
  )
}


#' Download Geofabrik PBF for a country
#'
#' @param country Country name (e.g., "Nepal")
#' @param dest_dir Destination directory for the PBF file
#' @param overwrite If FALSE, skip download when file already exists
#' @param verify_md5 If TRUE, validate downloaded file against Geofabrik MD5
#' @return Path to local .osm.pbf file
#' @importFrom tools file_path_sans_ext file_ext md5sum
download_geofabrik_pbf <- function(
    country,
    dest_dir,
    overwrite = FALSE,
    verify_md5 = TRUE
) {    
  extract <- resolve_geofabrik_pbf_url(country)
  pbf_url <- extract$url

  if (!dir.exists(dest_dir)) {
    dir.create(dest_dir, recursive = TRUE)
  }

  pbf_filename <- basename(pbf_url)
  pbf_path <- file.path(dest_dir, pbf_filename)

  if (file.exists(pbf_path) && !overwrite) {
    message("Using existing PBF file: ", pbf_path)
    return(pbf_path)
  }

  message("Downloading Geofabrik PBF for ", country, " from: ", pbf_url)
  curl::curl_download(url = pbf_url, destfile = pbf_path, mode = "wb", quiet = FALSE)

  if (verify_md5) {
    md5_url <- paste0(pbf_url, ".md5")
    md5_line <- tryCatch({
      md5_raw <- curl::curl_fetch_memory(md5_url)$content
      strsplit(rawToChar(md5_raw), "\\r?\\n")[[1]]
    }, error = function(e) character(0))

    md5_line <- md5_line[nzchar(md5_line)]

    if (length(md5_line) > 0) {
      expected_md5 <- strsplit(md5_line[[1]], "  ")[[1]][1]
      actual_md5 <- tools::md5sum(pbf_path)[[1]]
      if (!identical(tolower(expected_md5), tolower(actual_md5))) {
        stop("Checksum mismatch for downloaded PBF: ", pbf_path)
      }
      message("MD5 checksum passed for: ", pbf_path)
    } else {
      warning("Could not retrieve MD5 file from Geofabrik for validation: ", md5_url)
    }
  }

  pbf_path
}
