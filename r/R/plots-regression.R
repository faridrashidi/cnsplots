.linear_fit_data <- function(data, level = 0.95) {
  fit <- stats::lm(.y ~ .x, data = data)
  x_grid <- if (length(unique(data$.x)) == 1L) {
    unique(data$.x)
  } else {
    seq(min(data$.x), max(data$.x), length.out = 100L)
  }
  predicted <- suppressWarnings(stats::predict(
    fit, newdata = data.frame(.x = x_grid),
    interval = "confidence", level = level
  ))
  data.frame(
    .x = x_grid,
    .fit = predicted[, "fit"],
    .lower = predicted[, "lwr"],
    .upper = predicted[, "upr"],
    check.names = FALSE
  )
}

.pearson_label <- function(x, y, prefix = NULL) {
  n <- length(x)
  r <- suppressWarnings(stats::cor(x, y, method = "pearson"))
  p_value <- if (!is.finite(r)) {
    NA_real_
  } else if (n == 2L) {
    1
  } else if (abs(r) >= 1) {
    0
  } else {
    statistic <- r * sqrt((n - 2) / (1 - r^2))
    2 * stats::pt(-abs(statistic), df = n - 2)
  }
  p <- if (is.na(p_value)) "NA" else format.pval(p_value, digits = 2, eps = 1e-99)
  r_text <- if (is.na(r)) "NA" else sprintf("%.2f", r)
  label <- sprintf("r=%s, P=%s", r_text, p)
  if (is.null(prefix)) label else paste0(prefix, ": ", label)
}

#' Draw a linear regression plot
#'
#' @param data A data frame.
#' @param x,y Numeric column names.
#' @param hue Optional grouping column. Each group receives its own fit.
#' @param s Matplotlib-compatible marker area in points squared.
#' @param color A point/line colour, or a data column used to colour points.
#' @param hue_order Optional order of hue levels.
#' @param palette Palette name or custom colours.
#' @param level Confidence level for the fitted mean.
#' @param ... Additional arguments passed to `ggplot2::geom_point()`.
#' @return A ggplot object.
#' @export
regplot <- function(
  data, x, y, hue = NULL, s = 3, color = "black",
  hue_order = NULL, palette = NULL, level = 0.95, ...
) {
  columns <- c(x, y, if (!is.null(hue)) hue)
  color_is_column <- is.character(color) && length(color) == 1L && color %in% names(data)
  if (is.null(hue) && color_is_column) columns <- c(columns, color)
  .plot_check_data(data, columns, "regplot", numeric = c(x, y))
  level <- .cns_assert_scalar_number(level, "level", positive = TRUE)
  if (level >= 1) stop("level must be less than one.", call. = FALSE)

  keep <- is.finite(data[[x]]) & is.finite(data[[y]])
  if (!is.null(hue)) keep <- keep & !is.na(data[[hue]])
  if (is.null(hue) && color_is_column) keep <- keep & !is.na(data[[color]])
  plot_data <- data.frame(
    .x = data[[x]][keep], .y = data[[y]][keep], check.names = FALSE
  )
  if (nrow(plot_data) < 2L) {
    stop("[regplot] Pearson correlation requires at least 2 finite paired observations.", call. = FALSE)
  }
  point_size <- .plot_point_size(s)
  line_width <- .cns_pt_to_mm(1.2)

  if (!is.null(hue)) {
    levels <- .plot_levels(data[[hue]][keep], hue_order, "hue_order")
    plot_data$.group <- factor(as.character(data[[hue]][keep]), levels = levels)
    plot_data <- plot_data[!is.na(plot_data$.group), , drop = FALSE]
    counts <- table(plot_data$.group)
    if (any(counts < 2L)) {
      bad <- names(counts)[counts < 2L]
      stop(
        sprintf("[regplot] Pearson correlation requires at least 2 observations in: %s.", paste(bad, collapse = ", ")),
        call. = FALSE
      )
    }
    fits <- do.call(rbind, lapply(levels, function(group) {
      subset <- plot_data[plot_data$.group == group, , drop = FALSE]
      result <- .linear_fit_data(subset, level)
      result$.group <- factor(group, levels = levels)
      result
    }))
    labels <- do.call(rbind, lapply(seq_along(levels), function(i) {
      group <- levels[[i]]
      subset <- plot_data[plot_data$.group == group, , drop = FALSE]
      data.frame(
        .x = -Inf, .y = Inf, .group = factor(group, levels = levels),
        .label = .pearson_label(subset$.x, subset$.y, group),
        .vjust = 1 + (i - 1) * 1.25
      )
    }))
    colours <- .plot_colours(palette, length(levels))

    plot <- ggplot2::ggplot(plot_data, ggplot2::aes(x = .x, y = .y, colour = .group)) +
      ggplot2::geom_ribbon(
        data = fits,
        ggplot2::aes(x = .x, ymin = .lower, ymax = .upper, fill = .group),
        inherit.aes = FALSE, alpha = 0.2, colour = NA, show.legend = FALSE
      ) +
      ggplot2::geom_line(
        data = fits, ggplot2::aes(x = .x, y = .fit, colour = .group),
        inherit.aes = FALSE, linewidth = line_width
      ) +
      ggplot2::geom_point(size = point_size, stroke = 0, ...) +
      ggplot2::geom_text(
        data = labels,
        ggplot2::aes(x = .x, y = .y, label = .label, colour = .group, vjust = .vjust),
        inherit.aes = FALSE, hjust = -0.05,
        size = .cns_pt_to_mm(.plot_legend_fontsize()), show.legend = FALSE
      ) +
      scale_colour_palette(colours, limits = levels, drop = FALSE, name = hue) +
      scale_fill_palette(colours, limits = levels, drop = FALSE, name = hue)
  } else {
    fit <- .linear_fit_data(plot_data, level)
    line_colour <- if (color_is_column) "black" else color
    line_colour <- .cns_assert_colour(line_colour, "color")

    plot <- ggplot2::ggplot(plot_data, ggplot2::aes(x = .x, y = .y)) +
      ggplot2::geom_ribbon(
        data = fit, ggplot2::aes(x = .x, ymin = .lower, ymax = .upper),
        inherit.aes = FALSE, fill = line_colour, alpha = 0.2, colour = NA
      ) +
      ggplot2::geom_line(
        data = fit, ggplot2::aes(x = .x, y = .fit),
        inherit.aes = FALSE, colour = line_colour, linewidth = line_width
      )

    if (color_is_column) {
      levels <- .plot_levels(data[[color]][keep])
      plot_data$.group <- factor(as.character(data[[color]][keep]), levels = levels)
      plot <- plot +
        ggplot2::geom_point(
          data = plot_data, ggplot2::aes(x = .x, y = .y, colour = .group),
          size = point_size, stroke = 0, ...
        ) +
        scale_colour_palette(
          .plot_colours(palette, length(levels)),
          limits = levels, drop = FALSE, name = color
        )
    } else {
      point_colour <- .cns_assert_colour(color, "color")
      plot <- plot + ggplot2::geom_point(
        size = point_size, colour = point_colour, stroke = 0, ...
      )
    }
    plot <- plot + ggplot2::annotate(
      "text", x = -Inf, y = Inf,
      label = .pearson_label(plot_data$.x, plot_data$.y),
      hjust = -0.05, vjust = 1,
      colour = line_colour,
      size = .cns_pt_to_mm(.plot_legend_fontsize())
    )
  }

  .plot_finish(plot, x = x, y = y)
}
