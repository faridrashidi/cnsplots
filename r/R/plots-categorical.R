.cns_plot_column <- function(data, value, name, caller) {
  value <- .cns_assert_scalar_character(value, name)
  if (!value %in% names(data)) {
    stop(
      sprintf("[%s] Column '%s' was not found in data.", caller, value),
      call. = FALSE
    )
  }
  value
}

.cns_plot_data <- function(data, columns, caller) {
  if (!is.data.frame(data)) {
    stop(sprintf("[%s] data must be a data frame.", caller), call. = FALSE)
  }
  if (!nrow(data)) {
    stop(sprintf("[%s] data must not be empty.", caller), call. = FALSE)
  }
  invisible(lapply(
    names(columns),
    function(name) .cns_plot_column(data, columns[[name]], name, caller)
  ))
  invisible(data)
}

.cns_plot_numeric_column <- function(data, column, caller) {
  values <- data[[column]]
  if (!is.numeric(values)) {
    stop(
      sprintf("[%s] Column '%s' must be numeric.", caller, column),
      call. = FALSE
    )
  }
  if (any(!is.finite(values[!is.na(values)]))) {
    stop(
      sprintf(
        "[%s] Column '%s' must contain only finite values or NA.",
        caller, column
      ),
      call. = FALSE
    )
  }
  values
}

.cns_plot_order <- function(value, name) {
  if (is.null(value)) return(NULL)
  if (!is.character(value) || !length(value) || anyNA(value) ||
      any(!nzchar(value)) || anyDuplicated(value)) {
    stop(
      sprintf("%s must be a non-empty character vector of unique values.", name),
      call. = FALSE
    )
  }
  value
}

.cns_observed_levels <- function(values) {
  values <- as.character(values)
  unique(values[!is.na(values)])
}

.cns_resolve_levels <- function(values, requested, name, caller) {
  requested <- .cns_plot_order(requested, name)
  resolved <- if (is.null(requested)) .cns_observed_levels(values) else requested
  if (!length(resolved)) {
    stop(
      sprintf("[%s] No non-missing levels are available for %s.", caller, name),
      call. = FALSE
    )
  }
  resolved
}

.cns_plot_colours <- function(palette, n) {
  if (!is.numeric(n) || length(n) != 1L || is.na(n) || n < 1 || n != floor(n)) {
    stop("n must be one positive whole number.", call. = FALSE)
  }
  n <- as.integer(n)
  if (is.null(palette)) return(palettes(n = n))
  if (!is.character(palette) || !length(palette) || anyNA(palette)) {
    stop(
      "palette must be a registered palette name or a non-empty colour vector.",
      call. = FALSE
    )
  }

  if (length(palette) == 1L && palette %in% palette_names()) {
    return(palettes(palette, n = n))
  }

  custom <- tryCatch(
    .cns_normalize_colours(palette),
    error = function(...) NULL
  )
  if (!is.null(custom)) return(rep(custom, length.out = n))

  # Preserve the palette registry's informative unknown-name error.
  palettes(palette, n = n)
}

.cns_plot_text_size <- function() {
  value <- settings("legend_fontsize")
  if (is.na(value)) value <- settings("title_fontsize")
  .cns_pt_to_mm(value)
}

.cns_plot_text_family <- function() {
  .cns_resolve_family(settings("font_family"))
}

.cns_manual_scale <- function(aesthetic, levels, palette, title) {
  colours <- .cns_plot_colours(palette, length(levels))
  values <- stats::setNames(colours, levels)
  if (identical(aesthetic, "fill")) {
    ggplot2::scale_fill_manual(
      values = values, limits = levels, drop = FALSE, name = title
    )
  } else {
    ggplot2::scale_colour_manual(
      values = values, limits = levels, drop = FALSE, name = title
    )
  }
}

.cns_bar_summary <- function(data, x, y, hue, x_levels, hue_levels) {
  x_values <- as.character(data[[x]])
  y_values <- data[[y]]

  if (is.null(hue)) {
    means <- vapply(
      x_levels,
      function(level) {
        selected <- !is.na(x_values) & x_values == level & !is.na(y_values)
        if (!any(selected)) return(NA_real_)
        mean(y_values[selected])
      },
      numeric(1L)
    )
    result <- data.frame(
      .cns_x = factor(x_levels, levels = x_levels),
      .cns_y = unname(means),
      stringsAsFactors = FALSE
    )
    return(result[!is.na(result$.cns_y), , drop = FALSE])
  }

  hue_values <- as.character(data[[hue]])
  # expand.grid varies x fastest, matching the Python hue-container label order.
  result <- expand.grid(
    .cns_x = x_levels,
    .cns_hue = hue_levels,
    KEEP.OUT.ATTRS = FALSE,
    stringsAsFactors = FALSE
  )
  result$.cns_y <- vapply(
    seq_len(nrow(result)),
    function(index) {
      selected <- !is.na(x_values) & x_values == result$.cns_x[[index]] &
        !is.na(hue_values) & hue_values == result$.cns_hue[[index]] &
        !is.na(y_values)
      if (!any(selected)) return(NA_real_)
      mean(y_values[selected])
    },
    numeric(1L)
  )
  result$.cns_x <- factor(result$.cns_x, levels = x_levels)
  result$.cns_hue <- factor(result$.cns_hue, levels = hue_levels)
  result[!is.na(result$.cns_y), , drop = FALSE]
}

#' Plot category means as bars
#'
#' This R-native counterpart to the Python cnsplots bar plot computes group
#' means explicitly and does not add an uncertainty interval or statistical
#' test. The result is an ordinary ggplot object and can be extended with `+`.
#' A character `palette` is always a palette name or colour; unlike the legacy
#' Python overload, data-column fill mappings are not hidden in this argument.
#'
#' @param data A data frame.
#' @param x Name of the categorical column.
#' @param y Name of the numeric column to summarize.
#' @param add_tip Add a two-decimal mean label to every observed bar.
#' @param hue Optional grouping column used for dodged bars.
#' @param order Optional display order for `x`. Unobserved levels are retained
#'   as empty axis positions.
#' @param hue_order Optional display order for `hue`.
#' @param palette A registered cnsplots palette name or vector of R colours.
#' @return A ggplot2 plot.
#' @export
barplot <- function(
  data, x, y, add_tip = FALSE, hue = NULL, order = NULL,
  hue_order = NULL, palette = NULL
) {
  caller <- "barplot"
  columns <- list(x = x, y = y)
  if (!is.null(hue)) columns$hue <- hue
  .cns_plot_data(data, columns, caller)
  .cns_plot_numeric_column(data, y, caller)
  add_tip <- .cns_assert_scalar_logical(add_tip, "add_tip")
  if (is.null(hue) && !is.null(hue_order)) {
    stop("hue_order can only be used when hue is supplied.", call. = FALSE)
  }

  x_levels <- .cns_resolve_levels(data[[x]], order, "order", caller)
  hue_levels <- if (is.null(hue)) {
    NULL
  } else {
    .cns_resolve_levels(data[[hue]], hue_order, "hue_order", caller)
  }
  summary <- .cns_bar_summary(data, x, y, hue, x_levels, hue_levels)
  if (!nrow(summary)) {
    stop(
      "[barplot] No complete observations remain after applying the requested order.",
      call. = FALSE
    )
  }

  if (is.null(hue)) {
    plot <- ggplot2::ggplot(
      summary,
      ggplot2::aes(x = .cns_x, y = .cns_y, fill = .cns_x)
    ) +
      ggplot2::geom_col(width = 0.8, colour = NA) +
      .cns_manual_scale("fill", x_levels, palette, x) +
      ggplot2::guides(fill = "none")
    label_position <- "identity"
  } else {
    dodge <- ggplot2::position_dodge(width = 0.8, preserve = "single")
    plot <- ggplot2::ggplot(
      summary,
      ggplot2::aes(x = .cns_x, y = .cns_y, fill = .cns_hue)
    ) +
      ggplot2::geom_col(width = 0.8, position = dodge, colour = NA) +
      .cns_manual_scale("fill", hue_levels, palette, hue)
    label_position <- dodge
  }

  if (add_tip) {
    summary$.cns_label <- sprintf("%.2f", summary$.cns_y)
    summary$.cns_vjust <- ifelse(summary$.cns_y < 0, 1.3, -0.3)
    plot <- plot + ggplot2::geom_text(
      data = summary,
      mapping = ggplot2::aes(label = .cns_label, vjust = .cns_vjust),
      position = label_position,
      colour = "black",
      family = .cns_plot_text_family(),
      size = .cns_plot_text_size(),
      show.legend = FALSE
    )
  }

  plot +
    ggplot2::scale_x_discrete(limits = x_levels, drop = FALSE) +
    ggplot2::labs(x = x, y = y) +
    setup_ggplot("standard")
}

.cns_strip_summary <- function(data, x, y, x_levels) {
  x_values <- as.character(data[[x]])
  y_values <- data[[y]]
  result <- data.frame(
    .cns_x = seq_along(x_levels),
    .cns_y = vapply(
      x_levels,
      function(level) {
        selected <- !is.na(x_values) & x_values == level & !is.na(y_values)
        if (!any(selected)) return(NA_real_)
        stats::median(y_values[selected])
      },
      numeric(1L)
    ),
    .cns_mean = vapply(
      x_levels,
      function(level) {
        selected <- !is.na(x_values) & x_values == level & !is.na(y_values)
        if (!any(selected)) return(NA_real_)
        mean(y_values[selected])
      },
      numeric(1L)
    )
  )
  result[!is.na(result$.cns_y), , drop = FALSE]
}

#' Plot individual observations by category
#'
#' Points are jittered horizontally. Median and mean summaries are calculated
#' over each `x` category, not separately within `hue`, matching the original
#' cnsplots behavior.
#'
#' @param data A data frame.
#' @param x Name of the categorical column.
#' @param y Name of the numeric column.
#' @param size Point size.
#' @param showmedian Draw a black median segment for each observed category.
#' @param showmeans Draw a white-filled, black-outlined mean point.
#' @param add_count Append `(n=...)` to each category tick label.
#' @param hue Optional column used to colour individual points.
#' @param order Optional display order for `x`.
#' @param hue_order Optional display order for `hue`.
#' @param palette A registered cnsplots palette name or vector of R colours.
#' @return A ggplot2 plot.
#' @export
stripplot <- function(
  data, x, y, size = 2, showmedian = TRUE, showmeans = FALSE,
  add_count = FALSE, hue = NULL, order = NULL, hue_order = NULL,
  palette = NULL
) {
  caller <- "stripplot"
  columns <- list(x = x, y = y)
  if (!is.null(hue)) columns$hue <- hue
  .cns_plot_data(data, columns, caller)
  y_values <- .cns_plot_numeric_column(data, y, caller)
  size <- .cns_assert_scalar_number(size, "size", positive = TRUE)
  showmedian <- .cns_assert_scalar_logical(showmedian, "showmedian")
  showmeans <- .cns_assert_scalar_logical(showmeans, "showmeans")
  add_count <- .cns_assert_scalar_logical(add_count, "add_count")
  if (is.null(hue) && !is.null(hue_order)) {
    stop("hue_order can only be used when hue is supplied.", call. = FALSE)
  }

  x_levels <- .cns_resolve_levels(data[[x]], order, "order", caller)
  hue_levels <- if (is.null(hue)) {
    NULL
  } else {
    .cns_resolve_levels(data[[hue]], hue_order, "hue_order", caller)
  }

  x_values <- as.character(data[[x]])
  selected <- !is.na(x_values) & x_values %in% x_levels & !is.na(y_values)
  if (!any(selected)) {
    stop(
      "[stripplot] No complete observations remain after applying the requested order.",
      call. = FALSE
    )
  }
  if (is.null(hue)) {
    point_data <- data.frame(
      .cns_x = match(x_values[selected], x_levels),
      .cns_y = y_values[selected]
    )
  } else {
    hue_values <- as.character(data[[hue]])
    selected <- selected & !is.na(hue_values) & hue_values %in% hue_levels
    point_data <- data.frame(
      .cns_x = match(x_values[selected], x_levels),
      .cns_y = y_values[selected],
      .cns_hue = factor(hue_values[selected], levels = hue_levels)
    )
  }
  summary <- .cns_strip_summary(data, x, y, x_levels)

  jitter <- ggplot2::position_jitter(width = 0.1, height = 0, seed = 0)
  if (is.null(hue)) {
    point_colour <- .cns_plot_colours(palette, 1L)[[1L]]
    plot <- ggplot2::ggplot(
      point_data,
      ggplot2::aes(x = .cns_x, y = .cns_y)
    ) +
      ggplot2::geom_point(
        position = jitter, size = size, colour = point_colour,
        show.legend = FALSE
      )
  } else {
    plot <- ggplot2::ggplot(
      point_data,
      ggplot2::aes(x = .cns_x, y = .cns_y, colour = .cns_hue)
    ) +
      ggplot2::geom_point(position = jitter, size = size) +
      .cns_manual_scale("colour", hue_levels, palette, hue)
  }

  if (showmedian && nrow(summary)) {
    plot <- plot + ggplot2::geom_segment(
      data = summary,
      mapping = ggplot2::aes(
        x = .cns_x - 0.15, xend = .cns_x + 0.15,
        y = .cns_y, yend = .cns_y
      ),
      inherit.aes = FALSE,
      colour = "black",
      linewidth = .cns_pt_to_mm(1),
      lineend = "butt",
      show.legend = FALSE
    )
  }
  if (showmeans && nrow(summary)) {
    mean_data <- summary
    mean_data$.cns_y <- mean_data$.cns_mean
    plot <- plot + ggplot2::geom_point(
      data = mean_data,
      mapping = ggplot2::aes(x = .cns_x, y = .cns_y),
      inherit.aes = FALSE,
      shape = 21,
      size = size + 1,
      stroke = 0.5,
      fill = "white",
      colour = "black",
      show.legend = FALSE
    )
  }

  counts <- vapply(
    x_levels,
    function(level) sum(!is.na(x_values) & x_values == level),
    integer(1L)
  )
  labels <- if (add_count) {
    sprintf("%s\n(n=%d)", x_levels, counts)
  } else {
    x_levels
  }

  plot +
    ggplot2::scale_x_continuous(
      breaks = seq_along(x_levels), labels = labels,
      limits = c(0.5, length(x_levels) + 0.5),
      expand = ggplot2::expansion(mult = 0)
    ) +
    ggplot2::labs(x = x, y = y) +
    setup_ggplot("standard")
}

.cns_category_counts <- function(values, requested_order, caller) {
  values <- as.character(values)
  observed <- unique(values[!is.na(values)])
  if (!length(observed)) {
    stop(
      sprintf("[%s] The categorical column has no non-missing values.", caller),
      call. = FALSE
    )
  }
  observed_counts <- vapply(
    observed,
    function(level) sum(!is.na(values) & values == level),
    integer(1L)
  )

  requested_order <- .cns_plot_order(requested_order, "order")
  levels <- if (is.null(requested_order)) {
    observed[base::order(
      -observed_counts, seq_along(observed_counts), method = "radix"
    )]
  } else {
    missing <- setdiff(observed, requested_order)
    unknown <- setdiff(requested_order, observed)
    if (length(missing) || length(unknown)) {
      stop(
        sprintf(
          "[%s] order must contain every observed category exactly once.",
          caller
        ),
        call. = FALSE
      )
    }
    requested_order
  }
  counts <- vapply(
    levels,
    function(level) sum(!is.na(values) & values == level),
    integer(1L)
  )
  if (!sum(counts)) {
    stop(
      sprintf("[%s] order does not select any observed categories.", caller),
      call. = FALSE
    )
  }

  fraction <- counts / sum(counts)
  ymax <- cumsum(counts) / sum(counts)
  ymin <- c(0, ymax[-length(ymax)])
  result <- data.frame(
    .cns_category = factor(levels, levels = levels),
    .cns_count = unname(counts),
    .cns_fraction = unname(fraction),
    .cns_ymin = ymin,
    .cns_ymax = ymax,
    .cns_midpoint = ymin + fraction / 2,
    stringsAsFactors = FALSE
  )
  attr(result, "levels") <- levels
  result
}

.cns_annotation_text_colours <- function(colours) {
  if (!settings("annotation_auto_contrast")) {
    return(rep("white", length(colours)))
  }
  rgb <- grDevices::col2rgb(colours) / 255
  luminance <- 0.2126 * rgb[1L, ] + 0.7152 * rgb[2L, ] + 0.0722 * rgb[3L, ]
  ifelse(luminance < 0.5, "white", "black")
}

.cns_polar_theme <- function(legend) {
  direction <- if (legend %in% c("top", "bottom")) "horizontal" else "vertical"
  setup_ggplot("embedding") +
    ggplot2::theme(
      legend.position = legend,
      legend.direction = direction,
      aspect.ratio = 1
    )
}

#' Plot categorical proportions as a pie chart
#'
#' Categories are ordered by decreasing frequency unless `order` is supplied.
#' Percentage labels use automatic black/white contrast when
#' `annotation_auto_contrast` is enabled in [settings()].
#'
#' @param data A data frame.
#' @param x Name of the categorical column.
#' @param legend Legend position: `"right"`, `"left"`, `"top"`, or `"bottom"`.
#' @param order Optional complete category display order.
#' @param palette A registered cnsplots palette name or vector of R colours.
#' @return A ggplot2 plot.
#' @export
pieplot <- function(
  data, x, legend = "bottom", order = NULL, palette = NULL
) {
  caller <- "pieplot"
  .cns_plot_data(data, list(x = x), caller)
  legend <- .cns_match_choice(
    legend, c("right", "left", "top", "bottom"), "legend"
  )
  plot_data <- .cns_category_counts(data[[x]], order, caller)
  levels <- attr(plot_data, "levels")
  colours <- .cns_plot_colours(palette, length(levels))
  names(colours) <- levels
  plot_data$.cns_label <- sprintf("%.0f%%", 100 * plot_data$.cns_fraction)
  plot_data$.cns_text_colour <- .cns_annotation_text_colours(colours[levels])
  label_data <- plot_data[plot_data$.cns_count > 0, , drop = FALSE]

  ggplot2::ggplot(
    plot_data,
    ggplot2::aes(
      ymin = .cns_ymin, ymax = .cns_ymax, fill = .cns_category
    )
  ) +
    ggplot2::geom_rect(
      xmin = 0, xmax = 1, colour = "white",
      linewidth = .cns_pt_to_mm(0.3)
    ) +
    ggplot2::geom_text(
      data = label_data,
      mapping = ggplot2::aes(
        x = 0.5, y = .cns_midpoint, label = .cns_label,
        colour = .cns_text_colour
      ),
      inherit.aes = FALSE,
      family = .cns_plot_text_family(),
      size = .cns_plot_text_size(),
      show.legend = FALSE
    ) +
    ggplot2::scale_fill_manual(
      values = colours, limits = levels, drop = FALSE, name = x
    ) +
    ggplot2::scale_colour_identity(guide = "none") +
    ggplot2::scale_x_continuous(
      limits = c(0, 1), breaks = NULL, expand = ggplot2::expansion(mult = 0)
    ) +
    ggplot2::scale_y_continuous(
      limits = c(0, 1), breaks = NULL, expand = ggplot2::expansion(mult = 0)
    ) +
    ggplot2::coord_polar(theta = "y") +
    ggplot2::labs(x = NULL, y = NULL) +
    .cns_polar_theme(legend)
}

#' Plot categorical proportions as a donut chart
#'
#' The ring has an outer radius of one and a width of 0.4. The source column
#' name is shown at the centre; percentages are intentionally omitted.
#'
#' @param data A data frame.
#' @param x Name of the categorical column.
#' @param legend Legend position: `"right"`, `"left"`, `"top"`, or `"bottom"`.
#' @param order Optional complete category display order.
#' @param palette A registered cnsplots palette name or vector of R colours.
#' @return A ggplot2 plot.
#' @export
donutplot <- function(
  data, x, legend = "bottom", order = NULL, palette = NULL
) {
  caller <- "donutplot"
  .cns_plot_data(data, list(x = x), caller)
  legend <- .cns_match_choice(
    legend, c("right", "left", "top", "bottom"), "legend"
  )
  plot_data <- .cns_category_counts(data[[x]], order, caller)
  levels <- attr(plot_data, "levels")
  colours <- .cns_plot_colours(palette, length(levels))
  names(colours) <- levels

  centre <- data.frame(.cns_x = 0, .cns_y = 0, .cns_label = x)
  ggplot2::ggplot(
    plot_data,
    ggplot2::aes(x = 0.8, y = .cns_count, fill = .cns_category)
  ) +
    ggplot2::geom_col(
      width = 0.4, colour = "black",
      linewidth = .cns_pt_to_mm(0.3)
    ) +
    ggplot2::geom_text(
      data = centre,
      mapping = ggplot2::aes(x = .cns_x, y = .cns_y, label = .cns_label),
      inherit.aes = FALSE,
      colour = "black",
      family = .cns_plot_text_family(),
      size = .cns_plot_text_size(),
      show.legend = FALSE
    ) +
    ggplot2::scale_fill_manual(
      values = colours, limits = levels, drop = FALSE, name = x
    ) +
    ggplot2::scale_x_continuous(
      limits = c(0, 1), breaks = NULL, expand = ggplot2::expansion(mult = 0)
    ) +
    ggplot2::scale_y_continuous(
      breaks = NULL, expand = ggplot2::expansion(mult = 0)
    ) +
    ggplot2::coord_polar(theta = "y") +
    ggplot2::guides(
      fill = ggplot2::guide_legend(
        override.aes = list(colour = NA, linewidth = 0)
      )
    ) +
    ggplot2::labs(x = NULL, y = NULL) +
    .cns_polar_theme(legend)
}

.cns_lollipop_marker <- function(marker) {
  marker <- .cns_assert_scalar_character(marker, "marker")
  shapes <- c(
    "o" = 16, "s" = 15, "^" = 17, "v" = 25,
    "D" = 18, "d" = 18, "+" = 3, "x" = 4, "*" = 8
  )
  if (!marker %in% names(shapes)) {
    stop(
      paste0(
        "marker must be one of: ",
        paste(sprintf("'%s'", names(shapes)), collapse = ", "), "."
      ),
      call. = FALSE
    )
  }
  unname(shapes[[marker]])
}

.cns_lollipop_bootstrap <- function(values) {
  had_seed <- exists(".Random.seed", envir = globalenv(), inherits = FALSE)
  if (had_seed) {
    old_seed <- get(".Random.seed", envir = globalenv(), inherits = FALSE)
  }
  on.exit({
    if (had_seed) {
      assign(".Random.seed", old_seed, envir = globalenv())
    } else if (exists(".Random.seed", envir = globalenv(), inherits = FALSE)) {
      rm(".Random.seed", envir = globalenv())
    }
  }, add = TRUE)
  set.seed(0)
  replicate(1000L, stats::median(sample(values, replace = TRUE)))
}

.cns_lollipop_error <- function(values, estimator, errorbar) {
  if (is.null(errorbar)) return(c(NA_real_, NA_real_))
  values <- values[!is.na(values)]
  n <- length(values)
  if (!n) return(c(NA_real_, NA_real_))

  standard_deviation <- stats::sd(values)
  if (identical(errorbar, "sd")) {
    return(rep(standard_deviation, 2L))
  }
  if (n < 2L) return(c(NA_real_, NA_real_))

  if (identical(estimator, "median")) {
    bootstrap <- .cns_lollipop_bootstrap(values)
    estimate <- stats::median(values)
    if (identical(errorbar, "se")) {
      return(rep(stats::sd(bootstrap), 2L))
    }
    interval <- stats::quantile(
      bootstrap, probs = c(0.025, 0.975), names = FALSE, type = 7
    )
    return(c(estimate - interval[[1L]], interval[[2L]] - estimate))
  }

  standard_error <- standard_deviation / sqrt(n)
  if (identical(errorbar, "se")) return(rep(standard_error, 2L))
  rep(stats::qt(0.975, df = n - 1L) * standard_error, 2L)
}

.cns_lollipop_summary <- function(
  data, category, value, hue, categories, hue_levels, estimator, errorbar,
  dodge
) {
  category_values <- as.character(data[[category]])
  numeric_values <- data[[value]]
  combinations <- if (is.null(hue)) {
    data.frame(
      .cns_x = categories,
      .cns_hue = NA_character_,
      stringsAsFactors = FALSE
    )
  } else {
    expand.grid(
      .cns_x = categories,
      .cns_hue = hue_levels,
      KEEP.OUT.ATTRS = FALSE,
      stringsAsFactors = FALSE
    )
  }
  hue_values <- if (is.null(hue)) NULL else as.character(data[[hue]])

  estimates <- numeric(nrow(combinations))
  lower <- upper <- rep(NA_real_, nrow(combinations))
  counts <- integer(nrow(combinations))
  for (index in seq_len(nrow(combinations))) {
    selected <- !is.na(category_values) &
      category_values == combinations$.cns_x[[index]] &
      !is.na(numeric_values)
    if (!is.null(hue)) {
      selected <- selected & !is.na(hue_values) &
        hue_values == combinations$.cns_hue[[index]]
    }
    values <- numeric_values[selected]
    counts[[index]] <- length(values)
    estimates[[index]] <- if (!length(values)) {
      NA_real_
    } else if (identical(estimator, "median")) {
      stats::median(values)
    } else {
      mean(values)
    }
    errors <- .cns_lollipop_error(values, estimator, errorbar)
    lower[[index]] <- errors[[1L]]
    upper[[index]] <- errors[[2L]]
    if (!is.null(hue) && length(values) < 2L) {
      lower[[index]] <- upper[[index]] <- NA_real_
    }
  }

  combinations$.cns_y <- estimates
  combinations$.cns_ymin <- estimates - lower
  combinations$.cns_ymax <- estimates + upper
  combinations$.cns_count <- counts
  combinations$.cns_x <- factor(combinations$.cns_x, levels = categories)
  combinations$.cns_hue <- factor(combinations$.cns_hue, levels = hue_levels)

  base_positions <- match(as.character(combinations$.cns_x), categories)
  if (is.null(hue)) {
    combinations$.cns_vjust <- base_positions
  } else {
    n_hue <- length(hue_levels)
    width <- dodge / n_hue
    offsets <- seq(
      -(dodge - width) / 2,
      (dodge - width) / 2,
      length.out = n_hue
    )
    combinations$.cns_vjust <- base_positions +
      offsets[match(as.character(combinations$.cns_hue), hue_levels)]
  }
  combinations
}

#' Plot aggregated values as lollipops
#'
#' This is the native ggplot2 counterpart of the author's lollipop recipe.
#' It automatically uses a horizontal layout when `x` is numeric and `y` is
#' categorical. Mean intervals use the sample standard deviation, standard
#' error, or a Student 95 percent confidence interval. Median standard errors
#' and confidence intervals use a deterministic 1,000-resample bootstrap that
#' restores the caller's random-number state.
#'
#' @param data A data frame.
#' @param x,y Column names. One column supplies categories and the other must be
#'   numeric.
#' @param hue Optional grouping column used for dodged lollipops.
#' @param order Optional category order.
#' @param hue_order Optional hue order.
#' @param pairs Reserved for Welch-test annotations. Non-`NULL` values currently
#'   fail explicitly rather than being ignored.
#' @param add_tip Add a two-decimal value label at each observed marker.
#' @param estimator Either `"mean"` or `"median"`.
#' @param errorbar One of `NULL`, `"se"`, `"sd"`, or `"ci"`.
#' @param markersize Matplotlib-compatible marker area in squared points.
#' @param linewidth Stem width in points.
#' @param marker Matplotlib-style marker code for a supported common shape.
#' @param dodge Total grouped-lollipop width.
#' @param color Optional single colour overriding `palette`.
#' @param palette A registered palette name or colour vector.
#' @param baseline Value from which stems start.
#' @return A ggplot2 plot.
#' @export
lollipopplot <- function(
  data, x, y, hue = NULL, order = NULL, hue_order = NULL, pairs = NULL,
  add_tip = FALSE, estimator = "mean", errorbar = NULL, markersize = 20,
  linewidth = 1.5, marker = "o", dodge = 0.8, color = NULL,
  palette = NULL, baseline = 0
) {
  caller <- "lollipopplot"
  columns <- list(x = x, y = y)
  if (!is.null(hue)) columns$hue <- hue
  .cns_plot_data(data, columns, caller)
  if (!is.null(pairs)) {
    stop(
      "[lollipopplot] pairs statistical annotations are not supported yet.",
      call. = FALSE
    )
  }
  add_tip <- .cns_assert_scalar_logical(add_tip, "add_tip")
  estimator <- .cns_match_choice(estimator, c("mean", "median"), "estimator")
  if (!is.null(errorbar)) {
    errorbar <- .cns_match_choice(errorbar, c("se", "sd", "ci"), "errorbar")
  }
  markersize <- .cns_assert_scalar_number(
    markersize, "markersize", positive = TRUE
  )
  linewidth <- .cns_assert_scalar_number(
    linewidth, "linewidth", positive = TRUE
  )
  dodge <- .cns_assert_scalar_number(dodge, "dodge", positive = TRUE)
  baseline <- .cns_assert_scalar_number(baseline, "baseline")
  shape <- .cns_lollipop_marker(marker)
  if (is.null(hue) && !is.null(hue_order)) {
    stop("hue_order can only be used when hue is supplied.", call. = FALSE)
  }

  x_numeric <- is.numeric(data[[x]])
  y_numeric <- is.numeric(data[[y]])
  horizontal <- x_numeric && !y_numeric
  category <- if (horizontal) y else x
  value <- if (horizontal) x else y
  .cns_plot_numeric_column(data, value, caller)

  categories <- .cns_resolve_levels(data[[category]], order, "order", caller)
  hue_levels <- if (is.null(hue)) {
    NULL
  } else {
    .cns_resolve_levels(data[[hue]], hue_order, "hue_order", caller)
  }
  summary <- .cns_lollipop_summary(
    data, category, value, hue, categories, hue_levels, estimator, errorbar,
    dodge
  )
  summary <- summary[!is.na(summary$.cns_y), , drop = FALSE]
  if (!nrow(summary)) {
    stop(
      paste0(
        "[lollipopplot] No complete observations remain after applying ",
        "the requested order."
      ),
      call. = FALSE
    )
  }

  if (!is.null(color)) {
    color <- .cns_assert_scalar_character(color, "color")
    colours <- rep(.cns_normalize_colours(color), length(if (is.null(hue)) {
      categories
    } else {
      hue_levels
    }))
  } else {
    colours <- .cns_plot_colours(
      palette, length(if (is.null(hue)) categories else hue_levels)
    )
  }

  if (is.null(hue)) {
    plot <- ggplot2::ggplot(
      summary,
      ggplot2::aes(
        x = .cns_vjust, y = .cns_y, colour = .cns_x
      )
    ) +
      .cns_manual_scale("colour", categories, colours, category) +
      ggplot2::guides(colour = "none")
  } else {
    plot <- ggplot2::ggplot(
      summary,
      ggplot2::aes(
        x = .cns_vjust, y = .cns_y, colour = .cns_hue
      )
    ) +
      .cns_manual_scale("colour", hue_levels, colours, hue)
  }

  plot <- plot + ggplot2::geom_segment(
    ggplot2::aes(
      xend = .cns_vjust, y = baseline, yend = .cns_y
    ),
    linewidth = .cns_pt_to_mm(linewidth), alpha = 0.4,
    lineend = "butt", show.legend = FALSE
  )

  error_data <- summary[
    is.finite(summary$.cns_ymin) & is.finite(summary$.cns_ymax),
    , drop = FALSE
  ]
  if (nrow(error_data)) {
    plot <- plot + ggplot2::geom_errorbar(
      data = error_data,
      mapping = ggplot2::aes(
        x = .cns_vjust, ymin = .cns_ymin, ymax = .cns_ymax
      ),
      inherit.aes = FALSE,
      width = 0.08,
      colour = "black",
      linewidth = .cns_pt_to_mm(0.7),
      show.legend = FALSE
    )
  }

  # Matplotlib keeps markers above error bars. after_scale also gives filled
  # ggplot shapes 21--25 (notably marker = "v") the resolved group colour.
  plot <- plot + ggplot2::geom_point(
    ggplot2::aes(fill = ggplot2::after_scale(colour)),
    shape = shape,
    size = .plot_point_size(markersize),
    show.legend = !is.null(hue)
  )

  if (add_tip) {
    label_data <- summary
    if (is.null(hue)) {
      tip_offset <- (max(label_data$.cns_y) - baseline) * 0.02
      label_data$.cns_y <- label_data$.cns_y + tip_offset
    } else {
      label_data$.cns_y <- label_data$.cns_y + vapply(
        seq_len(nrow(label_data)),
        function(index) {
          selected <- label_data$.cns_hue == label_data$.cns_hue[[index]]
          max(label_data$.cns_y[selected]) * 0.02
        },
        numeric(1L)
      )
    }
    label_data$.cns_label <- sprintf("%.2f", summary$.cns_y)
    plot <- plot + ggplot2::geom_text(
      data = label_data,
      mapping = ggplot2::aes(
        x = .cns_vjust, y = .cns_y, label = .cns_label
      ),
      inherit.aes = FALSE,
      colour = "black",
      family = .cns_plot_text_family(),
      size = .cns_plot_text_size(),
      hjust = if (horizontal) 0 else 0.5,
      vjust = if (horizontal) 0.5 else 0,
      show.legend = FALSE
    )
  }

  plot <- plot +
    ggplot2::scale_x_continuous(
      breaks = seq_along(categories), labels = categories,
      limits = c(0.5, length(categories) + 0.5),
      expand = ggplot2::expansion(mult = 0)
    ) +
    ggplot2::labs(x = category, y = value) +
    setup_ggplot("standard")
  if (horizontal) plot <- plot + ggplot2::coord_flip()
  plot
}

.cns_stack_counts <- function(data, bar, stack, bar_levels, stack_levels) {
  bar_values <- as.character(data[[bar]])
  stack_values <- as.character(data[[stack]])
  result <- expand.grid(
    .cns_x = bar_levels,
    .cns_hue = stack_levels,
    KEEP.OUT.ATTRS = FALSE,
    stringsAsFactors = FALSE
  )
  result$.cns_y <- vapply(
    seq_len(nrow(result)),
    function(index) {
      sum(
        !is.na(bar_values) & bar_values == result$.cns_x[[index]] &
          !is.na(stack_values) & stack_values == result$.cns_hue[[index]]
      )
    },
    integer(1L)
  )
  result$.cns_x <- factor(result$.cns_x, levels = bar_levels)
  result$.cns_hue <- factor(result$.cns_hue, levels = stack_levels)
  result
}

.cns_stack_sorted_levels <- function(values, name, caller) {
  observed <- values[!is.na(values)]
  resolved <- tryCatch(
    sort(unique(observed), na.last = NA),
    error = function(...) {
      stop(
        sprintf("[%s] %s must contain sortable categorical values.", caller, name),
        call. = FALSE
      )
    }
  )
  resolved <- as.character(resolved)
  if (!length(resolved)) {
    stop(
      sprintf("[%s] No non-missing levels are available for %s.", caller, name),
      call. = FALSE
    )
  }
  resolved
}

.cns_stack_segment_levels <- function(values, requested, caller) {
  observed <- .cns_stack_sorted_levels(values, "stack_order", caller)
  requested <- .cns_plot_order(requested, "stack_order")
  if (is.null(requested)) return(observed)
  if (!setequal(observed, requested) || length(observed) != length(requested)) {
    stop(
      paste0(
        "[stackplot] stack_order must contain every observed stack level ",
        "exactly once and no other levels."
      ),
      call. = FALSE
    )
  }
  requested
}

#' Plot categorical compositions as stacked bars
#'
#' Exactly one of `x` and `y` identifies the bar categories; `stack` identifies
#' the segments. Values are row-normalized by default and can be scaled by
#' `n_factor`, matching the author's recipe. Horizontal plots preserve the same
#' bar and stack semantics through [ggplot2::coord_flip()].
#'
#' @param data A data frame.
#' @param x Optional vertical-bar category column.
#' @param y Optional horizontal-bar category column.
#' @param stack Column defining stack segments.
#' @param order Optional bar-category order.
#' @param stack_order Optional stack and legend order.
#' @param width Bar width.
#' @param normalize Convert each bar to proportions before applying `n_factor`.
#' @param pairs Reserved for Fisher or chi-square annotations. Non-`NULL` values
#'   currently fail explicitly rather than being ignored.
#' @param add_count Append the original category count to tick labels.
#' @param n_factor Positive value by which plotted values are divided.
#' @return A ggplot2 plot.
#' @export
stackplot <- function(
  data, x = NULL, y = NULL, stack, order = NULL, stack_order = NULL,
  width = 0.5, normalize = TRUE, pairs = NULL, add_count = FALSE,
  n_factor = 1
) {
  caller <- "stackplot"
  if (is.null(x) == is.null(y)) {
    stop("stackplot requires exactly one of `x` or `y`.", call. = FALSE)
  }
  bar <- if (is.null(x)) y else x
  .cns_plot_data(data, list(bar = bar, stack = stack), caller)
  if (!is.null(pairs)) {
    stop(
      "[stackplot] pairs statistical annotations are not supported yet.",
      call. = FALSE
    )
  }
  width <- .cns_assert_scalar_number(width, "width", positive = TRUE)
  normalize <- .cns_assert_scalar_logical(normalize, "normalize")
  add_count <- .cns_assert_scalar_logical(add_count, "add_count")
  n_factor <- .cns_assert_scalar_number(
    n_factor, "n_factor", positive = TRUE
  )

  bar_levels <- if (is.null(order)) {
    .cns_stack_sorted_levels(data[[bar]], "order", caller)
  } else {
    .cns_resolve_levels(data[[bar]], order, "order", caller)
  }
  stack_levels <- .cns_stack_segment_levels(
    data[[stack]], stack_order, caller
  )
  plot_data <- .cns_stack_counts(
    data, bar, stack, bar_levels, stack_levels
  )
  totals <- vapply(
    bar_levels,
    function(level) {
      sum(plot_data$.cns_y[as.character(plot_data$.cns_x) == level])
    },
    numeric(1L)
  )
  if (!any(totals > 0)) {
    stop(
      "[stackplot] No observations remain after applying the requested orders.",
      call. = FALSE
    )
  }
  if (normalize) {
    denominators <- totals[match(as.character(plot_data$.cns_x), bar_levels)]
    plot_data$.cns_y <- ifelse(
      denominators > 0, plot_data$.cns_y / denominators, 0
    )
    value_label <- "Frequency"
  } else {
    value_label <- "Count"
  }
  plot_data$.cns_y <- plot_data$.cns_y / n_factor

  colours <- .cns_plot_colours(NULL, length(stack_levels))
  names(colours) <- stack_levels
  counts <- vapply(
    bar_levels,
    function(level) {
      sum(!is.na(data[[bar]]) & as.character(data[[bar]]) == level)
    },
    integer(1L)
  )
  labels <- if (add_count) {
    sprintf("%s\n(n=%d)", bar_levels, counts)
  } else {
    bar_levels
  }

  plot <- ggplot2::ggplot(
    plot_data,
    ggplot2::aes(x = .cns_x, y = .cns_y, fill = .cns_hue)
  ) +
    ggplot2::geom_col(
      width = width,
      position = ggplot2::position_stack(reverse = TRUE),
      colour = NA
    ) +
    ggplot2::scale_fill_manual(
      values = colours, limits = stack_levels, breaks = stack_levels,
      drop = FALSE, name = stack
    ) +
    ggplot2::scale_x_discrete(
      limits = bar_levels, labels = labels, drop = FALSE
    ) +
    ggplot2::labs(x = NULL, y = value_label) +
    setup_ggplot("standard")
  if (!is.null(y)) plot <- plot + ggplot2::coord_flip()
  plot
}
