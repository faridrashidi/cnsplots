.cns_default_settings <- function() {
  list(
    palette_qual = "Ecotyper1",
    palette_seq = "gnuplot",
    title_fontsize = 8,
    title_fontweight = "bold",
    axes_linewidth = 0.5,
    verbosity = 1L,
    mathtext_fontset = "custom",
    font_family = "sans-serif",
    font_sans_serif = c("Helvetica", "Helvetica Neue", "Arial", "DejaVu Sans"),
    savefig_bbox = "tight",
    savefig_pad_inches = 0.01,
    savefig_dpi = 288,
    savefig_transparent = TRUE,
    svg_fonttype = "none",
    pdf_fonttype = 42L,
    axes_titlelocation = "center",
    axes_grid = FALSE,
    axes_spines_top = FALSE,
    axes_spines_right = FALSE,
    axes_edgecolor = "black",
    axes_labelcolor = "black",
    axes_labelpad = 2,
    axes_titlepad = 4,
    axes_xmargin = 0.05,
    axes_ymargin = 0.05,
    legend_fontsize = 7,
    legend_title_fontsize = NA_real_,
    pvalue_format = "star",
    pvalue_fontsize = "small",
    pvalue_loc = "inside",
    annotation_auto_contrast = TRUE,
    legend_frameon = FALSE,
    legend_markerscale = 0.5,
    legend_handlelength = 0.7,
    legend_handleheight = 0.7,
    legend_handletextpad = 0.3,
    xtick_bottom = TRUE,
    xtick_color = "black",
    xtick_major_size = 2,
    xtick_major_width = 0.6,
    xtick_major_pad = 1,
    xtick_alignment = "center",
    xtick_labelrotation = 0,
    ytick_left = TRUE,
    ytick_color = "black",
    ytick_major_size = 2,
    ytick_major_width = 0.6,
    ytick_major_pad = 1,
    ytick_alignment = "center_baseline",
    ytick_labelrotation = 0,
    setup_ax_colorbar_label = "FDR q-val",
    scanpy_use_default_style = FALSE,
    scanpy_figsize = c(2.5, 2.5),
    scanpy_facecolor = "none",
    ggplot_fontsize = 10,
    ggplot_font_family = "sans",
    ggplot_font_face = "plain",
    ggplot_text_color = "black",
    figure_width = 150,
    figure_height = 150,
    figure_dpi = 144,
    multipanel_max_width = 540,
    multipanel_title_loc = "center",
    multipanel_title_height_min = 12,
    multipanel_title_height_pad = 4,
    panel_width = 150,
    panel_height = 150,
    panel_pad_left = 0,
    panel_pad_top = 0,
    panel_margin_top = 0,
    panel_margin_bottom = 10,
    panel_margin_left = 0,
    panel_margin_right = 10,
    panel_label_fontname = "Helvetica",
    panel_label_fontweight = "bold",
    legend_out_bbox_to_anchor = c(1, 1.02),
    legend_out_loc = "upper left",
    legend_out_markerscale = 1
  )
}

.cns_state <- new.env(parent = emptyenv())
.cns_state$values <- .cns_default_settings()

#' Inspect or update cnsplots settings
#'
#' With no arguments, returns a copy of all 78 defaults inherited from Python
#' cnsplots 0.5.0. Character arguments retrieve named values. Named arguments
#' update later theme, palette, figure, and export calls.
#'
#' @param ... Character keys to retrieve, or named values to update.
#' @param .list Optional named list of updates.
#' @return A settings list, one setting value, or invisibly the previous values.
#' @export
settings <- function(..., .list = NULL) {
  dots <- list(...)
  unnamed <- length(dots) > 0L &&
    (is.null(names(dots)) || all(!nzchar(names(dots))))
  if (is.null(.list) && !length(dots)) {
    return(.cns_state$values)
  }
  if (is.null(.list) && unnamed && all(vapply(dots, is.character, logical(1)))) {
    keys <- unlist(dots, use.names = FALSE)
    unknown <- setdiff(keys, names(.cns_state$values))
    if (length(unknown)) {
      stop(sprintf("Unknown cnsplots setting: %s.", paste(unknown, collapse = ", ")), call. = FALSE)
    }
    result <- .cns_state$values[keys]
    if (length(keys) == 1L) return(result[[1L]])
    return(result)
  }
  if (!is.null(.list) && (!is.list(.list) || is.null(names(.list)) || any(!nzchar(names(.list))))) {
    stop(".list must be a fully named list.", call. = FALSE)
  }
  if (length(dots) && (is.null(names(dots)) || any(!nzchar(names(dots))))) {
    stop("Settings updates in ... must be named.", call. = FALSE)
  }
  updates <- if (is.null(.list)) list() else .list
  if (length(dots)) {
    for (key in names(dots)) updates[[key]] <- dots[[key]]
  }
  unknown <- setdiff(names(updates), names(.cns_state$values))
  if (length(unknown)) {
    stop(sprintf("Unknown cnsplots setting: %s.", paste(unknown, collapse = ", ")), call. = FALSE)
  }
  validated <- updates
  for (key in names(updates)) validated[[key]] <- .cns_validate_setting(key, updates[[key]])
  previous <- .cns_state$values[names(validated)]
  current <- .cns_state$values
  for (key in names(validated)) current[[key]] <- validated[[key]]
  .cns_state$values <- current
  invisible(previous)
}

#' Restore all cnsplots settings
#'
#' @return Invisibly, the settings in effect before the reset.
#' @export
reset_settings <- function() {
  previous <- .cns_state$values
  .cns_state$values <- .cns_default_settings()
  invisible(previous)
}

#' Evaluate code with temporary cnsplots settings
#'
#' @param values A named list of temporary settings.
#' @param code Code evaluated after applying the temporary settings.
#' @return The value produced by code.
#' @export
with_settings <- function(values, code) {
  if (!is.list(values) || is.null(names(values)) || any(!nzchar(names(values)))) {
    stop("settings must be a fully named list.", call. = FALSE)
  }
  previous <- .cns_state$values
  on.exit({ .cns_state$values <- previous }, add = TRUE)
  settings(.list = values)
  force(code)
}
