with_default_figure_settings <- function(code) {
  previous <- reset_settings()
  on.exit(settings(.list = previous), add = TRUE)
  force(code)
}

test_that("the default figure specification matches Python sizing semantics", {
  with_default_figure_settings({
    spec <- figure()

    expect_s3_class(spec, "figure_spec")
    expect_equal(spec$width, 150)
    expect_equal(spec$height, 150)
    expect_equal(spec$units, "pt")
    expect_equal(spec$width_in, 150 / 72)
    expect_equal(spec$height_in, 150 / 72)
    expect_equal(spec$dpi, 288)
    expect_equal(spec$pixel_width, 600L)
    expect_equal(spec$pixel_height, 600L)
    expect_equal(spec$palette, "Ecotyper1")
    expect_equal(spec$cmap, "gnuplot")
    expect_equal(spec$background, "transparent")
    expect_equal(spec$python_reference, "cnsplots 0.5.0")
  })
})

test_that("all supported figure units convert to inches", {
  cases <- list(px72 = 72, pt = 72, mm = 25.4, cm = 2.54, `in` = 1)

  for (units in names(cases)) {
    spec <- figure(
      width = cases[[units]], height = cases[[units]], units = units, dpi = 100
    )
    expect_equal(spec$width_in, 1, info = units)
    expect_equal(spec$height_in, 1, info = units)
    expect_equal(spec$width_mm, 25.4, info = units)
    expect_equal(spec$pixel_width, 100L, info = units)
  }
})

test_that("figure specifications validate dimensions and appearance", {
  expect_error(figure(width = 0), "greater than zero")
  expect_error(figure(height = NA_real_), "finite number")
  expect_error(figure(dpi = 0), "greater than zero")
  expect_error(figure(units = "pixels"), "arg")
  expect_error(figure(background = "not-a-colour"), "valid R colour")
})

test_that("figure specifications print a compact summary", {
  spec <- figure(width = 1, height = 2, units = "in", dpi = 100)

  output <- capture.output(returned <- print(spec))
  expect_match(paste(output, collapse = "\n"), "<figure_spec>", fixed = TRUE)
  expect_match(paste(output, collapse = "\n"), "25.400 x 50.800 mm", fixed = TRUE)
  expect_match(paste(output, collapse = "\n"), "100 x 200 px at 100 DPI", fixed = TRUE)
  expect_identical(returned, spec)
})

test_that("the direct figure API returns a reusable specification", {
  spec <- figure(width = 2, height = 3, units = "in")

  expect_s3_class(spec, "figure_spec")
  expect_equal(spec$width_in, 2)
  expect_equal(spec$height_in, 3)
})

test_that("export rejects ambiguous or inconsistent requests", {
  plot <- ggplot2::ggplot(mtcars, ggplot2::aes(wt, mpg)) +
    ggplot2::geom_point()
  spec <- figure(width = 1, height = 1, units = "in")

  expect_error(
    savefig(tempfile("cnsplots-no-extension-"), plot = plot, spec = spec),
    "supported extension"
  )
  expect_error(
    savefig(file.path(tempdir(), "cnsplots.unsupported"), plot = plot, spec = spec),
    "Unsupported extension"
  )
  expect_error(
    savefig(file.path(tempdir(), "cnsplots.png"), plot = plot, spec = spec, device = "pdf"),
    "does not match"
  )
  expect_error(
    savefig(file.path(tempdir(), "cnsplots.png"), plot = plot, spec = list()),
    "created by figure"
  )
  expect_error(
    savefig(file.path(tempdir(), "cnsplots.png"), plot = NULL, spec = spec),
    "plot must be supplied"
  )
})

test_that("PNG export creates parent directories and returns its path", {
  skip_if_not(capabilities("png"))

  root <- tempfile("cnsplots-export-")
  on.exit(unlink(root, recursive = TRUE, force = TRUE), add = TRUE)
  filename <- file.path(root, "nested", "scatter.png")
  plot <- ggplot2::ggplot(mtcars, ggplot2::aes(wt, mpg)) +
    ggplot2::geom_point() +
    setup_ggplot()
  spec <- figure(
    width = 1, height = 1, units = "in", dpi = 72, background = "white"
  )

  path <- savefig(filename, plot = plot, spec = spec)

  expect_true(dir.exists(dirname(filename)))
  expect_true(file.exists(filename))
  expect_identical(
    path,
    normalizePath(filename, winslash = "/", mustWork = FALSE)
  )
})
