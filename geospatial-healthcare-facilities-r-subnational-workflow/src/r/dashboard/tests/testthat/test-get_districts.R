# Unit tests for get_districts/get_file_districts

test_that("get_file_districts loads and renames selected name column", {
  src <- sf::st_sf(
    district_name = c("DistrictA", "DistrictB"),
    geometry = sf::st_sfc(
      sf::st_polygon(list(matrix(c(0,0, 1,0, 1,1, 0,1, 0,0), ncol = 2, byrow = TRUE))),
      sf::st_polygon(list(matrix(c(1,0, 2,0, 2,1, 1,1, 1,0), ncol = 2, byrow = TRUE)))
    ),
    crs = 4326
  )

  tmp <- tempfile(fileext = ".geojson")
  sf::write_sf(src, tmp, quiet = TRUE)

  res <- get_file_districts(filepath = tmp, name_col = "district_name", crs = 4326)
  expect_s3_class(res, "sf")
  expect_true(all(c("name") %in% names(res)))
  expect_equal(sf::st_crs(res)$epsg, 4326)
  expect_true(nrow(res) == 2)
  expect_true(all(res$name %in% c("DistrictA", "DistrictB")))
})

test_that("get_districts uses local file path when provided", {
  src <- sf::st_sf(
    district_name = c("DistrictA", "DistrictB"),
    geometry = sf::st_sfc(
      sf::st_polygon(list(matrix(c(0,0, 1,0, 1,1, 0,1, 0,0), ncol = 2, byrow = TRUE))),
      sf::st_polygon(list(matrix(c(1,0, 2,0, 2,1, 1,1, 1,0), ncol = 2, byrow = TRUE)))
    ),
    crs = 4326
  )

  tmp <- tempfile(fileext = ".geojson")
  sf::write_sf(src, tmp, quiet = TRUE)

  res <- suppressMessages(
    get_districts(country = "", filepath = tmp, name_col = "district_name", admin_level = 4, crs = 4326)
  )
  expect_s3_class(res, "sf")
  expect_equal(sort(unique(res$name)), c("DistrictA", "DistrictB"))
})
