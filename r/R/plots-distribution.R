.distribution_layer_args <- function(defaults, dots, caller, locked = character()) {
  if (!length(dots)) return(defaults)
  if (is.null(names(dots)) || any(!nzchar(names(dots)))) {
    stop(sprintf("[%s] all arguments in ... must be named.", caller), call. = FALSE)
  }
  conflicts <- intersect(names(dots), locked)
  if (length(conflicts)) {
    stop(
      sprintf(
        "[%s] %s cannot be supplied through ....",
        caller, paste(conflicts, collapse = ", ")
      ),
      call. = FALSE
    )
  }
  for (name in names(dots)) defaults[[name]] <- dots[[name]]
  defaults
}

.distribution_prepare <- function(
  data, x, y, caller, hue = NULL, order = NULL, hue_order = NULL
) {
  x <- .cns_assert_scalar_character(x, "x")
  y <- .cns_assert_scalar_character(y, "y")
  if (!is.null(hue)) hue <- .cns_assert_scalar_character(hue, "hue")
  columns <- c(x, y, if (!is.null(hue)) hue)
  .plot_check_data(data, columns, caller, numeric = y)
  if (!is.null(order) && !length(order)) {
    stop("order must not be empty.", call. = FALSE)
  }
  if (!is.null(hue) && !is.null(hue_order) && !length(hue_order)) {
    stop("hue_order must not be empty.", call. = FALSE)
  }

  x_levels <- .plot_levels(data[[x]], order, "order")
  if (!length(x_levels)) {
    stop(sprintf("[%s] x has no non-missing values.", caller), call. = FALSE)
  }

  if (is.null(hue)) {
    group_values <- as.character(data[[x]])
    group_levels <- x_levels
    legend_title <- x
  } else {
    group_values <- as.character(data[[hue]])
    group_levels <- .plot_levels(data[[hue]], hue_order, "hue_order")
    if (!length(group_levels)) {
      stop(sprintf("[%s] hue has no non-missing values.", caller), call. = FALSE)
    }
    legend_title <- hue
  }

  plot_data <- data.frame(
    .x = factor(as.character(data[[x]]), levels = x_levels),
    .y = as.numeric(data[[y]]),
    .group = factor(group_values, levels = group_levels),
    check.names = FALSE
  )
  keep <- !is.na(plot_data$.x) & is.finite(plot_data$.y) &
    !is.na(plot_data$.group)
  plot_data <- plot_data[keep, , drop = FALSE]
  if (!nrow(plot_data)) {
    stop(sprintf("[%s] no finite observations remain to plot.", caller), call. = FALSE)
  }

  list(
    data = plot_data,
    x_levels = x_levels,
    group_levels = group_levels,
    has_hue = !is.null(hue),
    legend_title = legend_title,
    x_name = x,
    y_name = y
  )
}

.distribution_prepare_x <- function(data, x, caller, hue = NULL, hue_order = NULL) {
  x <- .cns_assert_scalar_character(x, "x")
  if (!is.null(hue)) hue <- .cns_assert_scalar_character(hue, "hue")
  columns <- c(x, if (!is.null(hue)) hue)
  .plot_check_data(data, columns, caller, numeric = x)
  if (!is.null(hue) && !is.null(hue_order) && !length(hue_order)) {
    stop("hue_order must not be empty.", call. = FALSE)
  }

  if (is.null(hue)) {
    group_values <- rep(".all", nrow(data))
    group_levels <- ".all"
    legend_title <- NULL
  } else {
    group_values <- as.character(data[[hue]])
    group_levels <- .plot_levels(data[[hue]], hue_order, "hue_order")
    if (!length(group_levels)) {
      stop(sprintf("[%s] hue has no non-missing values.", caller), call. = FALSE)
    }
    legend_title <- hue
  }

  plot_data <- data.frame(
    .x = as.numeric(data[[x]]),
    .group = factor(group_values, levels = group_levels),
    check.names = FALSE
  )
  keep <- is.finite(plot_data$.x) & !is.na(plot_data$.group)
  plot_data <- plot_data[keep, , drop = FALSE]
  if (!nrow(plot_data)) {
    stop(sprintf("[%s] no finite observations remain to plot.", caller), call. = FALSE)
  }

  list(
    data = plot_data,
    group_levels = group_levels,
    has_hue = !is.null(hue),
    legend_title = legend_title,
    x_name = x
  )
}

.distribution_colours <- function(prepared, palette) {
  n <- length(prepared$group_levels)
  if (is.null(palette) && !prepared$has_hue) {
    return(rep(.plot_colours(NULL, 1L), length.out = n))
  }
  .plot_colours(palette, n)
}

.distribution_add_scales <- function(plot, prepared, palette) {
  colours <- .distribution_colours(prepared, palette)
  plot +
    scale_fill_palette(
      colours,
      limits = prepared$group_levels,
      drop = FALSE,
      name = prepared$legend_title
    ) +
    scale_colour_palette(
      colours,
      limits = prepared$group_levels,
      drop = FALSE,
      name = prepared$legend_title
    )
}

.distribution_x_scale <- function(data, x, levels, add_count) {
  labels <- levels
  if (add_count) {
    values <- as.character(data[[x]])
    counts <- vapply(
      levels,
      function(level) sum(!is.na(values) & values == level),
      numeric(1)
    )
    labels <- sprintf("%s\n(n=%d)", levels, counts)
  }
  ggplot2::scale_x_discrete(
    limits = levels,
    labels = stats::setNames(labels, levels),
    drop = FALSE
  )
}

.distribution_median <- function(values) {
  middle <- stats::median(values, na.rm = TRUE)
  data.frame(y = middle, ymin = middle, ymax = middle)
}

.distribution_validate_width <- function(width, caller) {
  .cns_assert_scalar_number(width, sprintf("%s width", caller), positive = TRUE)
}

.distribution_validate_whis <- function(whis) {
  if (is.numeric(whis) && length(whis) == 1L && !is.na(whis) &&
      is.finite(whis) && whis >= 0) {
    return(as.numeric(whis))
  }
  if (is.numeric(whis) && length(whis) == 2L &&
      all(is.finite(whis)) && identical(as.numeric(whis), c(0, 100))) {
    return(Inf)
  }
  stop(
    paste0(
      "whis must be a non-negative finite IQR multiplier or c(0, 100); ",
      "other percentile ranges are not yet supported."
    ),
    call. = FALSE
  )
}

.distribution_reject_pairs <- function(pairs, caller) {
  if (!is.null(pairs)) {
    stop(
      sprintf(
        paste0(
          "[%s] pairs is not supported in the R implementation yet; ",
          "add statistical annotations explicitly."
        ),
        caller
      ),
      call. = FALSE
    )
  }
  invisible(NULL)
}

#' Draw a styled box plot
#'
#' This is the native ggplot2 counterpart of the Python cnsplots box plot.
#' Boxes have no outline, whiskers use the group colour, medians are white,
#' caps are omitted, and outliers are hidden by default. Statistical pairwise
#' annotations remain explicit in the R implementation.
#'
#' @param data A data frame.
#' @param x Categorical column name.
#' @param y Numeric column name.
#' @param pairs Reserved for future statistical annotations. Non-`NULL` values
#'   currently produce an error.
#' @param showoutliers Show points beyond the whiskers.
#' @param add_count Add sample counts to category tick labels.
#' @param whis Non-negative IQR multiplier used for whiskers, or `c(0, 100)`
#'   to use the observed minimum and maximum.
#' @param hue Optional grouping column.
#' @param order,hue_order Optional category and hue orders.
#' @param palette Palette name or custom colour vector.
#' @param width Total box width within each x category.
#' @param ... Additional named arguments passed to `ggplot2::geom_boxplot()`.
#' @return A ggplot object.
#' @export
boxplot <- function(
  data,
  x,
  y,
  pairs = NULL,
  showoutliers = FALSE,
  add_count = FALSE,
  whis = 1.5,
  hue = NULL,
  order = NULL,
  hue_order = NULL,
  palette = NULL,
  width = 0.5,
  ...
) {
  .distribution_reject_pairs(pairs, "boxplot")
  dots <- list(...)
  if (!is.null(names(dots)) && "addcount" %in% names(dots)) {
    stop("[boxplot] use add_count instead of addcount.", call. = FALSE)
  }
  .cns_assert_scalar_logical(showoutliers, "showoutliers")
  .cns_assert_scalar_logical(add_count, "add_count")
  width <- .distribution_validate_width(width, "boxplot")
  whis <- .distribution_validate_whis(whis)
  prepared <- .distribution_prepare(
    data, x, y, "boxplot", hue = hue, order = order, hue_order = hue_order
  )

  dodge <- ggplot2::position_dodge2(
    width = width, preserve = "single", padding = 0
  )
  plot <- ggplot2::ggplot(
    prepared$data,
    ggplot2::aes(
      x = .x,
      y = .y,
      group = interaction(.x, .group, drop = TRUE)
    )
  ) +
    ggplot2::stat_boxplot(
      ggplot2::aes(colour = .group),
      geom = "errorbar",
      coef = whis,
      width = 0,
      position = dodge,
      linewidth = .cns_pt_to_mm(0.8),
      show.legend = FALSE,
      na.rm = TRUE
    )

  box_args <- .distribution_layer_args(
    list(
      mapping = ggplot2::aes(fill = .group),
      width = width,
      coef = whis,
      position = dodge,
      colour = NA,
      linewidth = .cns_pt_to_mm(0.8),
      outlier.shape = if (showoutliers) 19 else NA,
      outlier.colour = "black",
      outlier.fill = "black",
      outlier.size = .cns_pt_to_mm(1.5),
      outlier.stroke = 0,
      show.legend = prepared$has_hue,
      na.rm = TRUE
    ),
    dots,
    "boxplot",
    locked = c("data", "mapping", "stat", "position", "inherit.aes", "coef")
  )
  plot <- plot + do.call(ggplot2::geom_boxplot, box_args) +
    ggplot2::stat_summary(
      fun.data = .distribution_median,
      geom = "crossbar",
      width = width,
      position = dodge,
      colour = "white",
      fill = NA,
      linewidth = .cns_pt_to_mm(0.8),
      fatten = 1,
      show.legend = FALSE,
      na.rm = TRUE
    )

  plot <- .distribution_add_scales(plot, prepared, palette) +
    .distribution_x_scale(data, prepared$x_name, prepared$x_levels, add_count)
  if (!prepared$has_hue) {
    plot <- plot + ggplot2::guides(fill = "none", colour = "none")
  }
  .plot_finish(plot, x = prepared$x_name, y = prepared$y_name)
}

#' Draw a styled violin plot
#'
#' The violin is drawn with an effectively invisible outline and, by default,
#' a narrow white box plot with black whiskers and median is overlaid.
#'
#' @inheritParams boxplot
#' @param width Total violin width within each x category.
#' @param add_box Overlay a narrow box plot.
#' @param ... Additional named arguments passed to `ggplot2::geom_violin()`.
#' @return A ggplot object.
#' @export
violinplot <- function(
  data,
  x,
  y,
  pairs = NULL,
  width = 0.6,
  add_box = TRUE,
  add_count = FALSE,
  hue = NULL,
  order = NULL,
  hue_order = NULL,
  palette = NULL,
  ...
) {
  .distribution_reject_pairs(pairs, "violinplot")
  dots <- list(...)
  if (!is.null(names(dots)) && "addcount" %in% names(dots)) {
    stop("[violinplot] use add_count instead of addcount.", call. = FALSE)
  }
  .cns_assert_scalar_logical(add_box, "add_box")
  .cns_assert_scalar_logical(add_count, "add_count")
  width <- .distribution_validate_width(width, "violinplot")
  prepared <- .distribution_prepare(
    data, x, y, "violinplot", hue = hue, order = order,
    hue_order = hue_order
  )

  dodge <- ggplot2::position_dodge2(
    width = width, preserve = "single", padding = 0
  )
  plot <- ggplot2::ggplot(
    prepared$data,
    ggplot2::aes(
      x = .x,
      y = .y,
      group = interaction(.x, .group, drop = TRUE)
    )
  )
  violin_args <- .distribution_layer_args(
    list(
      mapping = ggplot2::aes(fill = .group, colour = .group),
      width = width,
      position = dodge,
      linewidth = .cns_pt_to_mm(0.001),
      trim = FALSE,
      show.legend = prepared$has_hue,
      na.rm = TRUE
    ),
    dots,
    "violinplot",
    locked = c("data", "mapping", "stat", "position", "inherit.aes")
  )
  plot <- plot + do.call(ggplot2::geom_violin, violin_args)

  if (add_box) {
    plot <- plot +
      ggplot2::geom_boxplot(
        width = 0.2,
        position = dodge,
        fill = "white",
        colour = "black",
        linewidth = .cns_pt_to_mm(0.4),
        outlier.shape = NA,
        show.legend = FALSE,
        na.rm = TRUE
      ) +
      ggplot2::stat_summary(
        fun.data = .distribution_median,
        geom = "crossbar",
        width = 0.2,
        position = dodge,
        colour = "black",
        fill = NA,
        linewidth = .cns_pt_to_mm(0.8),
        fatten = 1,
        show.legend = FALSE,
        na.rm = TRUE
      )
  }

  plot <- .distribution_add_scales(plot, prepared, palette) +
    .distribution_x_scale(data, prepared$x_name, prepared$x_levels, add_count)
  if (!prepared$has_hue) {
    plot <- plot + ggplot2::guides(fill = "none", colour = "none")
  }
  .plot_finish(plot, x = prepared$x_name, y = prepared$y_name)
}

.distribution_default_binwidth <- function(values) {
  span <- diff(range(values))
  if (!is.finite(span) || span <= 0) {
    reference <- max(abs(values), na.rm = TRUE)
    if (!is.finite(reference) || reference == 0) return(1)
    return(reference / 10)
  }
  candidates <- c(
    tryCatch(grDevices::nclass.Sturges(values), error = function(...) NA_real_),
    tryCatch(grDevices::nclass.FD(values), error = function(...) NA_real_)
  )
  candidates <- candidates[is.finite(candidates) & candidates > 0]
  bins <- if (length(candidates)) max(candidates) else ceiling(sqrt(length(values)))
  span / max(1, bins)
}

.distribution_density_data <- function(prepared, binwidth) {
  pieces <- lapply(prepared$group_levels, function(level) {
    values <- prepared$data$.x[prepared$data$.group == level]
    if (length(values) < 2L) return(NULL)
    estimate <- tryCatch(stats::density(values), error = function(...) NULL)
    if (is.null(estimate)) return(NULL)
    data.frame(
      .x = estimate$x,
      .count = estimate$y * length(values) * binwidth,
      .group = factor(level, levels = prepared$group_levels),
      check.names = FALSE
    )
  })
  pieces <- Filter(Negate(is.null), pieces)
  if (length(pieces)) return(do.call(rbind, pieces))
  data.frame(
    .x = numeric(),
    .count = numeric(),
    .group = factor(character(), levels = prepared$group_levels),
    check.names = FALSE
  )
}

#' Draw a histogram with a count-scaled density curve
#'
#' The histogram and KDE use common bins. Density values are scaled by group
#' sample size and bin width so they are directly comparable with histogram
#' counts, matching the intent of the Python `histplot(kde = TRUE)` recipe.
#'
#' @param data A data frame.
#' @param x Numeric column name.
#' @param hue Optional grouping column.
#' @param hue_order Optional hue order.
#' @param palette Palette name or custom colour vector.
#' @param binwidth Optional positive histogram bin width.
#' @param bins Optional positive number of common bins, ignored when
#'   `binwidth` is supplied.
#' @param ... Additional named arguments passed to
#'   `ggplot2::geom_histogram()`.
#' @return A ggplot object.
#' @export
distplot <- function(
  data,
  x,
  hue = NULL,
  hue_order = NULL,
  palette = NULL,
  binwidth = NULL,
  bins = NULL,
  ...
) {
  prepared <- .distribution_prepare_x(
    data, x, "distplot", hue = hue, hue_order = hue_order
  )
  if (!is.null(binwidth)) {
    binwidth <- .cns_assert_scalar_number(binwidth, "binwidth", positive = TRUE)
  } else if (!is.null(bins)) {
    bins <- .cns_assert_scalar_number(bins, "bins", positive = TRUE)
    if (bins != floor(bins)) {
      stop("bins must be one positive whole number.", call. = FALSE)
    }
    span <- diff(range(prepared$data$.x))
    binwidth <- if (span > 0) span / bins else .distribution_default_binwidth(prepared$data$.x)
  } else {
    binwidth <- .distribution_default_binwidth(prepared$data$.x)
  }

  plot <- ggplot2::ggplot(
    prepared$data,
    ggplot2::aes(x = .x, group = .group)
  )
  histogram_args <- .distribution_layer_args(
    list(
      mapping = ggplot2::aes(fill = .group),
      binwidth = binwidth,
      position = "identity",
      alpha = if (prepared$has_hue) 0.5 else 1,
      colour = NA,
      linewidth = 0,
      show.legend = prepared$has_hue,
      na.rm = TRUE
    ),
    list(...),
    "distplot",
    locked = c("data", "mapping", "stat", "inherit.aes", "binwidth", "bins")
  )
  plot <- plot + do.call(ggplot2::geom_histogram, histogram_args)

  density_data <- .distribution_density_data(prepared, binwidth)
  plot <- plot + ggplot2::geom_line(
    data = density_data,
    mapping = ggplot2::aes(x = .x, y = .count, colour = .group, group = .group),
    inherit.aes = FALSE,
    linewidth = .cns_pt_to_mm(1),
    show.legend = prepared$has_hue,
    na.rm = TRUE
  )
  plot <- .distribution_add_scales(plot, prepared, palette)
  if (!prepared$has_hue) {
    plot <- plot + ggplot2::guides(fill = "none", colour = "none")
  }
  .plot_finish(plot, x = prepared$x_name, y = "Count")
}

#' Draw a normal quantile-quantile plot
#'
#' Plotting positions use `i / (n + 1)`, the default used by the Python
#' statsmodels implementation. No reference line is added by default.
#'
#' @param data A data frame.
#' @param x Numeric column name.
#' @param ... Additional named arguments passed to `ggplot2::geom_point()`.
#' @return A ggplot object.
#' @export
qqplot <- function(data, x, ...) {
  x <- .cns_assert_scalar_character(x, "x")
  .plot_check_data(data, x, "qqplot", numeric = x)
  values <- as.numeric(data[[x]])
  values <- values[is.finite(values)]
  if (!length(values)) {
    stop("[qqplot] x has no finite observations.", call. = FALSE)
  }
  n <- length(values)
  plot_data <- data.frame(
    .theoretical = stats::qnorm(seq_len(n) / (n + 1)),
    .sample = sort(values),
    check.names = FALSE
  )
  point_args <- .distribution_layer_args(
    list(
      colour = "black",
      size = .cns_pt_to_mm(3),
      stroke = 0,
      shape = 19,
      na.rm = TRUE
    ),
    list(...),
    "qqplot",
    locked = c("data", "mapping", "stat", "position", "inherit.aes")
  )
  plot <- ggplot2::ggplot(
    plot_data,
    ggplot2::aes(x = .theoretical, y = .sample)
  ) + do.call(ggplot2::geom_point, point_args)
  .plot_finish(
    plot,
    x = "Theoretical Quantiles",
    y = "Sample Quantiles"
  )
}
