"""
multipanel
----------

Create multi-panel figures in Cell, Nature, Science journal style.

Multi-panel figures are essential for scientific publications. cnsplots
provides automatic panel labeling (A, B, C...), flexible layouts, and
precise control over figure dimensions in pixels.
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
# Basic 2x2 multi-panel figure
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create a simple grid layout with different panel sizes.
# Each panel has explicit size: ``mp.panel(label, height, width)``.
# Labels (A, B, C, D) are automatically added in bold, 8pt font.
mp = cns.multipanel((2, 2), max_width=540, hgap=50, vgap=40)

mp.panel("A", 70, 70)
cns.boxplot(data=tips, x="day", y="total_bill")

mp.panel("B", 100, 100)
cns.barplot(data=tips, x="day", y="total_bill", errorbar="se")

mp.panel("C", 80, 100)
cns.violinplot(data=iris, x="species", y="sepal_width")

mp.panel("D", 120, 80)
cns.stripplot(data=tips, x="day", y="tip", hue="sex")


# %%
# 1x3 horizontal layout with titles
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create a row of panels, useful for comparing related analyses.
mp = cns.multipanel((1, 3), max_width=540, hgap=40)

mp.panel("A", 120, 150, offset_x=-0.15)
cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", hue="species")
mp.get_axes("A").set_title("Scatter Plot")

mp.panel("B", 120, 150, offset_x=-0.15)
cns.histplot(data=tips, x="total_bill", bins=15)
mp.get_axes("B").set_title("Histogram")

mp.panel("C", 120, 150, offset_x=-0.15)
cns.kdeplot(data=iris, x="petal_length", hue="species")
mp.get_axes("C").set_title("KDE Plot")


# %%
# 3x2 grid with uniform panel sizes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Consistent panel sizes for organized appearance.
mp = cns.multipanel((3, 2), max_width=400, hgap=40, vgap=40)

mp.panel("A", 100, 120)
cns.boxplot(data=iris, x="species", y="sepal_length")

mp.panel("B", 100, 120)
cns.boxplot(data=iris, x="species", y="sepal_width")

mp.panel("C", 100, 120)
cns.barplot(data=tips, x="day", y="total_bill")

mp.panel("D", 100, 120)
cns.barplot(data=tips, x="day", y="tip")

mp.panel("E", 100, 120)
cns.stripplot(data=iris, x="species", y="petal_length")

mp.panel("F", 100, 120)
cns.stripplot(data=iris, x="species", y="petal_width")


# %%
# 2x3 layout with varying panel sizes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Different panel sizes for different plot types.
mp = cns.multipanel((2, 3), max_width=500, hgap=35, vgap=35)

mp.panel("A", 100, 100)
cns.boxplot(data=tips, x="day", y="total_bill", pairs="all")

mp.panel("B", 100, 100)
cns.violinplot(data=tips, x="day", y="tip")

mp.panel("C", 100, 100)
cns.stripplot(data=tips, x="day", y="size")

mp.panel("D", 100, 100)
cns.barplot(data=iris, x="species", y="sepal_length")

mp.panel("E", 100, 100)
cns.kdeplot(data=tips, x="total_bill", hue="sex")
mp.get_axes("E").legend().remove()

mp.panel("F", 100, 100)
cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=5)


# %%
# Vertical layout (3x1)
# ~~~~~~~~~~~~~~~~~~~~~
# Stack panels vertically for narrow figures.
mp = cns.multipanel((3, 1), max_width=200, vgap=30)

mp.panel("A", 100, 150)
cns.boxplot(data=tips, x="day", y="total_bill")

mp.panel("B", 100, 150)
cns.violinplot(data=tips, x="day", y="tip")

mp.panel("C", 100, 150)
cns.stripplot(data=tips, x="day", y="size")


# %%
# Custom label positioning
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Adjust label position with ``offset_x`` and ``offset_y``.
mp = cns.multipanel((1, 2), max_width=400, hgap=40)

# Default position
mp.panel("A", 120, 150)
cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", hue="species")
mp.get_axes("A").legend().remove()

# Adjusted position for tight layouts
mp.panel("B", 120, 150, offset_x=-0.1, offset_y=1.05)
cns.regplot(data=tips, x="total_bill", y="tip", s=5)


# %%
# Using get_axes() for customization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Access individual axes for further customization.
mp = cns.multipanel((1, 3), max_width=500, hgap=40)

mp.panel("A", 120, 140)
cns.boxplot(data=tips, x="day", y="total_bill")
ax_a = mp.get_axes("A")
ax_a.set_ylabel("Total Bill ($)")
ax_a.set_xlabel("")

mp.panel("B", 120, 140)
cns.boxplot(data=tips, x="day", y="tip")
ax_b = mp.get_axes("B")
ax_b.set_ylabel("Tip ($)")
ax_b.set_xlabel("")

mp.panel("C", 120, 140)
cns.boxplot(data=tips, x="day", y="size")
ax_c = mp.get_axes("C")
ax_c.set_ylabel("Party Size")
ax_c.set_xlabel("Day of Week")


# %%
# Different gap settings
# ~~~~~~~~~~~~~~~~~~~~~~
# Control spacing with ``hgap`` (horizontal) and ``vgap`` (vertical).
mp = cns.multipanel((2, 2), max_width=350, hgap=20, vgap=20)

mp.panel("A", 80, 100)
cns.boxplot(data=tips, x="sex", y="total_bill")

mp.panel("B", 80, 100)
cns.barplot(data=tips, x="sex", y="tip")

mp.panel("C", 80, 100)
cns.violinplot(data=tips, x="sex", y="total_bill")

mp.panel("D", 80, 100)
cns.stripplot(data=tips, x="sex", y="tip")


# %%
# Wide gaps for annotations
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Larger gaps when adding annotations between panels.
mp = cns.multipanel((1, 2), max_width=400, hgap=80)

mp.panel("A", 120, 130)
cns.boxplot(data=iris, x="species", y="sepal_length", pairs="all")

mp.panel("B", 120, 130)
cns.boxplot(data=iris, x="species", y="petal_length", pairs="all")


# %%
# Multi-panel with statistical testing
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Combine multiple plots with statistical annotations.
mp = cns.multipanel((2, 2), max_width=450, hgap=45, vgap=45)

mp.panel("A", 100, 130)
cns.boxplot(data=tips, x="day", y="total_bill", pairs=[("Thur", "Fri")])
mp.get_axes("A").set_title("Total Bill")

mp.panel("B", 100, 130)
cns.boxplot(data=tips, x="day", y="tip", pairs=[("Thur", "Fri")])
mp.get_axes("B").set_title("Tip Amount")

mp.panel("C", 100, 130)
cns.violinplot(data=tips, x="day", y="total_bill", pairs=[("Sat", "Sun")])
mp.get_axes("C").set_title("Total Bill (Violin)")

mp.panel("D", 100, 130)
cns.violinplot(data=tips, x="day", y="tip", pairs=[("Sat", "Sun")])
mp.get_axes("D").set_title("Tip Amount (Violin)")


# %%
# Using custom color palettes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Apply different palettes to the multi-panel figure.
mp = cns.multipanel((1, 3), max_width=480, hgap=35)

mp.panel("A", 100, 130, color_cycle="Tableau")
cns.barplot(data=tips, x="day", y="total_bill")
mp.get_axes("A").set_title("Tableau")

mp.panel("B", 100, 130)
cns.barplot(data=tips, x="day", y="tip")

mp.panel("C", 100, 130)
cns.barplot(data=tips, x="day", y="size")


# %%
# Complex scientific figure layout
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Realistic multi-panel figure for a publication.
mp = cns.multipanel((2, 3), max_width=540, hgap=40, vgap=40)

# Row 1: Distribution comparisons
mp.panel("A", 100, 140)
cns.boxplot(data=iris, x="species", y="sepal_length", pairs="all", addcount=True)
mp.get_axes("A").set_ylabel("Sepal Length (cm)")
mp.get_axes("A").set_xlabel("")

mp.panel("B", 100, 140)
cns.boxplot(data=iris, x="species", y="sepal_width", pairs="all", addcount=True)
mp.get_axes("B").set_ylabel("Sepal Width (cm)")
mp.get_axes("B").set_xlabel("")

mp.panel("C", 100, 140)
cns.violinplot(data=iris, x="species", y="petal_length")
mp.get_axes("C").set_ylabel("Petal Length (cm)")
mp.get_axes("C").set_xlabel("")

# Row 2: Correlations and distributions
mp.panel("D", 100, 140)
cns.scatterplot(data=iris, x="sepal_length", y="petal_length", hue="species", s=8)
mp.get_axes("D").legend().remove()
mp.get_axes("D").set_xlabel("Sepal Length")
mp.get_axes("D").set_ylabel("Petal Length")

mp.panel("E", 100, 140)
cns.regplot(data=iris, x="sepal_width", y="petal_width", hue="species", s=4)
mp.get_axes("E").legend().remove()
mp.get_axes("E").set_xlabel("Sepal Width")
mp.get_axes("E").set_ylabel("Petal Width")

mp.panel("F", 100, 140)
cns.kdeplot(data=iris, x="petal_length", hue="species", fill=True, alpha=0.3)
mp.get_axes("F").legend().remove()
mp.get_axes("F").set_xlabel("Petal Length")


# %%
# README Showcase figure
# ~~~~~~~~~~~~~~~~~~~~~~
# A comprehensive showcase of cnsplots capabilities for the README.

# Create synthetic survival data
np.random.seed(42)
survival_data = []
for grp, scale in [("Treatment", 36), ("Control", 24)]:
    times = np.random.exponential(scale=scale, size=50)
    events = np.random.binomial(1, 0.7, 50)
    for t, e in zip(times, events):
        survival_data.append({"time": t, "event": e, "group": grp})
survival_df = pd.DataFrame(survival_data)

mp = cns.multipanel((3, 3), max_width=540, hgap=45, vgap=45)

# Panel A: boxplot
mp.panel("A", 100, 100)
cns.boxplot(data=tips, x="day", y="total_bill")
mp.get_axes("A").set_title("Boxplot")

# Panel B: violinplot
mp.panel("B", 100, 100)
cns.violinplot(data=iris, x="species", y="sepal_width")
mp.get_axes("B").set_title("Violinplot")

# Panel C: stripplot
mp.panel("C", 100, 100)
cns.stripplot(data=tips, x="day", y="tip", hue="sex")
mp.get_axes("C").legend().remove()
mp.get_axes("C").set_title("Stripplot")

# Panel D: barplot
mp.panel("D", 100, 100)
cns.barplot(data=tips, x="day", y="total_bill", errorbar="se")
mp.get_axes("D").set_title("Barplot")

# Panel E: stackplot
mp.panel("E", 100, 100)
cns.stackplot(data=tips, x="day", y="sex")
mp.get_axes("E").set_title("Stackplot")

# Panel F: kdeplot
mp.panel("F", 100, 100)
cns.kdeplot(data=iris, x="petal_length", hue="species")
mp.get_axes("F").legend().remove()
mp.get_axes("F").set_title("KDE Plot")

# Panel G: regplot
mp.panel("G", 100, 100)
cns.regplot(data=tips, x="total_bill", y="tip", s=5)
mp.get_axes("G").set_title("Regplot")

# Panel H: pieplot
mp.panel("H", 100, 100)
cns.pieplot(iris, "species")
mp.get_axes("H").set_title("Pieplot")

# Panel I: survivalplot
mp.panel("I", 100, 100)
cns.survivalplot(data=survival_df, duration="time", event="event", hue="group")
mp.get_axes("I").legend().remove()
mp.get_axes("I").set_title("Survivalplot")
