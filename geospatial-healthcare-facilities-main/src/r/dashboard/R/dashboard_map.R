#' Build a log10-scale colour palette and legend metadata for a population raster
#'
#' Computes decade breaks (1, 10, 100, …) from the raster's non-zero values,
#' builds a viridis binned palette on the log10 scale, and returns everything
#' needed to render the raster and its legend in Leaflet.
#'
#' @param raster A SpatRaster of raw population values
#' @return A list with elements:
#'   \describe{
#'     \item{log_raster}{SpatRaster of log10-transformed values (non-positive → NA)}
#'     \item{pal}{leaflet colorBin palette function}
#'     \item{log_breaks}{Numeric vector of log10 break points}
#'     \item{legend_labels}{Character vector of human-readable bin labels}
#'   }
#'   Returns NULL if there are no positive population values.
build_log_palette <- function(raster) {
  log_raster <- terra::app(raster, fun = function(x) ifelse(x > 0, log10(x), NA))

  pop_vals <- terra::values(raster)
  pop_vals <- pop_vals[!is.na(pop_vals) & pop_vals > 0]

  if (length(pop_vals) == 0) return(NULL)

  log_min  <- max(0L, floor(log10(min(pop_vals))))
  log_max  <- ceiling(log10(max(pop_vals)))
  pop_breaks  <- unique(10^(log_min:log_max))
  log_breaks  <- log10(pop_breaks)

  pal <- leaflet::colorBin(
    palette  = viridisLite::viridis(length(log_breaks) - 1L),
    bins     = log_breaks,
    domain   = log10(pop_vals),
    na.color = "transparent"
  )

  legend_labels <- paste0(
    formatC(pop_breaks[-length(pop_breaks)], format = "d", big.mark = ","),
    " \u2013 ",
    formatC(pop_breaks[-1L],                format = "d", big.mark = ",")
  )

  list(
    log_raster    = log_raster,
    pal           = pal,
    log_breaks    = log_breaks,
    legend_labels = legend_labels
  )
}

#' Update a Leaflet map proxy with district, raster, and healthcare layers
#'
#' Clears all existing shapes, markers, and controls before re-drawing.
#' Silently returns the input proxy unchanged if palette is NULL (no data).
#'
#' @param map_proxy A leafletProxy object
#' @param district_sf An sf object for the selected district (used for bounding box)
#' @param palette_info List returned by build_log_palette (or NULL)
#' @param healthcare_sf An sf point object with a `popup` column
#' @param distance_band_km Numeric; distance band in km (used in legend title)
#' @return The updated leaflet proxy (invisibly)
update_leaflet_map <- function(map_proxy, district_sf, palette_info,
                                healthcare_sf, distance_band_km) {
  bbox <- as.vector(sf::st_bbox(district_sf))

  map_proxy <- map_proxy |>
    leaflet::addProviderTiles("CartoDB.Positron") |>
    leaflet::clearShapes() |>
    leaflet::clearMarkers() |>
    leaflet::clearControls() |>
    leaflet::fitBounds(bbox[1], bbox[2], bbox[3], bbox[4]) |>
    leaflet::addPolygons(data = district_sf, color = "#1E2A16", weight = 2) |>
    leaflet::addAwesomeMarkers(
      data = healthcare_sf,
      popup = ~popup,
      icon  = ~leaflet::makeAwesomeIcon(
        icon        = "stethoscope",
        library     = "fa",
        iconColor   = "white",
        markerColor = "orange"
      )
    )

  if (!is.null(palette_info)) {
    map_proxy <- map_proxy |>
      leaflet::addRasterImage(
        x       = palette_info$log_raster,
        colors  = palette_info$pal,
        opacity = 0.8
      ) |>
      leaflet::addLegend(
        colors  = palette_info$pal(palette_info$log_breaks[-length(palette_info$log_breaks)]),
        labels  = palette_info$legend_labels,
        title   = paste0("Estimated population within ", distance_band_km, " km"),
        opacity = 1
      )
  }

  invisible(map_proxy)
}
