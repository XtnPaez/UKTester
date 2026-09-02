# Unit tests for add_district_to_points and related functions

# Test find_crs

test_that("find_crs returns correct UTM zone for northern hemisphere", {
  # Create a simple square polygon in northern hemisphere (e.g., longitude 30, latitude 10)
  poly <- sf::st_sfc(sf::st_polygon(list(matrix(c(30,10, 31,10, 31,11, 30,11, 30,10), ncol=2, byrow=TRUE))), crs=4326)
  districts <- sf::st_sf(name = "TestDistrict", geometry = poly)
  crs_code <- find_crs(districts)
  # UTM zone for lon=30 is 36, so EPSG:32636
  expect_equal(crs_code, "EPSG:32636")
})

test_that("find_crs returns correct UTM zone for southern hemisphere", {
  # Create a simple square polygon in southern hemisphere (e.g., longitude 34, latitude -13)
  poly <- sf::st_sfc(sf::st_polygon(list(matrix(c(34,-13, 35,-13, 35,-12, 34,-12, 34,-13), ncol=2, byrow=TRUE))), crs=4326)
  districts <- sf::st_sf(name = "TestDistrict", geometry = poly)
  crs_code <- find_crs(districts)
  # UTM zone for lon=34 is 36, so EPSG:32736
  expect_equal(crs_code, "EPSG:32736")
})

test_that("find_crs works for multiple polygons", {
  # Two polygons, one in zone 35, one in zone 36, centroid should be between
  poly1 <- sf::st_sfc(sf::st_polygon(list(matrix(c(28,-13, 29,-13, 29,-12, 28,-12, 28,-13), ncol=2, byrow=TRUE))), crs=4326)
  poly2 <- sf::st_sfc(sf::st_polygon(list(matrix(c(34,-13, 35,-13, 35,-12, 34,-12, 34,-13), ncol=2, byrow=TRUE))), crs=4326)
  districts <- sf::st_sf(name = c("A", "B"), geometry = sf::st_sfc(poly1[[1]], poly2[[1]], crs=4326))
  crs_code <- find_crs(districts)
  # Centroid will be somewhere between, but still southern hemisphere, likely zone 36
  expect_true(grepl("EPSG:3273", crs_code))
})

test_that("raster_cells_to_sf returns empty sf for empty cell ids", {
  r <- terra::rast(nrows = 2, ncols = 2, xmin = 0, xmax = 2, ymin = 0, ymax = 1, crs = "EPSG:4326")
  out <- raster_cells_to_sf(r, integer(0))
  expect_s3_class(out, "sf")
  expect_equal(nrow(out), 0)
  expect_true(all(c("grid_id", "geometry") %in% names(out)))
})


# Helper: create a simple districts sf object
districts <- sf::st_sf(
  name = c("A", "B"),
  geometry = sf::st_sfc(
    sf::st_polygon(list(matrix(c(0,0, 1,0, 1,1, 0,1, 0,0), ncol=2, byrow=TRUE))),
    sf::st_polygon(list(matrix(c(1,0, 2,0, 2,1, 1,1, 1,0), ncol=2, byrow=TRUE)))
  ),
  crs = 4326
)

# Helper: create a simple population tibble
test_pop <- tibble::tibble(
  id = 1:2,
  lon = c(0.5, 1.5),
  lat = c(0.5, 0.5),
  population = c(100, 200)
)

# Test add_district_to_points

test_that("add_district_to_points assigns correct district", {
  res <- add_district_to_points(test_pop, districts)
  expect_equal(res$district, c("A", "B"))
  expect_equal(res$population, c(100, 200))
})

# Test add_district_to_points_raster

test_that("add_district_to_points_raster assigns correct district", {
  # Create a dummy raster covering both districts
  r <- terra::rast(nrows=2, ncols=2, xmin=0, xmax=2, ymin=0, ymax=1, crs="EPSG:4326")
  terra::values(r) <- 1:4
  tmpfile <- tempfile(fileext = ".tif")
  terra::writeRaster(r, tmpfile, overwrite=TRUE)
  res <- add_district_to_points_raster(
    destinations = test_pop,
    districts = districts,
    pop_raster_path = tmpfile,
    district_col = "name",
    fine_res = 0.5,
    proj_crs = "EPSG:4326"
  )
  expect_true(all(res$district %in% c("A", "B")))
})

# Test add_district_to_points_zonal

test_that("add_district_to_points_zonal assigns correct district", {
  # Create a dummy raster covering both districts
  r <- terra::rast(nrows=2, ncols=2, xmin=0, xmax=2, ymin=0, ymax=1, crs="EPSG:4326")
  terra::values(r) <- 1:4
  tmpfile <- tempfile(fileext = ".tif")
  terra::writeRaster(r, tmpfile, overwrite=TRUE)
  res <- add_district_to_points_zonal(
    points = test_pop,
    districts = districts,
    pop_raster_path = tmpfile,
    district_col = "name",
    crs_out = 4326
  )
  expect_true(all(res$district %in% c("A", "B")))
})

# Test assign_boundary_grids_by_area

test_that("assign_boundary_grids_by_area resolves duplicate grid assignment", {
  pop_grids_sf <- sf::st_sf(
    grid_id = 1L,
    geometry = sf::st_sfc(
      sf::st_polygon(list(matrix(c(0.4,0.4, 1.1,0.4, 1.1,0.6, 0.4,0.6, 0.4,0.4), ncol = 2, byrow = TRUE)))
    ),
    crs = 4326
  )

  assignment_sf <- sf::st_sf(
    grid_id = c(1L, 1L),
    name = c("A", "B"),
    geometry = sf::st_sfc(pop_grids_sf$geometry[[1]], pop_grids_sf$geometry[[1]], crs = 4326)
  )

  res <- assign_boundary_grids_by_area(
    pop_grids_sf = pop_grids_sf,
    assignment_sf = assignment_sf,
    districts = districts,
    district_col = "name"
  )

  expect_s3_class(res, "sf")
  expect_equal(nrow(res), 1)
  expect_equal(res$grid_id, 1L)
  expect_equal(as.character(res$name), "A")
})
