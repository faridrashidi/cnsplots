barplot_r <- getFromNamespace("barplot", "cnsplots")
stripplot_r <- getFromNamespace("stripplot", "cnsplots")
pieplot_r <- getFromNamespace("pieplot", "cnsplots")
donutplot_r <- getFromNamespace("donutplot", "cnsplots")

categorical_fixture <- function() {
  data.frame(
    category = c("A", "A", "A", "A", "B", "B", "B", "B"),
    value = c(1, 3, 2, 4, 5, 7, 6, 8),
    hue = c("H1", "H1", "H2", "H2", "H1", "H1", "H2", "H2"),
    stringsAsFactors = FALSE
  )
}

test_that("categorical plot APIs have the agreed R-native signatures", {
  expect_identical(
    names(formals(barplot_r)),
    c("data", "x", "y", "add_tip", "hue", "order", "hue_order", "palette")
  )
  expect_identical(
    names(formals(stripplot_r)),
    c(
      "data", "x", "y", "size", "showmedian", "showmeans", "add_count",
      "hue", "order", "hue_order", "palette"
    )
  )
  expect_identical(
    names(formals(pieplot_r)),
    c("data", "x", "legend", "order", "palette")
  )
  expect_identical(
    names(formals(donutplot_r)),
    c("data", "x", "legend", "order", "palette")
  )
})

test_that("all categorical constructors are quiet ordinary ggplots", {
  data <- categorical_fixture()
  original <- data
  constructors <- list(
    barplot = function() barplot_r(data, "category", "value"),
    stripplot = function() stripplot_r(data, "category", "value"),
    pieplot = function() pieplot_r(data, "category"),
    donutplot = function() donutplot_r(data, "category")
  )

  for (name in names(constructors)) {
    expect_output(plot <- constructors[[name]](), NA)
    expect_s3_class(plot, "ggplot")
  }
  expect_identical(data, original)
})

test_that("barplot computes means without implicit error bars", {
  data <- categorical_fixture()
  plot <- barplot_r(
    data, "category", "value", order = c("B", "A", "missing")
  )

  expect_equal(plot$data$.cns_y, c(6.5, 2.5))
  expect_identical(levels(plot$data$.cns_x), c("B", "A", "missing"))
  expect_length(plot$layers, 1L)
  expect_true(inherits(plot$layers[[1L]]$geom, "GeomCol"))
  expect_false(any(vapply(
    plot$layers,
    function(layer) inherits(layer$geom, "GeomErrorbar"),
    logical(1L)
  )))
})

test_that("barplot tips use two decimals and follow hue order", {
  data <- categorical_fixture()
  plot <- barplot_r(
    data,
    "category",
    "value",
    add_tip = TRUE,
    hue = "hue",
    order = c("A", "B", "missing"),
    hue_order = c("H2", "H1")
  )
  expect_identical(
    as.character(plot$data$.cns_hue),
    c("H2", "H2", "H1", "H1")
  )
  expect_identical(
    plot$layers[[2L]]$data$.cns_label,
    c("3.00", "7.00", "2.00", "6.00")
  )
  expect_identical(plot$scales$get_scales("x")$limits, c("A", "B", "missing"))
  expect_identical(plot$scales$get_scales("fill")$limits, c("H2", "H1"))
})

test_that("categorical palettes cycle deterministically", {
  data <- data.frame(
    category = rep("A", 3), value = 1:3,
    hue = c("H1", "H2", "H3")
  )
  plot <- barplot_r(
    data, "category", "value", hue = "hue",
    palette = c("#111111", "#eeeeee")
  )
  built <- ggplot2::ggplot_build(plot)
  scale <- built$plot$scales$get_scales("fill")

  expect_identical(
    unname(scale$map(c("H1", "H2", "H3"))),
    c("#111111", "#eeeeee", "#111111")
  )
})

test_that("barplot does not overload palette with a data column", {
  data <- categorical_fixture()
  expect_error(
    barplot_r(data, "category", "value", palette = "hue"),
    "Unknown palette"
  )
})

test_that("stripplot summaries remain category-wide with hue", {
  data <- data.frame(
    category = c("A", "A", "A", "A", "B", "B"),
    value = c(1, 3, 9, 11, 4, 8),
    hue = c("H1", "H1", "H2", "H2", "H1", "H2")
  )
  plot <- stripplot_r(
    data, "category", "value", hue = "hue",
    hue_order = c("H2", "H1"), showmeans = TRUE
  )
  built <- ggplot2::ggplot_build(plot)

  expect_length(plot$layers, 3L)
  expect_true(inherits(plot$layers[[1L]]$geom, "GeomPoint"))
  expect_true(inherits(plot$layers[[2L]]$geom, "GeomSegment"))
  expect_true(inherits(plot$layers[[3L]]$geom, "GeomPoint"))
  expect_equal(built$data[[2L]]$y, c(6, 6))
  expect_equal(built$data[[2L]]$xend - built$data[[2L]]$x, c(0.3, 0.3))
  expect_equal(built$data[[3L]]$y, c(6, 6))
  expect_identical(plot$scales$get_scales("colour")$limits, c("H2", "H1"))
})

test_that("stripplot can hide summaries and append raw category counts", {
  data <- data.frame(
    category = c("B", "A", "A", "B"),
    value = c(1, 2, NA, 4)
  )
  plot <- stripplot_r(
    data,
    "category",
    "value",
    showmedian = FALSE,
    showmeans = FALSE,
    add_count = TRUE,
    order = c("A", "B", "missing")
  )

  expect_length(plot$layers, 1L)
  expect_identical(
    plot$scales$get_scales("x")$labels,
    c("A\n(n=2)", "B\n(n=2)", "missing\n(n=0)")
  )
})

test_that("pieplot uses frequency order, percentages, and contrast text", {
  data <- data.frame(group = c(rep("dark", 3), rep("light", 2)))
  plot <- pieplot_r(
    data,
    "group",
    palette = c("#111111", "#eeeeee")
  )
  built <- ggplot2::ggplot_build(plot)

  expect_identical(as.character(plot$data$.cns_category), c("dark", "light"))
  expect_equal(plot$data$.cns_fraction, c(0.6, 0.4))
  expect_identical(built$data[[2L]]$label, c("60%", "40%"))
  expect_identical(built$data[[2L]]$colour, c("white", "black"))
  expect_true(all(built$data[[1L]]$colour == "white"))
  expect_equal(unique(built$data[[1L]]$linewidth), 0.3 * 25.4 / 72)
  expect_identical(plot$theme$legend.position, "bottom")
})

test_that("pie text can follow the fixed-white compatibility setting", {
  data <- data.frame(group = c(rep("dark", 3), rep("light", 2)))
  plot <- with_settings(
    list(annotation_auto_contrast = FALSE),
    pieplot_r(data, "group", palette = c("#111111", "#eeeeee"))
  )
  built <- ggplot2::ggplot_build(plot)

  expect_identical(built$data[[2L]]$colour, c("white", "white"))
})

test_that("donutplot has a 0.4 ring, black edge, and centre label", {
  data <- data.frame(group = c("B", "A", "B", "C", "B", "C"))
  plot <- donutplot_r(
    data, "group", legend = "top", order = c("A", "B", "C")
  )
  built <- ggplot2::ggplot_build(plot)

  expect_true(inherits(plot$coordinates, "CoordPolar"))
  expect_true(inherits(plot$layers[[1L]]$geom, "GeomCol"))
  expect_equal(
    unique(built$data[[1L]]$xmax - built$data[[1L]]$xmin),
    0.4
  )
  expect_true(all(built$data[[1L]]$colour == "black"))
  expect_equal(unique(built$data[[1L]]$linewidth), 0.3 * 25.4 / 72)
  expect_identical(built$data[[2L]]$label, "group")
  expect_false(any(grepl("%$", built$data[[2L]]$label)))
  expect_identical(plot$theme$legend.position, "top")
})

test_that("categorical plots do not mutate data, settings, or the global theme", {
  data <- categorical_fixture()
  original <- data
  settings_before <- settings()
  theme_before <- ggplot2::theme_get()

  invisible(barplot_r(data, "category", "value", add_tip = TRUE))
  invisible(stripplot_r(data, "category", "value", hue = "hue"))
  invisible(pieplot_r(data, "category"))
  invisible(donutplot_r(data, "category"))

  expect_identical(data, original)
  expect_identical(settings(), settings_before)
  expect_identical(ggplot2::theme_get(), theme_before)
})

test_that("categorical plots reject structurally invalid inputs", {
  data <- categorical_fixture()

  expect_error(barplot_r(list(), "category", "value"), "data frame")
  expect_error(barplot_r(data[0, ], "category", "value"), "must not be empty")
  expect_error(barplot_r(data, "missing", "value"), "was not found")
  expect_error(
    barplot_r(transform(data, value = as.character(value)), "category", "value"),
    "must be numeric"
  )
  expect_error(
    barplot_r(data, "category", "value", order = c("A", "A")),
    "unique values"
  )
  expect_error(
    stripplot_r(data, "category", "value", hue_order = "H1"),
    "when hue is supplied"
  )
  expect_error(
    barplot_r(data, "category", "value", palette = "not-a-palette"),
    "Unknown palette"
  )
  expect_error(
    pieplot_r(data, "category", legend = "centre"),
    "legend must be one of"
  )
  expect_error(
    pieplot_r(data, "category", order = "A"),
    "every observed category exactly once"
  )
  expect_error(
    donutplot_r(data.frame(category = NA_character_), "category"),
    "no non-missing"
  )
})

lollipopplot_r <- getFromNamespace("lollipopplot", "cnsplots")
stackplot_r <- getFromNamespace("stackplot", "cnsplots")

test_that("lollipop and stack APIs keep the author's direct names", {
  expect_identical(
    names(formals(lollipopplot_r)),
    c(
      "data", "x", "y", "hue", "order", "hue_order", "pairs",
      "add_tip", "estimator", "errorbar", "markersize", "linewidth",
      "marker", "dodge", "color", "palette", "baseline"
    )
  )
  expect_identical(
    names(formals(stackplot_r)),
    c(
      "data", "x", "y", "stack", "order", "stack_order", "width",
      "normalize", "pairs", "add_count", "n_factor"
    )
  )
})

test_that("lollipopplot preserves mean stems, errors, and tip labels", {
  data <- data.frame(
    category = c("A", "A", "B", "B"),
    value = c(1, 3, 5, 7)
  )
  original <- data
  plot <- lollipopplot_r(
    data, "category", "value", errorbar = "se", add_tip = TRUE,
    baseline = -1, palette = c("#111111", "#eeeeee")
  )
  built <- ggplot2::ggplot_build(plot)

  expect_s3_class(plot, "ggplot")
  expect_identical(data, original)
  expect_equal(plot$data$.cns_y, c(2, 6))
  expect_equal(plot$data$.cns_ymin, c(1, 5))
  expect_equal(plot$data$.cns_ymax, c(3, 7))
  expect_identical(
    unname(vapply(
      plot$layers, function(layer) class(layer$geom)[[1L]], character(1L)
    )),
    c("GeomSegment", "GeomErrorbar", "GeomPoint", "GeomText")
  )
  expect_true(all(built$data[[1L]]$y == -1))
  expect_identical(built$data[[4L]]$label, c("2.00", "6.00"))
})

test_that("lollipopplot honours hue order, dodge, and palette cycling", {
  data <- categorical_fixture()
  plot <- lollipopplot_r(
    data, "category", "value", hue = "hue",
    order = c("B", "A"), hue_order = c("H2", "H1"),
    palette = "#123456", dodge = 0.8
  )
  built <- ggplot2::ggplot_build(plot)

  expect_identical(levels(plot$data$.cns_x), c("B", "A"))
  expect_identical(levels(plot$data$.cns_hue), c("H2", "H1"))
  expect_equal(sort(unique(plot$data$.cns_vjust)), c(0.8, 1.2, 1.8, 2.2))
  expect_true(all(built$data[[2L]]$colour == "#123456"))
  expect_identical(
    plot$scales$get_scales("colour")$limits,
    c("H2", "H1")
  )
})

test_that("median bootstrap is deterministic without changing RNG state", {
  data <- data.frame(
    category = rep("A", 4),
    value = c(1, 2, 7, 11)
  )
  set.seed(812)
  seed_before <- .Random.seed
  first <- lollipopplot_r(
    data, "category", "value", estimator = "median", errorbar = "ci"
  )
  seed_after <- .Random.seed
  second <- lollipopplot_r(
    data, "category", "value", estimator = "median", errorbar = "ci"
  )

  expect_identical(seed_after, seed_before)
  expect_identical(.Random.seed, seed_before)
  expect_equal(first$data$.cns_ymin, second$data$.cns_ymin)
  expect_equal(first$data$.cns_ymax, second$data$.cns_ymax)
})

test_that("lollipopplot detects horizontal categorical orientation", {
  data <- data.frame(value = c(1, 3, 5, 7), category = c("A", "A", "B", "B"))
  plot <- lollipopplot_r(data, "value", "category", order = c("B", "A"))

  expect_true(inherits(plot$coordinates, "CoordFlip"))
  expect_identical(plot$labels$x, "category")
  expect_identical(plot$labels$y, "value")
  expect_identical(plot$scales$get_scales("x")$labels, c("B", "A"))
})



test_that("lollipop markers stay above errors and filled shapes use group colour", {
  data <- data.frame(category = c("A", "A"), value = c(1, 3))
  plot <- lollipopplot_r(
    data, "category", "value", marker = "v", errorbar = "se",
    palette = "#123456"
  )
  built <- ggplot2::ggplot_build(plot)

  expect_identical(
    unname(vapply(
      plot$layers, function(layer) class(layer$geom)[[1L]], character(1L)
    )),
    c("GeomSegment", "GeomErrorbar", "GeomPoint")
  )
  expect_identical(built$data[[3L]]$fill, "#123456")
  expect_identical(unique(built$data[[3L]]$shape), 25)
})

test_that("lollipop tip offsets and alignment follow plot orientation", {
  negative <- data.frame(category = c("A", "A"), value = c(-4, -2))
  vertical <- lollipopplot_r(
    negative, "category", "value", add_tip = TRUE, baseline = 0
  )
  horizontal <- lollipopplot_r(
    negative[c("value", "category")], "value", "category",
    add_tip = TRUE, baseline = 0
  )

  expect_lt(vertical$layers[[3L]]$data$.cns_y, vertical$data$.cns_y)
  horizontal_built <- ggplot2::ggplot_build(horizontal)
  expect_equal(horizontal_built$data[[3L]]$hjust, 0)
  expect_equal(horizontal_built$data[[3L]]$vjust, 0.5)
})

test_that("stackplot preserves normalized compositions and ordering", {
  data <- data.frame(
    group = c("A", "A", "A", "B", "B"),
    outcome = c("Yes", "Yes", "No", "Yes", "No")
  )
  original <- data
  plot <- stackplot_r(
    data, x = "group", stack = "outcome",
    order = c("B", "A", "missing"),
    stack_order = c("No", "Yes"), add_count = TRUE
  )
  built <- ggplot2::ggplot_build(plot)

  expect_s3_class(plot, "ggplot")
  expect_identical(data, original)
  expect_identical(levels(plot$data$.cns_x), c("B", "A", "missing"))
  expect_identical(levels(plot$data$.cns_hue), c("No", "Yes"))
  expect_equal(
    as.numeric(tapply(plot$data$.cns_y, plot$data$.cns_x, sum)),
    c(1, 1, 0)
  )
  expect_identical(
    plot$scales$get_scales("x")$labels,
    c("B\n(n=2)", "A\n(n=3)", "missing\n(n=0)")
  )
  expect_identical(plot$scales$get_scales("fill")$limits, c("No", "Yes"))
  expect_true(all(built$data[[1L]]$width == 0.5))
})



test_that("stackplot default levels follow Python pivot sorting", {
  data <- data.frame(
    group = c("B", "A", "B", "A"),
    outcome = c("z", "z", "y", "y")
  )
  plot <- stackplot_r(data, x = "group", stack = "outcome")

  expect_identical(levels(plot$data$.cns_x), c("A", "B"))
  expect_identical(levels(plot$data$.cns_hue), c("y", "z"))
})

test_that("stackplot supports horizontal counts and n_factor", {
  data <- data.frame(
    patient = c("P1", "P1", "P1", "P2", "P2"),
    mutation = c("M1", "M1", "M2", "M1", "M2")
  )
  plot <- stackplot_r(
    data, y = "patient", stack = "mutation", normalize = FALSE,
    n_factor = 2, order = c("P2", "P1"),
    stack_order = c("M2", "M1")
  )

  expect_true(inherits(plot$coordinates, "CoordFlip"))
  expect_identical(plot$labels$y, "Count")
  expect_equal(
    as.numeric(tapply(plot$data$.cns_y, plot$data$.cns_x, sum)),
    c(1, 1.5)
  )
})

test_that("new categorical functions reject unsupported or invalid contracts", {
  data <- categorical_fixture()

  expect_error(
    lollipopplot_r(data, "category", "value", estimator = "mode"),
    "estimator must be one of"
  )
  expect_error(
    lollipopplot_r(data, "category", "value", errorbar = "sem"),
    "errorbar must be one of"
  )
  expect_error(
    lollipopplot_r(data, "category", "value", pairs = list(c("A", "B"))),
    "pairs statistical annotations are not supported"
  )
  expect_error(
    stackplot_r(data, stack = "hue"),
    "exactly one"
  )
  expect_error(
    stackplot_r(data, x = "category", y = "hue", stack = "hue"),
    "exactly one"
  )
  expect_error(
    stackplot_r(data, x = "category", stack = "hue", n_factor = 0),
    "n_factor"
  )
  expect_error(
    stackplot_r(
      data, x = "category", stack = "hue", stack_order = "H1"
    ),
    "every observed stack level"
  )
  expect_error(
    stackplot_r(
      data, x = "category", stack = "hue",
      stack_order = c("H1", "H2", "extra")
    ),
    "every observed stack level"
  )
  expect_error(
    stackplot_r(
      data, x = "category", stack = "hue", pairs = list(c("A", "B"))
    ),
    "pairs statistical annotations are not supported"
  )
})
