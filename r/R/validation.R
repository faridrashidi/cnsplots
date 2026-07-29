.cns_assert_scalar_number <- function(value, name, positive = FALSE, non_negative = FALSE) {
  if (!is.numeric(value) || is.logical(value) || length(value) != 1L ||
      is.na(value) || !is.finite(value)) {
    stop(sprintf("%s must be one finite number.", name), call. = FALSE)
  }
  if (positive && value <= 0) {
    stop(sprintf("%s must be greater than zero.", name), call. = FALSE)
  }
  if (non_negative && value < 0) {
    stop(sprintf("%s must be non-negative.", name), call. = FALSE)
  }
  value
}

.cns_assert_whole_number <- function(value, name, positive = FALSE, non_negative = FALSE) {
  value <- .cns_assert_scalar_number(
    value, name, positive = positive, non_negative = non_negative
  )
  if (value != floor(value)) {
    stop(sprintf("%s must be one whole number.", name), call. = FALSE)
  }
  as.integer(value)
}

.cns_assert_scalar_logical <- function(value, name) {
  if (!is.logical(value) || length(value) != 1L || is.na(value)) {
    stop(sprintf("%s must be TRUE or FALSE.", name), call. = FALSE)
  }
  value
}

.cns_assert_scalar_character <- function(value, name, allow_empty = FALSE) {
  if (!is.character(value) || length(value) != 1L || is.na(value)) {
    stop(sprintf("%s must be one character value.", name), call. = FALSE)
  }
  if (!allow_empty && !nzchar(value)) {
    stop(sprintf("%s must not be empty.", name), call. = FALSE)
  }
  value
}

.cns_assert_colour <- function(value, name) {
  value <- .cns_assert_scalar_character(value, name)
  tryCatch(
    grDevices::col2rgb(value),
    error = function(...) {
      stop(sprintf("%s must be a valid R colour.", name), call. = FALSE)
    }
  )
  value
}

.cns_match_choice <- function(value, choices, name) {
  value <- .cns_assert_scalar_character(value, name)
  if (!value %in% choices) {
    stop(
      sprintf("%s must be one of: %s.", name, paste(choices, collapse = ", ")),
      call. = FALSE
    )
  }
  value
}

.cns_validate_setting <- function(name, value) {
  positive_numeric <- c(
    "title_fontsize", "axes_linewidth", "savefig_pad_inches", "savefig_dpi",
    "ggplot_fontsize", "figure_width", "figure_height", "figure_dpi",
    "multipanel_max_width", "panel_width", "panel_height"
  )
  non_negative_numeric <- c(
    "legend_markerscale", "legend_handlelength", "legend_handleheight",
    "legend_handletextpad", "xtick_major_size", "xtick_major_width",
    "ytick_major_size", "ytick_major_width", "multipanel_title_height_min",
    "multipanel_title_height_pad", "panel_pad_left", "panel_pad_top",
    "panel_margin_top", "panel_margin_bottom", "panel_margin_left",
    "panel_margin_right", "legend_out_markerscale"
  )
  numeric_values <- c(
    "axes_labelpad", "axes_titlepad", "axes_xmargin", "axes_ymargin",
    "xtick_major_pad", "xtick_labelrotation", "ytick_major_pad",
    "ytick_labelrotation"
  )
  logical_values <- c(
    "savefig_transparent", "axes_grid", "axes_spines_top",
    "axes_spines_right", "annotation_auto_contrast", "legend_frameon",
    "xtick_bottom", "ytick_left", "scanpy_use_default_style"
  )
  colour_values <- c(
    "axes_edgecolor", "axes_labelcolor", "xtick_color", "ytick_color",
    "ggplot_text_color"
  )
  character_values <- c(
    "palette_qual", "palette_seq", "mathtext_fontset", "font_family",
    "savefig_bbox", "svg_fonttype", "xtick_alignment", "ytick_alignment",
    "setup_ax_colorbar_label", "ggplot_font_family", "ggplot_font_face",
    "panel_label_fontname", "scanpy_facecolor"
  )

  if (name %in% positive_numeric) {
    return(.cns_assert_scalar_number(value, name, positive = TRUE))
  }
  if (name %in% non_negative_numeric) {
    return(.cns_assert_scalar_number(value, name, non_negative = TRUE))
  }
  if (name %in% numeric_values) {
    return(.cns_assert_scalar_number(value, name))
  }
  if (name == "verbosity") {
    return(.cns_assert_whole_number(value, name, non_negative = TRUE))
  }
  if (name == "pdf_fonttype") {
    return(.cns_assert_whole_number(value, name, positive = TRUE))
  }
  if (name %in% logical_values) {
    return(.cns_assert_scalar_logical(value, name))
  }
  if (name %in% colour_values) {
    return(.cns_assert_colour(value, name))
  }
  if (name %in% character_values) {
    return(.cns_assert_scalar_character(
      value, name, allow_empty = name == "setup_ax_colorbar_label"
    ))
  }
  if (name == "axes_titlelocation") {
    return(.cns_match_choice(value, c("left", "center", "right"), name))
  }
  if (name == "multipanel_title_loc") {
    return(.cns_match_choice(value, c("left", "center", "right"), name))
  }
  if (name == "pvalue_format") {
    return(.cns_match_choice(value, c("star", "threshold", "full"), name))
  }
  if (name == "pvalue_loc") {
    return(.cns_match_choice(value, c("inside", "outside"), name))
  }
  if (name == "legend_out_loc") {
    return(.cns_match_choice(value, c(
      "best", "upper right", "upper left", "lower left", "lower right",
      "right", "center left", "center right", "lower center",
      "upper center", "center"
    ), name))
  }
  if (name %in% c("legend_fontsize", "legend_title_fontsize")) {
    if (length(value) == 1L && is.numeric(value) && is.na(value)) {
      return(NA_real_)
    }
    return(.cns_assert_scalar_number(value, name, positive = TRUE))
  }
  if (name == "pvalue_fontsize") {
    if (is.character(value)) return(.cns_assert_scalar_character(value, name))
    return(.cns_assert_scalar_number(value, name, positive = TRUE))
  }
  if (name %in% c("title_fontweight", "panel_label_fontweight")) {
    if (is.character(value)) return(.cns_assert_scalar_character(value, name))
    return(.cns_assert_whole_number(value, name))
  }
  if (name == "font_sans_serif") {
    if (!is.character(value) || !length(value) || anyNA(value) || any(!nzchar(value))) {
      stop("font_sans_serif must be a non-empty character vector.", call. = FALSE)
    }
    return(value)
  }
  if (name == "scanpy_figsize") {
    if (!is.numeric(value) || length(value) != 2L || anyNA(value) ||
        any(!is.finite(value)) || any(value <= 0)) {
      stop("scanpy_figsize must contain two positive finite numbers.", call. = FALSE)
    }
    return(as.numeric(value))
  }
  if (name == "legend_out_bbox_to_anchor") {
    if (!is.numeric(value) || length(value) != 2L || anyNA(value) ||
        any(!is.finite(value))) {
      stop("legend_out_bbox_to_anchor must contain two finite numbers.", call. = FALSE)
    }
    return(as.numeric(value))
  }
  value
}
