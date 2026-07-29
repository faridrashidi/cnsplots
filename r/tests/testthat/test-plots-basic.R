test_that("scatterplot returns a composable ggplot without changing input", {
  data <- data.frame(
    x = 1:6,
    y = c(2, 1, 4, 3, 6, 5),
    group = c("B", "A", "B", "A", "C", "C")
  )
  original <- data

  plot <- scatterplot(
    data, "x", "y", hue = "group", hue_order = c("C", "B", "A")
  )

  expect_s3_class(plot, "ggplot")
  expect_identical(data, original)
  expect_length(plot$layers, 1)
  expect_equal(plot$labels$x, "x")
  expect_equal(plot$labels$y, "y")
  expect_equal(plot$scales$get_scales("colour")$name, "group")
  expect_equal(plot$scales$scales[[1]]$limits, c("C", "B", "A"))
})

test_that("scatterplot preserves the author marker defaults", {
  plot <- scatterplot(data.frame(x = 1:3, y = 3:1), "x", "y")
  layer <- plot$layers[[1]]

  expect_equal(layer$aes_params$stroke, 0)
  expect_equal(layer$aes_params$colour, palettes("Ecotyper1", n = 1))
  expect_equal(layer$aes_params$size, 2 * sqrt(7 / pi) * 25.4 / 72)
})

test_that("scatterplot validates its direct string-column API", {
  data <- data.frame(x = 1:2, y = 2:1)
  expect_error(scatterplot(list(x = 1), "x", "y"), "data frame")
  expect_error(scatterplot(data[FALSE, ], "x", "y"), "must not be empty")
  expect_error(scatterplot(data, "missing", "y"), "missing column")
  expect_error(scatterplot(data, "x", "y", s = 0), "greater than zero")
})

test_that("placeholderplot builds the six author shapes and caption", {
  plot <- placeholderplot("A description to be centered in the panel")

  expect_s3_class(plot, "ggplot")
  expect_length(plot$layers, 7)
  expect_equal(
    ggplot2::ggplot_build(plot)$data[[7L]]$label,
    "A description to be centered in the panel"
  )
  expect_s3_class(plot$theme$axis.text, "element_blank")
  expect_s3_class(plot$theme$axis.title, "element_blank")
})

test_that("placeholderplot requires one character description", {
  expect_error(placeholderplot(123), "character")
  expect_error(placeholderplot(c("a", "b")), "one character")
})
