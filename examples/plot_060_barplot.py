"""
barplot
-------

Create bar plots for comparing categorical data.

Bar plots display the mean (or other estimator) of a numeric variable
grouped by categories. cnsplots enhances bar plots with statistical
testing, error bars, and publication-ready styling.
"""

# %%
# Load data
# ~~~~~~~~~
import numpy as np
import pandas as pd
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")
tips = sns.load_dataset("tips")


# %%
# Basic barplot
# ~~~~~~~~~~~~~
# Simple bar plot with standard error bars.
cns.figure(150, 100)
ax = cns.barplot(data=tips, x="day", y="total_bill", errorbar="se")
ax.set_title("Basic Barplot")


# %%
# Barplot with Stripplot Overlay
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Overlay a stripplot to show individual observations on top of the summary bars.
# Use one palette so both bars and points share the same group colors.
day_order = ["Thur", "Fri", "Sat", "Sun"]
overlay_palette = dict(zip(day_order, sns.color_palette("NEJM", len(day_order))))
cns.figure(150, 100)
ax = cns.barplot(
    data=tips,
    x="day",
    y="total_bill",
    errorbar="se",
    order=day_order,
    palette=overlay_palette,
)
cns.stripplot(
    data=tips,
    x="day",
    y="total_bill",
    hue="day",
    order=day_order,
    hue_order=day_order,
    palette=overlay_palette,
    legend=False,
    ax=ax,
    size=2,
    alpha=0.5,
    showmedian=False,
)
ax.set_title("Barplot with Stripplot Overlay")


# %%
# Barplot with standard deviation
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Show variability with standard deviation error bars.
cns.figure(150, 100)
palette = {
    "Sat": cns.BLUE,
    "Fri": cns.BLUE,
    "Thur": cns.RED,
    "Sun": cns.RED,
}
cns.barplot(data=tips, x="day", y="total_bill", errorbar="sd", palette=palette)


# %%
# Barplot with confidence intervals
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Display 95% confidence intervals.
cns.figure(150, 100)
cns.barplot(data=tips, x="day", y="total_bill", errorbar="ci")


# %%
# No error bars
# ~~~~~~~~~~~~~
# Clean bars without error indicators.
cns.figure(150, 100)
cns.barplot(data=tips, x="day", y="total_bill", errorbar=None)


# %%
# Conditional coloring
# ~~~~~~~~~~~~~~~~~~~~
# Color bars based on value thresholds.
mean_bills = tips.groupby("day")["total_bill"].mean()
cols = ["grey" if x < 21.0 else "orange" for x in mean_bills]
cns.figure(150, 100)
cns.barplot(data=tips, x="day", y="total_bill", palette=cols)


# %%
# Statistical comparisons (all pairs)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Add significance annotations for all pairwise comparisons.
cns.figure(150, 100, "Tableau")
cns.barplot(data=tips, x="day", y="total_bill", pairs="all", addtip=True)


# %%
# Statistical comparisons (specific pairs)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare only selected pairs of groups.
cns.figure(150, 100, "Set1")
cns.barplot(
    data=tips,
    x="day",
    y="total_bill",
    pairs=[("Thur", "Fri"), ("Sat", "Sun")],
    addtip=True,
)


# %%
# Grouped barplot with hue
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Split bars by a secondary categorical variable.
cns.figure(180, 100, "BlueRed")
cns.barplot(data=tips, x="day", y="total_bill", hue="sex")
cns.take_legend_out()


# %%
# Grouped barplot with statistical testing
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare specific groups across hue levels.
cns.figure(180, 100, "BlueRed")
cns.barplot(
    data=tips,
    x="day",
    y="total_bill",
    hue="sex",
    pairs=[(("Thur", "Male"), ("Fri", "Male"))],
)
cns.take_legend_out()


# %%
# Horizontal barplot
# ~~~~~~~~~~~~~~~~~~
# Flip axes for horizontal layout.
cns.figure(100, 180, "Set1")
cns.barplot(
    data=tips,
    x="total_bill",
    y="day",
    order=["Sun", "Fri", "Thur", "Sat"],
    pairs=[("Sun", "Fri")],
)


# %%
# Custom order
# ~~~~~~~~~~~~
# Specify the order of categories.
cns.figure(150, 100, "Tableau")
cns.barplot(
    data=tips,
    x="day",
    y="total_bill",
    order=["Thur", "Fri", "Sat", "Sun"],
)


# %%
# Diverging barplot (centered on mean)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Show deviations from the mean with centered bars.
tips_centered = tips.copy()
tips_centered["bill_deviation"] = (
    tips_centered["total_bill"] - tips_centered["total_bill"].mean()
)
cns.figure(100, 150, "Tableau")
ax = cns.barplot(data=tips_centered, x="day", y="bill_deviation")
ax.axhline(0, color="k", clip_on=False, lw=0.8)
ax.spines["bottom"].set_visible(False)


# %%
# Horizontal diverging barplot
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Horizontal layout for diverging bars.
cns.figure(150, 100, "Tableau")
ax = cns.barplot(data=tips_centered, y="day", x="bill_deviation")
ax.axvline(0, color="k", clip_on=False, lw=0.8)
ax.spines["left"].set_visible(False)


# %%
# Barplot with species data
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare measurements across species.
cns.figure(150, 100, "Bold")
ax = cns.barplot(data=iris, x="species", y="sepal_width", pairs="all", addtip=True)
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)


# %%
# Barplot with sample counts
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Display number of samples above bars.
cns.figure(150, 150)
cns.barplot(data=iris, x="species", y="sepal_length", addtip=True)


# %%
# Multiple metrics comparison
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare different measurements using multipanel.
mp = cns.multipanel(max_width=310)

mp.panel("A", 80, 120, margin_bottom=20)
cns.barplot(data=iris, x="species", y="sepal_length")
mp.get_axes("A").set_title("Sepal Length")

mp.panel("B", 80, 120, margin_right=0)
cns.barplot(data=iris, x="species", y="sepal_width")
mp.get_axes("B").set_title("Sepal Width")

mp.newline()

mp.panel("C", 80, 120)
cns.barplot(data=iris, x="species", y="petal_length")
mp.get_axes("C").set_title("Petal Length")

mp.panel("D", 80, 120, margin_right=0)
cns.barplot(data=iris, x="species", y="petal_width")
mp.get_axes("D").set_title("Petal Width")


# %%
# Error bar comparison
# ~~~~~~~~~~~~~~~~~~~~
# Compare different error bar types side by side.
mp = cns.multipanel(max_width=420)

mp.panel("A", 100, 100)
cns.barplot(data=tips, x="day", y="total_bill", errorbar="se")
mp.get_axes("A").set_title("Standard Error")

mp.panel("B", 100, 100)
cns.barplot(data=tips, x="day", y="total_bill", errorbar="sd")
mp.get_axes("B").set_title("Std Deviation")

mp.panel("C", 100, 100, margin_right=0)
cns.barplot(data=tips, x="day", y="total_bill", errorbar="ci")
mp.get_axes("C").set_title("95% CI")


# %%
# Grouped analysis by time
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Compare groups across different time periods.
mp = cns.multipanel(max_width=410)

lunch = tips[tips["time"] == "Lunch"]
dinner = tips[tips["time"] == "Dinner"]

mp.panel("A", 100, 150)
cns.barplot(data=lunch, x="day", y="total_bill", hue="sex")
mp.get_axes("A").legend().remove()
mp.get_axes("A").set_title("Lunch")

mp.panel("B", 100, 150, margin_right=0)
cns.barplot(data=dinner, x="day", y="total_bill", hue="sex")
cns.take_legend_out()
mp.get_axes("B").set_title("Dinner")


# %%
# Percentage change visualization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Show relative changes from baseline.
np.random.seed(42)
baseline = pd.DataFrame(
    {
        "treatment": ["Control", "Drug A", "Drug B", "Drug C"],
        "pct_change": [0, 25, -15, 45],
        "error": [5, 8, 6, 10],
    }
)
colors = [
    "gray" if x == 0 else ("green" if x > 0 else "red") for x in baseline["pct_change"]
]
cns.figure(150, 100, color_cycle=colors)
ax = cns.barplot(data=baseline, x="treatment", y="pct_change", errorbar=None)
ax.axhline(0, color="k", lw=0.8)
ax.set_ylabel("% Change from Baseline")
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)


# %%
# Gene expression comparison
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Biological example: gene expression by condition.
np.random.seed(42)
gene_data = pd.DataFrame(
    {
        "gene": ["TP53"] * 30 + ["BRCA1"] * 30 + ["MYC"] * 30,
        "expression": np.concatenate(
            [
                np.random.normal(5, 1, 30),
                np.random.normal(3, 0.8, 30),
                np.random.normal(7, 1.5, 30),
            ]
        ),
        "condition": (["Control"] * 15 + ["Treatment"] * 15) * 3,
    }
)

cns.figure(180, 100)
ax = cns.barplot(
    data=gene_data,
    x="gene",
    y="expression",
    hue="condition",
    pairs=[(("TP53", "Control"), ("TP53", "Treatment"))],
)
ax.set_ylabel("Expression (log2 TPM)")
cns.take_legend_out()


# %%
# Palette comparison with bars
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Different palettes for the same data.
mp = cns.multipanel(max_width=310)

mp.panel("A", 80, 120, color_cycle="Set1", margin_bottom=20)
cns.barplot(data=tips, x="day", y="total_bill")
mp.get_axes("A").set_title("Set1")

mp.panel("B", 80, 120, color_cycle="Tableau", margin_right=0)
cns.barplot(data=tips, x="day", y="total_bill")
mp.get_axes("B").set_title("Tableau")

mp.newline()

mp.panel("C", 80, 120, color_cycle="Bold")
cns.barplot(data=tips, x="day", y="total_bill")
mp.get_axes("C").set_title("Bold")

mp.panel("D", 80, 120, color_cycle="Pastel1", margin_right=0)
cns.barplot(data=tips, x="day", y="total_bill")
mp.get_axes("D").set_title("Pastel1")
