# Unit tests for get_subgroup_population_files and create_population_subgroup_rasters

test_that("get_subgroup_population_files returns folder path and skips if exists", {
  tmpdir <- tempfile()
  dir.create(tmpdir)
  # Simulate extracted folder
  folder_path <- file.path(tmpdir, "test")
  dir.create(folder_path)

  res <- suppressMessages(
    get_subgroup_population_files(
      filepath = file.path(tmpdir, "dummy.zip"),
      year = 2025,
      release = "R2025A",
      dest_dir = tmpdir,
      zip_name = "test.zip",
      unzip_folder = tmpdir
    )
  )
  expect_equal(res, folder_path)
})

test_that("create_population_subgroup_rasters creates and returns a raster stack", {
  # Create dummy rasters for subgroups
  tmp_raw <- tempfile()
  dir.create(tmp_raw)
  folder_name <- "dummy"
  input_dir <- file.path(tmp_raw, folder_name)
  dir.create(input_dir)

  # Create 2 dummy tif files for females and males
  f1 <- file.path(input_dir, "mwi_f_00_2025_CN_100m_R2025A_v1.tif")
  f2 <- file.path(input_dir, "mwi_m_00_2025_CN_100m_R2025A_v1.tif")
  r <- terra::rast(nrows = 2, ncols = 2, xmin = 0, xmax = 2, ymin = 0, ymax = 2)
  terra::values(r) <- 1:4
  terra::writeRaster(r, f1, overwrite = TRUE)
  terra::writeRaster(r, f2, overwrite = TRUE)

  tmp_out <- tempfile()
  dir.create(tmp_out)
  stack <- suppressMessages(
    create_population_subgroup_rasters(
      country = "Malawi",
      raw_dir = tmp_raw,
      filepath = input_dir,
      year = 2025,
      out_dir = tmp_out
    )
  )
  expect_true(inherits(stack, "SpatRaster"))
  expect_true(all(c("Females", "Males", "Total population") %in% names(stack)))
})
