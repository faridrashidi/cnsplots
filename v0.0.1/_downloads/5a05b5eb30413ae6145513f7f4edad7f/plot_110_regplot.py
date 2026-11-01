"""
regplot
-------

Create regression plots showing relationships with fitted lines.

Regression plots combine scatter plots with fitted regression lines,
making them ideal for visualizing linear relationships and comparing
trends across groups.
"""

# %%
# Load data
# ~~~~~~~~~
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

import cnsplots as cns

tips = sns.load_dataset("tips")
iris = sns.load_dataset("iris")


# %%
# Basic regression plot
# ~~~~~~~~~~~~~~~~~~~~~
# Simple scatter plot with fitted regression line.
cns.figure(150, 150)
ax = cns.regplot(data=tips, x="tip", y="total_bill")
ax.set_title("Basic Regression Plot")
ax.set_xlabel("Tip ($)")
ax.set_ylabel("Total Bill ($)")


# %%
# Grouped regression plot with hue
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Fit separate regression lines for each group.
cns.figure(150, 150)
ax = cns.regplot(data=tips, x="tip", y="total_bill", hue="sex")
cns.take_legend_out()
ax.set_title("Grouped Regression")


# %%
# Regression plot with different groups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare trends across multiple categories.
cns.figure(150, 150, "Tableau")
ax = cns.regplot(data=tips, x="tip", y="total_bill", hue="day")
cns.take_legend_out()
ax.set_title("Regression by Day")


# %%
# Regression plot with varying point sizes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Adjust point size with the ``s`` parameter.
mp = cns.multipanel(max_width=350)

mp.panel("A", 100, 120)
cns.regplot(data=tips, x="tip", y="total_bill", s=2)
mp.get_axes("A").set_title("s=2 (small)")

mp.panel("B", 100, 120)
cns.regplot(data=tips, x="tip", y="total_bill", s=10)
mp.get_axes("B").set_title("s=10 (large)")


# %%
# Regression plot with custom palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use built-in color palettes.
cns.figure(150, 150, "Set2")
ax = cns.regplot(data=tips, x="tip", y="total_bill", hue="smoker")
cns.take_legend_out()
ax.set_title("Set2 Palette")


# %%
# Multiple regression comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare regression trends across different subsets.
mp = cns.multipanel(max_width=500)

for i, day in enumerate(["Thur", "Fri", "Sat", "Sun"]):
    label = chr(65 + i)  # A, B, C, D
    mp.panel(label, 80, 100)
    subset = tips[tips["day"] == day]
    cns.regplot(data=subset, x="tip", y="total_bill", s=5)
    mp.get_axes(label).set_title(day)
    if i == 0:
        mp.get_axes(label).set_xlabel("Tip")
        mp.get_axes(label).set_ylabel("Total Bill")


# %%
# Regression plot with correlation statistics
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Add correlation coefficient and p-value annotation.
cns.figure(150, 150)
ax = cns.regplot(data=tips, x="tip", y="total_bill", s=5)

r, p = stats.pearsonr(tips["tip"], tips["total_bill"])
ax.text(
    0.05,
    0.95,
    f"r = {r:.3f}\np = {p:.2e}",
    transform=ax.transAxes,
    fontsize=7,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
)

ax.set_title("With Correlation Stats")


# %%
# Regression plot for iris data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Apply to a different dataset.
cns.figure(150, 150)
ax = cns.regplot(data=iris, x="petal_length", y="petal_width", hue="species")
cns.take_legend_out()
ax.set_title("Petal Dimensions by Species")


# %%
# Regression plot with equation annotation
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Show the regression equation on the plot.
cns.figure(150, 150)
ax = cns.regplot(data=tips, x="tip", y="total_bill", s=5)

# Calculate regression parameters
slope, intercept, r, p, se = stats.linregress(tips["tip"], tips["total_bill"])
ax.text(
    0.05,
    0.95,
    f"y = {slope:.2f}x + {intercept:.2f}\nR² = {r**2:.3f}",
    transform=ax.transAxes,
    fontsize=7,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
)

ax.set_title("With Regression Equation")
ax.set_xlabel("Tip ($)")
ax.set_ylabel("Total Bill ($)")


# %%
# Regression plot comparing smokers vs non-smokers
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare linear trends between groups.
cns.figure(150, 150, "BlueRed")
ax = cns.regplot(data=tips, x="total_bill", y="tip", hue="smoker", s=5)
cns.take_legend_out()
ax.set_title("Tipping by Smoking Status")


# %%
# Side-by-side regression comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare regressions in separate panels.
mp = cns.multipanel(max_width=350)

male_tips = tips[tips["sex"] == "Male"]
female_tips = tips[tips["sex"] == "Female"]

mp.panel("A", 100, 120)
cns.regplot(data=male_tips, x="total_bill", y="tip", s=5)
r, p = stats.pearsonr(male_tips["total_bill"], male_tips["tip"])
mp.get_axes("A").set_title(f"Male (r={r:.2f})")

mp.panel("B", 100, 120)
cns.regplot(data=female_tips, x="total_bill", y="tip", s=5)
r, p = stats.pearsonr(female_tips["total_bill"], female_tips["tip"])
mp.get_axes("B").set_title(f"Female (r={r:.2f})")


# %%
# Regression with synthetic data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Demonstrate different correlation strengths.
np.random.seed(42)
n = 100

# Strong positive correlation
strong_pos = pd.DataFrame(
    {
        "x": np.random.randn(n),
    }
)
strong_pos["y"] = 2 * strong_pos["x"] + np.random.randn(n) * 0.3

# Weak correlation
weak = pd.DataFrame(
    {
        "x": np.random.randn(n),
    }
)
weak["y"] = 0.3 * weak["x"] + np.random.randn(n) * 1.5

# No correlation
no_corr = pd.DataFrame(
    {
        "x": np.random.randn(n),
        "y": np.random.randn(n),
    }
)

mp = cns.multipanel(max_width=450)

mp.panel("A", 90, 110)
cns.regplot(data=strong_pos, x="x", y="y", s=5)
r = stats.pearsonr(strong_pos["x"], strong_pos["y"])[0]
mp.get_axes("A").set_title(f"Strong (r={r:.2f})")

mp.panel("B", 90, 110)
cns.regplot(data=weak, x="x", y="y", s=5)
r = stats.pearsonr(weak["x"], weak["y"])[0]
mp.get_axes("B").set_title(f"Weak (r={r:.2f})")

mp.panel("C", 90, 110)
cns.regplot(data=no_corr, x="x", y="y", s=5)
r = stats.pearsonr(no_corr["x"], no_corr["y"])[0]
mp.get_axes("C").set_title(f"None (r={r:.2f})")


# %%
# Regression with confidence interval visualization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# The shaded region shows the 95% confidence interval.
cns.figure(150, 150)
ax = cns.regplot(data=tips, x="total_bill", y="tip", s=5)
ax.set_title("Regression with 95% CI")
ax.set_xlabel("Total Bill ($)")
ax.set_ylabel("Tip ($)")
