# API

Import cnsplots as:

```python
import cnsplots as cns
```

## Plotting Functions

Every plotting function accepts a keyword-only `ax` argument for composition
inside an existing Matplotlib layout. Most return the target
`matplotlib.axes.Axes`; `heatmapplot`, `dotplot`, `upsetplot`, and `vennplot`
instead preserve their backend-native results: `ClusterMapPlotterNew`,
`DotClustermapPlotterNew`, a dictionary of panel axes, and a matplotlib-venn
diagram object, respectively.

### Distribution & Comparison Plots

```{eval-rst}
.. currentmodule:: cnsplots
.. apirootsummary::
   :toctree: api
   :nosignatures:

   boxplot
   violinplot
   stripplot
   barplot
   lollipopplot
   dumbbellplot
   histplot
   distplot
   kdeplot
   ridgeplot
```

### Scatter & Regression Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   scatterplot
   regplot
   lineplot
   slopeplot
```

### Heatmaps & Matrix Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   heatmapplot
   dotplot
   confusionplot
```

### Categorical & Proportion Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   stackplot
   pieplot
   donutplot
   vennplot
   upsetplot
   sankeyplot
```

### Survival Analysis Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   survivalplot
   cumulativeincidenceplot
```

### Genomics & Statistical Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   volcanoplot
   gseaplot
   rocplot
   precisionrecallplot
   calibrationplot
   qqplot
   forestplot
```

### Specialized Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   phyloplot
   placeholderplot
```

## Statistical Comparison Results

After calling `boxplot`, `violinplot`, `barplot`, `lollipopplot`, or `stackplot`
with `pairs`, use `get_comparison_results(ax)` to retrieve the statistics used
for its annotations. The plot still returns its Matplotlib axes; the accessor
returns a separate DataFrame without rerunning any tests.

This example uses the bundled tips dataset:

```python
import cnsplots as cns

tips = cns.datasets.load_dataset("tips")
cns.figure(width=180, height=140)
with cns.settings.context(pvalue_format="threshold"):
    ax = cns.boxplot(
        tips,
        x="day",
        y="total_bill",
        pairs="all",
        p_adjust="holm",
    )
comparisons = cns.get_comparison_results(ax)
print(comparisons.to_string(index=False))
```

Each row identifies `group1`, `group2`, the test, its alternative, whether
observations are paired, and the contributing counts `n1` and `n2`. Hue groups
use `(category, hue)` tuples. Rows follow annotation drawing order, with shorter
brackets first; group order follows the categorical axis rather than the order
of each supplied pair. The p-value columns distinguish computation from display:

| Column | Meaning |
| --- | --- |
| `pvalue_raw` | Uncorrected test p-value. |
| `pvalue_adjusted` | Numerical p-value after the requested correction. |
| `pvalue_annotation` | P-value used to format the rendered label. |
| `p_adjust` | Correction method, or `None` when no correction was requested. |
| `significant` | Significance decision after correction. |
| `annotation` | Exact rendered label, including any correction suffix. |

Without correction, all three p-value columns agree. Bonferroni labels use
adjusted p-values. Holm and FDR labels preserve the raw p-values and add a
nonsignificance suffix when correction removes significance; read
`pvalue_adjusted` for their numerical corrected values. Correction covers all
resolved pairs in one plot call, including every category with `pairs="hue"`.
It does not combine comparisons from separate calls.

Continuous comparisons count complete rows after category and hue filters.
Stackplot comparisons use original complete category/stack counts before
normalization or `n_factor` scaling. Missing stack values can therefore make
these counts differ from the raw category counts on its ticks.

Each accessor call returns a copy. On reused axes it returns the latest call
that added comparisons; drawing another plot without `pairs` leaves those
results available. Clearing the axes or removing their annotations makes the
result empty. Axes without stored comparisons return an empty table with the
same columns. Omitting `ax` selects the current axes.

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   get_comparison_results
```

## Survival Results

After `survivalplot`, use `get_survival_results(ax)` to retrieve the estimates
and tests used for its annotations. The plot still returns its Matplotlib axes.
The accessor returns a DataFrame snapshot without refitting models or rerunning
tests; it also works with `descriptive_only=True`.

For example, compare stages in the synthetic showcase data, correcting two
explicitly requested Cox contrasts as one family:

```python
survival = cns.datasets.get_showcase_data().survival_df
cns.figure(width=260, height=240)
ax = cns.survivalplot(
    survival,
    duration="time",
    event="event",
    hue="stage",
    hue_order=["I", "II", "III"],
    pairs=[("I", "II"), ("I", "III")],
    p_adjust="holm",
)
results = cns.get_survival_results(ax)
contrasts = results.loc[results["kind"] == "pairwise_cox"]
print(contrasts[["group1", "group2", "estimate", "pvalue_raw", "pvalue_adjusted"]])
```

Pair tuples are `(reference, comparison)`: the hazard ratio estimates the
comparison group's hazard relative to the reference. `p_adjust` accepts `None`
(the default), `"bonferroni"`, `"holm"`, `"fdr_bh"`, or `"fdr_by"`. Correction
covers the requested pairwise Cox contrasts in that call, excluding the overall
and landmark tests. Duplicate contrasts, including reversed pairs, are rejected
when pairwise inference is enabled. An unavailable contrast still counts toward
the family size and contributes a placeholder p-value of 1 to correction; its
returned p-values remain missing. Corrected annotations show the raw and adjusted
p-values, method, and family size. Hazard-ratio confidence intervals remain
unadjusted 95% intervals.

The table has the same columns for every call:

| Columns | Meaning |
| --- | --- |
| `kind` | `overall`, `pairwise_cox`, `median_survival`, `landmark_survival`, `landmark_test`, or `rmst`. |
| `test` | `logrank`, `trend`, `cox_wald`, or `fixed_time_log_minus_log`; `None` for descriptive estimates. |
| `groups` | Tuple of contributing groups, in `hue_order` for overall tests and `(reference, comparison)` order for Cox contrasts. |
| `group1`, `group2` | The estimate's group, or reference and comparison groups; unused entries are `None`. |
| `n`, `events` | Total contributing observations and observed events over full follow-up, not truncated at the landmark or RMST horizon. |
| `n1`, `events1`, `n2`, `events2` | Counts for the named groups; unused entries, including for overall tests, are missing. |
| `time` | Landmark or RMST horizon; missing for other rows. |
| `estimate` | Hazard ratio, median survival time, landmark survival probability, or restricted mean survival time, as indicated by `kind`. |
| `ci_lower`, `ci_upper`, `ci_level` | Hazard-ratio confidence interval and level (`0.95`); missing for other kinds. |
| `statistic` | Chi-square for log-rank, landmark, or Cox likelihood-ratio trend tests; Wald z for pairwise Cox tests; missing for descriptive estimates. |
| `pvalue_raw`, `pvalue_adjusted` | Raw and corrected p-values; equal when no correction applies and missing for descriptive estimates or unavailable tests. |
| `p_adjust`, `family_size` | Pairwise correction method and number of requested Cox contrasts. |
| `status`, `reason` | `available`, `unavailable`, or `not_reached`, with a reason when a result is unavailable. |
| `annotation` | The exact annotation text for that result. |

Only enabled annotations produce rows. For example, median rows require
`show_median_survival=True`; `show_hazard_ratio=False` omits pairwise Cox rows,
and `descriptive_only=True` omits all tests. A median that is not reached has
`estimate=inf` and `status="not_reached"`. Numerical values retain their full
precision independently of annotation formatting.

The overall log-rank test treats groups as categories. The optional Cox trend
test uses equally spaced scores in the explicit `hue_order`, recorded in
`groups`, and reports a one-degree-of-freedom likelihood-ratio test.

Durations are finite, nonnegative times to the event or censoring; event code 1
means observed and 0 means censored. Landmark and RMST horizons must be finite,
positive, and at most the smallest maximum follow-up among the plotted groups.
The endpoint is inclusive: the right-continuous Kaplan-Meier estimate at a
landmark includes events at that time. These summaries do not extrapolate beyond
the common follow-up. The table's `attrs` record the `duration`, `event`, and
`hue` column names, `time_label`, `event_observed=1`, `event_censored=0`, and
`common_follow_up`.

Every accessor call returns a copy. A new `survivalplot` call on the same axes
replaces its results, including when no annotations are requested. Clearing the
axes removes the stored results. Axes without survival results return an empty
table with the same columns; omitting `ax` selects the current axes.

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   get_survival_results
```

## Prediction Evaluation Results

`rocplot`, `precisionrecallplot`, and `calibrationplot` return the target
Matplotlib axes. Their result accessors return typed dictionaries of detached
DataFrames containing the numbers used to draw the plot, without recomputing
metrics. Rows identify prediction columns using `model`; comparisons identify
`model1` and `model2`. Models retain the supplied column order.

```python
import pandas as pd
import cnsplots as cns

data = pd.DataFrame(
    {
        "truth": [0, 0, 1, 1],
        "model_a": [0.1, 0.4, 0.35, 0.8],
        "model_b": [0.2, 0.3, 0.5, 0.7],
    }
)
panels = cns.multipanel(max_width=800)
roc_ax = panels.panel("A", width=200, height=180)
cns.rocplot(data, "truth", ["model_a", "model_b"], pairs="all", ax=roc_ax)
pr_ax = panels.panel("B", width=200, height=180)
cns.precisionrecallplot(data, "truth", ["model_a", "model_b"], ax=pr_ax)
cal_ax = panels.panel("C", width=200, height=180)
cns.calibrationplot(data, "truth", ["model_a", "model_b"], n_bins=4, ax=cal_ax)

roc = cns.get_roc_results(roc_ax)
pr = cns.get_precision_recall_results(pr_ax)
calibration = cns.get_calibration_results(cal_ax)
print(roc["comparisons"])
print(pr["metrics"])
print(calibration["bins"])
```

### ROC coordinates and inference

`get_roc_results(ax)` returns `ROCResults` with four tables:

| Table | Contents |
| --- | --- |
| `curves` | `model`, `fpr`, `tpr`, and `threshold` in sklearn curve order; the initial threshold is infinity. |
| `metrics` | Full-precision `auc`, `method`, `pos_label`, and sample counts per model. |
| `bands` | `fpr`, `lower`, `upper`, `ci_level`, and `method` per model; empty unless `ci_show=True`. |
| `comparisons` | Compared models and AUCs, `pvalue_raw`, `pvalue_adjusted`, `method`, `p_adjust`, `family_size`, and sample counts. Empty unless pairs are requested. |

ROC truth remains encoded as 0/1, with 1 positive. Scores may be any finite real
numbers; larger scores indicate the positive class. The default sklearn ROC
coordinates omit redundant intermediate points. AUC is trapezoidal ROC area.
Bands retain the existing deterministic, stratified 1,000-sample pointwise 95%
bootstrap on 101 false-positive-rate grid points; they are neither simultaneous
bands nor AUC confidence intervals. Comparisons remain paired, two-sided DeLong
tests. `p_adjust` corrects the requested pairs as one family and adjusted p-values
equal raw p-values when no correction is requested. DeLong comparisons require
at least two observations of each class. Existing labels and axes returns are
unchanged.

### Precision and recall

`precisionrecallplot` draws recall on the x-axis and precision on the y-axis,
both as fractions from 0 to 1. Its reference line is positive-class prevalence.
Legend labels explicitly report **AP**, sklearn average precision: a sum of
precision values weighted by increases in recall, not trapezoidal PR area.
The initial implementation has no PR confidence bands or comparison tests.

`get_precision_recall_results(ax)` returns `PrecisionRecallResults` with
`curves` (`model`, `recall`, `precision`, `threshold`) and `metrics`
(`model`, `average_precision`, `prevalence`, `method`, `pos_label`, and counts).
Coordinates preserve sklearn's order of increasing thresholds and decreasing
recall. The final precision=1, recall=0 endpoint has a missing threshold.

### Probability calibration

Pass held-out or out-of-fold positive-class probabilities to `calibrationplot`;
it never fits, refits, or recalibrates a model. The x-axis is mean predicted
probability, the y-axis is observed positive-class frequency, and the diagonal
is ideal calibration. Both axes use fractions from 0 to 1.

`n_bins` defaults to 5. `strategy="uniform"` uses equal-width bins on `[0, 1]`;
`strategy="quantile"` uses each model's empirical quantiles. Quantile bin edges
can repeat with tied predictions, so counts need not be equal. Interior-edge
values belong to the bin on their left; the first bin includes its lower edge.
Endpoint probabilities 0 and 1 are accepted.

`get_calibration_results(ax)` returns `CalibrationResults`. Its `bins` table
contains `model`, zero-based `bin`, `bin_lower`, `bin_upper`, `count`,
`mean_predicted_probability`, and `observed_frequency`. Every requested bin is
included; empty bins have count 0 and missing means and are omitted from curves.
The `metrics` table contains `brier_score`, `method`, `pos_label`, counts,
`strategy`, and `n_bins` per model. The binary Brier score is the mean squared
probability error, measuring overall probabilistic prediction quality rather
than calibration alone. `brier_show=False` hides its legend value while keeping
the score available in results.

### Input and snapshot policies

Both new plots accept `pos_label` (default 1), including string labels. Scores
must refer to that class; changing `pos_label` does not invert the supplied
scores. Both classes must be observed. Missing truth/scores and nonfinite,
nonnumeric, complex, or Boolean scores are rejected without dropping rows.
Precision–recall accepts unbounded decision scores; calibration requires
probabilities in `[0, 1]`. The input DataFrame is left unchanged. The metrics
tables record `n`, `n_positive`, and `n_negative` for the shared observations.

Each accessor returns copies of the stored tables. A later call to the same
plotter on the same axes replaces its snapshot. Axes without a corresponding
plot, or whose stored plot artists have been removed, return empty tables with
the same columns. Omitting `ax` selects the current axes.

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   get_roc_results
   get_precision_recall_results
   get_calibration_results
```

## Statistical Models

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   CoxModel
   LogisticModel
   prerank
```

## Figure & Layout Utilities

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   figure
   savefig
   multipanel
   add_panel_label
   take_legend_out
```

## Example Datasets

The gallery datasets are bundled with cnsplots, so loading them does not
require network access.

Discover the packaged tabular datasets without loading them:

```python
import cnsplots as cns

cns.datasets.get_dataset_names()
# ['flights', 'fmri', 'iris', 'penguins', 'tips']
tips = cns.datasets.load_dataset("tips")
```

Showcase results support named access as well as the existing positional
indexing and unpacking. The default `ShowcaseData` has 13 fields;
`include_showcase_images=True` returns `ShowcaseDataWithImages` with the same
fields followed by `showcase_images` as the 14th field. Both modes generate
all showcase datasets, so named access selects from the complete result:

```python
survival_df = cns.datasets.get_showcase_data().survival_df
showcase = cns.datasets.get_showcase_data(include_showcase_images=True)
images = showcase.showcase_images
```

```{eval-rst}
.. currentmodule:: cnsplots.datasets
.. apirootsummary::
   :toctree: api
   :nosignatures:

   load_dataset
   get_dataset_names
   get_showcase_data
   ShowcaseData
   ShowcaseDataWithImages
```

## Configuration & Setup

```{eval-rst}
.. currentmodule:: cnsplots
.. apirootsummary::
   :toctree: api
   :nosignatures:

   setup_matplotlib
   setup_scanpy
   setup_ax
   setup_ggplot
```

## Settings

`cnsplots` exposes its package-wide defaults through `cns.settings`.
Use it to inspect current defaults, set global styling and helper behavior,
restore package defaults with `cns.settings.reset()`, or apply temporary
overrides with `cns.settings.context(...)`.

```python
print(cns.settings)
cns.settings.title_fontsize = 10

with cns.settings.context(palette_qual="Dark2", figure_width=200):
    ...

cns.settings.reset()
```

See the {doc}`settings reference <settings>` for the full catalog of settings
and the runnable {doc}`settings example <examples/settings>` for end-to-end
usage.

```{toctree}
:hidden: true

settings
```

## Color Palettes

Discover built-in and registered cnsplots palettes, optionally filtering by
`"qualitative"` or `"continuous"`. Names available only in Matplotlib or Seaborn
are outside this registry.

```python
cns.available_palettes()
cns.available_palettes(kind="qualitative")
cns.available_palettes(kind="continuous")
```

Register a nonempty sequence of Matplotlib-compatible colors to reuse a
qualitative palette by name. Registration copies the colors and lasts for the
current Python process. Existing cnsplots and Matplotlib palette names cannot
be overwritten.

```python
cns.register_palette("MyLab", ["#4477AA", "#EE6677", "#228833"])
colors = cns.palettes("MyLab")
cns.figure(color_cycle="MyLab")
```

Use `get_palette_colors()` to select colors by zero-based index from a named
palette or an explicit color sequence. It returns hex strings and defaults to
`"Set1"` when `palette` is omitted or `None`. The original
`get_hexcolors_from_apalette()` name remains supported, including its `alist`
keyword.

```python
cns.get_palette_colors([0, 2])
cns.get_palette_colors(indices=[2, 0], palette="MyLab")
cns.get_palette_colors([1], palette=["red", "blue"])
cns.get_hexcolors_from_apalette(alist=[0, 2], palette="Set1")
```

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   palettes
   available_palettes
   register_palette
   get_palette_colors
   get_hexcolors_from_apalette
```

## Constants

The following color constants are available:

- `RED` - #D6372E
- `BLUE` - #5189BB
- `GREEN` - #70B460
- `PURPLE` - #985EA8
- `ORANGE` - #F08F35
- `YELLOW` - #FADD4B
- `BROWN` - #9C5732
- `PINK` - #E787E5
- `GRAY` - #A3A3A3
- `VIOLET` - #442288
- `CHOCOLATE` - #662506
