#' Download and extract population subgroup files from a specified URL.
#' 
#' This function checks if the target folder for the extracted files already exists.
#' If it does, it skips the download and extraction steps. Otherwise, it downloads the
#' ZIP file from the provided URL, extracts its contents to a specified directory,
#' and then removes the ZIP file.
#' 
#' @param country Country name used to derive ISO3 code when filepath is missing.
#' @param filepath The filepath of the ZIP file downloaded from WorldPop.
#' @param year WorldPop data year.
#' @param dest_dir The directory to save the downloaded ZIP file (default: "data
#' /raw").
#' @param zip_name The name to save the downloaded ZIP file as (default: basename
#' of the URL).
#' @param unzip_folder The directory to extract the ZIP file to (default: same as
#' dest_dir).
#' 
#' @return The path to the folder where the files were extracted, or NULL if there
#' was an error.
get_subgroup_population_files <- function(
  country = NULL,
  filepath,
  year,
  release,
  version = "v1",
  dest_dir = here::here("data", "raw"),
  zip_name = NULL,
  unzip_folder = NULL
) {
  if (missing(filepath) || is.null(filepath) || identical(filepath, "")) {
    message("No population_filepath provided. Attempting to download WorldPop data...")

    if (is.null(country) || !nzchar(country)) {
      stop(
        "population_filepath is missing. Provide either filepath or country ",
        "to enable automatic WorldPop download."
      )
    }

    iso3 <- countrycode::countrycode(country, "country.name", "iso3c")
    if (is.na(iso3) || !nzchar(iso3)) {
      stop(
        "Could not derive ISO3 code for country '", country,
        "'. Please provide a valid country name or set population_filepath."
      )
    }
    filepath <- download_worldpop(iso_code = iso3, year = year, release = release, version = version, dest_dir = dest_dir)
  }

  if (is.null(zip_name)) {
    zip_name <- paste0(
      tolower(iso3), "_agesex_structures_", year,
      "_CN_1km_", release, "_UA_", version, ".zip"
    )
  }

  # Set unzip_folder to dest_dir if not specified
  if (is.null(unzip_folder)) {
    unzip_folder <- dest_dir
  }

  # Remove .zip extension for folder check
  folder_name <- tools::file_path_sans_ext(zip_name)
  folder_path <- file.path(unzip_folder, folder_name)

  # If folder already exists, skip download and extraction
  if (dir.exists(folder_path)) {
    message("Folder ", folder_path, " already exists. Skipping download and extraction.")
    return(invisible(folder_path))
  }

  # Ensure destination directory exists
  if (!dir.exists(here::here(dest_dir, folder_name))) {
    ok <- dir.create(here::here(dest_dir, folder_name), recursive = TRUE, showWarnings = FALSE)
    if (!ok && !dir.exists(here::here(dest_dir, folder_name))) {
      stop("Could not create destination directory for extraction: ", here::here(dest_dir, folder_name))
    }
  }

  tryCatch(
    {
      message("Extracting WorldPop ZIP '", filepath, "' to '", folder_path, "'...")
      unzip(filepath, exdir = folder_path)
    },
    error = function(e) {
      stop(
        "Failed to extract WorldPop ZIP '", filepath, "' to '", folder_path,
        "'.\nOriginal error: ", conditionMessage(e)
      )
    }
  )

  extracted_tifs <- list.files(folder_path, pattern = "\\.tif$", recursive = TRUE)
  if (length(extracted_tifs) == 0) {
    stop(
      "Extraction completed but no .tif files were found in: ", folder_path,
      ". Check whether the ZIP matches the expected WorldPop age-sex structure format."
    )
  }

  message("Files extracted to ", folder_path, "\n")
  invisible(folder_path)
}

#' Download and extract population subgroup files from a specified URL.
#' 
#' This function checks if the target folder for the extracted files already exists.
#' If it does, it skips the download and extraction steps. Otherwise, it downloads the
#' ZIP file from the provided URL, extracts its contents to a specified directory,
#' and then removes the ZIP file.
#' 
#' @param country Country name used to derive ISO3 code when filepath is missing.
#' @param filepath The filepath of the ZIP file downloaded from WorldPop.
#' @param year WorldPop data year.
#' @param dest_dir The directory to save the downloaded ZIP file (default: "data
#' /raw").
#' @param zip_name The name to save the downloaded ZIP file as (default: basename
#' of the URL).
#' @param unzip_folder The directory to extract the ZIP file to (default: same as
#' dest_dir).
#' 
#' @return The path to the folder where the files were extracted, or NULL if there
#' was an error.
download_worldpop <- function(
    iso_code,
    year,
    release,
    version = "v1",
    dest_dir = here::here("data", "raw")
  ) {
  if (is.null(iso_code) || !nzchar(iso_code)) {
    stop("iso_code must be provided to download WorldPop data.")
  }

  iso_up <- toupper(iso_code)
  iso_low <- tolower(iso_code)

  url <- paste0(
    "https://data.worldpop.org/GIS/AgeSex_structures/Global_2015_2030/", release, "/",
    year, "/", iso_up, "/", version, "/1km_ua/", iso_low,
    "_agesex_structures_", year, "_CN_1km_", release, "_UA_", version, ".zip"
  )

  if (!dir.exists(dest_dir)) {
    ok <- dir.create(dest_dir, recursive = TRUE, showWarnings = FALSE)
    if (!ok && !dir.exists(dest_dir)) {
      stop("Could not create destination directory for WorldPop download: ", dest_dir)
    }
  }

  dest <- file.path(dest_dir, paste0(iso_low, "_agesex_structures_", year, "_CN_1km_", release, "_UA_", version, ".zip"))
  if (file.exists(dest)) {
    message("WorldPop ZIP already exists: ", dest, " (skipping download)")
    return(dest)
  }

  message("Downloading WorldPop data from: ", url)
  tryCatch(
    {
      curl::curl_download(url, destfile = dest, mode = "wb", quiet = FALSE)
    },
    error = function(e) {
      stop(
        "WorldPop download failed for ISO code '", iso_up, "' and year ", year, ".",
        "\nOriginal error: ", conditionMessage(e)
      )
    }
  )

  if (!file.exists(dest) || file.info(dest)$size <= 0) {
    stop("WorldPop download completed but ZIP is missing or empty: ", dest)
  }

  message("Downloaded WorldPop ZIP: ", dest)
  return(dest)
}

#' Create and write population subgroup rasters from WorldPop files
#' 
#' This function reads the unzipped WorldPop .tif files for a specified country
#' and creates combined stack rasters for different population subgroups
#'
#' @param country Country name used to derive ISO3 code.
#' @param raw_dir Directory containing the unzipped WorldPop .tif files
#' @param filepath The filepath of the ZIP file downloaded from WorldPop.
#' @param year WorldPop data year.
#' @param out_dir Directory to write output rasters (default: "data")
#' 
#' @return A combined stack raster for each population sub group
#' 
#' @export
create_population_subgroup_rasters <- function(
  country,
  raw_dir,
  filepath,
  year,
  out_dir = here::here("data", "population")
) {
  dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
  
  prefix <- tolower(countrycode::countrycode(country, "country.name", "iso3c"))

  folder_name <- paste0(prefix, "_agesex_", year)
  folder_path <- file.path(out_dir, folder_name)

  # If the folder does not exist, attempt to create it
  if (!dir.exists(folder_path)) {
    ok <- dir.create(folder_path, recursive = TRUE, showWarnings = FALSE)
    if (!ok && !dir.exists(folder_path)) {
      stop("Could not create folder for extracted WorldPop files: ", folder_path)
    }
  }

  subgroups <- list(
    Females = paste0("^", prefix, "_f.*\\.tif$"),
    Males = paste0("^", prefix, "_m.*\\.tif$"),
    `Children (0-14)` = paste0("^", prefix, "_t_(00|01|05|10).*\\.tif$"),
    `Working-age adults (15-64)` = paste0("^", prefix, "_t_(15|20|25|30|35|40|45|50|55|60).*\\.tif$"),
    `Older people (65+)` = paste0("^", prefix, "_t_(65|70|75|80|85|90).*\\.tif$"),
    `Women of reproductive age (15-49)` = paste0("^", prefix, "_f_(15|20|25|30|35|40|45).*\\.tif$")
  )

  rasters <- list()
  for (name in names(subgroups)) {
    out_path <- file.path(folder_path, paste0(gsub(" ", "_", tolower(name)), ".tif"))
    if (file.exists(out_path)) {
      message("File ", out_path, " already exists. Skipping creation.\n")
      rasters[[name]] <- terra::rast(out_path)
      next
    }

    if (!dir.exists(filepath)) {
      stop("Expected folder for subgroup population files does not exist: ", filepath)
    }

    files <- list.files(filepath, subgroups[[name]], full.names = TRUE)
    if (length(files) == 0) {
      message("No files found for subgroup ", name, "- skipping.\n")
      next
    }
    message("Creating ", name, " raster file...")
    rlist <- purrr::map(files, terra::rast)
    rsrc <- terra::sprc(rlist)
    out_raster <- terra::mosaic(rsrc, fun = "sum")
    names(out_raster) <- name
    terra::writeRaster(out_raster, out_path, overwrite = TRUE)
    rasters[[name]] <- out_raster
  }

  # Check if total population raster already exists
  total_pop_path <- file.path(folder_path, "total_population.tif")
  if (file.exists(total_pop_path)) {
    message("File ", total_pop_path, " already exists. Skipping creation.\n")
    total_pop_raster <- terra::rast(total_pop_path)
  } else {
    total_pop_raster <- rasters[["Females"]] + rasters[["Males"]]
    names(total_pop_raster) <- "Total population"
    terra::writeRaster(total_pop_raster, total_pop_path, overwrite = TRUE)
  }
  rasters[["Total population"]] <- total_pop_raster

  # Combine all rasters into a stack and write
  message(
    "Combining rasters into a stack and writing to file ",
    file.path(folder_path, "geodemographics.tif"),
    "..."
  )
  stack <- terra::rast(rasters)
  terra::writeRaster(stack, file.path(folder_path, "geodemographics.tif"), overwrite = TRUE)
  return(stack)
}
