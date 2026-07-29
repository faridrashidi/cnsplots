#' Modify cnsplots axes
#'
#' @param x,y Whether to display each axis.
#' @param ticks Whether to display tick marks.
#' @param tick_labels Whether to display tick labels.
#' @param titles Whether to display axis titles.
#' @return An incomplete ggplot2 theme patch.
#' @export
theme_axes <- function(
  x = TRUE, y = TRUE, ticks = TRUE, tick_labels = TRUE, titles = TRUE
) {
  values <- list(x = x, y = y, ticks = ticks, tick_labels = tick_labels, titles = titles)
  for (name in names(values)) .cns_assert_scalar_logical(values[[name]], name)
  reference <- setup_ggplot("standard")
  resolved <- function(name) .cns_resolve_theme_element(reference, name)
  ggplot2::theme(
    axis.line.x = if (x) resolved("axis.line.x") else ggplot2::element_blank(),
    axis.line.y = if (y) resolved("axis.line.y") else ggplot2::element_blank(),
    axis.ticks.x = if (x && ticks) resolved("axis.ticks.x") else ggplot2::element_blank(),
    axis.ticks.y = if (y && ticks) resolved("axis.ticks.y") else ggplot2::element_blank(),
    axis.text.x = if (x && tick_labels) resolved("axis.text.x") else ggplot2::element_blank(),
    axis.text.y = if (y && tick_labels) resolved("axis.text.y") else ggplot2::element_blank(),
    axis.title.x = if (x && titles) resolved("axis.title.x") else ggplot2::element_blank(),
    axis.title.y = if (y && titles) resolved("axis.title.y") else ggplot2::element_blank()
  )
}

#' Modify a cnsplots legend
#'
#' @param position A ggplot2 legend position.
#' @param direction Optional "horizontal" or "vertical".
#' @param title Whether to display the legend title.
#' @return An incomplete ggplot2 theme patch.
#' @export
theme_legend <- function(position = "right", direction = NULL, title = TRUE) {
  .cns_assert_scalar_logical(title, "title")
  if (!is.null(direction)) {
    direction <- .cns_match_choice(direction, c("horizontal", "vertical"), "direction")
  }
  legend_title <- if (title) {
    .cns_resolve_theme_element(setup_ggplot("standard"), "legend.title")
  } else {
    ggplot2::element_blank()
  }
  ggplot2::theme(
    legend.position = position,
    legend.direction = direction,
    legend.title = legend_title,
    legend.background = ggplot2::element_blank(),
    legend.box.background = ggplot2::element_blank()
  )
}

#' Modify cnsplots facet strips
#'
#' @param background Whether strip backgrounds are visible.
#' @param face Font face for strip text.
#' @param size Optional strip text size in points.
#' @return An incomplete ggplot2 theme patch.
#' @export
theme_facet <- function(background = FALSE, face = "bold", size = NULL) {
  .cns_assert_scalar_logical(background, "background")
  if (!is.null(size)) size <- .cns_assert_scalar_number(size, "size", positive = TRUE)
  ggplot2::theme(
    strip.background = if (background) {
      ggplot2::element_rect(fill = "grey95", colour = NA)
    } else {
      ggplot2::element_blank()
    },
    strip.text = ggplot2::element_text(face = face, size = size)
  )
}

#' Modify cnsplots grid lines
#'
#' @param major,minor One of "none", "x", "y", or "both".
#' @param colour Grid colour.
#' @param linewidth Grid width in points.
#' @return An incomplete ggplot2 theme patch.
#' @export
theme_grid <- function(
  major = c("none", "x", "y", "both"),
  minor = c("none", "x", "y", "both"),
  colour = "grey85",
  linewidth = 0.3
) {
  major <- match.arg(major)
  minor <- match.arg(minor)
  colour <- .cns_assert_colour(colour, "colour")
  linewidth <- .cns_assert_scalar_number(linewidth, "linewidth", positive = TRUE)
  line <- ggplot2::element_line(
    colour = colour, linewidth = .cns_pt_to_mm(linewidth)
  )
  blank <- ggplot2::element_blank()
  choose_x <- function(value) if (value %in% c("x", "both")) line else blank
  choose_y <- function(value) if (value %in% c("y", "both")) line else blank
  ggplot2::theme(
    panel.grid.major.x = choose_x(major),
    panel.grid.major.y = choose_y(major),
    panel.grid.minor.x = choose_x(minor),
    panel.grid.minor.y = choose_y(minor)
  )
}

#' Modify cnsplots spacing
#'
#' @param plot_margin Numeric top, right, bottom, and left margins in points.
#' @param panel_spacing Panel spacing in points.
#' @param legend_spacing Legend spacing in points.
#' @return An incomplete ggplot2 theme patch.
#' @export
theme_spacing <- function(
  plot_margin = c(0, 0, 0, 0), panel_spacing = 4, legend_spacing = 2
) {
  if (!is.numeric(plot_margin) || length(plot_margin) != 4L || anyNA(plot_margin)) {
    stop("plot_margin must contain top, right, bottom, and left values.", call. = FALSE)
  }
  panel_spacing <- .cns_assert_scalar_number(
    panel_spacing, "panel_spacing", non_negative = TRUE
  )
  legend_spacing <- .cns_assert_scalar_number(
    legend_spacing, "legend_spacing", non_negative = TRUE
  )
  ggplot2::theme(
    plot.margin = ggplot2::margin(
      t = plot_margin[[1L]], r = plot_margin[[2L]],
      b = plot_margin[[3L]], l = plot_margin[[4L]], unit = "pt"
    ),
    panel.spacing = grid::unit(panel_spacing, "pt"),
    legend.spacing = grid::unit(legend_spacing, "pt")
  )
}
