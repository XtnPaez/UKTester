# Unit tests for io_helpers.R

library(testthat)

test_that("write_output writes CSV correctly", {
  tmpfile <- tempfile(fileext = ".csv")
  df <- tibble::tibble(x = 1:3, y = c("a", "b", "c"))
  write_output(df, tmpfile, format = "csv")
  df2 <- read.csv(tmpfile)
  expect_equal(df2$x, 1:3)
  expect_equal(as.character(df2$y), c("a", "b", "c"))
})

test_that("write_output writes Parquet correctly", {
  tmpfile <- tempfile(fileext = ".parquet")
  df <- tibble::tibble(x = 1:3, y = c("a", "b", "c"))
  write_output(df, tmpfile, format = "parquet")
  df2 <- as.data.frame(arrow::read_parquet(tmpfile))
  expect_equal(df2$x, 1:3)
  expect_equal(as.character(df2$y), c("a", "b", "c"))
})

# Test error for unsupported format

test_that("write_output errors for unsupported format", {
  tmpfile <- tempfile()
  df <- tibble::tibble(x = 1:3)
  expect_error(write_output(df, tmpfile, format = "xlsx"), "Unsupported format")
})
