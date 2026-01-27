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
plt.savefig("my_figure.svg")
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
plt.savefig("boxplot.svg")
```

### Barplot

```python
cns.figure(100, 80)
cns.barplot(data=df, x="day", y="total_bill", hue="sex")
plt.savefig("barplot.svg")
```

### Scatter Plot

```python
cns.figure(100, 80)
cns.scatterplot(data=df, x="total_bill", y="tip", hue="day")
plt.savefig("scatter.svg")
```

## Customizing Plots

### Adding Labels

```python
cns.figure(100, 80)
cns.boxplot(data=df, x="day", y="total_bill")
plt.xlabel("Day of Week")
plt.ylabel("Total Bill ($)")
plt.title("Tips by Day")
plt.savefig("labeled_plot.svg")
```

### Working with Subplots

```python
fig, axes = cns.subplots(1, 2, figsize=(170, 80))

cns.boxplot(data=df, x="day", y="total_bill", ax=axes[0])
axes[0].set_title("Box Plot")

cns.barplot(data=df, x="day", y="total_bill", ax=axes[1])
axes[1].set_title("Bar Plot")

plt.tight_layout()
plt.savefig("subplots.svg")
```

## Saving Figures

For publication, save figures in vector formats:

```python
# SVG - editable in Adobe Illustrator
plt.savefig("figure.svg")

# PDF - maintains vector quality
plt.savefig("figure.pdf")

# High-resolution PNG (300 DPI)
plt.savefig("figure.png", dpi=300)
```

## Next Steps

- Browse the {doc}`examples/index` for more detailed examples
- Check the {doc}`api` for all available functions
- See {doc}`installation` for advanced setup options
