# CNSPlots Plot Catalog

Use this catalog to select a public function, then inspect its installed
signature and docstring before writing code.

## Distribution and group comparison

- `boxplot`: quartiles and medians across categories; optional pairwise tests.
- `violinplot`: distribution shape across categories.
- `stripplot`: individual observations across categories.
- `barplot`: group estimates displayed as bars.
- `lollipopplot`: values or summaries with stems and markers.
- `dumbbellplot`: two endpoints per category connected by a line.
- `histplot`: binned univariate or bivariate distributions.
- `kdeplot`: smoothed density estimates.
- `distplot`: compact distribution visualization.
- `ridgeplot`: stacked densities across groups.
- `qqplot`: observed versus theoretical quantiles.

## Relationships and change

- `scatterplot`: relationships between numeric variables.
- `regplot`: fitted relationship with regression context.
- `lineplot`: trends or repeated measurements over an ordered axis.
- `slopeplot`: changes between conditions or time points.

## Matrices and classifications

- `heatmapplot`: clustered or annotated matrix heatmaps.
- `dotplot`: matrix-like values encoded by dot size and color.
- `confusionplot`: predicted versus observed class performance.

`heatmapplot` and `dotplot` return backend-native plotter objects rather than a
plain Matplotlib `Axes`.

## Proportions, sets, and flows

- `stackplot`: categorical composition across groups.
- `pieplot` and `donutplot`: parts of a whole when few categories are present.
- `vennplot`: overlap among a small number of sets.
- `upsetplot`: scalable set intersections.
- `sankeyplot`: flow across two or more ordered categorical stages.

`upsetplot` returns panel axes and `vennplot` returns a matplotlib-venn diagram
object.

## Survival and model summaries

- `survivalplot`: Kaplan-Meier curves, overall tests, and optional pairwise
  hazard-ratio inference.
- `cumulativeincidenceplot`: competing-risk cumulative incidence.
- `forestplot`: effect estimates and confidence intervals from a results table
  or a fitted `CoxModel` or `LogisticModel`. For table input, map the label,
  estimate, and absolute confidence-bound columns explicitly.
- `CoxModel` and `LogisticModel`: fitted statistical models used by relevant
  plotting workflows.

Confirm event coding, reference groups, time units, and requested contrasts
before plotting.

## Genomics and evaluation

- `volcanoplot`: effect size versus transformed adjusted significance.
- `gseaplot`: gene-set enrichment results.
- `rocplot`: receiver operating characteristic curves with optional pointwise
  bootstrap confidence bands and paired DeLong AUC comparisons. Retrieve exact
  coordinates, AUCs, bands, and tests with `get_roc_results(ax)`.
- `precisionrecallplot`: precision versus recall with average precision (AP)
  labels and a prevalence reference. `get_precision_recall_results(ax)` returns
  coordinates and metrics; no confidence bands or comparison tests are run.
- `calibrationplot`: reliability curves from held-out probabilities, uniform or
  quantile bins, and optional Brier labels. `get_calibration_results(ax)` exposes
  bin counts and metrics. Brier measures overall probabilistic prediction quality.
- `phyloplot`: phylogenetic visualization from `AnnData`.
- `prerank`: preranked enrichment analysis.

Do not infer column transformations or significance thresholds. Verify the
input columns expected by the installed version.

## Figure composition and export

- `figure`: size a styled whole canvas in points (1/72 inch) by default, or
  explicitly use `unit="pt"`, `unit="in"`, or `unit="mm"`. Return the
  Matplotlib `Figure`, which also becomes current.
- `multipanel`: set the full canvas width with `max_width` and create labeled
  panels. Explicit panel dimensions inherit the constructor's `unit`, with
  a per-panel override. `panel(...)` sizes the axes area and returns the target
  `Axes`; decorations and margins occupy additional space in the layout.
- `add_panel_label`: label an existing axes.
- `take_legend_out`: position a legend outside its axes.
- `savefig`: save the current figure or an explicit `fig=`, with per-save DPI,
  transparency, crop, and padding options; create parent directories as needed.
- `settings.context(...)`: apply temporary package-wide style settings.
- `palettes`: retrieve curated categorical or continuous palettes.

Typical multi-panel structure:

```python
import cnsplots as cns

mp = cns.multipanel(max_width=540)

ax_a = mp.panel("A", width=150, height=150)
cns.boxplot(data=grouped, x="group", y="value", ax=ax_a)

ax_b = mp.panel("B", width=150, height=150)
cns.scatterplot(data=continuous, x="x", y="y", ax=ax_b)

cns.savefig("multipanel.svg")
```

All dimensions above are in points. For physical units, use, for example,
`mp = cns.multipanel(max_width=180, unit="mm")` and
`mp.panel("A", width=50.8, height=25.4)` for a 2 × 1 inch axes area, or
`mp.panel("B", width=2, height=1, unit="in")` for an equivalent panel.
Omitted dimensions always use settings stored in points. Panel margins remain
in points, and label `pad_left`/`pad_top` remain in display pixels, regardless
of `unit`.

Display and export DPI determine raster resolution without changing physical
size. Default tight cropping exports the artists' bounds plus `pad_inches`
in inches; set `bbox_inches=None` to preserve the full canvas size.

See the current API documentation at <https://cnsplots.farid.one/latest/api.html>
when web access is available.
