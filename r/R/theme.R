#' Set up the canonical cnsplots ggplot2 theme
#'
#' The canonical R baseline follows Python setup_matplotlib() and setup_ax():
#' 8 pt titles and axis labels, 7 pt ticks and legend text, bottom/left axes,
#' no grid, and the Ecotyper1 default palette.
#'
#' @param profile One of "standard", "embedding", or "matrix".
#' @param base_family Optional R graphics family. The default maps the Python
#'   generic sans-serif stack to R's portable "sans" family.
#' @param base_size Optional title and axis-title size in points.
#' @return A complete ggplot2 theme.
#' @export
setup_ggplot <- function(
  profile = c("standard", "embedding", "matrix"),
  base_family = NULL,
  base_size = NULL
) {
  profile <- match.arg(profile)
  settings <- settings()
  if (is.null(base_family)) base_family <- .cns_resolve_family(settings$font_family)
  if (is.null(base_size)) base_size <- settings$title_fontsize
  base_family <- .cns_assert_scalar_character(base_family, "base_family")
  base_size <- .cns_assert_scalar_number(base_size, "base_size", positive = TRUE)

  legend_size <- if (is.na(settings$legend_fontsize)) base_size else settings$legend_fontsize
  legend_title_size <- if (is.na(settings$legend_title_fontsize)) {
    base_size
  } else {
    settings$legend_title_fontsize
  }
  axis_linewidth <- .cns_pt_to_mm(settings$axes_linewidth)
  tick_linewidth <- .cns_pt_to_mm(max(settings$xtick_major_width, settings$ytick_major_width))
  title_face <- .cns_resolve_face(settings$title_fontweight)
  transparent <- "transparent"

  result <- ggplot2::theme_classic(
    base_size = base_size,
    base_family = base_family,
    base_line_size = axis_linewidth,
    base_rect_size = axis_linewidth
  ) +
    ggplot2::theme(
      text = ggplot2::element_text(
        family = base_family, face = "plain",
        colour = settings$axes_labelcolor, size = base_size
      ),
      plot.title = ggplot2::element_text(
        family = base_family, face = title_face, size = base_size,
        colour = settings$axes_labelcolor, hjust = 0.5,
        margin = ggplot2::margin(b = settings$axes_titlepad, unit = "pt")
      ),
      plot.subtitle = ggplot2::element_text(
        family = base_family, face = "plain", size = legend_size,
        colour = settings$axes_labelcolor
      ),
      plot.caption = ggplot2::element_text(
        family = base_family, face = "plain", size = legend_size,
        colour = settings$axes_labelcolor, hjust = 1
      ),
      plot.tag = ggplot2::element_text(
        family = .cns_resolve_family(settings$panel_label_fontname),
        face = .cns_resolve_face(settings$panel_label_fontweight),
        size = base_size, colour = settings$axes_labelcolor
      ),
      axis.title = ggplot2::element_text(
        family = base_family, face = "plain", size = base_size,
        colour = settings$axes_labelcolor
      ),
      axis.title.x = ggplot2::element_text(
        margin = ggplot2::margin(t = settings$axes_labelpad, unit = "pt")
      ),
      axis.title.y = ggplot2::element_text(
        margin = ggplot2::margin(r = settings$axes_labelpad, unit = "pt")
      ),
      axis.text = ggplot2::element_text(
        family = base_family, face = "plain", size = legend_size,
        colour = settings$axes_labelcolor
      ),
      axis.text.x = ggplot2::element_text(
        angle = settings$xtick_labelrotation, hjust = 0.5,
        margin = ggplot2::margin(t = settings$xtick_major_pad, unit = "pt")
      ),
      axis.text.y = ggplot2::element_text(
        angle = settings$ytick_labelrotation, vjust = 0.5,
        margin = ggplot2::margin(r = settings$ytick_major_pad, unit = "pt")
      ),
      axis.line = ggplot2::element_line(
        colour = settings$axes_edgecolor, linewidth = axis_linewidth,
        lineend = "butt"
      ),
      axis.ticks = ggplot2::element_line(
        colour = settings$xtick_color, linewidth = tick_linewidth,
        lineend = "butt"
      ),
      axis.ticks.length = grid::unit(
        max(settings$xtick_major_size, settings$ytick_major_size), "pt"
      ),
      panel.grid.major = ggplot2::element_blank(),
      panel.grid.minor = ggplot2::element_blank(),
      panel.background = ggplot2::element_rect(fill = transparent, colour = NA),
      plot.background = ggplot2::element_rect(fill = transparent, colour = NA),
      legend.background = ggplot2::element_rect(fill = transparent, colour = NA),
      legend.box.background = ggplot2::element_blank(),
      legend.key = ggplot2::element_rect(fill = transparent, colour = NA),
      legend.text = ggplot2::element_text(
        family = base_family, face = "plain", size = legend_size,
        colour = settings$axes_labelcolor,
        margin = ggplot2::margin(
          l = settings$legend_handletextpad * legend_size, unit = "pt"
        )
      ),
      legend.title = ggplot2::element_text(
        family = base_family, face = "plain", size = legend_title_size,
        colour = settings$axes_labelcolor
      ),
      legend.key.width = grid::unit(
        settings$legend_handlelength * legend_size, "pt"
      ),
      legend.key.height = grid::unit(
        settings$legend_handleheight * legend_size, "pt"
      ),
      strip.background = ggplot2::element_blank(),
      strip.text = ggplot2::element_text(
        family = base_family, face = title_face, size = base_size,
        colour = settings$axes_labelcolor
      )
    )

  if (!settings$axes_spines_top) {
    result <- result + ggplot2::theme(axis.line.x.top = ggplot2::element_blank())
  }
  if (!settings$axes_spines_right) {
    result <- result + ggplot2::theme(axis.line.y.right = ggplot2::element_blank())
  }
  if (!settings$xtick_bottom) {
    result <- result + ggplot2::theme(
      axis.ticks.x = ggplot2::element_blank(),
      axis.text.x = ggplot2::element_blank()
    )
  }
  if (!settings$ytick_left) {
    result <- result + ggplot2::theme(
      axis.ticks.y = ggplot2::element_blank(),
      axis.text.y = ggplot2::element_blank()
    )
  }

  if (profile == "embedding") {
    result <- result + ggplot2::theme(
      axis.title = ggplot2::element_blank(),
      axis.text = ggplot2::element_blank(),
      axis.line = ggplot2::element_blank(),
      axis.ticks = ggplot2::element_blank()
    )
  } else if (profile == "matrix") {
    result <- result + ggplot2::theme(
      axis.title = ggplot2::element_blank(),
      axis.line = ggplot2::element_blank(),
      axis.ticks = ggplot2::element_blank(),
      panel.border = ggplot2::element_blank()
    )
  }
  result
}

.cns_resolve_theme_element <- function(theme, name) {
  element <- ggplot2::calc_element(name, theme)
  if (is.null(element)) {
    stop(
      sprintf("Could not resolve ggplot2 theme element '%s'.", name),
      call. = FALSE
    )
  }
  element
}
