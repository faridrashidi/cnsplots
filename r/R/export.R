.cns_file_extension <- function(filename) {
  base <- basename(filename)
  if (!grepl("\\.", base)) return("")
  tolower(sub("^.*\\.", "", base))
}

.cns_default_device <- function(extension) {
  switch(
    extension,
    pdf = if (capabilities("cairo")) grDevices::cairo_pdf else grDevices::pdf,
    svg = grDevices::svg,
    png = "png",
    tiff = "tiff",
    tif = "tiff",
    jpg = "jpeg",
    jpeg = "jpeg",
    eps = if (capabilities("cairo")) grDevices::cairo_ps else grDevices::postscript,
    stop(
      sprintf(
        "Unsupported extension .%s. Use pdf, svg, png, tiff, jpg, or eps.",
        extension
      ),
      call. = FALSE
    )
  )
}

.cns_validate_device_extension <- function(device, extension) {
  if (!is.character(device) || length(device) != 1L) return(invisible(TRUE))
  normalized <- tolower(device)
  normalized <- switch(normalized, tif = "tiff", jpg = "jpeg", normalized)
  expected <- switch(extension, tif = "tiff", jpg = "jpeg", extension)
  if (!identical(normalized, expected)) {
    stop(
      sprintf("device '%s' does not match filename extension '.%s'.", device, extension),
      call. = FALSE
    )
  }
  invisible(TRUE)
}

#' Save a plot
#'
#' Parent directories are created automatically and the graphics device follows
#' the filename extension. Dimensions may be supplied directly, or bundled in
#' a reusable object from `figure()`.
#'
#' @param filename Output filename.
#' @param plot A ggplot2 plot. Defaults to the last plot.
#' @param width,height Optional direct figure dimensions.
#' @param units One of "pt", "mm", "cm", "in", or the legacy alias "px72".
#' @param spec Optional object returned by `figure()`.
#' @param device Optional ggplot2 device name or device function.
#' @param dpi Optional raster DPI override.
#' @param background Optional background override.
#' @param ... Additional arguments passed to `ggplot2::ggsave()`.
#' @return Invisibly, the normalized output path.
#' @export
savefig <- function(
  filename, plot = ggplot2::last_plot(),
  width = NULL, height = NULL,
  units = c("pt", "mm", "cm", "in", "px72"),
  spec = NULL, device = NULL, dpi = NULL, background = NULL, ...
) {
  filename <- path.expand(.cns_assert_scalar_character(filename, "filename"))
  if (is.null(plot)) {
    stop("plot must be supplied when there is no last ggplot2 plot.", call. = FALSE)
  }

  if (is.null(spec)) {
    spec <- figure(
      width = width, height = height, units = match.arg(units),
      dpi = dpi, background = background
    )
  } else {
    if (!inherits(spec, "figure_spec")) {
      stop("spec must be created by figure().", call. = FALSE)
    }
    if (!is.null(width) || !is.null(height)) {
      stop("Supply either spec or direct width/height, not both.", call. = FALSE)
    }
  }

  extension <- .cns_file_extension(filename)
  if (!nzchar(extension)) {
    stop("filename must include a supported extension.", call. = FALSE)
  }
  if (is.null(device)) {
    device <- .cns_default_device(extension)
  } else {
    .cns_validate_device_extension(device, extension)
  }
  if (is.null(dpi)) dpi <- spec$dpi
  if (is.null(background)) background <- spec$background
  dpi <- .cns_assert_scalar_number(dpi, "dpi", positive = TRUE)
  background <- .cns_assert_colour(background, "background")

  parent <- dirname(filename)
  if (!dir.exists(parent)) dir.create(parent, recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(
    filename = filename, plot = plot, device = device,
    width = spec$width_in, height = spec$height_in, units = "in",
    dpi = dpi, bg = background, limitsize = FALSE, ...
  )
  invisible(normalizePath(filename, winslash = "/", mustWork = FALSE))
}
