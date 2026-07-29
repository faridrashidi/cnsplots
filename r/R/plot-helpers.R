.plot_check_data <- function(data, columns, caller, numeric = character()) {
  if (!is.data.frame(data)) {
    stop(sprintf("[%s] data must be a data frame.", caller), call. = FALSE)
  }
  if (!nrow(data)) {
    stop(sprintf("[%s] data must not be empty.", caller), call. = FALSE)
  }
  columns <- as.character(columns)
  missing <- setdiff(columns, names(data))
  if (length(missing)) {
    stop(
      sprintf("[%s] missing column(s): %s.", caller, paste(missing, collapse = ", ")),
      call. = FALSE
    )
  }
  wrong <- numeric[!vapply(data[numeric], is.numeric, logical(1))]
  if (length(wrong)) {
    stop(
      sprintf("[%s] column(s) must be numeric: %s.", caller, paste(wrong, collapse = ", ")),
      call. = FALSE
    )
  }
  invisible(data)
}

.plot_levels <- function(values, order = NULL, argument = "order") {
  observed <- if (is.factor(values)) {
    levels(values)[levels(values) %in% as.character(values[!is.na(values)])]
  } else {
    unique(as.character(values[!is.na(values)]))
  }
  if (is.null(order)) return(observed)
  if (!is.atomic(order) || anyNA(order) || anyDuplicated(order)) {
    stop(sprintf("%s must contain unique, non-missing values.", argument), call. = FALSE)
  }
  as.character(order)
}

.plot_colours <- function(palette = NULL, n) {
  if (is.null(palette)) palette <- settings("palette_qual")
  if (is.character(palette) && length(palette) == 1L &&
      !palette %in% palette_names()) {
    valid_colour <- tryCatch({ grDevices::col2rgb(palette); TRUE }, error = function(...) FALSE)
    if (valid_colour) palette <- rep(palette, max(1L, n))
  }
  palettes(palette, n = n)
}

.plot_point_size <- function(area_pt2) {
  area_pt2 <- .cns_assert_scalar_number(area_pt2, "s", positive = TRUE)
  .cns_pt_to_mm(2 * sqrt(area_pt2 / pi))
}

.plot_contrast_colour <- function(colour) {
  if (!settings("annotation_auto_contrast")) return(rep("white", length(colour)))
  rgb <- grDevices::col2rgb(colour) / 255
  luminance <- 0.2126 * rgb[1L, ] + 0.7152 * rgb[2L, ] + 0.0722 * rgb[3L, ]
  ifelse(luminance < 0.5, "white", "black")
}

.plot_legend_position <- function(position) {
  positions <- c(left = "left", right = "right", top = "top", bottom = "bottom", none = "none")
  position <- .cns_assert_scalar_character(position, "legend")
  if (!position %in% names(positions)) {
    stop("legend must be one of: left, right, top, bottom, none.", call. = FALSE)
  }
  unname(positions[[position]])
}

.plot_finish <- function(plot, x = NULL, y = NULL, legend = NULL) {
  plot <- plot + ggplot2::labs(x = x, y = y) + setup_ggplot()
  if (!is.null(legend)) plot <- plot + theme_legend(position = legend)
  plot
}

.plot_legend_fontsize <- function() {
  value <- settings("legend_fontsize")
  if (is.na(value)) settings("title_fontsize") else value
}
