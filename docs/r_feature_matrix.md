> **Status:** audit matrix. Current public names and implemented scope are documented in `r/README.md`; later-phase rows remain planning only.

# Python-to-R Feature Matrix

Status: Reviewed planning baseline
Related plan: `docs/r_package_plan.md`
Python reference: `0.5.0` at commit `e678e2d5e975c4595b1d7c8bc4d07b4030a29d14`

Current native R plot coverage: `scatterplot()`, `regplot()`, `slopeplot()`,
`barplot()`, `lollipopplot()`, `stackplot()`, `stripplot()`, `boxplot()`,
`violinplot()`, `distplot()`, `kdeplot()`, `qqplot()`, `pieplot()`,
`donutplot()`, `placeholderplot()`, `confusionplot()`, `volcanoplot()`, and
`gseaplot()`.

## 1. Priority definitions

| Priority | Meaning |
|---|---|
| P0 | Required to prove or complete the native R package foundation |
| P1 | High-value R-native plot recipe after the theme architecture stabilizes |
| P2 | Specialized computation or ecosystem integration evaluated separately |
| Defer | Not planned until a concrete R use case and maintenance owner justify it |

The target is conceptual and visual parity where useful. Python implementation
details, mutable matplotlib `Axes` behavior, and pixel-identical rendering are
not compatibility requirements. “Available in the R ecosystem” does not mean
“committed for the first R release.”

## 2. Foundation, layout, and infrastructure

| Python API or area | Current responsibility | Proposed R design | Priority |
|---|---|---|---|
| `settings` | 78 mutable defaults mixing appearance, palettes, export, layout, and statistics | Split visual values into `settings()`, palettes into the registry, export into `figure()`, layout into later composition APIs, and statistical defaults into explicit compute/annotation arguments | P0/P1/P2 |
| `setup_matplotlib()` | Global style, fonts, axes, palettes, and renderer configuration | Conceptually split appearance into `setup_ggplot()` and scales, and output behavior into export APIs; no global R mutation | P0 |
| `setup_ax()` | Restyle axes and also alter ticks, labels, limits, and colour bars | Map non-data appearance to additive theme components; keep limits, scales, coordinates, and data-driven ticks outside themes | P0/P1 |
| `setup_ggplot()` | Return a basic R `theme()` string | Replace rather than port: provide a native installed R package and never generate R code strings from Python | P0 |
| `figure()` | Create a matplotlib Figure/Axes canvas from nominal 72-DPI layout units | `figure()` covers physical size, units, background, and raster DPI only; it does not emulate the Figure/Axes container or absolute panel placement | P0 |
| `savefig()` / `save()` | Format dispatch and Illustrator-oriented export | `savefig()` with explicit extension/device agreement, physical dimensions, vector/raster policy, and tested output | P0 |
| `palettes()` | Raw qualitative and continuous palettes | `palettes()` and a typed, attributed registry | P0 |
| colour constants | Eleven exported single-colour globals | Export `RED` through `CHOCOLATE` directly, backed by the verified colour registry | P0 |
| `get_hexcolors_from_apalette()` | Select colours by zero-based index | Fold into validated palette selection and ordinary R subsetting; do not mechanically copy the Python name | P0 |
| `take_legend_out()` | Reposition or detach a matplotlib legend | Ordinary legend styling/position belongs to `theme_legend()`; extraction, shared guides, and outside-canvas layout belong to later composition APIs | P0/P1 |
| `add_panel_label()` | Add an axes-relative panel letter | Single-plot tags use `labs(tag=)` plus tag typography; automatic A/B/C numbering and layout-aware positioning are later composition behavior | P0/P1 |
| `multipanel` | Absolute panel sizes, wrapping, labels, and measured decoration space | Start with documented ggplot composition contracts; evaluate patchwork/grid only after the theme core is stable | P1 |
| `placeholderplot()` | Figure-layout mock panel | A lightweight `placeholderplot()` returning a ggplot object | P1 |
| bundled `datasets` | Public offline datasets and gallery inputs | No initial API parity: use base R data or deterministic fixtures for examples; selectively port only after provenance, licence, and package-size review | Defer |
| validation helpers | Validate pandas and AnnData inputs | Small internal R-native validators; do not freeze them as public API | P0 |

## 3. Distribution plots

| Python plot | Important current behavior | R-native direction | Priority |
|---|---|---|---|
| `boxplot()` | Styled box with optional counts and Mann-Whitney annotation | `geom_boxplot()` recipe; counts and inference are explicit add-ons | P1 |
| `violinplot()` | Violin with optional narrow box overlay | `geom_violin()` plus optional `geom_boxplot()` | P1 |
| `stripplot()` | Jittered points with optional median/mean overlay | `geom_jitter()` plus explicit summary layer | P1 |
| `distplot()` | Histogram plus KDE | Explicit histogram/density composition recipe | P1 |
| `histplot()` | Broad seaborn histogram wrapper | Small opinionated recipe, not full seaborn parameter parity | P1 |
| `kdeplot()` | Density with optional mode annotation | `geom_density()` plus an explicit mode-stat helper | P1 |
| `ridgeplot()` | Ridgeline densities | Optional `ggridges` integration in Suggests | P1 optional |
| `qqplot()` | Normal Q-Q display | `stat_qq()` plus `stat_qq_line()` with configurable theoretical distribution | P1 |

## 4. Categorical summaries and composition

| Python plot | Important current behavior | R-native direction | Priority |
|---|---|---|---|
| `barplot()` | Mean bars, optional labels, and Welch test | Explicit summary transformation plus `geom_col()`; inference separate | P1 |
| `lollipopplot()` | Summary values, intervals, and grouped dodge | `geom_segment()` plus `geom_point()` and optional interval layer | P1 |
| `stackplot()` | Counts/proportions and Fisher/chi-square annotations | Count/proportion recipe with inference separate | P1 |
| `pieplot()` | Category proportions and configurable legend | Bar-to-polar recipe with documented perceptual limits | P1 |
| `donutplot()` | Pie variant with centre annotation | Polar recipe with explicit inner radius and annotation | P1 |

## 5. Relationships and trajectories

| Python plot | Important current behavior | R-native direction | Priority |
|---|---|---|---|
| `scatterplot()` | Styled points and corrected legend markers | `geom_point()` plus replaceable scales and themes | P1 |
| `regplot()` | Linear fit with Pearson statistics | `geom_smooth(method="lm")`; correlation annotation explicit | P1 |
| `lineplot()` | Seaborn-compatible estimator and intervals | R-native grouped line and summary recipe; no full seaborn signature emulation | P1 |
| `slopeplot()` | Paired changes across conditions | `geom_line()` and `geom_point()` grouped by explicit pair ID | P1 |

## 6. Model diagnostics and classification displays

| Python plot | Important current behavior | R-native direction | Priority |
|---|---|---|---|
| `confusionplot()` | Matrix, annotations, and optional Fisher-derived metric | P1 accepts a precomputed matrix or explicit truth/prediction data; metric computation and normalization contracts are separate P2 concerns | P1/P2 |
| `rocplot()` | Multiple ROC curves, AUC, and optional uncertainty | P1 can plot precomputed FPR/TPR data; `pROC`/`yardstick` calculation, AUC CI, and direction inference are P2 adapters | P1/P2 |

## 7. Genomics, matrices, and specialised backends

| Python plot | Important current behavior | R-native direction | Priority |
|---|---|---|---|
| `volcanoplot()` | Fixed threshold defaults and automatic labels | ggplot2 recipe with visible thresholds and optional `ggrepel` | P1 |
| `gseaplot()` | GSEA result dot plot | Adapter for tidy result frames; optional `fgsea`/`clusterProfiler` integration | P2 |
| `heatmapplot()` | AnnData input, clustering, annotations, dendrograms, and detached legends | Prefer a `ComplexHeatmap` adapter; do not promise `setup_ggplot()` works directly on non-ggplot objects | P2 |
| `dotplot()` | Matrix with colour and size encodings | P1 tidy long-form ggplot recipe; P2 Seurat/SingleCellExperiment adapters | P1/P2 |
| `phyloplot()` | Tree plus associated heatmaps from AnnData metadata | Optional `ggtree` integration using R-native phylogenetic objects | P2 |

## 8. Survival and statistical-model output

| Python API | Important current behavior | R-native direction | Priority |
|---|---|---|---|
| `survivalplot()` | Kaplan-Meier, log-rank/trend tests, and Cox contrasts | Adapter around `survival` results and an optional `ggsurvfit`-style recipe | P2 |
| `cumulativeincidenceplot()` | Competing risks, Gray test, and optional risk table | Adapter around `cmprsk`/`tidycmprsk` results | P2 |
| `forestplot()` | Cox/logistic model effect display | P1 accepts tidy `term/estimate/conf.low/conf.high` input; P2 adds model-object adapters | P1/P2 |
| `CoxModel` | Fit multiple Cox models | Do not wrap `survival::coxph()` in phase one; accept tidy results later | Defer |
| `LogisticModel` | L1 CV logistic model and bootstrap AUC | Do not duplicate `glmnet`/`tidymodels` in the plotting core | Defer |
| `prerank()` | Run pre-ranked GSEA | Use established R analysis packages; cnsplots may visualize their outputs | Defer |

## 9. Sets and flows

| Python plot | Important current behavior | R-native direction | Priority |
|---|---|---|---|
| `vennplot()` | Two- or three-set diagrams | Optional `ggVennDiagram` or `eulerr` adapter | P2 |
| `upsetplot()` | Set-intersection layout with multiple axes | Optional `ComplexUpset` adapter | P2 |
| `sankeyplot()` | Two-category weighted flows | Static `ggalluvial` recipe with explicit semantic differences from Sankey | P2 |

## 10. Embedded statistical behavior

The Python recipes sometimes compute inference while drawing. R plot-only
recipes can remain P1 while the corresponding computation and annotation
helpers are later, explicit deliverables.

| Python behavior | R boundary |
|---|---|
| box/violin/strip rank tests | `compute_*()` result plus explicit `annotate_*()` layer |
| bar/lollipop Welch tests | summary geometry separate from `stats::t.test()` results |
| stack Fisher/chi-square | composition plot separate from contingency inference |
| regression Pearson statistics | fit geometry separate from `stats::cor.test()` annotation |
| volcano thresholds and automatic labels | visible parameters and deterministic label selection |
| ROC AUC/CI | curve display separate from estimation and bootstrap configuration |

No plot constructor silently performs inferential testing merely because a
geometry was selected.

## 11. Ecosystem integrations

| Python integration | R decision | Priority |
|---|---|---|
| Matplotlib | No API emulation; ggplot2 is the native graphics contract | P0 |
| Seaborn | Recreate useful visual recipes, not wrapper signatures | P1 |
| Scanpy/AnnData | Prefer Seurat and SingleCellExperiment adapters after the core stabilizes | P2 |
| PyComplexHeatmap | Prefer ComplexHeatmap rather than forcing ggplot compatibility | P2 |
| lifelines/comprisk | Prefer survival/cmprsk/tidycmprsk result adapters | P2 |
| gseapy | Prefer fgsea/clusterProfiler result adapters | P2 |
| matplotlib SVG post-processing | Use R-native vector devices and document differences | P0 |

## 12. Recommended delivery order

1. P0 architecture proof: package metadata, tokens, `standard` and `embedding`
   themes, one component, one discrete palette, colour/fill scales, and tests.
2. Complete phase-one theme components and `distribution`/`matrix` profiles.
3. Complete attributed palettes and continuous/discrete scales.
4. Add physical figure specifications and `savefig()`.
5. Add P1 recipes by figure family, selected from real publication cases.
6. Add specialised P2 adapters only after the ggplot contract is stable.
7. Reconsider deferred analysis wrappers only if established R packages leave a
   demonstrated gap.

Later plot recipes keep the author's direct function names without a `cns_`
prefix. When a name also exists in base R or an attached package, users can
write it explicitly as `cnsplots::boxplot()` or the corresponding namespaced
call. Each recipe returns a standard ggplot object, accepts tidy long-form
data, and allows its theme and scales to be replaced.

Statistical layers follow explicit boundaries:

```text
compute_*()   -> statistical computation
tidy_*()      -> standardized result data
plot name     -> author-compatible direct plot recipe
annotate_*()  -> optional statistical display
setup_ggplot*()  -> non-data appearance
```

The matrix must be revisited after every milestone. A Python feature is not
automatically an R requirement merely because it exists upstream.
