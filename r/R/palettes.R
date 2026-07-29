#' List available palettes
#'
#' @param kind One of "all", "qualitative", or "continuous".
#' @param details Return the palette metadata instead of only names.
#' @return A character vector or metadata data frame.
#' @export
palette_names <- function(
  kind = c("all", "qualitative", "continuous"), details = FALSE
) {
  kind <- match.arg(kind)
  .cns_assert_scalar_logical(details, "details")
  selected <- if (kind == "all") {
    rep(TRUE, nrow(.cns_palette_metadata))
  } else {
    .cns_palette_metadata$kind == kind
  }
  result <- .cns_palette_metadata[selected, , drop = FALSE]
  rownames(result) <- NULL
  if (details) result else result$name
}

.cns_palette_n <- function(n, default) {
  if (is.null(n)) return(as.integer(default))
  if (!is.numeric(n) || length(n) != 1L || is.na(n) ||
      !is.finite(n) || n < 0 || n != floor(n)) {
    stop("n must be one non-negative whole number.", call. = FALSE)
  }
  as.integer(n)
}

.cns_normalize_colours <- function(colours) {
  if (!is.character(colours) || !length(colours) || anyNA(colours)) {
    stop("A custom palette must be a non-empty character vector of R colours.", call. = FALSE)
  }
  rgb <- tryCatch(
    grDevices::col2rgb(colours),
    error = function(...) {
      stop("A custom palette contains an invalid R colour.", call. = FALSE)
    }
  )
  tolower(grDevices::rgb(rgb[1L, ], rgb[2L, ], rgb[3L, ], maxColorValue = 255))
}

.cns_continuous_colours <- function(name, n) {
  lut <- .cns_continuous_lut[[name]]
  if (n == 0L) return(character())
  if (n == length(lut)) return(lut)
  if (n == 1L) return(lut[[1L]])
  ramp <- grDevices::colorRamp(lut, space = "rgb", interpolate = "linear")
  values <- ramp(seq(0, 1, length.out = n))
  tolower(grDevices::rgb(
    values[, 1L], values[, 2L], values[, 3L], maxColorValue = 255
  ))
}

#' Get colours from a palette
#'
#' Qualitative palettes cycle when `n` exceeds their native length, matching
#' Matplotlib's property-cycle behavior. Continuous palettes use fixed
#' 256-colour lookup tables generated from Matplotlib 3.10.8.
#'
#' @param color A palette name, or a character vector of custom R colours.
#' @param n Number of colours to return.
#' @param direction `1` for the author order or `-1` for reverse order.
#' @return A character vector of hexadecimal colours.
#' @export
palettes <- function(color = NULL, n = NULL, direction = 1) {
  if (is.null(color)) color <- settings("palette_qual")
  if (!is.numeric(direction) || length(direction) != 1L || is.na(direction) ||
      !direction %in% c(-1, 1)) {
    stop("direction must be 1 or -1.", call. = FALSE)
  }

  if (is.character(color) && length(color) > 1L) {
    colours <- .cns_normalize_colours(color)
    n <- .cns_palette_n(n, length(colours))
    if (direction == -1) colours <- rev(colours)
    return(rep(colours, length.out = n))
  }
  if (is.character(color) && length(color) == 1L &&
      !color %in% palette_names()) {
    colours <- tryCatch(
      .cns_normalize_colours(color),
      error = function(...) NULL
    )
    if (!is.null(colours)) {
      n <- .cns_palette_n(n, 1L)
      return(rep(colours, length.out = n))
    }
  }

  color <- .cns_assert_scalar_character(color, "color")
  if (color %in% names(.cns_qualitative_palettes)) {
    colours <- .cns_qualitative_palettes[[color]]
    n <- .cns_palette_n(n, length(colours))
    if (direction == -1) colours <- rev(colours)
    return(rep(colours, length.out = n))
  }
  if (color %in% names(.cns_continuous_lut)) {
    n <- .cns_palette_n(n, 256L)
    colours <- .cns_continuous_colours(color, n)
    if (direction == -1) colours <- rev(colours)
    return(colours)
  }

  stop(
    sprintf(
      "Unknown palette '%s'. Use one of: %s.",
      color, paste(palette_names(), collapse = ", ")
    ),
    call. = FALSE
  )
}

#' Extract selected colours from a palette
#'
#' Indices are one-based, following ordinary R indexing.
#'
#' @param index One or more positive integer indices.
#' @param palette A registered qualitative palette or custom colour vector.
#' @return A character vector of normalized hexadecimal colours.
#' @export
get_hexcolors_from_apalette <- function(index, palette = "Set1") {
  if (!is.numeric(index) || anyNA(index) || any(!is.finite(index)) ||
      any(index < 1) || any(index != floor(index))) {
    stop("index must contain positive one-based whole numbers.", call. = FALSE)
  }
  colours <- palettes(palette)
  if (any(index > length(colours))) {
    stop("index exceeds the palette length.", call. = FALSE)
  }
  unname(colours[as.integer(index)])
}

.cns_discrete_scale <- function(aesthetics, palette, ..., na.value = "grey50") {
  if (is.null(palette)) palette <- settings("palette_qual")
  colours <- palettes(palette)
  ggplot2::discrete_scale(
    aesthetics = aesthetics,
    palette = function(n) rep(colours, length.out = n),
    na.value = na.value,
    ...
  )
}

.cns_gradient_palette <- function(colours) {
  ramp <- grDevices::colorRamp(colours, space = "rgb", interpolate = "linear")
  function(x) {
    if (!length(x)) return(character())
    result <- rep(NA_character_, length(x))
    valid <- !is.na(x)
    if (any(valid)) {
      values <- ramp(pmin(pmax(x[valid], 0), 1))
      result[valid] <- tolower(grDevices::rgb(
        values[, 1L], values[, 2L], values[, 3L], maxColorValue = 255
      ))
    }
    result
  }
}

.cns_continuous_scale <- function(aesthetics, palette, ..., na.value = "grey50") {
  if (is.null(palette)) palette <- settings("palette_seq")
  palette <- .cns_assert_scalar_character(palette, "palette")
  if (!palette %in% names(.cns_continuous_lut)) {
    stop(sprintf("'%s' is not a continuous palette.", palette), call. = FALSE)
  }
  ggplot2::continuous_scale(
    aesthetics = aesthetics,
    palette = .cns_gradient_palette(.cns_continuous_lut[[palette]]),
    na.value = na.value,
    guide = "colourbar",
    ...
  )
}

#' Use a qualitative palette for colour
#'
#' @param palette A qualitative palette name or custom colour vector.
#' @param ... Arguments passed to the ggplot2 scale constructor.
#' @param na.value Colour used for missing values.
#' @return A ggplot2 scale.
#' @export
scale_colour_palette <- function(palette = NULL, ..., na.value = "grey50") {
  .cns_discrete_scale("colour", palette, ..., na.value = na.value)
}

#' @rdname scale_colour_palette
#' @export
scale_color_palette <- scale_colour_palette

#' @rdname scale_colour_palette
#' @export
scale_fill_palette <- function(palette = NULL, ..., na.value = "grey50") {
  .cns_discrete_scale("fill", palette, ..., na.value = na.value)
}

#' Use a continuous colour map
#'
#' @param palette A continuous palette name.
#' @param ... Arguments passed to the ggplot2 scale constructor.
#' @param na.value Colour used for missing values.
#' @return A ggplot2 scale.
#' @export
scale_colour_map <- function(palette = NULL, ..., na.value = "grey50") {
  .cns_continuous_scale("colour", palette, ..., na.value = na.value)
}

#' @rdname scale_colour_map
#' @export
scale_color_map <- scale_colour_map

#' @rdname scale_colour_map
#' @export
scale_fill_map <- function(palette = NULL, ..., na.value = "grey50") {
  .cns_continuous_scale("fill", palette, ..., na.value = na.value)
}

#' Author colour constants
#'
#' Length-one hexadecimal colour tokens matching the author's Python API.
#' They can be used anywhere an R colour is accepted.
#'
#' @format A length-one character vector containing a hexadecimal R colour.
#' @name colour_constants
NULL

#' @rdname colour_constants
#' @export
RED <- unname(.cns_colour_constants[["RED"]])

#' @rdname colour_constants
#' @export
BLUE <- unname(.cns_colour_constants[["BLUE"]])

#' @rdname colour_constants
#' @export
GREEN <- unname(.cns_colour_constants[["GREEN"]])

#' @rdname colour_constants
#' @export
PURPLE <- unname(.cns_colour_constants[["PURPLE"]])

#' @rdname colour_constants
#' @export
ORANGE <- unname(.cns_colour_constants[["ORANGE"]])

#' @rdname colour_constants
#' @export
YELLOW <- unname(.cns_colour_constants[["YELLOW"]])

#' @rdname colour_constants
#' @export
BROWN <- unname(.cns_colour_constants[["BROWN"]])

#' @rdname colour_constants
#' @export
PINK <- unname(.cns_colour_constants[["PINK"]])

#' @rdname colour_constants
#' @export
GRAY <- unname(.cns_colour_constants[["GRAY"]])

#' @rdname colour_constants
#' @export
VIOLET <- unname(.cns_colour_constants[["VIOLET"]])

#' @rdname colour_constants
#' @export
CHOCOLATE <- unname(.cns_colour_constants[["CHOCOLATE"]])
