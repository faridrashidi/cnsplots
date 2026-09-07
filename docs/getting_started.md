# Getting Started

This guide will help you create your first publication-ready figure with cnsplots.

## Quick Start

```python
import cnsplots as cns
import matplotlib.pyplot as plt

# Load example data
df = cns.datasets.load_dataset("tips")

# Create a figure with specific dimensions (width x height in pixels)
fig = cns.figure(100, 150)

# Create a boxplot
cns.boxplot(data=df, x="day", y="total_bill")

# Save the figure
cns.savefig("my_figure.svg", fig=fig)
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

`cns.figure(...)` returns the created `matplotlib.figure.Figure` and makes it
the current figure, so subsequent cnsplots calls still draw on it. Keep this
handle to save it later, even after creating another figure:

```python
fig = cns.figure(150, 100)
cns.boxplot(data=df, x="day", y="total_bill")
cns.figure(150, 100)
cns.barplot(data=df, x="day", y="tip")
cns.savefig("boxplot.svg", fig=fig)
```

Previously, `cns.figure(...)` returned `None`. Calls that ignore the return value
continue to work, but code that checks for `None` or uses the result as a boolean
must be updated for the returned `Figure`.

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
cns.savefig("subplots.svg", fig=fig)
```

All plotting functions accept `ax` as a keyword-only argument, so they can be
composed into an existing Matplotlib layout. Most return the target
`matplotlib.axes.Axes`. `heatmapplot`, `dotplot`, `upsetplot`, and `vennplot`
retain their backend-native return objects so callers can access their
multi-panel layout or diagram elements.

## Saving Figures

For publication, save figures in vector formats:

```python
# SVG - editable in Adobe Illustrator
cns.savefig("figure.svg")

# PDF - maintains vector quality
cns.savefig("figure.pdf")

# PNG for presentations or raster workflows
cns.savefig("figure.png", dpi=300, transparent=False)
```

By default, `cns.savefig(...)` saves the current figure. Pass `fig=fig` to save
a retained `Figure` without changing which figure is current. Export options
are keyword-only and apply to that save without changing `cns.settings`:

```python
# Tight crop with 0.1 inches of padding around the plotted contents
cns.savefig("figure-tight.pdf", bbox_inches="tight", pad_inches=0.1)

# Preserve the full figure canvas without cropping
cns.savefig("figure-full.png", bbox_inches=None)

# Export a specific rectangle in inches: left, bottom, width, height
from matplotlib.transforms import Bbox

cns.savefig("figure-region.pdf", bbox_inches=Bbox.from_bounds(0, 0, 1, 1))
```

Omitting `dpi`, `transparent`, `bbox_inches`, or `pad_inches` uses the matching
export default in {doc}`settings`. Passing `None` for `dpi`, `transparent`, or
`pad_inches` also uses the setting; explicit `bbox_inches=None` instead disables
cropping. Padding applies only to `bbox_inches="tight"` and is ignored for
`None` or a `Bbox`. Raster output dimensions depend on the figure's size in
inches, export DPI, and any crop or padding; export DPI does not resize the
figure itself.

If MuPDF's `mutool` is available, `cnsplots` uses an enhanced SVG export path
for Illustrator workflows. Otherwise it saves a standard matplotlib SVG and
warns instead of failing.

## Next Steps

- Browse the {doc}`examples/index` for more detailed examples
- Check the {doc}`api` for all available functions
- See {doc}`installation` for advanced setup options
