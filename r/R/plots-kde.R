.kde_data <- function(values, adjust = 1, n = 200L) {
  values <- values[is.finite(values)]
  if (length(values) < 2L || length(unique(values)) < 2L) {
    stop("[kdeplot] each density requires at least 2 distinct finite values.", call. = FALSE)
  }
  bw <- stats::sd(values) * length(values)^(-1 / 5) * adjust
  if (!is.finite(bw) || bw <= 0) {
    stop("[kdeplot] could not determine a positive bandwidth.", call. = FALSE)
  }
  estimate <- stats::density(
    values, bw = bw, n = n,
    from = min(values) - 3 * bw,
    to = max(values) + 3 * bw
  )
  data.frame(.x = estimate$x, .density = estimate$y)
}

#' Draw a kernel density estimate
#'
#' @param data A data frame.
#' @param x Numeric column name.
#' @param add_mode Add the author's dashed KDE-peak marker when ungrouped.
#' @param hue Optional grouping column.
#' @param hue_order Optional order of hue levels.
#' @param palette Palette name or custom colours.
#' @param fill Fill the area below each density.
#' @param linewidth Line width in points.
#' @param adjust Bandwidth multiplier.
#' @return A ggplot object.
#' @export
kdeplot <- function(
  data, x, add_mode = TRUE, hue = NULL, hue_order = NULL,
  palette = NULL, fill = FALSE, linewidth = 1, adjust = 1
) {
  columns <- c(x, if (!is.null(hue)) hue)
  .plot_check_data(data, columns, "kdeplot", numeric = x)
  .cns_assert_scalar_logical(add_mode, "add_mode")
  .cns_assert_scalar_logical(fill, "fill")
  linewidth <- .cns_assert_scalar_number(linewidth, "linewidth", positive = TRUE)
  adjust <- .cns_assert_scalar_number(adjust, "adjust", positive = TRUE)

  if (is.null(hue)) {
    density <- .kde_data(data[[x]], adjust = adjust)
    colour <- .plot_colours(palette, 1L)[[1L]]
    plot <- ggplot2::ggplot(density, ggplot2::aes(x = .x, y = .density))
    if (fill) {
      plot <- plot + ggplot2::geom_area(fill = colour, alpha = 0.25, colour = NA)
    }
    plot <- plot + ggplot2::geom_line(
      colour = colour, linewidth = .cns_pt_to_mm(linewidth)
    )

    if (add_mode) {
      peak <- density[which.max(density$.density), , drop = FALSE]
      plot <- plot +
        ggplot2::geom_segment(
          data = peak,
          ggplot2::aes(x = .x, xend = .x, y = 0, yend = .density),
          inherit.aes = FALSE,
          colour = colour, linewidth = .cns_pt_to_mm(0.8),
          linetype = "dashed"
        ) +
        ggplot2::annotate(
          "label", x = peak$.x, y = max(density$.density) * 0.05,
          label = sprintf("%.2f", peak$.x),
          hjust = 0.5, vjust = 0,
          colour = colour, fill = "white", linewidth = 0,
          size = .cns_pt_to_mm(.plot_legend_fontsize())
        )
    }
  } else {
    keep <- !is.na(data[[hue]]) & is.finite(data[[x]])
    levels <- .plot_levels(data[[hue]][keep], hue_order, "hue_order")
    densities <- do.call(rbind, lapply(levels, function(group) {
      result <- .kde_data(data[[x]][keep & as.character(data[[hue]]) == group], adjust)
      result$.group <- factor(group, levels = levels)
      result
    }))
    colours <- .plot_colours(palette, length(levels))
    plot <- ggplot2::ggplot(
      densities, ggplot2::aes(x = .x, y = .density, colour = .group)
    )
    if (fill) {
      plot <- plot + ggplot2::geom_area(
        ggplot2::aes(fill = .group), alpha = 0.25,
        position = "identity", colour = NA, show.legend = FALSE
      )
    }
    plot <- plot +
      ggplot2::geom_line(linewidth = .cns_pt_to_mm(linewidth)) +
      scale_colour_palette(colours, limits = levels, drop = FALSE, name = hue)
    if (fill) {
      plot <- plot + scale_fill_palette(
        colours, limits = levels, drop = FALSE, name = hue
      )
    }

    if (length(levels) == 2L) {
      first <- data[[x]][keep & as.character(data[[hue]]) == levels[[1L]]]
      second <- data[[x]][keep & as.character(data[[hue]]) == levels[[2L]]]
      p <- suppressWarnings(stats::ks.test(first, second, exact = FALSE)$p.value)
      plot <- plot + ggplot2::annotate(
        "text", x = Inf, y = Inf,
        label = paste0("P=", format.pval(p, digits = 2, eps = 1e-99)),
        hjust = 1, vjust = 1,
        size = .cns_pt_to_mm(.plot_legend_fontsize())
      )
      if (settings("verbosity") > 0) {
        message("P-value was determined by two-sided Kolmogorov-Smirnov test.")
      }
    }
  }

  .plot_finish(plot, x = x, y = "Density")
}
