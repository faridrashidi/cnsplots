.label_x <- .label_y <- .xend <- .yend <- NULL

.specialized_column <- function(data, value, name, caller) {
  if (!is.data.frame(data)) {
    stop(sprintf("[%s] data must be a data frame.", caller), call. = FALSE)
  }
  if (!nrow(data)) {
    stop(sprintf("[%s] data must not be empty.", caller), call. = FALSE)
  }
  value <- .cns_assert_scalar_character(value, name)
  if (!value %in% names(data)) {
    stop(
      sprintf("[%s] missing column: %s.", caller, value),
      call. = FALSE
    )
  }
  value
}

.specialized_cmap_colours <- function(cmap, caller) {
  brewer <- list(
    Blues = c(
      "#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6",
      "#4292c6", "#2171b5", "#08519c", "#08306b"
    ),
    Reds = c(
      "#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a",
      "#ef3b2c", "#cb181d", "#a50f15", "#67000d"
    ),
    Greys = c(
      "#ffffff", "#f0f0f0", "#d9d9d9", "#bdbdbd", "#969696",
      "#737373", "#525252", "#252525", "#000000"
    ),
    Purples = c(
      "#fcfbfd", "#efedf5", "#dadaeb", "#bcbddc", "#9e9ac8",
      "#807dba", "#6a51a3", "#54278f", "#3f007d"
    ),
    Greens = c(
      "#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476",
      "#41ab5d", "#238b45", "#006d2c", "#00441b"
    ),
    Oranges = c(
      "#fff5eb", "#fee6ce", "#fdd0a2", "#fdae6b", "#fd8d3c",
      "#f16913", "#d94801", "#a63603", "#7f2704"
    ),
    viridis = c(
      "#440154", "#482878", "#3e4989", "#31688e", "#26828e",
      "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"
    )
  )

  if (!is.character(cmap) || !length(cmap) || anyNA(cmap)) {
    stop(
      sprintf(
        paste0(
          "[%s] cmap must be a registered continuous palette name, ",
          "a supported Matplotlib-style name, or a colour vector; ",
          "Matplotlib colormap objects are not supported in R."
        ),
        caller
      ),
      call. = FALSE
    )
  }
  if (length(cmap) > 1L) return(.cns_normalize_colours(cmap))

  reverse <- grepl("_r$", cmap)
  name <- if (reverse) sub("_r$", "", cmap) else cmap
  if (name %in% palette_names("continuous")) {
    colours <- palettes(name, n = 256L)
  } else if (name %in% names(brewer)) {
    colours <- grDevices::colorRampPalette(
      brewer[[name]], space = "rgb"
    )(256L)
  } else {
    stop(
      sprintf(
        paste0(
          "[%s] unsupported cmap '%s'. Use a registered continuous palette, ",
          "Blues, Reds, Greys, Purples, Greens, Oranges, viridis, or a ",
          "custom colour vector."
        ),
        caller, cmap
      ),
      call. = FALSE
    )
  }
  colours <- .cns_normalize_colours(colours)
  if (reverse) rev(colours) else colours
}

.specialized_colour_at <- function(values, colours) {
  limits <- range(values)
  scaled <- if (diff(limits) == 0) {
    rep(0, length(values))
  } else {
    (values - limits[[1L]]) / diff(limits)
  }
  .cns_gradient_palette(colours)(scaled)
}

.confusion_order <- function(values, order, name) {
  observed <- unique(as.character(values))
  if (is.null(order)) return(observed)
  if (!is.atomic(order) || !length(order) || anyNA(order)) {
    stop(
      sprintf(
        "[confusionplot] %s must contain each observed label exactly once.",
        name
      ),
      call. = FALSE
    )
  }

  resolved <- as.character(order)
  missing <- setdiff(observed, resolved)
  extra <- setdiff(resolved, observed)
  duplicates <- unique(resolved[duplicated(resolved)])
  if (length(missing) || length(extra) || length(duplicates)) {
    show_values <- function(x) {
      if (!length(x)) "[]" else paste0("[", paste(x, collapse = ", "), "]")
    }
    stop(
      sprintf(
        paste0(
          "[confusionplot] %s must contain each observed label exactly once ",
          "and no other labels. Missing labels: %s; Extra labels: %s; ",
          "Duplicate labels: %s."
        ),
        name,
        show_values(missing),
        show_values(extra),
        show_values(duplicates)
      ),
      call. = FALSE
    )
  }
  resolved
}

.confusion_safe_divide <- function(numerator, denominator) {
  if (denominator == 0) NaN else numerator / denominator
}

.confusion_statistics <- function(counts, x_levels, y_levels, positive_x, positive_y) {
  positive_x <- if (is.null(positive_x)) x_levels[[length(x_levels)]] else as.character(positive_x)
  positive_y <- if (is.null(positive_y)) y_levels[[length(y_levels)]] else as.character(positive_y)
  if (length(positive_x) != 1L || is.na(positive_x) ||
      !positive_x %in% x_levels) {
    stop(
      "[confusionplot] positive_x must be one label present in x_order.",
      call. = FALSE
    )
  }
  if (length(positive_y) != 1L || is.na(positive_y) ||
      !positive_y %in% y_levels) {
    stop(
      "[confusionplot] positive_y must be one label present in y_order.",
      call. = FALSE
    )
  }

  negative_x <- x_levels[x_levels != positive_x][[1L]]
  negative_y <- y_levels[y_levels != positive_y][[1L]]
  tn <- unname(counts[negative_y, negative_x])
  fp <- unname(counts[negative_y, positive_x])
  fn <- unname(counts[positive_y, negative_x])
  tp <- unname(counts[positive_y, positive_x])

  specificity <- .confusion_safe_divide(tn, tn + fp)
  sensitivity <- .confusion_safe_divide(tp, tp + fn)
  ppv <- .confusion_safe_divide(tp, tp + fp)
  npv <- .confusion_safe_divide(tn, tn + fn)
  total <- tp + tn + fp + fn
  observed_agreement <- .confusion_safe_divide(tp + tn, total)
  expected_agreement <- .confusion_safe_divide(
    (tp + fp) * (tp + fn) + (tn + fp) * (tn + fn),
    total^2
  )
  kappa <- if (is.nan(expected_agreement) || expected_agreement == 1) {
    NaN
  } else {
    .confusion_safe_divide(
      observed_agreement - expected_agreement,
      1 - expected_agreement
    )
  }
  fisher_p <- tryCatch(
    stats::fisher.test(
      matrix(c(tp, fp, fn, tn), nrow = 2L, byrow = TRUE)
    )$p.value,
    error = function(error) {
      stop(
        paste0(
          "[confusionplot] Fisher's exact test failed. Ensure the confusion ",
          "matrix has valid counts. Details: ", conditionMessage(error)
        ),
        call. = FALSE
      )
    }
  )
  odds_ratio <- .confusion_safe_divide(tp * tn, fp * fn)
  metric <- function(value) sprintf("%.2f", value)
  p_text <- formatC(fisher_p, format = "g", digits = 2L)

  list(
    specificity = specificity,
    sensitivity = sensitivity,
    ppv = ppv,
    npv = npv,
    kappa = kappa,
    fisher_p = fisher_p,
    odds_ratio = odds_ratio,
    label = paste(
      sprintf("Specificity: %s", metric(specificity)),
      sprintf("Sensitivity: %s", metric(sensitivity)),
      sprintf("PPV: %s", metric(ppv)),
      sprintf("NPV: %s", metric(npv)),
      sprintf("Cohen's kappa: %s", metric(kappa)),
      sprintf("Fisher's exact test: %s", p_text),
      sprintf("Odds ratio: %s", metric(odds_ratio)),
      sep = "\n"
    )
  )
}

#' Plot a confusion matrix
#'
#' This native ggplot2 counterpart preserves the author's observed-label
#' ordering, exact-order validation, count annotations, automatic annotation
#' contrast, and optional binary classification statistics. The colour bar is
#' intentionally hidden, as in the Python function.
#'
#' @param data A non-empty data frame containing predictions and truth labels.
#' @param x Prediction column name.
#' @param y Truth column name.
#' @param add_pvalue Add the binary metrics, Fisher exact test, and odds-ratio
#'   block. This requires a 2 by 2 matrix.
#' @param x_order,y_order Optional complete display orders. Each must contain
#'   every observed label exactly once and cannot filter the input.
#' @param positive_x,positive_y Optional positive labels for predictions and
#'   truth. The last displayed label is positive by default.
#' @param annot Display integer counts in the cells.
#' @param cmap A registered continuous palette, one of the supported
#'   Matplotlib-style sequential names, or a custom colour vector.
#' @param pvalue_x_pad,pvalue_y_pad Horizontal and vertical offsets for the
#'   statistics block; larger values move it farther left or down.
#' @return An ordinary ggplot object.
#' @export
confusionplot <- function(
  data,
  x,
  y,
  add_pvalue = FALSE,
  x_order = NULL,
  y_order = NULL,
  positive_x = NULL,
  positive_y = NULL,
  annot = TRUE,
  cmap = "Blues",
  pvalue_x_pad = 0.25,
  pvalue_y_pad = 1.5
) {
  caller <- "confusionplot"
  x <- .specialized_column(data, x, "x", caller)
  y <- .specialized_column(data, y, "y", caller)
  .plot_check_data(data, c(x, y), caller)
  add_pvalue <- .cns_assert_scalar_logical(add_pvalue, "add_pvalue")
  annot <- .cns_assert_scalar_logical(annot, "annot")
  pvalue_x_pad <- .cns_assert_scalar_number(pvalue_x_pad, "pvalue_x_pad")
  pvalue_y_pad <- .cns_assert_scalar_number(pvalue_y_pad, "pvalue_y_pad")
  if (anyNA(data[c(x, y)])) {
    stop(
      "[confusionplot] x and y must not contain missing values.",
      call. = FALSE
    )
  }

  x_values <- as.character(data[[x]])
  y_values <- as.character(data[[y]])
  x_levels <- .confusion_order(x_values, x_order, "x_order")
  y_levels <- .confusion_order(y_values, y_order, "y_order")
  counts <- table(
    factor(y_values, levels = y_levels),
    factor(x_values, levels = x_levels),
    dnn = c(y, x)
  )
  counted_rows <- sum(counts)
  if (is.na(counted_rows) || counted_rows != nrow(data)) {
    stop(
      sprintf(
        paste0(
          "[confusionplot] confusion matrix count mismatch: expected %d ",
          "input rows, counted %s."
        ),
        nrow(data), as.character(counted_rows)
      ),
      call. = FALSE
    )
  }
  if (add_pvalue && !identical(dim(counts), c(2L, 2L))) {
    stop(
      paste0(
        "add_pvalue=TRUE requires a 2x2 confusion matrix. Provide y_order ",
        "and x_order with exactly two labels each."
      ),
      call. = FALSE
    )
  }

  matrix_data <- expand.grid(
    .x = seq_along(x_levels),
    .row = seq_along(y_levels),
    KEEP.OUT.ATTRS = FALSE
  )
  matrix_data$.y <- length(y_levels) - matrix_data$.row + 1L
  matrix_data$.count <- as.integer(counts[cbind(
    matrix_data$.row,
    matrix_data$.x
  )])
  cmap_colours <- .specialized_cmap_colours(cmap, caller)
  matrix_data$.group <- .specialized_colour_at(
    matrix_data$.count, cmap_colours
  )
  matrix_data$.hue <- .plot_contrast_colour(matrix_data$.group)

  plot <- ggplot2::ggplot(
    matrix_data,
    ggplot2::aes(x = .x, y = .y)
  ) +
    ggplot2::geom_tile(
      ggplot2::aes(fill = .group),
      width = 1,
      height = 1
    ) +
    ggplot2::scale_fill_identity(guide = "none") +
    ggplot2::scale_x_continuous(
      breaks = seq_along(x_levels),
      labels = x_levels,
      expand = c(0, 0)
    ) +
    ggplot2::scale_y_continuous(
      breaks = seq_along(y_levels),
      labels = rev(y_levels),
      expand = c(0, 0)
    )

  if (annot) {
    plot <- plot +
      ggplot2::geom_text(
        ggplot2::aes(label = .count, colour = .hue),
        family = .cns_resolve_family(settings("font_family")),
        size = .cns_pt_to_mm(settings("title_fontsize")),
        show.legend = FALSE
      ) +
      ggplot2::scale_colour_identity(guide = "none")
  }

  stats_result <- NULL
  if (add_pvalue) {
    stats_result <- .confusion_statistics(
      counts, x_levels, y_levels, positive_x, positive_y
    )
    stats_data <- data.frame(
      .x = 0.5 - pvalue_x_pad,
      .y = 0.5 - 0.1 * pvalue_y_pad,
      .label = stats_result$label,
      stringsAsFactors = FALSE
    )
    plot <- plot + ggplot2::geom_text(
      data = stats_data,
      ggplot2::aes(x = .x, y = .y, label = .label),
      inherit.aes = FALSE,
      hjust = 0,
      vjust = 1,
      lineheight = 1.05,
      family = .cns_resolve_family(settings("font_family")),
      size = .cns_pt_to_mm(.plot_legend_fontsize()),
      colour = settings("axes_labelcolor")
    )
  }

  current <- settings()
  bottom_margin <- if (add_pvalue) {
    (7 * 1.1 + max(0, pvalue_y_pad)) * .plot_legend_fontsize()
  } else {
    5.5
  }
  plot <- .plot_finish(plot, x = x, y = y) +
    ggplot2::coord_fixed(
      xlim = c(0.5, length(x_levels) + 0.5),
      ylim = c(0.5, length(y_levels) + 0.5),
      expand = FALSE,
      clip = "off"
    ) +
    ggplot2::theme(
      axis.line = ggplot2::element_blank(),
      panel.border = ggplot2::element_rect(
        fill = NA,
        colour = current$axes_edgecolor,
        linewidth = .cns_pt_to_mm(current$axes_linewidth)
      ),
      plot.margin = ggplot2::margin(
        5.5, 5.5, bottom_margin,
        5.5 + max(0, pvalue_x_pad) * .plot_legend_fontsize(),
        unit = "pt"
      )
    )
  plot
}

.volcano_label_data <- function(data) {
  labels <- data[data$.group %in% c("Up", "Down"), , drop = FALSE]
  if (!nrow(labels)) return(labels)
  labels <- labels[
    order(match(labels$.group, c("Up", "Down")), seq_len(nrow(labels))),
    ,
    drop = FALSE
  ]
  x_range <- diff(range(data$.x))
  y_range <- diff(range(data$.y))
  if (x_range == 0) x_range <- max(1, abs(data$.x[[1L]]))
  if (y_range == 0) y_range <- max(1, abs(data$.y[[1L]]))
  direction <- ifelse(labels$.group == "Up", 1, -1)
  labels$.label_x <- labels$.x + direction * 0.025 * x_range
  labels$.label_y <- labels$.y + 0.02 * y_range
  labels$.vjust <- ifelse(direction > 0, 0, 1)
  labels
}

#' Plot differential-expression results as a volcano plot
#'
#' Significance uses the author's fixed adjusted-p threshold of 0.05 and
#' absolute log2-fold-change threshold of 0.5. When `show_list` is absent, the
#' top `n_show` up- and down-regulated features are ranked independently by
#' `y * abs(x)`. Direct labels and leader lines are implemented with ggplot2;
#' dependency-free placement is deterministic rather than the Python
#' `adjustText` force layout.
#'
#' @param data A non-empty differential-expression data frame.
#' @param x Numeric log2-fold-change column.
#' @param y Numeric negative-log10 adjusted-p column.
#' @param symbol Feature-label column.
#' @param show_list Optional feature labels to highlight. When supplied it
#'   takes precedence over automatic ranking.
#' @param n_show Non-negative number of top features to label in each
#'   direction when `show_list` is `NULL`.
#' @return An ordinary ggplot object.
#' @export
volcanoplot <- function(
  data,
  x = "log2FoldChange",
  y = "-log10(adjp)",
  symbol = "symbol",
  show_list = NULL,
  n_show = 10
) {
  caller <- "volcanoplot"
  x <- .specialized_column(data, x, "x", caller)
  y <- .specialized_column(data, y, "y", caller)
  symbol <- .specialized_column(data, symbol, "symbol", caller)
  .plot_check_data(data, c(x, y, symbol), caller, numeric = c(x, y))
  n_show <- .cns_assert_whole_number(
    n_show, "n_show", non_negative = TRUE
  )
  if (!is.null(show_list)) {
    if (!is.character(show_list) || anyNA(show_list)) {
      stop("show_list must be NULL or a character vector without NA.", call. = FALSE)
    }
  }
  if (any(!is.finite(data[[x]])) || any(!is.finite(data[[y]]))) {
    stop(
      "[volcanoplot] x and y must contain only finite numeric values.",
      call. = FALSE
    )
  }
  if (anyNA(data[[symbol]])) {
    stop("[volcanoplot] symbol must not contain missing values.", call. = FALSE)
  }

  plot_data <- data.frame(
    .x = as.numeric(data[[x]]),
    .y = as.numeric(data[[y]]),
    .label = as.character(data[[symbol]]),
    stringsAsFactors = FALSE
  )
  p_threshold <- -log10(0.05)
  up <- plot_data$.y > p_threshold & plot_data$.x > 0.5
  down <- plot_data$.y > p_threshold & plot_data$.x < -0.5
  group <- rep("NS", nrow(plot_data))
  group[plot_data$.y > p_threshold] <- "p_adj < 0.05"

  if (is.null(show_list)) {
    rank <- plot_data$.y * abs(plot_data$.x)
    take_top <- function(indices) {
      if (!length(indices) || n_show == 0L) return(integer())
      ordered <- indices[order(-rank[indices], indices, method = "radix")]
      ordered[seq_len(min(n_show, length(ordered)))]
    }
    group[take_top(which(up))] <- "Up"
    group[take_top(which(down))] <- "Down"
  } else {
    selected <- plot_data$.label %in% show_list
    group[selected & up] <- "Up"
    group[selected & down] <- "Down"
  }

  group_levels <- c("Down", "NS", "Up", "p_adj < 0.05")
  observed_group_levels <- group_levels[group_levels %in% unique(group)]
  plot_data$.group <- factor(group, levels = group_levels)
  plot_data <- plot_data[
    order(plot_data$.group, seq_len(nrow(plot_data)), method = "radix"),
    ,
    drop = FALSE
  ]
  blue_red <- palettes("BlueRed", n = 2L)
  colours <- c(
    Down = blue_red[[1L]],
    NS = "#808080",
    Up = blue_red[[2L]],
    `p_adj < 0.05` = "#000000"
  )
  point_sizes <- c(
    Down = .plot_point_size(10),
    NS = .plot_point_size(2),
    Up = .plot_point_size(10),
    `p_adj < 0.05` = .plot_point_size(2)
  )
  max_y <- max(plot_data$.y)
  zero_line <- data.frame(
    .x = 0,
    .y = 0,
    .xend = 0,
    .yend = max_y
  )

  plot <- ggplot2::ggplot(
    plot_data,
    ggplot2::aes(x = .x, y = .y)
  ) +
    ggplot2::geom_point(
      ggplot2::aes(colour = .group, size = .group),
      stroke = 0
    ) +
    ggplot2::geom_segment(
      data = zero_line,
      ggplot2::aes(x = .x, y = .y, xend = .xend, yend = .yend),
      inherit.aes = FALSE,
      colour = "black",
      linewidth = .cns_pt_to_mm(0.8),
      linetype = "longdash"
    ) +
    ggplot2::scale_colour_manual(
      values = colours,
      limits = group_levels,
      breaks = observed_group_levels,
      drop = TRUE,
      name = "DEG"
    ) +
    ggplot2::scale_size_manual(
      values = point_sizes,
      limits = group_levels,
      breaks = observed_group_levels,
      drop = TRUE,
      name = "DEG"
    )

  label_data <- .volcano_label_data(plot_data)
  if (nrow(label_data)) {
    plot <- plot +
      ggplot2::geom_segment(
        data = label_data,
        ggplot2::aes(
          x = .x,
          y = .y,
          xend = .label_x,
          yend = .label_y
        ),
        inherit.aes = FALSE,
        colour = "black",
        linewidth = .cns_pt_to_mm(0.5),
        show.legend = FALSE
      ) +
      ggplot2::geom_text(
        data = label_data,
        ggplot2::aes(
          x = .label_x,
          y = .label_y,
          label = .label,
          colour = .group,
          hjust = .vjust
        ),
        inherit.aes = FALSE,
        family = .cns_resolve_family(settings("font_family")),
        size = .cns_pt_to_mm(.plot_legend_fontsize()),
        show.legend = FALSE
      )
  }

  .plot_finish(
    plot,
    x = "log2(fold change)",
    y = "\u2013log10(adjusted p-value)",
    legend = "right"
  ) +
    ggplot2::coord_cartesian(clip = "off") +
    ggplot2::theme(
      panel.border = ggplot2::element_rect(
        fill = NA,
        colour = settings("axes_edgecolor"),
        linewidth = .cns_pt_to_mm(settings("axes_linewidth"))
      )
    ) +
    ggplot2::guides(
      colour = ggplot2::guide_legend(
        override.aes = list(size = .plot_point_size(20), stroke = 0)
      ),
      size = "none"
    )
}

.gsea_hit_ratios <- function(data) {
  ratio_columns <- names(data)[names(data) %in% c("Overlap", "Tag %")]
  if (!length(ratio_columns)) return(rep(1, nrow(data)))
  if (length(ratio_columns) > 1L) {
    stop(
      paste0(
        "[gseaplot] only one of Overlap or Tag % can define dot size; ",
        "the upstream backend is also ambiguous when both are present."
      ),
      call. = FALSE
    )
  }
  raw <- data[[ratio_columns[[1L]]]]
  if (!is.character(raw) || anyNA(raw)) {
    stop(
      sprintf(
        "[gseaplot] %s must contain non-missing 'hits/total' strings.",
        ratio_columns[[1L]]
      ),
      call. = FALSE
    )
  }
  pieces <- strsplit(raw, "/", fixed = TRUE)
  valid <- lengths(pieces) == 2L
  numerator <- denominator <- rep(NA_real_, length(pieces))
  if (any(valid)) {
    numerator[valid] <- suppressWarnings(as.numeric(vapply(
      pieces[valid], `[[`, character(1L), 1L
    )))
    denominator[valid] <- suppressWarnings(as.numeric(vapply(
      pieces[valid], `[[`, character(1L), 2L
    )))
  }
  if (any(!valid) || any(!is.finite(numerator)) ||
      any(!is.finite(denominator)) || any(denominator <= 0) ||
      any(numerator < 0)) {
    stop(
      sprintf(
        "[gseaplot] %s must contain valid non-negative 'hits/total' ratios.",
        ratio_columns[[1L]]
      ),
      call. = FALSE
    )
  }
  numerator / denominator
}

.gsea_size_breaks <- function(ratios, multiplier) {
  unique_ratios <- sort(unique(ratios))
  ratio_breaks <- if (length(unique_ratios) <= 3L) {
    unique_ratios
  } else {
    candidates <- pretty(range(ratios), n = 3L)
    candidates[candidates >= min(ratios) & candidates <= max(ratios)]
  }
  if (!length(ratio_breaks)) ratio_breaks <- range(ratios)
  diameters <- 2 * ratio_breaks * multiplier * 6 / sqrt(pi) * 25.4 / 72
  labels <- ifelse(
    abs(ratio_breaks * 100 - round(ratio_breaks * 100)) < 1e-8,
    sprintf("%.0f", ratio_breaks * 100),
    formatC(ratio_breaks * 100, format = "fg", digits = 3L)
  )
  list(ratio = ratio_breaks, diameter = diameters, label = labels)
}

#' Plot GSEA terms as an enrichment dot plot
#'
#' Rows are first filtered by `significance_column <= cutoff`. Selection of the
#' top terms is then based on the colour variable, matching the author's
#' gseapy-backed implementation, and the displayed rows are ordered by
#' increasing NES. `Overlap` or `Tag %` values written as `"hits/total"`
#' control dot size; otherwise every dot represents 100 percent.
#'
#' @param data A non-empty GSEA result data frame.
#' @param y Gene-set or pathway label column.
#' @param color Numeric column encoded by dot colour.
#' @param cutoff Inclusive cutoff applied only to `significance_column`.
#' @param cmap A registered continuous palette, supported Matplotlib-style
#'   name, or custom colour vector.
#' @param top_term Positive maximum number of terms to show.
#' @param size Positive multiplier for dot diameters.
#' @param significance_column Numeric significance column used for filtering,
#'   independently of `color`.
#' @return An ordinary ggplot object.
#' @export
gseaplot <- function(
  data,
  y,
  color = "NES",
  cutoff = 0.05,
  cmap = "BuRd_custom",
  top_term = 20,
  size = 1.8,
  significance_column = "FDR q-val"
) {
  caller <- "gseaplot"
  y <- .specialized_column(data, y, "y", caller)
  color <- .specialized_column(data, color, "color", caller)
  significance_column <- .specialized_column(
    data, significance_column, "significance_column", caller
  )
  .specialized_column(data, "NES", "NES", caller)
  .plot_check_data(
    data,
    unique(c(y, "NES", color, significance_column)),
    caller,
    numeric = unique(c("NES", color, significance_column))
  )
  cutoff <- .cns_assert_scalar_number(
    cutoff, "cutoff", non_negative = TRUE
  )
  top_term <- .cns_assert_whole_number(
    top_term, "top_term", positive = TRUE
  )
  size <- .cns_assert_scalar_number(size, "size", positive = TRUE)
  cmap_colours <- .specialized_cmap_colours(cmap, caller)

  significant <- !is.na(data[[significance_column]]) &
    data[[significance_column]] <= cutoff
  plot_data <- data[significant, , drop = FALSE]
  if (!nrow(plot_data)) {
    stop(
      sprintf("[gseaplot] no enriched terms pass cutoff = %s.", cutoff),
      call. = FALSE
    )
  }
  if (anyNA(plot_data[[y]])) {
    stop("[gseaplot] y must not contain missing values after filtering.", call. = FALSE)
  }
  if (any(!is.finite(plot_data[["NES"]])) ||
      any(!is.finite(plot_data[[color]]))) {
    stop(
      "[gseaplot] NES and color must be finite after significance filtering.",
      call. = FALSE
    )
  }

  pvalue_colours <- c(
    "Adjusted P-value", "P-value", "NOM p-val", "FDR q-val"
  )
  colour_values <- as.numeric(plot_data[[color]])
  colour_title <- color
  if (color %in% pvalue_colours) {
    if (!any(abs(colour_values) > 0)) {
      stop(
        sprintf(
          "[gseaplot] cannot determine colormap because all %s values are zero.",
          color
        ),
        call. = FALSE
      )
    }
    colour_values <- log10(1 / pmax(colour_values, .Machine$double.xmin))
    colour_title <- if (color %in% c("Adjusted P-value", "FDR q-val")) {
      "log10(1/FDR)"
    } else {
      "log10(1/Pval)"
    }
  }

  selection_order <- order(
    colour_values,
    seq_along(colour_values),
    method = "radix"
  )
  take <- min(top_term, length(selection_order))
  selected <- selection_order[seq.int(length(selection_order) - take + 1L, length(selection_order))]
  plot_data <- plot_data[selected, , drop = FALSE]
  colour_values <- colour_values[selected]
  nes <- as.numeric(plot_data[["NES"]])
  display_order <- order(nes, seq_along(nes), method = "radix")
  plot_data <- plot_data[display_order, , drop = FALSE]
  colour_values <- colour_values[display_order]
  nes <- nes[display_order]
  ratios <- .gsea_hit_ratios(plot_data)
  diameters <- 2 * ratios * size * 6 / sqrt(pi) * 25.4 / 72
  term_values <- as.character(plot_data[[y]])
  term_levels <- unique(term_values)

  gg_data <- data.frame(
    .x = nes,
    .y = factor(term_values, levels = term_levels),
    .group = colour_values,
    .density = ratios,
    .count = diameters,
    stringsAsFactors = FALSE
  )
  size_breaks <- .gsea_size_breaks(ratios, size)
  plot <- ggplot2::ggplot(
    gg_data,
    ggplot2::aes(x = .x, y = .y)
  ) +
    ggplot2::geom_point(
      ggplot2::aes(colour = .group, size = .count),
      stroke = 0
    ) +
    ggplot2::scale_colour_gradientn(
      colours = cmap_colours,
      name = colour_title,
      na.value = "grey50"
    ) +
    ggplot2::scale_size_identity(
      name = "% Genes\nin set",
      breaks = size_breaks$diameter,
      labels = size_breaks$label,
      guide = "legend"
    )

  .plot_finish(
    plot,
    x = "Normalized Enrichment Score (NES)",
    y = NULL,
    legend = "right"
  ) +
    ggplot2::guides(
      colour = ggplot2::guide_colourbar(order = 1),
      size = ggplot2::guide_legend(order = 2, override.aes = list(colour = "grey50"))
    )
}
