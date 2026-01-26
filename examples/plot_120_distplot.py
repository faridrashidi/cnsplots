"""
distplot
--------

Create distribution plots combining histograms with KDE curves.

Distribution plots provide a comprehensive view of data distributions
by overlaying kernel density estimates on histograms.
"""

# %%
# Load data
# ~~~~~~~~~
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")
iris = sns.load_dataset("iris")


# %%
# Basic distribution plot
# ~~~~~~~~~~~~~~~~~~~~~~~
# Histogram with KDE overlay.
cns.figure(150, 100)
cns.distplot(data=tips, x="total_bill")
plt.title("Basic Distribution Plot")


# %%
# Grouped distribution plot
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare distributions across groups using ``hue``.
cns.figure(150, 100)
cns.distplot(data=tips, x="total_bill", hue="sex")
cns.take_legend_out()
plt.title("Distribution by Sex")


# %%
# Distribution plot with multiple groups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare more than two groups.
cns.figure(150, 100, "Tableau")
cns.distplot(data=tips, x="total_bill", hue="day")
cns.take_legend_out()
plt.title("Distribution by Day")


# %%
# Distribution comparison for iris dataset
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare species distributions.
cns.figure(150, 100)
cns.distplot(data=iris, x="sepal_length", hue="species")
cns.take_legend_out()
plt.title("Sepal Length Distribution")


# %%
# Side-by-side distribution comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare different variables.
mp = cns.multipanel((1, 2), max_width=400, hgap=40)

mp.panel("A", 80, 140)
cns.distplot(data=iris, x="sepal_length", hue="species")
mp.get_axes("A").legend().remove()
mp.get_axes("A").set_title("Sepal Length")

mp.panel("B", 80, 140)
cns.distplot(data=iris, x="petal_length", hue="species")
mp.get_axes("B").legend().remove()
mp.get_axes("B").set_title("Petal Length")


# %%
# Distribution plot with different palettes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Showcase color palette options.
mp = cns.multipanel((1, 2), max_width=400, hgap=40)

mp.panel("A", 80, 140, color_cycle="Set2")
cns.distplot(data=tips, x="total_bill", hue="sex")
mp.get_axes("A").legend().remove()
mp.get_axes("A").set_title("Set2 Palette")

mp.panel("B", 80, 140, color_cycle="Bold")
cns.distplot(data=tips, x="total_bill", hue="sex")
mp.get_axes("B").legend().remove()
mp.get_axes("B").set_title("Bold Palette")


# %%
# Distribution of tips by time
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare lunch vs dinner distributions.
cns.figure(150, 100)
cns.distplot(data=tips, x="tip", hue="time")
cns.take_legend_out()
plt.title("Tip Distribution by Time")


# %%
# Distribution plot for synthetic data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Demonstrate with different distribution shapes.
np.random.seed(42)
synthetic = pd.DataFrame(
    {
        "value": np.concatenate(
            [
                np.random.normal(0, 1, 500),
                np.random.normal(3, 0.5, 500),
            ]
        ),
        "group": ["Normal (μ=0, σ=1)"] * 500 + ["Normal (μ=3, σ=0.5)"] * 500,
    }
)

cns.figure(180, 100)
cns.distplot(data=synthetic, x="value", hue="group")
cns.take_legend_out()
plt.title("Comparing Two Distributions")
