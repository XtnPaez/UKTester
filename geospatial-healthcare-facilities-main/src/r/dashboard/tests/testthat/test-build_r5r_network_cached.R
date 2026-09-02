test_that("build_r5r_network_cached exposes expected interface", {
	expect_true(is.function(build_r5r_network_cached))
	expect_equal(names(formals(build_r5r_network_cached)), "data_path")
})
