# cnsplots for R

A native R/ggplot2 implementation of the visual conventions and plotting
behavior in Python **cnsplots 0.5.0**.

The public API is intentionally direct. Use `settings()`, `setup_ggplot()`,
`palettes()`, `figure()`, `savefig()`, and the original plot names; no `cns_`
prefix is required. A complete Chinese guide with examples for every implemented plot is available in [README_zh.md](README_zh.md).

These direct names intentionally match the author's API. If `boxplot()`,
`barplot()`, or `qqplot()` conflicts with an attached R function, call it
explicitly as `cnsplots::boxplot()`, `cnsplots::barplot()`, or
`cnsplots::qqplot()`.

## Current scope

The package currently provides:

- all 78 author settings;
- 28 qualitative palettes and 7 continuous colour maps;
- the canonical 8/7 pt theme, plus small theme components;
- reproducible figure sizing and extension-driven export;
- `scatterplot()`, `regplot()`, `slopeplot()`, `barplot()`,
  `lollipopplot()`, `stackplot()`, `boxplot()`, `violinplot()`,
  `stripplot()`, `distplot()`, `kdeplot()`, `qqplot()`, `pieplot()`,
  `donutplot()`, `placeholderplot()`, `confusionplot()`, `volcanoplot()`,
  and `gseaplot()`.

Every plot constructor returns a normal `ggplot` object. It does not print,
open a device, change the global theme, or mutate the input data.

## Installation

```sh
R CMD INSTALL r
```

The current development branch can also be installed from the maintainer fork:

```r
remotes::install_github(
  "jarxunlai/cnsplots",
  ref = "feature/r-package-foundation",
  subdir = "r"
)
```

```r
library(ggplot2)
library(cnsplots)
```


## Validation

The package has been exercised with R 4.5.3 and ggplot2 4.0.3. All testthat
checks pass, and `R CMD check --no-manual` completes with `Status: OK` (zero
errors, warnings, or notes). The unchanged Python baseline also passes all 357
pytest cases at 100% coverage, and the repository pre-commit suite passes.

## Direct plotting API

Column arguments are strings, matching the original Python calls:

```r
p <- scatterplot(
  iris,
  x = "Sepal.Length",
  y = "Petal.Length",
  hue = "Species"
)

p + labs(title = "Iris morphology")
```

The same palette and theme defaults are already applied by the constructor.
For raw ggplot2 code, add them explicitly:

```r
p <- ggplot(iris, aes(Sepal.Length, Petal.Length, colour = Species)) +
  geom_point() +
  scale_colour_palette("Ecotyper1") +
  setup_ggplot()
```

## Theme without repeated code

`setup_ggplot()` supplies the author's canonical baseline: 8 pt titles and
axis titles, 7 pt ticks and legends, bottom/left axes, no grid, transparent
backgrounds, and publication-scale line widths.

```r
p + setup_ggplot("standard")
p + setup_ggplot("embedding")
p + setup_ggplot("matrix")
```

Figure-specific changes stay short and composable:

```r
p +
  setup_ggplot() +
  theme_legend(position = "bottom", direction = "horizontal") +
  theme_axes(ticks = FALSE) +
  theme_grid(major = "y")
```

Available components are `theme_axes()`, `theme_legend()`, `theme_facet()`,
`theme_grid()`, and `theme_spacing()`. A final ordinary `ggplot2::theme()` call
can always override them.

## Palettes

```r
palette_names("qualitative")
palettes("Ecotyper1", n = 5)
palettes("Ecotyper2", n = 8)  # cycles in author order

p + scale_colour_palette("Nature")
p + scale_fill_map("gnuplot")
```

Palette names, order, and hexadecimal values are locked to Python cnsplots
0.5.0. Historical names such as `NPG`, `AAAS`, `OrBl_custom`, and
`RdBu_custom` are not aliases.

## Settings

```r
settings("title_fontsize")
settings(title_fontsize = 9, legend_fontsize = 8)

large <- with_settings(
  list(title_fontsize = 10, legend_fontsize = 9),
  p + setup_ggplot()
)

reset_settings()
```

Temporary settings are restored even when the enclosed expression fails.
Package loading itself has no graphics side effects.

## Saving

The short path is to pass dimensions directly:

```r
savefig(
  "figures/iris.pdf",
  p,
  width = 85,
  height = 65,
  units = "mm"
)
```

A reusable specification is also available:

```r
spec <- figure(85, 65, units = "mm", dpi = 300)
savefig("figures/iris.png", p, spec = spec)
```

Parent directories are created automatically. Supported extensions are PDF,
SVG, PNG, TIFF/TIF, JPEG/JPG, and EPS. The author defaults are transparent
output and 288 DPI.

## Data contract

Plot constructors accept a non-empty data frame and string column names. They
validate numeric columns and complete category orders, do not mutate their
input, and fail explicitly when an option is not implemented. Constructors
return an ordinary ggplot object without printing or opening a graphics device.

```r
p <- cnsplots::boxplot(iris, "Species", "Sepal.Length")

p +
  labs(tag = "A", title = "Sepal length") +
  theme(plot.tag = element_text(face = "bold"))
```

## Plot recipes

The examples below use one small data frame:

```r
set.seed(42)

demo <- data.frame(
  group = rep(c("Control", "Treatment"), each = 30),
  subtype = rep(c("A", "B", "C"), length.out = 60),
  value = c(rnorm(30, 5, 0.8), rnorm(30, 6, 1.0)),
  score = seq_len(60) + rnorm(60, sd = 5)
)
```

### Relationships

```r
scatterplot(demo, "score", "value", hue = "group")
regplot(demo, "score", "value", hue = "group")
```

For paired changes, every pair must belong to one x category and contain one
observation from each of exactly two conditions:

```r
paired <- expand.grid(
  cohort = c("Cohort 1", "Cohort 2"),
  subject = seq_len(6),
  condition = c("Before", "After"),
  KEEP.OUT.ATTRS = FALSE,
  stringsAsFactors = FALSE
)
paired$pair_id <- interaction(paired$cohort, paired$subject, drop = TRUE)
paired$value <- as.numeric(paired$pair_id) +
  ifelse(paired$condition == "After", 0.8, 0) +
  rnorm(nrow(paired), sd = 0.15)

slopeplot(
  paired, "cohort", "value", "condition", "pair_id",
  hue_order = c("Before", "After")
)
```

### Categorical summaries and compositions

```r
barplot(demo, "group", "value", hue = "subtype", add_tip = TRUE)

lollipopplot(
  demo, "group", "value",
  hue = "subtype", estimator = "mean", errorbar = "ci", add_tip = TRUE
)

stackplot(
  demo, x = "group", stack = "subtype",
  stack_order = c("A", "B", "C"), normalize = TRUE, add_count = TRUE
)

stripplot(
  demo, "group", "value",
  hue = "subtype", showmedian = TRUE, showmeans = TRUE, add_count = TRUE
)
```

`lollipopplot()` supports mean or median summaries and SD, SE, or confidence
intervals. `stackplot()` accepts exactly one of `x` and `y`; supplying `y`
produces the horizontal form.

### Distributions

```r
cnsplots::boxplot(
  demo, "group", "value", hue = "subtype", add_count = TRUE
)

violinplot(
  demo, "group", "value", hue = "subtype", add_box = TRUE
)

distplot(demo, "value", hue = "group", bins = 20, alpha = 0.35)
kdeplot(demo, "value", hue = "group")
cnsplots::qqplot(demo, "value")
```

The histogram density is scaled to the count axis. An ungrouped KDE can mark
its estimated peak; exactly two hue groups reproduce the author's
Kolmogorov-Smirnov annotation. Q-Q plotting positions are `i / (n + 1)` and no
reference line is added by default.

### Circular and placeholder plots

```r
pieplot(demo, "subtype", order = c("A", "B", "C"))
donutplot(demo, "subtype")
placeholderplot("Panel reserved for validation cohort")
```

### Matrices and genomics

```r
classification <- data.frame(
  prediction = c("neg", "neg", "neg", "pos", "pos", "pos", "pos", "neg"),
  truth = c("neg", "neg", "pos", "pos", "pos", "neg", "pos", "neg")
)

confusionplot(
  classification, "prediction", "truth",
  x_order = c("neg", "pos"), y_order = c("neg", "pos"),
  add_pvalue = TRUE, positive_x = "pos", positive_y = "pos"
)
```

```r
de <- data.frame(
  log2FoldChange = c(-2.2, -1.1, -0.3, 0.1, 0.7, 1.4, 2.3, 0.2),
  `-log10(adjp)` = c(5, 3, 0.7, 0.2, 2, 3.5, 6, 1.5),
  symbol = paste0("GENE", seq_len(8)),
  check.names = FALSE
)

volcanoplot(de, n_show = 2)
```

```r
gsea <- data.frame(
  Term = c("Interferon", "Cell cycle", "Oxidative phosphorylation", "ECM"),
  NES = c(2.1, -1.8, 1.5, -1.3),
  `FDR q-val` = c(0.01, 0.02, 0.03, 0.2),
  Overlap = c("12/100", "18/140", "8/80", "5/90"),
  check.names = FALSE
)

gseaplot(gsea, y = "Term", color = "NES", cutoff = 0.05)
```

`confusionplot(add_pvalue = TRUE)` requires a 2-by-2 table. `volcanoplot()`
retains the author's fixed adjusted-p and fold-change thresholds. `gseaplot()`
visualizes a tidy result table; it does not run enrichment analysis.

## Explicitly unsupported options

- `pairs` is not yet supported by `boxplot()`, `violinplot()`,
  `lollipopplot()`, or `stackplot()`; non-`NULL` values fail explicitly.
- `barplot()` does not preserve the ambiguous Python overload in which a
  `palette` string can mean a data column.
- `histplot()`, `lineplot()`, `ridgeplot()`, `rocplot()`, `forestplot()`,
  survival, heatmap/phylogeny, set, flow, and absolute multipanel APIs are not
  yet implemented.
- Arbitrary Matplotlib colormap objects cannot be passed to R.

See [README_zh.md](README_zh.md) for parameter-level guidance, complete export
rules, and the current migration boundary.

## Compatibility boundary

The target is semantic and visual fidelity, not pixel identity between
Matplotlib and ggplot2. The port preserves palette roles, default statistics,
layer composition, annotations, typography, line widths, and physical figure
size. Matplotlib's automatic “best” legend placement, renderer-tight bounding
box, per-string font fallback, PDF Type 42 internals, and Illustrator-specific
SVG post-processing have no exact ggplot2 equivalent.

Some advanced Python functions still require R data-model or statistical
backends. Unsupported behavior fails explicitly rather than being silently
ignored. See [README_zh.md](README_zh.md) for the implementation rationale and
current migration boundary.
