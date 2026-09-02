# Unit tests for get_population_points

library(testthat)

test_that("get_population_points returns correct columns and values", {
  # Create a dummy raster
  r <- terra::rast(nrows=2, ncols=2, xmin=0, xmax=2, ymin=0, ymax=2)
  terra::values(r) <- c(10, 20, 30, 40)
  tmpfile <- tempfile(fileext = ".tif")
  terra::writeRaster(r, tmpfile, overwrite=TRUE)
  pts <- get_population_points(tmpfile)
  expect_true(all(c("id", "lon", "lat", "population") %in% names(pts)))
  expect_equal(nrow(pts), 4)
  expect_true(all(pts$population %in% c(10, 20, 30, 40)))
  expect_true(is.numeric(pts$lon) && is.numeric(pts$lat))
})
