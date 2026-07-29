#' Describe a cnsplots figure
#'
#' The default point unit preserves Python cnsplots' actual width / 72 inch
#' behavior. It is a nominal layout unit, not a final raster pixel.
#'
#' @param width,height Figure dimensions.
#' @param units One of "pt", "mm", "cm", "in", or the legacy alias "px72".
#' @param dpi Raster export resolution.
#' @param palette Default qualitative palette name.
#' @param cmap Default continuous palette name.
#' @param background Export background.
#' @return A figure_spec object.
#' @export
figure <- function(
  width = NULL, height = NULL,
  units = c("pt", "mm", "cm", "in", "px72"),
  dpi = NULL, palette = NULL, cmap = NULL, background = NULL
) {
  settings <- settings()
  units <- match.arg(units)
  if (is.null(width)) width <- settings$figure_width
  if (is.null(height)) height <- settings$figure_height
  if (is.null(dpi)) dpi <- settings$savefig_dpi
  if (is.null(palette)) palette <- settings$palette_qual
  if (is.null(cmap)) cmap <- settings$palette_seq
  if (is.null(background)) {
    background <- if (settings$savefig_transparent) "transparent" else "white"
  }
  width <- .cns_assert_scalar_number(width, "width", positive = TRUE)
  height <- .cns_assert_scalar_number(height, "height", positive = TRUE)
  dpi <- .cns_assert_scalar_number(dpi, "dpi", positive = TRUE)
  palette <- .cns_assert_scalar_character(palette, "palette")
  cmap <- .cns_assert_scalar_character(cmap, "cmap")
  background <- .cns_assert_colour(background, "background")
  width_in <- .cns_to_inches(width, units)
  height_in <- .cns_to_inches(height, units)
  structure(
    list(
      width = width, height = height, units = units,
      width_in = width_in, height_in = height_in,
      width_mm = width_in * 25.4, height_mm = height_in * 25.4,
      dpi = dpi,
      pixel_width = as.integer(round(width_in * dpi)),
      pixel_height = as.integer(round(height_in * dpi)),
      palette = palette, cmap = cmap, background = background,
      python_reference = "cnsplots 0.5.0"
    ),
    class = "figure_spec"
  )
}

#' @export
print.figure_spec <- function(x, ...) {
  cat("<figure_spec>\n")
  cat(sprintf("  physical: %.3f x %.3f mm\n", x$width_mm, x$height_mm))
  cat(sprintf(
    "  raster:   %d x %d px at %g DPI\n",
    x$pixel_width, x$pixel_height, x$dpi
  ))
  cat(sprintf("  palette:  %s; cmap: %s\n", x$palette, x$cmap))
  cat(sprintf("  background: %s\n", x$background))
  invisible(x)
}
