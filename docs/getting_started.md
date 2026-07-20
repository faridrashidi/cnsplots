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
