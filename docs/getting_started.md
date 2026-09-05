# Getting Started

This guide will help you create your first publication-ready figure with cnsplots.

## Quick Start

```python
import cnsplots as cns
import matplotlib.pyplot as plt

# Load example data
df = cns.datasets.load_dataset("tips")

# Create a figure with specific dimensions (width x height in pixels)
cns.figure(100, 150)

# Create a boxplot
cns.boxplot(data=df, x="day", y="total_bill")

# Save the figure
cns.savefig("my_figure.svg")
```

In these examples, `data` is a pandas DataFrame, and `x`, `y`, and `hue`
refer to column names in that DataFrame.

## Understanding Figure Dimensions

cnsplots uses **pixels** for figure dimensions:

```python
# Small figure: 80 px wide and 100 px tall
cns.figure(80, 100)

# Larger figure: 150 px wide and 200 px tall
cns.figure(150, 200)
```

`cns.figure(width, height)` uses the conventional width-first order, and those
values are the final canvas size in pixels.

## Basic Plot Types

### Boxplot

```python
cns.figure(80, 100)
cns.boxplot(data=df, x="day", y="total_bill", hue="sex")
cns.savefig("boxplot.svg")
```

### Barplot

```python
cns.figure(80, 100)
cns.barplot(data=df, x="day", y="total_bill", hue="sex")
cns.savefig("barplot.svg")
```

### Scatter Plot

```python
cns.figure(80, 100)
cns.scatterplot(data=df, x="total_bill", y="tip", hue="day")
cns.savefig("scatter.svg")
```

## Customizing Plots

### Adding Labels

```python
cns.figure(80, 100)
ax = cns.boxplot(data=df, x="day", y="total_bill")
ax.set_xlabel("Day of Week")
ax.set_ylabel("Total Bill ($)")
ax.set_title("Tips by Day")
cns.savefig("labeled_plot.svg")
```

### Working with Subplots

```python
cns.setup_matplotlib()
fig, axes = plt.subplots(1, 2, figsize=(170 / 72, 80 / 72), dpi=144)

cns.boxplot(data=df, x="day", y="total_bill", ax=axes[0])
axes[0].set_title("Box Plot")

cns.barplot(data=df, x="day", y="total_bill", ax=axes[1])
axes[1].set_title("Bar Plot")

plt.tight_layout()
cns.savefig("subplots.svg")
```

All plotting functions accept `ax` as a keyword-only argument, so they can be
composed into an existing Matplotlib layout. Most return the target
`matplotlib.axes.Axes`. `heatmapplot`, `dotplot`, `upsetplot`, and `vennplot`
retain their backend-native return objects so callers can access their
multi-panel layout or diagram elements.

## Descriptive Survival Curves

Use `descriptive_only=True` to draw survival curves without statistical tests or
Cox model fitting. This mode supports a single group, groups with only censored
observations, and cohorts in which every event was observed. Confidence bands,
risk tables, median survival, landmark survival estimates, and restricted mean
survival time (RMST) remain available.

```python
import pandas as pd

survival_data = pd.DataFrame(
    {
        "time": [1, 2, 3, 4, 1, 2, 3, 4],
        "event": [0, 0, 0, 0, 1, 0, 1, 0],
        "group": ["A"] * 4 + ["B"] * 4,
    }
)
cns.figure(180, 150)
cns.survivalplot(
    survival_data,
    "time",
    "event",
    "group",
    descriptive_only=True,
    show_risk_table=True,
)
```

`survivalplot` accepts event codes 0 (censored) and 1 (event observed); either
code may be absent. Durations must still be finite, non-negative real numbers,
and duration, event, and group values cannot be missing.

`cumulativeincidenceplot(..., descriptive_only=True)` similarly skips Gray's
test while drawing Aalen–Johansen estimates. Its event codes always mean
0 = censored, 1 = event of interest, and 2 or higher = competing events.
These meanings do not change when a code is absent: a group with no events of
interest has a flat cumulative-incidence curve at zero. Competing events are
never recoded as censoring.

With the default `descriptive_only=False`, each requested comparison checks
whether it can be estimated. Unavailable results are marked `unavailable` on
the plot, and a `UserWarning` explains why; valid curves and other comparisons
are retained. Log-rank and Gray's tests require multiple groups, events of
interest, and a nonsingular comparison variance. An all-censored group can
still contribute to these tests. Cox results require a converged fit and finite
estimates; a two-group contrast with no events in one group is unavailable.
The two-group landmark test requires survival estimates strictly between 0
and 1. Pairwise Cox p-values remain unadjusted.

For `survivalplot`, `show_hazard_ratio=False` skips pairwise Cox fitting while
retaining the overall test. `descriptive_only=True` skips all tests, including
the landmark test, and ignores `overall_test`, `pairs`, and `show_hazard_ratio`.

## Saving Figures

For publication, save figures in vector formats:

```python
# SVG - editable in Adobe Illustrator
cns.savefig("figure.svg")

# PDF - maintains vector quality
cns.savefig("figure.pdf")

# PNG for presentations or raster workflows
cns.savefig("figure.png")
```

If MuPDF's `mutool` is available, `cnsplots` uses an enhanced SVG export path
for Illustrator workflows. Otherwise it saves a standard matplotlib SVG and
warns instead of failing.

## Next Steps

- Browse the {doc}`examples/index` for more detailed examples
- Check the {doc}`api` for all available functions
- See {doc}`installation` for advanced setup options
