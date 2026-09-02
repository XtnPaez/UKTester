# Unit tests for dashboard_server.R helpers

library(testthat)

test_that("travel_time_threshold_from_km uses WALK speed", {
  expect_equal(
    travel_time_threshold_from_km(10, mode = "WALK"),
    10 * 60 / 3.6,
    tolerance = 1e-8
  )
})

test_that("travel_time_threshold_from_km uses BICYCLE speed", {
  expect_equal(
    travel_time_threshold_from_km(10, mode = "BICYCLE"),
    10 * 60 / 12,
    tolerance = 1e-8
  )
})

test_that("travel_time_threshold_from_km accepts case-insensitive mode", {
  expect_equal(
    travel_time_threshold_from_km(8, mode = "bicycle"),
    8 * 60 / 12,
    tolerance = 1e-8
  )
})

test_that("travel_time_threshold_from_km validates mode", {
  expect_error(
    travel_time_threshold_from_km(10, mode = "CAR"),
    "mode must be either 'WALK' or 'BICYCLE'"
  )
})
