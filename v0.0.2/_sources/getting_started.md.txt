# Getting Started

This guide will help you create your first publication-ready figure with cnsplots.

## Quick Start

```python
import cnsplots as cns
import seaborn as sns
import matplotlib.pyplot as plt

# Load example data
df = sns.load_dataset("tips")

# Create a figure with specific dimensions (width x height in pixels)
cns.figure(150, 100)

# Create a boxplot
cns.boxplot(data=df, x="day", y="total_bill")

# Save the figure
cns.savefig("my_figure.svg")
```

## Understanding Figure Dimensions

cnsplots uses **pixels** for figure dimensions:

```python
# Small figure
cns.figure(100, 80)

# Larger figure
cns.figure(200, 150)
```

## Basic Plot Types

### Boxplot

```python
cns.figure(100, 80)
cns.boxplot(data=df, x="day", y="total_bill", hue="sex")
cns.savefig("boxplot.svg")
```

### Barplot

```python
cns.figure(100, 80)
cns.barplot(data=df, x="day", y="total_bill", hue="sex")
cns.savefig("barplot.svg")
```

### Scatter Plot

```python
cns.figure(100, 80)
cns.scatterplot(data=df, x="total_bill", y="tip", hue="day")
cns.savefig("scatter.svg")
```

## Customizing Plots

### Adding Labels

```python
cns.figure(100, 80)
cns.boxplot(data=df, x="day", y="total_bill")
plt.xlabel("Day of Week")
plt.ylabel("Total Bill ($)")
plt.title("Tips by Day")
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
