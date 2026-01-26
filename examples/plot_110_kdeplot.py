"""
kdeplot
-------

Create kernel density estimation (KDE) plots for visualizing distributions.

KDE plots show the estimated probability density function of a continuous
variable, providing a smooth representation of the data distribution.
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
# Basic KDE plot
# ~~~~~~~~~~~~~~
# Simple density estimation with mode line.
cns.figure(150, 100)
cns.kdeplot(data=tips, x="total_bill", add_mode=True)
plt.title("Basic KDE with Mode Line")


# %%
# KDE plot without mode line
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Density curve only.
cns.figure(150, 100)
cns.kdeplot(data=tips, x="total_bill", add_mode=False)
plt.title("KDE without Mode")


# %%
# Grouped KDE plot with hue
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare distributions across groups.
cns.figure(150, 100)
cns.kdeplot(data=tips, x="total_bill", hue="sex")
cns.take_legend_out()
plt.title("KDE by Sex")


# %%
# KDE plot with multiple groups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare more than two groups.
cns.figure(150, 100)
cns.kdeplot(data=tips, x="total_bill", hue="day")
cns.take_legend_out()
plt.title("KDE by Day")


# %%
# Filled KDE plot
# ~~~~~~~~~~~~~~~
# Fill the area under the curve with ``fill=True``.
cns.figure(150, 100)
cns.kdeplot(data=tips, x="total_bill", fill=True, alpha=0.5)
plt.title("Filled KDE")


# %%
# Filled grouped KDE plot
# ~~~~~~~~~~~~~~~~~~~~~~~
# Filled density curves for multiple groups.
cns.figure(150, 100)
cns.kdeplot(data=tips, x="total_bill", hue="sex", fill=True, alpha=0.3)
cns.take_legend_out()
plt.title("Filled Grouped KDE")


# %%
# Cumulative KDE plot
# ~~~~~~~~~~~~~~~~~~~
# Show cumulative distribution with ``cumulative=True``.
cns.figure(150, 100)
cns.kdeplot(data=tips, x="total_bill", cumulative=True)
plt.title("Cumulative KDE (CDF)")
plt.ylabel("Cumulative Probability")


# %%
# Cumulative grouped KDE
# ~~~~~~~~~~~~~~~~~~~~~~
# Compare cumulative distributions.
cns.figure(150, 100)
cns.kdeplot(data=tips, x="total_bill", hue="sex", cumulative=True)
cns.take_legend_out()
plt.title("Cumulative KDE by Sex")


# %%
# KDE with different bandwidth
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Adjust smoothness with ``bw_adjust``.
mp = cns.multipanel((1, 3), max_width=450, hgap=30)

mp.panel("A", 80, 110)
cns.kdeplot(data=tips, x="total_bill", bw_adjust=0.3)
mp.get_axes("A").set_title("bw_adjust=0.3 (rough)")

mp.panel("B", 80, 110)
cns.kdeplot(data=tips, x="total_bill", bw_adjust=1.0)
mp.get_axes("B").set_title("bw_adjust=1.0 (default)")

mp.panel("C", 80, 110)
cns.kdeplot(data=tips, x="total_bill", bw_adjust=2.0)
mp.get_axes("C").set_title("bw_adjust=2.0 (smooth)")


# %%
# KDE with line styles
# ~~~~~~~~~~~~~~~~~~~~
# Customize line width and style.
mp = cns.multipanel((1, 2), max_width=350, hgap=40)

mp.panel("A", 80, 120)
cns.kdeplot(data=tips, x="total_bill", linewidth=0.5)
mp.get_axes("A").set_title("Thin line")

mp.panel("B", 80, 120)
cns.kdeplot(data=tips, x="total_bill", linewidth=2)
mp.get_axes("B").set_title("Thick line")


# %%
# KDE plot with custom palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use different color palettes.
cns.figure(150, 100, "Tableau")
cns.kdeplot(data=tips, x="total_bill", hue="day", fill=True, alpha=0.3)
cns.take_legend_out()
plt.title("Tableau Palette")


# %%
# Multiple KDE comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Compare distributions across different variables.
mp = cns.multipanel((1, 2), max_width=350, hgap=40)

mp.panel("A", 80, 120)
cns.kdeplot(data=iris, x="sepal_length", hue="species")
mp.get_axes("A").legend().remove()
mp.get_axes("A").set_title("Sepal Length")

mp.panel("B", 80, 120)
cns.kdeplot(data=iris, x="petal_length", hue="species")
mp.get_axes("B").legend().remove()
mp.get_axes("B").set_title("Petal Length")


# %%
# 2D KDE plot (bivariate)
# ~~~~~~~~~~~~~~~~~~~~~~~
# Visualize joint distribution of two variables.
cns.figure(150, 150)
cns.kdeplot(data=iris, x="sepal_length", y="sepal_width")
plt.title("2D KDE")


# %%
# 2D KDE with filled contours
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Fill the 2D density contours.
cns.figure(150, 150)
cns.kdeplot(data=iris, x="sepal_length", y="sepal_width", fill=True, cmap="parula")
plt.title("Filled 2D KDE")


# %%
# 2D KDE by group
# ~~~~~~~~~~~~~~~
# Compare bivariate distributions across groups.
cns.figure(150, 150)
cns.kdeplot(data=iris, x="sepal_length", y="sepal_width", hue="species")
cns.take_legend_out()
plt.title("2D KDE by Species")


# %%
# KDE for comparing distributions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Visual comparison of different groups.
np.random.seed(42)
comparison_data = pd.DataFrame(
    {
        "value": np.concatenate(
            [
                np.random.normal(10, 2, 200),
                np.random.normal(15, 3, 200),
                np.random.normal(12, 1.5, 200),
            ]
        ),
        "group": ["A"] * 200 + ["B"] * 200 + ["C"] * 200,
    }
)

cns.figure(150, 100, "Bold")
cns.kdeplot(data=comparison_data, x="value", hue="group", fill=True, alpha=0.3)
cns.take_legend_out()
plt.title("Group Distribution Comparison")


# %%
# KDE with vertical reference lines
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Add mean/median reference lines.
cns.figure(150, 100)
cns.kdeplot(data=tips, x="total_bill")

ax = plt.gca()
mean_val = tips["total_bill"].mean()
median_val = tips["total_bill"].median()
ax.axvline(
    mean_val, color="red", linestyle="--", linewidth=0.8, label=f"Mean: {mean_val:.1f}"
)
ax.axvline(
    median_val,
    color="blue",
    linestyle=":",
    linewidth=0.8,
    label=f"Median: {median_val:.1f}",
)
plt.legend(fontsize=7)
plt.title("KDE with Mean and Median")
