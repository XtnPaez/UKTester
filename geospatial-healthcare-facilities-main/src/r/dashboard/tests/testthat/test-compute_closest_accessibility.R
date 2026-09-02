# Unit tests for compute_closest_accessibility

destinations <- tibble::tibble(
  id = 1:2,
  lon = c(34.0, 34.1),
  lat = c(-13.9, -13.8),
  population = c(100, 200)
)

healthcare <- tibble::tibble(
  id = 101:102,
  lon = c(34.0, 34.1),
  lat = c(-13.9, -13.8),
  type = c("Hospital", "Clinic")
)

test_that("compute_closest_accessibility validates max_travel_time", {
  expect_error(
    compute_closest_accessibility(
      r5r_network = NULL,
      healthcare = healthcare,
      destinations = destinations,
      max_travel_time = 0
    ),
    "single positive number"
  )

  expect_error(
    compute_closest_accessibility(
      r5r_network = NULL,
      healthcare = healthcare,
      destinations = destinations,
      max_travel_time = c(10, 20)
    ),
    "single positive number"
  )
})

test_that("compute_closest_accessibility validates mode", {
  expect_error(
    compute_closest_accessibility(
      r5r_network = NULL,
      healthcare = healthcare,
      destinations = destinations,
      mode = "CAR",
      max_travel_time = 10
    ),
    "mode must be either 'WALK' or 'BICYCLE'"
  )
})
