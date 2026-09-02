# Unit tests for get_healthcare_facilities

# Create a mock districts sf object
districts <- sf::st_sf(
  name = c("DistrictA", "DistrictB"),
  geometry = sf::st_sfc(
    sf::st_polygon(list(matrix(c(0,0, 1,0, 1,1, 0,1, 0,0), ncol=2, byrow=TRUE))),
    sf::st_polygon(list(matrix(c(1,0, 2,0, 2,1, 1,1, 1,0), ncol=2, byrow=TRUE)))
  ),
  crs = 4326
)

test_that("get_healthcare_facilities loads local healthsites-like CSV and joins districts", {
  test_facilities <- data.frame(
    X = c(0.5, 1.5, NA),
    Y = c(0.5, 0.5, 0.7),
    osm_id = c("A1", "B1", "C1"),
    amenity = c("Hospital", "Clinic", "Clinic"),
    operator = c("Govt", "Private", "Govt"),
    name = c("FacilityA", "FacilityB", "FacilityC")
  )
  tmp <- tempfile(fileext = ".csv")
  readr::write_csv(test_facilities, tmp)

  res <- suppressWarnings(
    get_healthcare_facilities(districts = districts, filepath = tmp, country = "Malawi", crs_out = 4326)
  )
  expect_true(all(c("id", "lon", "lat", "name", "type", "ownership", "district") %in% names(res)))
  expect_true(all(res$id %in% c("A1", "B1")))
  expect_true(all(res$district %in% c("DistrictA", "DistrictB")))
  expect_true(all(res$type %in% c("Hospital", "Clinic")))
})

test_that("clean_healthcare_facilities maps x/y/osm_id columns", {
  df <- data.frame(
    X = c("34.1", "34.2"),
    Y = c("-13.9", "-13.8"),
    osm_id = c("id1", "id2"),
    amenity = c("Hospital", "Clinic"),
    operator = c("Govt", "Private")
  )

  cleaned <- clean_healthcare_facilities(df)
  expect_true(all(c("lon", "lat", "id", "type", "ownership") %in% names(cleaned)))
  expect_equal(cleaned$id, c("id1", "id2"))
  expect_equal(cleaned$type, c("Hospital", "Clinic"))
})
