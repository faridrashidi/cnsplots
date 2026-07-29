#' cnsplots: scientific plotting tools for R
#'
#' The native R package follows the visual baseline of Python cnsplots 0.5.0
#' while returning ordinary ggplot2 objects. Package loading has no theme,
#' option, font, or graphics-device side effects.
#'
#' @keywords internal
"_PACKAGE"

# Bind internal ggplot2 data-mask names for R CMD check. These objects are not
# part of the public API and remain NULL outside ggplot2 evaluation contexts.
.x <- .y <- .hue <- .group <- .density <- .fit <- .lower <- .upper <- NULL
.label <- .vjust <- .count <- .theoretical <- .sample <- colour <- NULL
.cns_x <- .cns_y <- .cns_hue <- .cns_label <- .cns_vjust <- NULL
.cns_category <- .cns_ymin <- .cns_ymax <- .cns_midpoint <- NULL
.cns_count <- .cns_text_colour <- NULL
