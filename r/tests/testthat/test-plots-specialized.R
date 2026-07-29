confusionplot_r <- getFromNamespace("confusionplot", "cnsplots")
volcanoplot_r <- getFromNamespace("volcanoplot", "cnsplots")
gseaplot_r <- getFromNamespace("gseaplot", "cnsplots")
confusion_statistics_r <- getFromNamespace(".confusion_statistics", "cnsplots")

specialized_confusion_fixture <- function() {
  data.frame(
    pred = c("neg", "neg", "neg", "pos", "pos", "pos", "pos", "neg"),
    truth = c("neg", "neg", "pos", "pos", "pos", "neg", "pos", "neg"),
    stringsAsFactors = FALSE
  )
}

specialized_volcano_fixture <- function() {
  data.frame(
    log2FoldChange = c(-2, -1.2, -0.2, 0.1, 1.4, 2.2),
    `-log10(adjp)` = c(4, 3, 0.5, 0.2, 3.5, 5),
    symbol = paste0("GENE", seq_len(6)),
    check.names = FALSE,
    stringsAsFactors = FALSE
  )
}

specialized_gsea_fixture <- function() {
  data.frame(
    Term = c("PATHWAY_A", "PATHWAY_B", "PATHWAY_C"),
    Clean_Term = c("Pathway A", "Pathway B", "Pathway C"),
    NES = c(2.1, -1.8, 1.6),
    `FDR q-val` = c(0.01, 0.02, 0.03),
    check.names = FALSE,
    stringsAsFactors = FALSE
  )
}

test_that("specialized APIs retain the direct author-facing signatures", {
  expect_identical(
    names(formals(confusionplot_r)),
    c(
      "data", "x", "y", "add_pvalue", "x_order", "y_order",
      "positive_x", "positive_y", "annot", "cmap",
      "pvalue_x_pad", "pvalue_y_pad"
    )
  )
  expect_identical(
    names(formals(volcanoplot_r)),
    c("data", "x", "y", "symbol", "show_list", "n_show")
  )
  expect_identical(
    names(formals(gseaplot_r)),
    c(
      "data", "y", "color", "cutoff", "cmap", "top_term", "size",
      "significance_column"
    )
  )
})

test_that("confusionplot preserves counts, order, and contrast annotations", {
  data <- specialized_confusion_fixture()
  original <- data
  plot <- confusionplot_r(
    data,
    "pred",
    "truth",
    x_order = c("neg", "pos"),
    y_order = c("neg", "pos")
  )
  built <- ggplot2::ggplot_build(plot)

  expect_s3_class(plot, "ggplot")
  expect_identical(data, original)
  expect_identical(plot$data$.count, c(3L, 1L, 1L, 3L))
  expect_identical(plot$data$.x, c(1L, 2L, 1L, 2L))
  expect_identical(plot$data$.y, c(2L, 2L, 1L, 1L))
  expect_identical(plot$scales$get_scales("x")$labels, c("neg", "pos"))
  expect_identical(plot$scales$get_scales("y")$labels, c("pos", "neg"))
  expect_identical(built$data[[2L]]$label, c(3L, 1L, 1L, 3L))
  expect_identical(built$data[[2L]]$colour, c("white", "black", "black", "white"))
  expect_identical(built$data[[1L]]$fill, c("#08306b", "#f7fbff", "#f7fbff", "#08306b"))
  expect_identical(plot$labels$x, "pred")
  expect_identical(plot$labels$y, "truth")
  expect_length(plot$layers, 2L)
})

test_that("confusionplot exact orders cannot filter or duplicate labels", {
  data <- data.frame(
    pred = c("a", "b", "c"),
    truth = c("a", "b", "c"),
    stringsAsFactors = FALSE
  )
  ordered <- confusionplot_r(
    data,
    "pred",
    "truth",
    x_order = c("c", "b", "a"),
    y_order = c("c", "b", "a")
  )

  expect_equal(sum(ordered$data$.count), nrow(data))
  expect_identical(ordered$scales$get_scales("x")$labels, c("c", "b", "a"))
  expect_identical(ordered$scales$get_scales("y")$labels, c("a", "b", "c"))
  expect_identical(ordered$data$.count, c(1L, 0L, 0L, 0L, 1L, 0L, 0L, 0L, 1L))

  expect_error(
    confusionplot_r(data, "pred", "truth", x_order = c("a", "b")),
    "Missing labels: \\[c\\]"
  )
  expect_error(
    confusionplot_r(
      data, "pred", "truth", x_order = c("a", "b", "c", "extra")
    ),
    "Extra labels: \\[extra\\]"
  )
  expect_error(
    confusionplot_r(
      data, "pred", "truth", x_order = c("a", "b", "c", "c")
    ),
    "Duplicate labels: \\[c\\]"
  )
})

test_that("confusionplot reports the author's binary statistics", {
  data <- specialized_confusion_fixture()
  plot <- confusionplot_r(
    data,
    "pred",
    "truth",
    add_pvalue = TRUE,
    x_order = c("neg", "pos"),
    y_order = c("neg", "pos"),
    positive_x = "pos",
    positive_y = "pos"
  )
  label_layer <- plot$layers[[3L]]
  label <- label_layer$data$.label

  expect_match(label, "Specificity: 0.75", fixed = TRUE)
  expect_match(label, "Sensitivity: 0.75", fixed = TRUE)
  expect_match(label, "PPV: 0.75", fixed = TRUE)
  expect_match(label, "NPV: 0.75", fixed = TRUE)
  expect_match(label, "Cohen's kappa: 0.50", fixed = TRUE)
  expect_match(label, "Fisher's exact test: 0.49", fixed = TRUE)
  expect_match(label, "Odds ratio: 9.00", fixed = TRUE)
  expect_equal(label_layer$data$.x, 0.25)
  expect_equal(label_layer$data$.y, 0.35)

  counts <- table(data$truth, data$pred)
  metrics <- confusion_statistics_r(
    counts, c("neg", "pos"), c("neg", "pos"), "pos", "pos"
  )
  expect_equal(metrics$fisher_p, stats::fisher.test(
    matrix(c(3, 1, 1, 3), nrow = 2, byrow = TRUE)
  )$p.value)
  expect_equal(metrics$odds_ratio, 9)
})

test_that("confusionplot pads, annotation switch, and cmaps remain explicit", {
  data <- specialized_confusion_fixture()
  no_counts <- confusionplot_r(data, "pred", "truth", annot = FALSE)
  expect_length(no_counts$layers, 1L)

  custom_pad <- confusionplot_r(
    data,
    "pred",
    "truth",
    annot = FALSE,
    add_pvalue = TRUE,
    pvalue_x_pad = 0.4,
    pvalue_y_pad = 2.2
  )
  expect_equal(custom_pad$layers[[2L]]$data$.x, 0.1)
  expect_equal(custom_pad$layers[[2L]]$data$.y, 0.28)

  red <- confusionplot_r(data, "pred", "truth", cmap = "Reds")
  red_fill <- ggplot2::ggplot_build(red)$data[[1L]]$fill
  expect_identical(red_fill, c("#67000d", "#fff5f0", "#fff5f0", "#67000d"))
  expect_error(
    confusionplot_r(data, "pred", "truth", cmap = "not-a-cmap"),
    "unsupported cmap"
  )

  fixed_white <- with_settings(
    list(annotation_auto_contrast = FALSE),
    confusionplot_r(data, "pred", "truth")
  )
  expect_identical(
    unique(ggplot2::ggplot_build(fixed_white)$data[[2L]]$colour),
    "white"
  )
})

test_that("confusionplot rejects invalid matrix contracts", {
  data <- specialized_confusion_fixture()
  expect_error(confusionplot_r(list(), "pred", "truth"), "data frame")
  expect_error(confusionplot_r(data[FALSE, ], "pred", "truth"), "must not be empty")
  expect_error(confusionplot_r(data, "missing", "truth"), "missing column")
  expect_error(
    confusionplot_r(transform(data, truth = replace(truth, 1, NA)), "pred", "truth"),
    "must not contain missing"
  )
  expect_error(
    confusionplot_r(
      data.frame(pred = c("a", "b", "c"), truth = c("a", "b", "c")),
      "pred",
      "truth",
      add_pvalue = TRUE
    ),
    "2x2 confusion matrix"
  )
  expect_error(
    confusionplot_r(data, "pred", "truth", add_pvalue = TRUE, positive_x = "other"),
    "positive_x"
  )
})

test_that("volcanoplot preserves thresholds, ranking, colours, and labels", {
  data <- specialized_volcano_fixture()
  original <- data
  plot <- volcanoplot_r(data)
  labels <- plot$layers[[4L]]$data$.label

  expect_s3_class(plot, "ggplot")
  expect_identical(data, original)
  expect_setequal(labels, c("GENE1", "GENE2", "GENE5", "GENE6"))
  expect_identical(
    as.character(plot$data$.group),
    c("Down", "Down", "NS", "NS", "Up", "Up")
  )
  expect_identical(plot$labels$x, "log2(fold change)")
  expect_identical(plot$labels$y, "\u2013log10(adjusted p-value)")
  expect_equal(plot$layers[[2L]]$data$.x, 0)
  expect_equal(plot$layers[[2L]]$data$.y, 0)
  expect_equal(plot$layers[[2L]]$data$.yend, 5)
  expect_identical(
    unname(plot$scales$get_scales("colour")$map(c("Down", "NS", "Up", "p_adj < 0.05"))),
    c(palettes("BlueRed", n = 2L)[[1L]], "#808080", palettes("BlueRed", n = 2L)[[2L]], "#000000")
  )
})

test_that("volcanoplot honours n_show and show_list precedence", {
  data <- specialized_volcano_fixture()
  top_one <- volcanoplot_r(data, n_show = 1)
  expect_identical(top_one$layers[[4L]]$data$.label, c("GENE6", "GENE1"))

  none <- volcanoplot_r(data, n_show = 0)
  expect_length(none$layers, 2L)
  expect_identical(
    as.character(none$data$.group),
    c("NS", "NS", "p_adj < 0.05", "p_adj < 0.05", "p_adj < 0.05", "p_adj < 0.05")
  )

  selected <- volcanoplot_r(
    data,
    show_list = c("GENE1", "GENE6"),
    n_show = 1
  )
  expect_identical(selected$layers[[4L]]$data$.label, c("GENE6", "GENE1"))
})

test_that("volcanoplot applies strict author thresholds", {
  threshold <- -log10(0.05)
  data <- data.frame(
    log2FoldChange = c(0.5, 0.5001, -0.5, -0.5001, 2),
    `-log10(adjp)` = c(threshold + 0.1, threshold + 0.1, threshold + 0.1, threshold + 0.1, threshold),
    symbol = c("fold-edge-up", "up", "fold-edge-down", "down", "p-edge"),
    check.names = FALSE
  )
  plot <- volcanoplot_r(data)
  group_by_label <- stats::setNames(as.character(plot$data$.group), plot$data$.label)

  expect_identical(group_by_label[["up"]], "Up")
  expect_identical(group_by_label[["down"]], "Down")
  expect_identical(group_by_label[["fold-edge-up"]], "p_adj < 0.05")
  expect_identical(group_by_label[["fold-edge-down"]], "p_adj < 0.05")
  expect_identical(group_by_label[["p-edge"]], "NS")
})

test_that("volcanoplot rejects invalid direct inputs", {
  data <- specialized_volcano_fixture()
  expect_error(volcanoplot_r(list()), "data frame")
  expect_error(volcanoplot_r(data, n_show = 1.5), "whole number")
  expect_error(volcanoplot_r(data, n_show = -1), "non-negative")
  expect_error(volcanoplot_r(data, n_show = TRUE), "finite number")
  expect_error(volcanoplot_r(data, show_list = 1:2), "character vector")
  expect_error(
    volcanoplot_r(transform(data, log2FoldChange = Inf)),
    "finite numeric"
  )
  expect_error(
    volcanoplot_r(transform(data, symbol = NA_character_)),
    "symbol must not contain"
  )
})

test_that("gseaplot filters, selects, and orders terms like the author backend", {
  data <- specialized_gsea_fixture()
  original <- data
  plot <- gseaplot_r(data, "Clean_Term", top_term = 3)

  expect_s3_class(plot, "ggplot")
  expect_identical(data, original)
  expect_equal(plot$data$.x, c(-1.8, 1.6, 2.1))
  expect_identical(levels(plot$data$.y), c("Pathway B", "Pathway C", "Pathway A"))
  expect_equal(plot$data$.group, c(-1.8, 1.6, 2.1))
  expect_equal(plot$data$.density, rep(1, 3))
  expect_equal(
    plot$data$.count,
    rep(2 * 1.8 * 6 / sqrt(pi) * 25.4 / 72, 3)
  )
  expect_identical(plot$labels$x, "Normalized Enrichment Score (NES)")
  expect_null(plot$labels$y)
  expect_identical(plot$scales$get_scales("colour")$name, "NES")
  expect_identical(plot$scales$get_scales("size")$name, "% Genes\nin set")
  expect_length(plot$layers, 1L)

  top_two <- gseaplot_r(data, "Clean_Term", top_term = 2)
  expect_equal(top_two$data$.x, c(1.6, 2.1))
  expect_identical(levels(top_two$data$.y), c("Pathway C", "Pathway A"))
})

test_that("gseaplot filters significance independently from colour", {
  data <- specialized_gsea_fixture()
  data$score <- c(10, 20, 30)
  data$`FDR q-val`[[2L]] <- 0.2
  plot <- gseaplot_r(
    data,
    "Clean_Term",
    color = "score",
    cutoff = 0.05,
    cmap = "viridis"
  )

  expect_equal(plot$data$.x, c(1.6, 2.1))
  expect_identical(levels(plot$data$.y), c("Pathway C", "Pathway A"))
  expect_equal(plot$data$.group, c(30, 10))
  expect_identical(plot$scales$get_scales("colour")$name, "score")
})

test_that("gseaplot transforms p-value colours before top-term selection", {
  data <- data.frame(
    term = c("A", "B", "C", "D"),
    NES = c(-2, -1, 1, 2),
    `P-value` = c(0.04, 0.001, 0.02, 0.03),
    q = rep(0.01, 4),
    check.names = FALSE
  )
  plot <- gseaplot_r(
    data,
    "term",
    color = "P-value",
    significance_column = "q",
    top_term = 2
  )

  expect_equal(plot$data$.x, c(-1, 1))
  expect_identical(levels(plot$data$.y), c("B", "C"))
  expect_equal(plot$data$.group, c(3, log10(50)))
  expect_identical(plot$scales$get_scales("colour")$name, "log10(1/Pval)")
})

test_that("gseaplot uses overlap ratios for Python-compatible dot diameters", {
  data <- specialized_gsea_fixture()
  data$Overlap <- c("1/10", "5/10", "10/10")
  plot <- gseaplot_r(data, "Clean_Term", top_term = 3, size = 2)
  expected_ratios <- c(0.5, 1, 0.1)

  expect_equal(plot$data$.density, expected_ratios)
  expect_equal(
    plot$data$.count,
    2 * expected_ratios * 2 * 6 / sqrt(pi) * 25.4 / 72
  )

  both <- transform(data, `Tag %` = Overlap, check.names = FALSE)
  expect_error(
    gseaplot_r(both, "Clean_Term"),
    "only one of Overlap or Tag %"
  )
  malformed <- data
  malformed$Overlap[[1L]] <- "not-a-ratio"
  expect_error(
    gseaplot_r(malformed, "Clean_Term"),
    "valid non-negative"
  )
})

test_that("gseaplot rejects unsupported or invalid contracts explicitly", {
  data <- specialized_gsea_fixture()
  expect_error(gseaplot_r(list(), "Clean_Term"), "data frame")
  expect_error(
    gseaplot_r(data, "Clean_Term", significance_column = "missing"),
    "missing column"
  )
  expect_error(
    gseaplot_r(transform(data, `FDR q-val` = 1), "Clean_Term"),
    "no enriched terms"
  )
  expect_error(gseaplot_r(data, "Clean_Term", top_term = 0), "greater than zero")
  expect_error(gseaplot_r(data, "Clean_Term", size = 0), "greater than zero")
  expect_error(
    gseaplot_r(data, "Clean_Term", cmap = list("BuRd_custom")),
    "Matplotlib colormap objects"
  )
  expect_error(
    gseaplot_r(transform(data, score = letters[1:3]), "Clean_Term", color = "score"),
    "must be numeric"
  )
  expect_error(
    gseaplot_r(transform(data, NES = Inf), "Clean_Term"),
    "must be finite"
  )

  all_zero <- transform(data, p = 0)
  expect_s3_class(
    gseaplot_r(
      all_zero,
      "Clean_Term",
      color = "p",
      significance_column = "FDR q-val"
    ),
    "ggplot"
  )
  names(all_zero)[names(all_zero) == "p"] <- "P-value"
  expect_error(
    gseaplot_r(
      all_zero,
      "Clean_Term",
      color = "P-value",
      significance_column = "FDR q-val"
    ),
    "all P-value values are zero"
  )
})

test_that("specialized constructors are quiet and do not change global state", {
  confusion_data <- specialized_confusion_fixture()
  volcano_data <- specialized_volcano_fixture()
  gsea_data <- specialized_gsea_fixture()
  settings_before <- settings()
  theme_before <- ggplot2::theme_get()

  expect_output(confusion <- confusionplot_r(confusion_data, "pred", "truth"), NA)
  expect_output(volcano <- volcanoplot_r(volcano_data, n_show = 1), NA)
  expect_output(gsea <- gseaplot_r(gsea_data, "Clean_Term"), NA)
  expect_s3_class(confusion, "ggplot")
  expect_s3_class(volcano, "ggplot")
  expect_s3_class(gsea, "ggplot")
  expect_identical(settings(), settings_before)
  expect_identical(ggplot2::theme_get(), theme_before)
})
