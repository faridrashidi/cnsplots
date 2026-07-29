test_that("regplot draws an overall fit and Pearson annotation", {
  data <- data.frame(x = 1:8, y = c(1.1, 2.0, 2.8, 4.2, 4.9, 6.1, 6.8, 8.2))
  original <- data

  plot <- regplot(data, "x", "y")

  expect_s3_class(plot, "ggplot")
  expect_identical(data, original)
  expect_length(plot$layers, 4)
  label <- ggplot2::ggplot_build(plot)$data[[4L]]$label
  expect_match(label, "r=")
  expect_match(label, "P=")
})

test_that("regplot honours hue order and creates one fit per group", {
  data <- data.frame(
    x = rep(1:5, 2),
    y = c(1:5, 2:6),
    group = rep(c("B", "A"), each = 5)
  )

  plot <- regplot(data, "x", "y", hue = "group", hue_order = c("A", "B"))

  expect_equal(plot$scales$scales[[1]]$limits, c("A", "B"))
  expect_equal(unique(as.character(plot$layers[[2]]$data$.group)), c("A", "B"))
  expect_equal(nrow(plot$layers[[4]]$data), 2)
})

test_that("regplot column colour keeps one black overall fit", {
  data <- data.frame(
    x = 1:6, y = c(1, 2, 2.5, 4, 5, 6),
    cell = c("T", "T", "B", "B", "M", "M")
  )
  plot <- regplot(data, "x", "y", color = "cell")

  expect_equal(plot$layers[[2]]$aes_params$colour, "black")
  expect_equal(plot$scales$get_scales("colour")$name, "cell")
})

test_that("regplot rejects insufficient finite pairs", {
  data <- data.frame(x = c(1, NA), y = c(2, 3))
  expect_error(regplot(data, "x", "y"), "at least 2 finite")
})

test_that("kdeplot marks the estimated density peak, not a sample mode", {
  data <- data.frame(value = c(-2, -1.5, -1, -0.5, 0, 0.2, 0.4, 0.8, 1.2, 2))
  plot <- kdeplot(data, "value", add_mode = TRUE)

  expect_s3_class(plot, "ggplot")
  expect_length(plot$layers, 3)
  expect_s3_class(plot$layers[[2L]]$geom, "GeomSegment")
  expect_match(
    ggplot2::ggplot_build(plot)$data[[3L]]$label,
    "^-?[0-9]+\\.[0-9]{2}$"
  )
})

test_that("kdeplot performs KS only for exactly two hue groups", {
  data <- data.frame(
    value = c(1:5, 2:6),
    group = rep(c("B", "A"), each = 5)
  )
  expect_message(
    plot <- kdeplot(data, "value", hue = "group", hue_order = c("A", "B")),
    "Kolmogorov-Smirnov"
  )
  expect_equal(plot$scales$scales[[1]]$limits, c("A", "B"))
  expect_match(ggplot2::ggplot_build(plot)$data[[2L]]$label, "P=")
})
