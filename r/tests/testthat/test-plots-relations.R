slopeplot_r <- getFromNamespace("slopeplot", "cnsplots")

slope_fixture <- function() {
  data.frame(
    site = c("A", "A", "A", "A"),
    subject = c("one", "two", "two", "one"),
    condition = c("before", "before", "after", "after"),
    value = c(1, 10, 20, 2),
    stringsAsFactors = FALSE
  )
}

slope_line_data <- function(plot) {
  rbind(plot$layers[[1L]]$data, plot$layers[[2L]]$data)
}

test_that("slopeplot exposes the direct R API without changing state", {
  data <- slope_fixture()
  original <- data
  settings_before <- settings()
  theme_before <- ggplot2::theme_get()

  expect_identical(
    names(formals(slopeplot_r)),
    c("data", "x", "y", "hue", "pair", "hue_order")
  )
  expect_output(
    plot <- slopeplot_r(data, "site", "value", "condition", "subject"),
    NA
  )
  expect_s3_class(plot, "ggplot")
  expect_identical(data, original)
  expect_identical(settings(), settings_before)
  expect_identical(ggplot2::theme_get(), theme_before)
})

test_that("slopeplot aligns conditions by the pair key", {
  plot <- slopeplot_r(
    slope_fixture(), "site", "value", "condition", "subject"
  )
  lines <- slope_line_data(plot)
  lines <- lines[order(lines$.group), , drop = FALSE]

  expect_identical(lines$.group, c("one", "two"))
  expect_equal(lines$.y, c(1, 10))
  expect_equal(lines$.fit, c(2, 20))
})

test_that("slopeplot keeps Python group and hue ordering", {
  data <- data.frame(
    site = c("B", "B", "A", "A"),
    subject = c("b", "b", "a", "a"),
    condition = c("before", "after", "before", "after"),
    value = c(3, 4, 1, 2),
    stringsAsFactors = FALSE
  )
  plot <- slopeplot_r(
    data, "site", "value", "condition", "subject",
    hue_order = c("after", "before")
  )
  built <- ggplot2::ggplot_build(plot)
  colour_scale <- built$plot$scales$get_scales("colour")
  x_scale <- plot$scales$get_scales("x")
  subject_a <- plot$data[plot$data$.group == "a", , drop = FALSE]

  expect_identical(x_scale$labels, c("A", "B"))
  expect_identical(levels(plot$data$.hue), c("after", "before"))
  expect_equal(subject_a$.x, c(0.8, 1.2))
  expect_identical(as.character(subject_a$.hue), c("after", "before"))
  expect_identical(colour_scale$limits, c("after", "before"))
  expect_identical(
    unname(colour_scale$map(c("after", "before"))),
    c("#377eb8", "#e41a1c")
  )
})

test_that("slopeplot reproduces the Set1 direction and marker defaults", {
  data <- data.frame(
    site = rep("A", 4),
    subject = c("down", "up", "up", "down"),
    condition = c("before", "before", "after", "after"),
    value = c(5, 1, 4, 2),
    stringsAsFactors = FALSE
  )
  plot <- slopeplot_r(data, "site", "value", "condition", "subject")
  built <- ggplot2::ggplot_build(plot)

  expect_identical(plot$layers[[1L]]$data$.group, "down")
  expect_identical(plot$layers[[2L]]$data$.group, "up")
  expect_identical(unique(built$data[[1L]]$colour), "#377eb8")
  expect_identical(unique(built$data[[2L]]$colour), "#e41a1c")
  expect_equal(unique(built$data[[1L]]$alpha), 0.4)
  expect_equal(unique(built$data[[2L]]$alpha), 0.4)
  expect_equal(
    unique(c(built$data[[1L]]$linewidth, built$data[[2L]]$linewidth)),
    1.5 * 25.4 / 72
  )
  expect_identical(
    built$data[[3L]]$colour,
    c("#377eb8", "#377eb8", "#e41a1c", "#e41a1c")
  )
  expect_equal(unique(built$data[[3L]]$size), 2 * sqrt(10 / pi) * 25.4 / 72)
  expect_equal(unique(built$data[[3L]]$stroke), 0.5 * 25.4 / 72)
  expect_identical(plot$labels$x, NULL)
  expect_identical(plot$labels$y, "value")
  expect_identical(plot$theme$legend.position, "top")
  expect_identical(plot$theme$legend.direction, "horizontal")
  expect_s3_class(plot$theme$legend.title, "element_blank")
})

test_that("slopeplot accepts the x column itself as the pair key", {
  data <- data.frame(
    site = rep(c("site1", "site2"), each = 2),
    condition = rep(c("healthy", "disease"), 2),
    value = c(1, 2, 2, 1),
    stringsAsFactors = FALSE
  )
  plot <- slopeplot_r(data, "site", "value", "condition", "site")
  lines <- slope_line_data(plot)

  expect_s3_class(plot, "ggplot")
  expect_identical(sort(lines$.group), c("site1", "site2"))
})

test_that("slopeplot enforces the two-condition contract", {
  data <- slope_fixture()

  expect_error(
    slopeplot_r(transform(data, condition = "before"),
                "site", "value", "condition", "subject"),
    "exactly 2 unique values"
  )
  three_hues <- rbind(
    data,
    transform(data[1:2, ], subject = c("three", "three"),
              condition = c("before", "follow-up"))
  )
  expect_error(
    slopeplot_r(three_hues, "site", "value", "condition", "subject"),
    "exactly 2 unique values"
  )
  expect_error(
    slopeplot_r(
      data, "site", "value", "condition", "subject",
      hue_order = c("before", "missing")
    ),
    "hue_order.*both observed"
  )
  expect_error(
    slopeplot_r(
      data, "site", "value", "condition", "subject",
      hue_order = c("before", "before")
    ),
    "hue_order.*both observed"
  )
})

test_that("slopeplot rejects ambiguous or incomplete pairs", {
  data <- slope_fixture()
  duplicate <- rbind(data, data[1L, , drop = FALSE])
  incomplete <- data[-1L, , drop = FALSE]
  crossed <- data
  crossed$site[crossed$subject == "one" & crossed$condition == "after"] <- "B"

  expect_error(
    slopeplot_r(duplicate, "site", "value", "condition", "subject"),
    "exactly one.*value for each"
  )
  expect_error(
    slopeplot_r(incomplete, "site", "value", "condition", "subject"),
    "exactly one.*value for each"
  )
  expect_error(
    slopeplot_r(crossed, "site", "value", "condition", "subject"),
    "belong to exactly one"
  )
})

test_that("slopeplot rejects structurally invalid inputs", {
  data <- slope_fixture()

  expect_error(
    slopeplot_r(list(), "site", "value", "condition", "subject"),
    "data frame"
  )
  expect_error(
    slopeplot_r(data[FALSE, ], "site", "value", "condition", "subject"),
    "must not be empty"
  )
  expect_error(
    slopeplot_r(data, "missing", "value", "condition", "subject"),
    "missing column"
  )
  expect_error(
    slopeplot_r(transform(data, value = as.character(value)),
                "site", "value", "condition", "subject"),
    "must be numeric"
  )
  missing_value <- data
  missing_value$value[[1L]] <- NA_real_
  expect_error(
    slopeplot_r(missing_value, "site", "value", "condition", "subject"),
    "must not contain missing values"
  )
})
