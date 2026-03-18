"""
scatterplot
-----------

Create scatter plots for visualizing relationships between continuous variables.

Scatter plots are essential for exploring correlations, clusters, and patterns
in bivariate data. cnsplots provides publication-ready scatter plots with
flexible customization options.
"""

# %%
# Load data
# ~~~~~~~~~
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

import cnsplots as cns

iris = sns.load_dataset("iris")
tips = sns.load_dataset("tips")


# %%
# Basic scatter plot
# ~~~~~~~~~~~~~~~~~~
# Simple scatter plot showing relationship between two variables.
cns.figure(120, 120)
ax = cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=7)
ax.set_title("Basic Scatter Plot")
ax.set_xlabel("Sepal Length (cm)")
ax.set_ylabel("Sepal Width (cm)")


# %%
# Scatter plot with hue
# ~~~~~~~~~~~~~~~~~~~~~
# Color points by a categorical variable using ``hue``.
cns.figure(120, 120)
ax = cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=7, hue="species")
ax.set_title("Scatter Plot with Groups")
ax.set_xlabel("Sepal Length (cm)")
ax.set_ylabel("Sepal Width (cm)")
cns.take_legend_out()


# %%
# Scatter plot with legend inside
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Keep the legend inside the plot area.
cns.figure(150, 120)
ax = cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=7, hue="species")
ax.legend(loc="upper left")
ax.set_title("Legend Inside Plot")


# %%
# Scatter plot with varying point sizes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Adjust point size with the ``s`` parameter.
mp = cns.multipanel(max_width=450)

mp.panel("A", 90, 90)
cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=3)
mp.get_axes("A").set_title("s=3 (small)")

mp.panel("B", 90, 90)
cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=10)
mp.get_axes("B").set_title("s=10 (medium)")

mp.panel("C", 90, 90)
cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=25)
mp.get_axes("C").set_title("s=25 (large)")


# %%
# Scatter plot with transparency
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``alpha`` for overlapping points.
mp = cns.multipanel(max_width=350)

mp.panel("A", 100, 120)
cns.scatterplot(data=tips, x="total_bill", y="tip", s=15, alpha=1.0)
mp.get_axes("A").set_title("alpha=1.0 (opaque)")

mp.panel("B", 100, 120)
cns.scatterplot(data=tips, x="total_bill", y="tip", s=15, alpha=0.4)
mp.get_axes("B").set_title("alpha=0.4 (transparent)")


# %%
# Scatter plot with custom palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use different color palettes.
cns.figure(120, 120, "Tableau")
ax = cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=10, hue="species")
ax.set_title("Tableau Palette")
cns.take_legend_out()


# %%
# Scatter plot with custom colors
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Pass specific colors via ``palette``.
custom_palette = {
    "setosa": cns.RED,
    "versicolor": cns.GREEN,
    "virginica": cns.BLUE,
}
cns.figure(120, 120)
ax = cns.scatterplot(
    data=iris,
    x="sepal_length",
    y="sepal_width",
    s=10,
    hue="species",
    palette=custom_palette,
)
ax.set_title("Custom Color Palette")
cns.take_legend_out()


# %%
# Scatter plot with style by category
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use different marker styles with ``style``.
cns.figure(150, 120)
ax = cns.scatterplot(
    data=iris,
    x="sepal_length",
    y="sepal_width",
    s=15,
    hue="species",
    style="species",
)
ax.set_title("Different Markers by Group")
cns.take_legend_out()


# %%
# Scatter plot with size encoding
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Map a variable to point size using ``size``.
cns.figure(150, 120)
ax = cns.scatterplot(
    data=tips,
    x="total_bill",
    y="tip",
    hue="day",
    size="size",
    sizes=(20, 200),
)
ax.set_title("Size Encoding")
cns.take_legend_out()


# %%
# Scatter plot with reference lines
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Add horizontal and vertical reference lines.
cns.figure(120, 120)
ax = cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=7, hue="species")
ax.axhline(y=iris["sepal_width"].mean(), color="gray", linestyle="--", linewidth=0.8)
ax.axvline(x=iris["sepal_length"].mean(), color="gray", linestyle="--", linewidth=0.8)
ax.set_title("With Reference Lines")
cns.take_legend_out()


# %%
# Scatter plot with quadrant labels
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Add annotations to different regions.
cns.figure(140, 120)
ax = cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=7, hue="species")

mean_x = iris["sepal_length"].mean()
mean_y = iris["sepal_width"].mean()
ax.axhline(y=mean_y, color="gray", linestyle="--", linewidth=0.5)
ax.axvline(x=mean_x, color="gray", linestyle="--", linewidth=0.5)

# Add quadrant labels
ax.text(7.5, 4.2, "Q1", fontsize=8, ha="center", color="gray")
ax.text(5.0, 4.2, "Q2", fontsize=8, ha="center", color="gray")
ax.text(5.0, 2.2, "Q3", fontsize=8, ha="center", color="gray")
ax.text(7.5, 2.2, "Q4", fontsize=8, ha="center", color="gray")

ax.set_title("Quadrant Analysis")
cns.take_legend_out()


# %%
# Scatter plot matrix concept (single comparison)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare different variable pairs.
mp = cns.multipanel(max_width=350)

labels = ["A", "B", "C", "D"]
label_idx = 0
for var_y in ["sepal_width", "petal_width"]:
    for var_x in ["sepal_length", "petal_length"]:
        mp.panel(labels[label_idx], 100, 120)
        cns.scatterplot(data=iris, x=var_x, y=var_y, s=5, hue="species")
        mp.get_axes(labels[label_idx]).set_xlabel(var_x.replace("_", " ").title())
        mp.get_axes(labels[label_idx]).set_ylabel(var_y.replace("_", " ").title())
        mp.get_axes(labels[label_idx]).legend().remove()
        label_idx += 1


# %%
# Large dataset scatter plot with rasterization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``rasterized=True`` for large datasets to reduce file size.
np.random.seed(42)
large_data = pd.DataFrame(
    {
        "x": np.random.randn(5000),
        "y": np.random.randn(5000),
        "group": np.random.choice(["A", "B", "C"], 5000),
    }
)

cns.figure(120, 120)
ax = cns.scatterplot(
    data=large_data,
    x="x",
    y="y",
    s=3,
    hue="group",
    alpha=0.5,
    rasterized=True,
)
ax.set_title("Large Dataset (Rasterized)")
cns.take_legend_out()


# %%
# Scatter plot with marginal annotations
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Add correlation coefficient as annotation.
cns.figure(120, 120)
ax = cns.scatterplot(data=tips, x="total_bill", y="tip", s=10, alpha=0.6)

r, p = stats.pearsonr(tips["total_bill"], tips["tip"])
ax.text(
    0.05,
    0.95,
    f"r = {r:.3f}\np = {p:.2e}",
    transform=ax.transAxes,
    fontsize=7,
    verticalalignment="top",
)

ax.set_title("With Correlation Stats")
ax.set_xlabel("Total Bill ($)")
ax.set_ylabel("Tip ($)")
