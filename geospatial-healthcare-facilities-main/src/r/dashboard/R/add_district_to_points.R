#' Attach district names to destination points
#'
#' @param population Tibble of destination points (must include lon, lat)
#' @param districts An sf object of Malawi districts
#' @param crs_out Output CRS for coordinates (default: 4326)
#' @return A tibble with district column added
#' @importFrom sf st_as_sf st_intersection st_transform st_drop_geometry st_coordinates
#' @importFrom dplyr mutate select
#' @importFrom purrr map_dbl
#' @export
add_district_to_points <- function(population, districts, crs_out = 4326) {
  pts_sf <- sf::st_as_sf(population, coords = c("lon", "lat"), crs = crs_out)
  pts_sf <- sf::st_join(pts_sf, districts["name"], left = TRUE)
  pts_sf <- pts_sf[!is.na(pts_sf$name), ]
  pts_sf <- dplyr::mutate(pts_sf,
                          lon = purrr::map_dbl(geometry, ~sf::st_coordinates(.x)[[1]]),
                          lat = purrr::map_dbl(geometry, ~sf::st_coordinates(.x)[[2]]))
  pts_sf <- sf::st_drop_geometry(pts_sf)
  pts_sf <- dplyr::select(pts_sf, id, lon, lat, district = name, population)
  return(pts_sf)
}

#' Find the appropriate CRS for a set of districts
#'
#' @param districts An sf object of districts
#' @return A character string with the EPSG code of the appropriate CRS
#' @importFrom sf st_centroid st_union st_coordinates
find_crs <- function(districts) {
  centroid <- sf::st_centroid(sf::st_union(districts))
  utm_zone <- floor((sf::st_coordinates(centroid)[1] + 180) / 6) + 1
  south <- sf::st_coordinates(centroid)[2] < 0
  if (south) {
    paste0("EPSG:", 32700 + utm_zone)
  } else {
    paste0("EPSG:", 32600 + utm_zone)
  }
}

#' Build sf polygons for a subset of raster cells by cell id
#'
#' Constructs one square polygon per unique cell id directly from raster
#' geometry
#'
#' @param pop_rast A terra SpatRaster object
#' @param cell_ids Integer vector of raster cell ids (from terra::cellFromXY)
#' @return An sf data frame with columns grid_id and geometry, CRS from pop_rast
raster_cells_to_sf <- function(pop_rast, cell_ids) {
  unique_cells <- sort(unique(stats::na.omit(cell_ids)))
  if (length(unique_cells) == 0) {
    return(sf::st_sf(grid_id = integer(0),
                    geometry = sf::st_sfc(crs = terra::crs(pop_rast))))
  }
  centers  <- terra::xyFromCell(pop_rast, unique_cells)
  half_x   <- terra::res(pop_rast)[1] / 2
  half_y   <- terra::res(pop_rast)[2] / 2
  polys <- lapply(seq_along(unique_cells), function(i) {
    x <- centers[i, 1]; y <- centers[i, 2]
    sf::st_polygon(list(rbind(
      c(x - half_x, y - half_y),
      c(x + half_x, y - half_y),
      c(x + half_x, y + half_y),
      c(x - half_x, y + half_y),
      c(x - half_x, y - half_y)
    )))
  })
  sf::st_sf(
    grid_id  = unique_cells,
    geometry = sf::st_sfc(polys, crs = terra::crs(pop_rast))
  )
}

#' Assign district to points using fine raster zonal majority (generalized)
#'
#' Rasterizes districts at fine resolution and assigns each point the district of the cell it falls in.
#'
#' @param destinations Tibble/data.frame with lon, lat columns
#' @param districts An sf object of districts (must have a unique name/id column)
#' @param pop_raster_path Path to population raster (for extent, resolution, and CRS)
#' @param district_col Name of the column in `districts` to use as the district label (default: "name")
#' @param fine_res Resolution for fine rasterization in meters (default: 100)
#' @param proj_crs Optional: EPSG code for projected CRS (default: auto-UTM based on centroid)
#' @return A tibble with district column added
#' @importFrom terra rast ext res crs vect rasterize extract project
#' @export
add_district_to_points_raster <- function(
    destinations,
    districts,
    pop_raster_path,
    district_col = "name",
    fine_res = 100,
    proj_crs = NULL
) {
  # Check district_col exists
  if (!district_col %in% names(districts)) stop("district_col not found in districts")
  # Read population raster for template
  pop_rast <- rast(pop_raster_path)
  # Auto-select projected CRS if not provided (UTM zone for centroid)
  if (is.null(proj_crs)) {
    proj_crs <- find_crs(districts)
  }
  # Transform districts and raster to projected CRS
  districts_proj <- sf::st_transform(districts, crs = proj_crs)
  pop_rast_proj <- terra::project(pop_rast, proj_crs)
  # Create fine raster template in projected CRS
  template <- rast(ext(pop_rast_proj), resolution = fine_res, crs = crs(pop_rast_proj))
  # Rasterize districts (by district_col)
  districts_proj$district_id <- as.integer(as.factor(districts_proj[[district_col]]))
  district_rast <- rasterize(vect(districts_proj), template, field = "district_id")
  # Map district_id back to name
  id_to_name <- setNames(as.character(districts_proj[[district_col]]), districts_proj$district_id)
  # Transform points to projected CRS
  points_proj <- sf::st_transform(
    sf::st_as_sf(destinations, coords = c("lon", "lat"), crs = 4326), crs = proj_crs
  )
  coords_df <- as.data.frame(sf::st_coordinates(points_proj))
  points_vect <- vect(coords_df, crs = sf::st_crs(points_proj)$wkt)
  cell_ids <- terra::extract(district_rast, points_vect)[,2]
  destinations$district <- id_to_name[as.character(cell_ids)]
  destinations <- destinations[!is.na(destinations$district), ]
  return(destinations)
}

#' Assign district to grid cells by zonal majority
#'
#' Processes grid cells that intersect multiple districts. Grid cells intersecting
#' only one district are kept as-is.
#'
#' @param pop_grids_sf An sf object of population grid cell polygons with grid_id column
#' @param assignment_sf An sf object with geometry and assigned district (from st_join)
#' @param districts An sf object of district boundaries (must have unique name/id column)
#' @param district_col Name of the column in `districts` to use as the district label
#' @return An sf object with grid cells assigned to district with largest overlap
#' @importFrom sf st_intersection st_area
#' @importFrom dplyr filter group_by slice_max select bind_rows
#' @keywords internal
assign_boundary_grids_by_area <- function(pop_grids_sf, assignment_sf, districts, district_col) {
  # Identify grid cells with duplicate assignments (intersecting multiple districts)
  boundary_grids <- assignment_sf |>
    dplyr::group_by(grid_id) |>
    dplyr::filter(dplyr::n() > 1) |>
    dplyr::ungroup()
  
  if (nrow(boundary_grids) == 0) {
    return(assignment_sf)
  }
  
  boundary_intersections <- suppressWarnings(
    sf::st_intersection(boundary_grids, districts[district_col])
  )
  
  boundary_intersections$overlap_area <- sf::st_area(boundary_intersections)
  
  # For each grid cell, keep only the district with maximum overlap
  resolved_boundary <- boundary_intersections |>
    dplyr::group_by(grid_id) |>
    dplyr::slice_max(order_by = overlap_area, n = 1, with_ties = FALSE) |>
    dplyr::select(grid_id, geometry = geometry, !!district_col := !!rlang::sym(district_col)) |>
    dplyr::ungroup()
  
  # Combine non-boundary cells with resolved boundary cells
  non_boundary <- assignment_sf |>
    dplyr::group_by(grid_id) |>
    dplyr::filter(dplyr::n() == 1) |>
    dplyr::ungroup()
  
  result <- dplyr::bind_rows(non_boundary, resolved_boundary)
  return(result)
}

#' Assign district to points using zonal majority for ambiguous points
#'
#' Assign grid cells to districts. For points that fall in grid cells intersecting multiple districts, 
#' assign the district with the largest overlap.
#'
#' @param points Tibble/data.frame with lon, lat columns (and optionally id, population)
#' @param districts An sf object of districts (must have a unique name/id column)
#' @param district_col Name of the column in `districts` to use as the district label (default: "name")
#' @param pop_raster_path Path to population raster (for extent, resolution, and CRS)
#' @param crs_out Output CRS for coordinates (default: 4326)
#' @return A tibble with district column added
#' @importFrom sf st_as_sf st_join st_intersection st_area st_drop_geometry st_coordinates
#' @importFrom dplyr mutate bind_cols row_number everything
#' @export
add_district_to_points_zonal <- function(
  points,
  districts,
  pop_raster_path,
  district_col = "name",
  crs_out = 4326
) {
  pop_rast <- terra::rast(pop_raster_path)

  points_rast_crs <- sf::st_transform(
    sf::st_as_sf(points, coords = c("lon", "lat"), crs = crs_out, remove = FALSE),
    crs = terra::crs(pop_rast)
  )
  point_cell_ids <- terra::cellFromXY(pop_rast, sf::st_coordinates(points_rast_crs))

  # Drop points that fall outside the raster extent
  valid <- !is.na(point_cell_ids)
  points_valid <- points[valid, , drop = FALSE]
  points_valid$.grid_id <- point_cell_ids[valid]

  # Build polygons for the unique cells occupied by population points
  pop_grids_sf <- raster_cells_to_sf(pop_rast, points_valid$.grid_id)
  districts_matched_crs <- sf::st_transform(districts, crs = sf::st_crs(pop_grids_sf))

  assigned_sf <- sf::st_join(
    pop_grids_sf,
    districts_matched_crs[district_col],
    left  = TRUE,
    join  = sf::st_intersects
  ) |>
    dplyr::filter(!is.na(!!rlang::sym(district_col)))

  # Resolve boundary cells (those touching >1 district) by largest overlap
  resolved_sf <- assign_boundary_grids_by_area(
    pop_grids_sf, assigned_sf, districts_matched_crs, district_col
  )

  resolved_tidy <- resolved_sf |>
    sf::st_drop_geometry() |>
    dplyr::transmute(.grid_id = grid_id, district = !!rlang::sym(district_col))

  result <- points_valid |>
    dplyr::left_join(resolved_tidy, by = ".grid_id") |>
    dplyr::filter(!is.na(district)) |>
    dplyr::select(-.grid_id)

  return(result)
}
