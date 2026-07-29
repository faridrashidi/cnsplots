.slope_x_levels <- function(values) {
  levels <- tryCatch(
    sort(unique(values), na.last = NA),
    error = function(...) {
      stop(
        "[slopeplot] x must contain sortable categorical values.",
        call. = FALSE
      )
    }
  )
  as.character(levels)
}

.slope_prepare <- function(data, x, y, hue, pair, hue_order) {
  columns <- unique(c(x, y, hue, pair))
  .plot_check_data(data, columns, "slopeplot", numeric = y)

  missing <- columns[vapply(data[columns], anyNA, logical(1L))]
  if (length(missing)) {
    stop(
      sprintf(
        "[slopeplot] Columns must not contain missing values: %s.",
        paste(missing, collapse = ", ")
      ),
      call. = FALSE
    )
  }

  observed_hues <- unique(as.character(data[[hue]]))
  if (length(observed_hues) != 2L) {
    stop(
      sprintf(
        paste0(
          "[slopeplot] Column '%s' must have exactly 2 unique values, ",
          "found %d: %s."
        ),
        hue,
        length(observed_hues),
        paste(observed_hues, collapse = ", ")
      ),
      call. = FALSE
    )
  }

  if (is.null(hue_order)) {
    hues <- observed_hues
  } else {
    valid_order <- is.atomic(hue_order) && length(hue_order) == 2L &&
      !anyNA(hue_order) && !anyDuplicated(hue_order) &&
      setequal(as.character(hue_order), observed_hues)
    if (!valid_order) {
      stop(
        paste0(
          "[slopeplot] hue_order must contain both observed hue levels ",
          "exactly once."
        ),
        call. = FALSE
      )
    }
    hues <- as.character(hue_order)
  }

  pair_count <- nrow(unique(data[pair]))
  pair_x_keys <- unique(c(pair, x))
  if (nrow(unique(data[pair_x_keys])) != pair_count) {
    stop(
      sprintf(
        "[slopeplot] Each '%s' pair must belong to exactly one '%s' group.",
        pair, x
      ),
      call. = FALSE
    )
  }

  observation_keys <- unique(c(pair, hue))
  observations <- data[observation_keys]
  has_duplicates <- any(duplicated(observations))
  observed_count <- nrow(unique(observations))
  if (has_duplicates || observed_count != 2L * pair_count) {
    stop(
      sprintf(
        paste0(
          "[slopeplot] Each '%s' pair must have exactly one '%s' value ",
          "for each '%s' level."
        ),
        pair, y, hue
      ),
      call. = FALSE
    )
  }

  x_levels <- .slope_x_levels(data[[x]])
  x_values <- as.character(data[[x]])
  hue_values <- as.character(data[[hue]])
  line_parts <- vector("list", length(x_levels))
  point_parts <- vector("list", length(x_levels))

  for (i in seq_along(x_levels)) {
    in_group <- x_values == x_levels[[i]]
    first_rows <- in_group & hue_values == hues[[1L]]
    second_rows <- in_group & hue_values == hues[[2L]]
    first_pairs <- data[[pair]][first_rows]
    second_pairs <- data[[pair]][second_rows]
    second_index <- match(first_pairs, second_pairs)
    first_values <- as.numeric(data[[y]][first_rows])
    second_values <- as.numeric(data[[y]][second_rows][second_index])
    pair_values <- as.character(first_pairs)
    count <- length(first_values)

    line_parts[[i]] <- data.frame(
      .x = rep(as.numeric(i), count),
      .y = first_values,
      .fit = second_values,
      .group = pair_values,
      stringsAsFactors = FALSE,
      check.names = FALSE
    )
    point_parts[[i]] <- data.frame(
      .x = c(rep(i - 0.2, count), rep(i + 0.2, count)),
      .y = c(first_values, second_values),
      .hue = factor(rep(hues, each = count), levels = hues),
      .group = rep(pair_values, 2L),
      stringsAsFactors = FALSE,
      check.names = FALSE
    )
  }

  list(
    lines = do.call(rbind, line_parts),
    points = do.call(rbind, point_parts),
    x_levels = x_levels,
    hues = hues
  )
}

#' Draw paired changes between two conditions
#'
#' `slopeplot()` joins each pair across exactly two conditions within its
#' categorical x group. The first condition is drawn to the left in blue and
#' the second to the right in red. Lines that decrease from left to right are
#' blue; all other lines are red, matching the Python cnsplots 0.5.0 recipe.
#'
#' @param data A data frame containing paired observations.
#' @param x Categorical column defining groups along the x-axis.
#' @param y Numeric column containing the paired values.
#' @param hue Column defining exactly two conditions.
#' @param pair Subject or observation identifier. Every pair must belong to one
#'   x group and have exactly one value for each hue level.
#' @param hue_order Optional order of the two observed hue levels from left to
#'   right. By default, first-observed order is used.
#' @return A ggplot object.
#' @export
slopeplot <- function(data, x, y, hue, pair, hue_order = NULL) {
  x <- .cns_assert_scalar_character(x, "x")
  y <- .cns_assert_scalar_character(y, "y")
  hue <- .cns_assert_scalar_character(hue, "hue")
  pair <- .cns_assert_scalar_character(pair, "pair")
  prepared <- .slope_prepare(data, x, y, hue, pair, hue_order)

  set1 <- palettes("Set1", n = 2L)
  red <- unname(set1[[1L]])
  blue <- unname(set1[[2L]])
  hue_colours <- stats::setNames(c(blue, red), prepared$hues)
  decreasing <- prepared$lines$.y > prepared$lines$.fit
  line_width <- .cns_pt_to_mm(1.5)
  point_size <- .plot_point_size(10)
  point_stroke <- .cns_pt_to_mm(0.5)

  plot <- ggplot2::ggplot(
    prepared$points,
    ggplot2::aes(x = .x, y = .y)
  ) +
    ggplot2::geom_segment(
      data = prepared$lines[decreasing, , drop = FALSE],
      mapping = ggplot2::aes(
        x = .x - 0.2, xend = .x + 0.2, y = .y, yend = .fit
      ),
      inherit.aes = FALSE,
      colour = blue,
      alpha = 0.4,
      linewidth = line_width,
      lineend = "square",
      show.legend = FALSE
    ) +
    ggplot2::geom_segment(
      data = prepared$lines[!decreasing, , drop = FALSE],
      mapping = ggplot2::aes(
        x = .x - 0.2, xend = .x + 0.2, y = .y, yend = .fit
      ),
      inherit.aes = FALSE,
      colour = red,
      alpha = 0.4,
      linewidth = line_width,
      lineend = "square",
      show.legend = FALSE
    ) +
    ggplot2::geom_point(
      ggplot2::aes(colour = .hue),
      shape = 19,
      size = point_size,
      stroke = point_stroke
    ) +
    ggplot2::scale_colour_manual(
      values = hue_colours,
      limits = prepared$hues,
      drop = FALSE,
      name = NULL
    ) +
    ggplot2::scale_x_continuous(
      breaks = seq_along(prepared$x_levels),
      labels = prepared$x_levels
    ) +
    ggplot2::guides(
      colour = ggplot2::guide_legend(
        nrow = 1,
        byrow = TRUE,
        override.aes = list(
          size = .plot_point_size(12),
          stroke = point_stroke,
          alpha = 1
        )
      )
    )

  .plot_finish(plot, x = NULL, y = y) +
    theme_legend(position = "top", direction = "horizontal", title = FALSE) +
    ggplot2::theme(
      legend.justification = "center",
      legend.box.just = "center"
    )
}
