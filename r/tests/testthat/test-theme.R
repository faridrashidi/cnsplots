test_that("setup_ggplot returns a complete native theme", {
  theme <- setup_ggplot()

  expect_s3_class(theme, "theme")
  expect_true(isTRUE(attr(theme, "complete")))
})

test_that("the standard profile encodes the publication baseline", {
  theme <- setup_ggplot("standard")

  expect_equal(theme$plot.title$size, 8)
  expect_equal(theme$plot.title$face, "bold")
  expect_equal(theme$plot.title$hjust, 0.5)
  expect_equal(theme$axis.title$size, 8)
  expect_equal(theme$axis.text$size, 7)
  expect_equal(theme$legend.text$size, 7)
  expect_s3_class(theme$panel.grid.major, "element_blank")
  expect_s3_class(theme$panel.grid.minor, "element_blank")
  expect_equal(theme$panel.background$fill, "transparent")
  expect_equal(theme$plot.background$fill, "transparent")
  expect_equal(as.numeric(theme$axis.ticks.length), 2)
  expect_s3_class(theme$axis.line.x.top, "element_blank")
  expect_s3_class(theme$axis.line.y.right, "element_blank")
})

test_that("specialized profiles remove only their intended axes", {
  embedding <- setup_ggplot("embedding")
  matrix <- setup_ggplot("matrix")

  expect_s3_class(embedding$axis.title, "element_blank")
  expect_s3_class(embedding$axis.text, "element_blank")
  expect_s3_class(embedding$axis.line, "element_blank")
  expect_s3_class(embedding$axis.ticks, "element_blank")

  expect_s3_class(matrix$axis.title, "element_blank")
  expect_s3_class(matrix$axis.line, "element_blank")
  expect_s3_class(matrix$axis.ticks, "element_blank")
  expect_s3_class(matrix$panel.border, "element_blank")
  expect_s3_class(matrix$axis.text, "element_text")
})

test_that("axis and legend components are incomplete theme patches", {
  axes <- theme_axes(
    x = FALSE, y = FALSE, ticks = FALSE,
    tick_labels = FALSE, titles = FALSE
  )
  legend <- theme_legend(
    position = "bottom", direction = "horizontal", title = FALSE
  )

  expect_s3_class(axes, "theme")
  expect_false(isTRUE(attr(axes, "complete")))
  expect_s3_class(axes$axis.line.x, "element_blank")
  expect_s3_class(axes$axis.line.y, "element_blank")
  expect_s3_class(axes$axis.ticks.x, "element_blank")
  expect_s3_class(axes$axis.ticks.y, "element_blank")
  expect_s3_class(axes$axis.text.x, "element_blank")
  expect_s3_class(axes$axis.text.y, "element_blank")
  expect_s3_class(axes$axis.title.x, "element_blank")
  expect_s3_class(axes$axis.title.y, "element_blank")

  expect_false(isTRUE(attr(legend, "complete")))
  expect_equal(legend$legend.position, "bottom")
  expect_equal(legend$legend.direction, "horizontal")
  expect_s3_class(legend$legend.title, "element_blank")
  expect_s3_class(legend$legend.background, "element_blank")
})

test_that("facet, grid, and spacing components are composable", {
  facet_blank <- theme_facet(background = FALSE)
  facet_filled <- theme_facet(background = TRUE, face = "italic", size = 9)
  grid <- theme_grid(major = "x", minor = "y")
  spacing <- theme_spacing(
    plot_margin = c(1, 2, 3, 4), panel_spacing = 5, legend_spacing = 6
  )

  expect_s3_class(facet_blank$strip.background, "element_blank")
  expect_s3_class(facet_filled$strip.background, "element_rect")
  expect_equal(facet_filled$strip.background$fill, "grey95")
  expect_equal(facet_filled$strip.text$face, "italic")
  expect_equal(facet_filled$strip.text$size, 9)

  expect_s3_class(grid$panel.grid.major.x, "element_line")
  expect_s3_class(grid$panel.grid.major.y, "element_blank")
  expect_s3_class(grid$panel.grid.minor.x, "element_blank")
  expect_s3_class(grid$panel.grid.minor.y, "element_line")

  expect_false(isTRUE(attr(spacing, "complete")))
  expect_equal(as.numeric(spacing$plot.margin), c(1, 2, 3, 4))
  expect_equal(as.numeric(spacing$panel.spacing), 5)
  expect_equal(as.numeric(spacing$legend.spacing), 6)
})

test_that("temporary settings flow into newly created themes", {
  before <- settings()

  theme <- with_settings(
    list(
      title_fontsize = 11,
      title_fontweight = "plain",
      legend_fontsize = 6,
      axes_labelcolor = "navy",
      xtick_major_size = 3,
      ytick_major_size = 3
    ),
    setup_ggplot()
  )

  expect_equal(theme$plot.title$size, 11)
  expect_equal(theme$plot.title$face, "plain")
  expect_equal(theme$axis.text$size, 6)
  expect_equal(theme$text$colour, "navy")
  expect_equal(as.numeric(theme$axis.ticks.length), 3)
  expect_identical(settings(), before)
})

test_that("theme components validate structural arguments", {
  expect_error(theme_axes(x = NA), "TRUE or FALSE")
  expect_error(
    theme_legend(direction = "diagonal"),
    "direction must be one of"
  )
  expect_error(theme_facet(size = 0), "greater than zero")
  expect_error(theme_grid(linewidth = 0), "greater than zero")
  expect_error(theme_spacing(plot_margin = c(1, 2)), "top, right, bottom")
})
