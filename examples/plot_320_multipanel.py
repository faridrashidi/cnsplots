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
mp = cns.multipanel(max_width=350)

mp.panel("A", 70, 70)
cns.boxplot(data=tips, x="day", y="total_bill")

mp.panel("B", 100, 100)
cns.barplot(data=tips, x="day", y="total_bill", errorbar="se")

mp.panel("C", 100, 80)
cns.violinplot(data=iris, x="species", y="sepal_width")

mp.panel("D", 120, 80)
cns.stripplot(data=tips, x="day", y="tip", hue="sex")


# %%
# 1x3 horizontal layout with titles
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create a row of panels, useful for comparing related analyses.
mp = cns.multipanel(max_width=540)

mp.panel("A", 120, 120, pad_top=10)
cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", hue="species")
mp.get_axes("A").set_title("Scatter Plot")

mp.panel("B", 120, 120, pad_top=10)
cns.histplot(data=tips, x="total_bill", bins=15)
mp.get_axes("B").set_title("Histogram")

mp.panel("C", 120, 120, pad_top=10)
cns.kdeplot(data=iris, x="petal_length", hue="species")
mp.get_axes("C").set_title("KDE Plot")


# %%
# 3x2 grid with uniform panel sizes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Consistent panel sizes for organized appearance.
mp = cns.multipanel(max_width=500)

mp.panel("A", 100, 100)
cns.boxplot(data=iris, x="species", y="sepal_length")

mp.panel("B", 100, 100)
cns.boxplot(data=iris, x="species", y="sepal_width")

mp.panel("C", 100, 100)
cns.barplot(data=tips, x="day", y="total_bill")

mp.panel("D", 100, 100)
cns.barplot(data=tips, x="day", y="tip")

mp.panel("E", 100, 100)
cns.stripplot(data=iris, x="species", y="petal_length")

mp.panel("F", 100, 100)
cns.stripplot(data=iris, x="species", y="petal_width")


# %%
# 2x3 layout with varying panel sizes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Different panel sizes for different plot types.
mp = cns.multipanel(max_width=500)

mp.panel("A", 100, 100)
cns.boxplot(data=tips, x="day", y="total_bill", pairs="all")

mp.panel("B", 100, 100)
cns.violinplot(data=tips, x="day", y="tip")

mp.panel("C", 100, 100)
cns.stripplot(data=tips, x="day", y="size")

mp.panel("D", 80, 80, margin=(10, 0, 20, 20))
cns.barplot(data=iris, x="species", y="sepal_length")
mp.get_axes("D").tick_params(axis="x", rotation=40)

mp.panel("E", 100, 100)
cns.kdeplot(data=tips, x="total_bill", hue="sex")
mp.get_axes("E").legend().remove()

mp.panel("F", 100, 100)
cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=5)


# %%
# Using get_axes() for customization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Access individual axes for further customization.
mp = cns.multipanel(max_width=500)

mp.panel("A", 120, 120)
cns.boxplot(data=tips, x="day", y="total_bill")
ax_a = mp.get_axes("A")
ax_a.set_ylabel("Total Bill ($)")
ax_a.set_xlabel("")

mp.panel("B", 120, 120)
cns.boxplot(data=tips, x="day", y="tip")
ax_b = mp.get_axes("B")
ax_b.set_ylabel("Tip ($)")
ax_b.set_xlabel("")

mp.panel("C", 120, 120)
cns.boxplot(data=tips, x="day", y="size")
ax_c = mp.get_axes("C")
ax_c.set_ylabel("Party Size")
ax_c.set_xlabel("Day of Week")


# %%
# Using custom color palettes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Apply different palettes to the multi-panel figure.
mp = cns.multipanel(max_width=480)

mp.panel("A", 100, 100, pad_top=5, color_cycle="Tableau")
cns.barplot(data=tips, x="day", y="total_bill")
mp.get_axes("A").set_title("Tableau")

mp.panel("B", 100, 100, pad_top=5, color_cycle="Ecotyper1")
cns.barplot(data=tips, x="day", y="tip")
mp.get_axes("A").set_title("Ecotyper1")

mp.panel("C", 100, 100, pad_top=5, color_cycle="Ecotyper2")
cns.barplot(data=tips, x="day", y="size")
mp.get_axes("A").set_title("Ecotyper2")


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

mp = cns.multipanel(max_width=500)

# Panel A: boxplot
mp.panel("A", 100, 100, pad_top=5)
cns.boxplot(data=tips, x="day", y="total_bill")
mp.get_axes("A").set_title("Boxplot")

# Panel B: violinplot
mp.panel("B", 100, 100, pad_top=5)
cns.violinplot(data=iris, x="species", y="sepal_width")
mp.get_axes("B").set_title("Violinplot")

# Panel C: stripplot
mp.panel("C", 100, 100, pad_top=5)
cns.stripplot(data=tips, x="day", y="tip", hue="sex")
mp.get_axes("C").legend().remove()
mp.get_axes("C").set_title("Stripplot")

# Panel D: barplot
mp.panel("D", 100, 60, pad_top=5)
cns.barplot(data=tips, x="day", y="total_bill", errorbar="se")
mp.get_axes("D").set_title("Barplot")

# Panel E: stackplot
mp.panel("E", 100, 100, pad_top=5, margin=(10, 0, 40, 20))
cns.stackplot(data=tips, x="day", y="sex")
mp.get_axes("E").set_title("Stackplot")

# Panel F: kdeplot
mp.panel("F", 100, 100, pad_top=5)
cns.kdeplot(data=iris, x="petal_length", hue="species")
mp.get_axes("F").legend().remove()
mp.get_axes("F").set_title("KDE Plot")

# Panel G: regplot
mp.panel("G", 100, 100, pad_top=5)
cns.regplot(data=tips, x="total_bill", y="tip", s=5)
mp.get_axes("G").set_title("Regplot")

# Panel H: pieplot
mp.panel("H", 80, 80, pad_top=5, margin=(10, 0, 40, 20))
cns.pieplot(iris, "species")
mp.get_axes("H").set_title("Pieplot")

# Panel I: survivalplot
mp.panel("I", 100, 100, pad_top=5)
cns.survivalplot(data=survival_df, duration="time", event="event", hue="group")
mp.get_axes("I").legend().remove()
mp.get_axes("I").set_title("Survivalplot")
