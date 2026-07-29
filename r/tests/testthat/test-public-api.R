test_that("the installed namespace exposes only direct public names", {
  expected <- c(
    "settings", "reset_settings", "with_settings", "setup_ggplot",
    "theme_axes", "theme_legend", "theme_facet", "theme_grid",
    "theme_spacing", "palettes", "palette_names",
    "get_hexcolors_from_apalette", "scale_colour_palette",
    "scale_color_palette", "scale_fill_palette", "scale_colour_map",
    "scale_color_map", "scale_fill_map", "figure", "savefig",
    "scatterplot", "regplot", "barplot", "stripplot", "boxplot",
    "violinplot", "distplot", "kdeplot", "qqplot", "pieplot",
    "donutplot", "placeholderplot", "lollipopplot", "stackplot",
    "slopeplot", "confusionplot", "volcanoplot", "gseaplot"
  )
  exports <- getNamespaceExports("cnsplots")

  expect_setequal(intersect(expected, exports), expected)
  expect_false(any(grepl("^cns_", exports)))
  for (name in expected) {
    expect_true(exists(name, envir = asNamespace("cnsplots"), inherits = FALSE))
  }
})
