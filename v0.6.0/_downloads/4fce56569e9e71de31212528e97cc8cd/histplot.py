"""
Histogram
---------

Create histograms for visualizing data distributions.

Histograms bin continuous data and display frequencies, providing
a direct view of the underlying distribution shape.
"""

# %%
# Load data
# ~~~~~~~~~
import numpy as np
import pandas as pd

import cnsplots as cns

iris = cns.datasets.load_dataset("iris")
tips = cns.datasets.load_dataset("tips")


# %%
# Basic histogram
# ~~~~~~~~~~~~~~~
# Simple histogram of a single variable.
cns.figure(100, 100)
ax = cns.histplot(data=tips, x="total_bill")
ax.set_title("Basic Histogram")


# %%
# Histogram with custom bins
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Control the number of bins.
mp = cns.multipanel(max_width=420)

mp.panel("A", 100, 80)
cns.histplot(data=tips, x="total_bill", bins=10)
mp.get_axes("A").set_title("10 bins")

mp.panel("B", 100, 80)
cns.histplot(data=tips, x="total_bill", bins=20)
mp.get_axes("B").set_title("20 bins")

mp.panel("C", 100, 80)
cns.histplot(data=tips, x="total_bill", bins=30)
mp.get_axes("C").set_title("30 bins")


# %%
# Histogram with KDE overlay
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Add kernel density estimate with ``kde=True``.
cns.figure(100, 100)
ax = cns.histplot(data=tips, x="total_bill", kde=True)
ax.set_title("Histogram with KDE")


# %%
# Grouped histogram with hue
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare distributions across groups.
cns.figure(100, 100)
ax = cns.histplot(data=tips, x="total_bill", hue="sex")
ax.set_title("Histogram by Sex")
cns.take_legend_out()


# %%
# Stacked histogram
# ~~~~~~~~~~~~~~~~~
# Stack bars for grouped data with ``multiple="stack"``.
cns.figure(100, 100)
ax = cns.histplot(data=tips, x="total_bill", hue="sex", multiple="stack")
ax.set_title("Stacked Histogram")
cns.take_legend_out()


# %%
# Dodged histogram
# ~~~~~~~~~~~~~~~~
# Side-by-side bars with ``multiple="dodge"``.
cns.figure(100, 100)
ax = cns.histplot(data=tips, x="total_bill", hue="sex", multiple="dodge")
ax.set_title("Dodged Histogram")
cns.take_legend_out()


# %%
# Layered histogram
# ~~~~~~~~~~~~~~~~~
# Overlapping transparent bars with ``multiple="layer"``.
cns.figure(100, 100)
ax = cns.histplot(data=tips, x="total_bill", hue="sex", multiple="layer", alpha=0.5)
ax.set_title("Layered Histogram")
cns.take_legend_out()


# %%
# Histogram with step style
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Show outline only with ``element="step"``.
cns.figure(100, 100)
ax = cns.histplot(data=tips, x="total_bill", element="step")
ax.set_title("Step Histogram")


# %%
# Histogram with step and fill
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Filled step histogram for cleaner look.
cns.figure(100, 100)
ax = cns.histplot(
    data=tips, x="total_bill", hue="sex", element="step", fill=True, alpha=0.5
)
ax.set_title("Filled Step Histogram")
cns.take_legend_out()

# %%
# Histogram with density normalization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Normalize to show probability density with ``stat="density"``.
cns.figure(100, 100)
ax = cns.histplot(data=tips, x="total_bill", stat="density")
ax.set_title("Density Histogram")
ax.set_ylabel("Density")


# %%
# Histogram with probability normalization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Show proportion with ``stat="probability"``.
cns.figure(100, 100)
ax = cns.histplot(data=tips, x="total_bill", stat="probability")
ax.set_title("Probability Histogram")
ax.set_ylabel("Probability")


# %%
# 2D histogram (heatmap)
# ~~~~~~~~~~~~~~~~~~~~~~
# Visualize joint distribution of two variables.
cns.figure(150, 100)
ax = cns.histplot(
    data=iris, x="sepal_length", y="sepal_width", cbar=True, cmap="gnuplot"
)
ax.set_title("2D Histogram (gnuplot)")


# %%
# 2D histogram with parula colormap
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use cnsplots parula colormap.
cns.figure(150, 100)
ax = cns.histplot(
    data=iris, x="sepal_length", y="sepal_width", cbar=True, cmap="parula"
)
ax.set_title("2D Histogram (parula)")


# %%
# 2D histogram with different colormaps
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare colormap options.
mp = cns.multipanel(max_width=380)

mp.panel("A", 120, 120, margin_right=30)
cns.histplot(data=iris, x="sepal_length", y="sepal_width", cbar=True, cmap="hot")
mp.get_axes("A").set_title("hot colormap")

mp.panel("B", 120, 120)
cns.histplot(
    data=iris, x="sepal_length", y="sepal_width", cbar=True, cmap="BuRd_custom"
)
mp.get_axes("B").set_title("BuRd_custom colormap")


# %%
# Histogram with custom palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use built-in color palettes.
cns.figure(100, 100, "Tableau")
ax = cns.histplot(data=tips, x="total_bill", hue="day")
ax.set_title("Tableau Palette")
cns.take_legend_out()


# %%
# Histogram comparison across species
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare distributions across multiple groups.
cns.figure(100, 100)
ax = cns.histplot(
    data=iris, x="sepal_length", hue="species", multiple="layer", alpha=0.5
)
ax.set_title("Sepal Length Distribution by Species")
cns.take_legend_out()


# %%
# Horizontal histogram
# ~~~~~~~~~~~~~~~~~~~~
# Swap x and y for horizontal orientation.
cns.figure(150, 100)
ax = cns.histplot(data=tips, y="total_bill", bins=15)
ax.set_title("Horizontal Histogram")


# %%
# Histogram with discrete data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# For discrete/categorical counts, use ``discrete=True``.
cns.figure(100, 100)
ax = cns.histplot(data=tips, x="size", discrete=True)
ax.set_title("Discrete Histogram")
ax.set_xlabel("Party Size")


# %%
# Log-scale histogram
# ~~~~~~~~~~~~~~~~~~~
# Use log scale for skewed distributions.
np.random.seed(42)
log_data = pd.DataFrame({"value": np.random.lognormal(3, 1, 1000)})

mp = cns.multipanel(max_width=320)

mp.panel("A", 120, 80)
cns.histplot(data=log_data, x="value", bins=30)
mp.get_axes("A").set_title("Linear Scale")

mp.panel("B", 120, 80, margin_right=0)
cns.histplot(data=log_data, x="value", bins=30, log_scale=True)
mp.get_axes("B").set_title("Log Scale")
