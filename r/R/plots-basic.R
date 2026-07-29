#' Draw a scatter plot
#'
#' @param data A data frame.
#' @param x,y Column names.
#' @param s Matplotlib-compatible marker area in points squared.
#' @param hue Optional grouping column.
#' @param hue_order Optional order of hue levels.
#' @param palette Palette name or custom colours.
#' @param ... Additional arguments passed to `ggplot2::geom_point()`.
#' @return A ggplot object.
#' @export
scatterplot <- function(
  data, x, y, s = 7, hue = NULL, hue_order = NULL, palette = NULL, ...
) {
  columns <- c(x, y, if (!is.null(hue)) hue)
  .plot_check_data(data, columns, "scatterplot")
  point_size <- .plot_point_size(s)
  plot_data <- data.frame(.x = data[[x]], .y = data[[y]], check.names = FALSE)

  if (is.null(hue)) {
    colour <- .plot_colours(palette, 1L)[[1L]]
    plot <- ggplot2::ggplot(plot_data, ggplot2::aes(x = .x, y = .y)) +
      ggplot2::geom_point(size = point_size, colour = colour, stroke = 0, ...)
  } else {
    levels <- .plot_levels(data[[hue]], hue_order, "hue_order")
    plot_data$.hue <- factor(as.character(data[[hue]]), levels = levels)
    plot_data <- plot_data[!is.na(plot_data$.hue), , drop = FALSE]
    if (!nrow(plot_data)) {
      stop("[scatterplot] no observations match hue_order.", call. = FALSE)
    }
    plot <- ggplot2::ggplot(
      plot_data, ggplot2::aes(x = .x, y = .y, colour = .hue)
    ) +
      ggplot2::geom_point(size = point_size, stroke = 0, ...) +
      scale_colour_palette(
        .plot_colours(palette, length(levels)),
        limits = levels, drop = FALSE, name = hue
      )
  }

  .plot_finish(plot, x = x, y = y)
}

#' Draw a placeholder panel
#'
#' @param description Text shown in the placeholder caption.
#' @return A ggplot object.
#' @export
placeholderplot <- function(description) {
  description <- .cns_assert_scalar_character(description, "description", allow_empty = TRUE)
  current <- settings()
  font_family <- .cns_resolve_family(current$font_family)
  font_face <- .cns_resolve_face(current$title_fontweight)
  label <- paste(strwrap(description, width = 48), collapse = "\n")

  rounded <- function(fill, colour = NA, linewidth = 0, radius = 0.04) {
    grid::roundrectGrob(
      r = grid::unit(radius, "snpc"),
      gp = grid::gpar(
        fill = fill, col = colour,
        lwd = linewidth * 96 / 72
      )
    )
  }

  ggplot2::ggplot() +
    ggplot2::annotation_custom(
      rounded("#EEF1F4", "#B8C0CC", 0.9),
      xmin = 0.02, xmax = 0.98, ymin = 0.02, ymax = 0.98
    ) +
    ggplot2::annotation_custom(
      rounded("#E0E5EB", "#C5CCD6", 0.8),
      xmin = 0.08, xmax = 0.92, ymin = 0.34, ymax = 0.78
    ) +
    ggplot2::annotation_custom(
      grid::circleGrob(gp = grid::gpar(fill = "#C7D0DB", col = NA)),
      xmin = 0.725, xmax = 0.815, ymin = 0.635, ymax = 0.725
    ) +
    ggplot2::annotation_custom(
      grid::polygonGrob(
        x = c(0, 0.514, 1), y = c(0, 1, 0),
        gp = grid::gpar(fill = "#B7C2D0", col = NA)
      ),
      xmin = 0.15, xmax = 0.52, ymin = 0.38, ymax = 0.60
    ) +
    ggplot2::annotation_custom(
      grid::polygonGrob(
        x = c(0, 0.478, 1), y = c(0, 1, 0),
        gp = grid::gpar(fill = "#A8B5C5", col = NA)
      ),
      xmin = 0.36, xmax = 0.82, ymin = 0.38, ymax = 0.55
    ) +
    ggplot2::annotation_custom(
      rounded("#F8F9FB"),
      xmin = 0.13, xmax = 0.87, ymin = 0.10, ymax = 0.24
    ) +
    ggplot2::annotate(
      "text", x = 0.5, y = 0.17, label = label,
      family = font_family, fontface = font_face,
      colour = "#59616B", size = .cns_pt_to_mm(current$title_fontsize),
      lineheight = 0.95
    ) +
    ggplot2::coord_cartesian(
      xlim = c(0, 1), ylim = c(0, 1), expand = FALSE, clip = "off"
    ) +
    ggplot2::theme_void(base_family = font_family, base_size = current$title_fontsize) +
    ggplot2::theme(
      plot.background = ggplot2::element_rect(fill = "transparent", colour = NA),
      panel.background = ggplot2::element_rect(fill = "transparent", colour = NA),
      plot.margin = ggplot2::margin(0, 0, 0, 0)
    )
}
