distribution_fixture <- function() {
  data.frame(
    category = rep(c("B", "A"), each = 6),
    value = c(1, 2, 2, 3, 4, 12, 4, 5, 5, 6, 7, 8),
    hue = rep(c("h1", "h2"), 6),
    stringsAsFactors = FALSE
  )
}

distribution_layer_value <- function(layer, name) {
  for (slot in c("aes_params", "geom_params", "stat_params")) {
    params <- layer[[slot]]
    if (name %in% names(params)) return(params[[name]])
  }
  if (startsWith(name, "outlier.")) {
    parameter <- sub("^outlier[.]", "", name)
    outlier <- layer[["geom_params"]][["outlier_gp"]]
    if (parameter %in% names(outlier)) return(outlier[[parameter]])
  }
  NULL
}

test_that("distribution functions return ordinary ggplots without changing input", {
  data <- distribution_fixture()
  original <- data

  plots <- list(
    boxplot(data, "category", "value"),
    violinplot(data, "category", "value"),
    distplot(data, "value"),
    qqplot(data, "value")
  )

  expect_true(all(vapply(plots, inherits, logical(1), what = "ggplot")))
  expect_identical(data, original)
})

test_that("boxplot encodes the Python visual defaults and count labels", {
  data <- distribution_fixture()
  plot <- boxplot(data, "category", "value", add_count = TRUE)

  expect_equal(distribution_layer_value(plot$layers[[2L]], "width"), 0.5)
  expect_true(is.na(distribution_layer_value(plot$layers[[2L]], "outlier.shape")))
  expect_equal(
    distribution_layer_value(plot$layers[[2L]], "linewidth"),
    0.8 * 25.4 / 72
  )
  expect_identical(
    distribution_layer_value(plot$layers[[3L]], "colour"),
    "white"
  )
  expect_equal(
    unname(plot$scales$get_scales("x")$labels),
    c("B\n(n=6)", "A\n(n=6)")
  )

  with_outliers <- boxplot(data, "category", "value", showoutliers = TRUE)
  expect_equal(
    distribution_layer_value(with_outliers$layers[[2L]], "outlier.shape"),
    19
  )
  expect_equal(
    distribution_layer_value(with_outliers$layers[[2L]], "outlier.size"),
    1.5 * 25.4 / 72
  )

  min_to_max <- boxplot(data, "category", "value", whis = c(0, 100))
  expect_equal(
    distribution_layer_value(min_to_max$layers[[2L]], "coef"),
    Inf
  )
})

test_that("violinplot adds the narrow white box recipe on request", {
  data <- distribution_fixture()
  with_box <- violinplot(data, "category", "value", add_count = TRUE)
  without_box <- violinplot(data, "category", "value", add_box = FALSE)

  expect_equal(distribution_layer_value(with_box$layers[[1L]], "width"), 0.6)
  expect_equal(
    distribution_layer_value(with_box$layers[[1L]], "linewidth"),
    0.001 * 25.4 / 72
  )
  expect_equal(distribution_layer_value(with_box$layers[[2L]], "width"), 0.2)
  expect_identical(
    distribution_layer_value(with_box$layers[[2L]], "fill"),
    "white"
  )
  expect_identical(
    distribution_layer_value(with_box$layers[[2L]], "colour"),
    "black"
  )
  expect_equal(
    distribution_layer_value(with_box$layers[[2L]], "linewidth"),
    0.4 * 25.4 / 72
  )
  expect_identical(
    distribution_layer_value(with_box$layers[[3L]], "colour"),
    "black"
  )
  expect_equal(
    distribution_layer_value(with_box$layers[[3L]], "linewidth"),
    0.8 * 25.4 / 72
  )
  expect_length(with_box$layers, 3L)
  expect_length(without_box$layers, 1L)
  expect_equal(
    unname(with_box$scales$get_scales("x")$labels),
    c("B\n(n=6)", "A\n(n=6)")
  )
})

test_that("category order, hue order, and palette cycling are deterministic", {
  data <- distribution_fixture()
  ordered <- boxplot(
    data,
    "category",
    "value",
    hue = "hue",
    order = c("A", "B"),
    hue_order = c("h2", "h1")
  )

  expect_identical(levels(ordered$data$.x), c("A", "B"))
  expect_identical(levels(ordered$data$.group), c("h2", "h1"))

  many_hues <- data.frame(
    category = rep("A", 22),
    value = seq_len(22),
    hue = rep(sprintf("h%02d", seq_len(11)), each = 2),
    stringsAsFactors = FALSE
  )
  cycled <- boxplot(many_hues, "category", "value", hue = "hue")
  colours <- cycled$scales$get_scales("fill")$palette(11)

  expect_length(colours, 11L)
  expect_equal(colours[[10L]], colours[[1L]])
  expect_equal(colours[[11L]], colours[[2L]])
})

test_that("statistical pairs fail explicitly until the R API supports them", {
  data <- distribution_fixture()

  expect_error(
    boxplot(data, "category", "value", pairs = list(c("A", "B"))),
    "pairs is not supported"
  )
  expect_error(
    violinplot(data, "category", "value", pairs = list(c("A", "B"))),
    "pairs is not supported"
  )
  expect_error(
    boxplot(data, "category", "value", addcount = TRUE),
    "use add_count"
  )
  expect_error(
    violinplot(data, "category", "value", addcount = TRUE),
    "use add_count"
  )
})

test_that("distplot combines a common-bin histogram with count-scaled KDE", {
  data <- distribution_fixture()
  plot <- distplot(data, "value")

  expect_length(plot$layers, 2L)
  expect_s3_class(plot$layers[[1L]]$geom, "GeomBar")
  expect_s3_class(plot$layers[[2L]]$geom, "GeomLine")

  binwidth <- distribution_layer_value(plot$layers[[1L]], "binwidth")
  estimate <- stats::density(data$value)
  expect_equal(plot$layers[[2L]]$data$.x, estimate$x)
  expect_equal(
    plot$layers[[2L]]$data$.count,
    estimate$y * nrow(data) * binwidth
  )

  grouped <- distplot(
    data,
    "value",
    hue = "hue",
    hue_order = c("h2", "h1")
  )
  expect_identical(levels(grouped$data$.group), c("h2", "h1"))
})

test_that("qqplot uses statsmodels plotting positions and marker defaults", {
  data <- data.frame(value = c(8, 1, 5, 3))
  plot <- qqplot(data, "value")

  expect_equal(
    plot$data$.theoretical,
    stats::qnorm(seq_len(4) / 5)
  )
  expect_identical(plot$data$.sample, c(1, 3, 5, 8))
  expect_identical(
    distribution_layer_value(plot$layers[[1L]], "colour"),
    "black"
  )
  expect_equal(
    distribution_layer_value(plot$layers[[1L]], "size"),
    3 * 25.4 / 72
  )
  expect_equal(distribution_layer_value(plot$layers[[1L]], "stroke"), 0)
})

test_that("distribution functions reject invalid data contracts", {
  data <- distribution_fixture()

  expect_error(boxplot(data, "missing", "value"), "missing column")
  expect_error(boxplot(data, "category", "missing"), "missing column")
  expect_error(
    boxplot(transform(data, value = as.character(value)), "category", "value"),
    "must be numeric"
  )
  expect_error(distplot(data, "category"), "must be numeric")
  expect_error(qqplot(data, "category"), "must be numeric")
  expect_error(
    boxplot(data, "category", "value", order = character()),
    "order must not be empty"
  )
  expect_error(
    boxplot(
      data, "category", "value", hue = "hue", hue_order = character()
    ),
    "hue_order must not be empty"
  )
  expect_error(
    violinplot(data[FALSE, , drop = FALSE], "category", "value"),
    "must not be empty"
  )
  expect_error(
    qqplot(transform(data, value = Inf), "value"),
    "no finite observations"
  )
})
