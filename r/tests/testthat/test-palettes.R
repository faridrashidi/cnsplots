test_that("the palette registry matches the Python 0.5.0 surface", {
  expect_length(palette_names(), 35)
  expect_length(palette_names("qualitative"), 28)
  expect_length(palette_names("continuous"), 7)
  expect_equal(palette_names()[1:3], c("Set1", "Set2", "Set3"))
  expect_equal(tail(palette_names(), 2), c("gnuplot", "hot"))
  expect_false(any(c("NPG", "AAAS", "OrBl_custom", "RdBu_custom") %in% palette_names()))
})

test_that("all qualitative colours exactly match the locked fixture", {
  fixture <- utils::read.csv(
    testthat::test_path("fixtures", "python-v0.5.0-qualitative-palettes.csv"),
    stringsAsFactors = FALSE
  )
  for (name in unique(fixture$palette)) {
    expected <- fixture$hex[fixture$palette == name]
    expect_identical(palettes(name), expected, info = name)
  }
})

test_that("all continuous lookup tables exactly match the locked fixture", {
  fixture <- utils::read.csv(
    testthat::test_path("fixtures", "python-v0.5.0-continuous-lut.csv"),
    stringsAsFactors = FALSE
  )
  for (name in unique(fixture$palette)) {
    expected <- fixture$hex[fixture$palette == name]
    expect_identical(palettes(name), expected, info = name)
  }
})

test_that("qualitative palettes cycle in author order", {
  base <- palettes("Ecotyper2")
  expect_identical(palettes("Ecotyper2", n = 7), c(base, base[1:2]))
  expect_identical(palettes("Ecotyper2", n = 3, direction = -1), rev(base)[1:3])
  expect_identical(palettes(c("red", "#00ff00")), c("#ff0000", "#00ff00"))
  expect_identical(palettes("red"), "#ff0000")
})

test_that("palette lookup rejects historical aliases and invalid requests", {
  expect_error(palettes("NPG"), "Unknown palette")
  expect_error(palettes("AAAS"), "Unknown palette")
  expect_error(palettes("Parula"), "Unknown palette")
  expect_error(palettes("Set1", n = -1), "non-negative whole")
  expect_error(palettes("Set1", direction = 0), "1 or -1")
})

test_that("colour extraction uses ordinary one-based R indices", {
  expect_identical(
    get_hexcolors_from_apalette(c(1, 2), "Set1"),
    c("#e41a1c", "#377eb8")
  )
  expect_error(get_hexcolors_from_apalette(0, "Set1"), "one-based")
})

test_that("public colour constants match the author values", {
  expect_identical(RED, "#D6372E")
  expect_identical(BLUE, "#5189BB")
  expect_identical(CHOCOLATE, "#662506")
})
