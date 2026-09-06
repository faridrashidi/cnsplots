"""
Multipanel Layout
-----------------

Create multi-panel figures in Cell, Nature, Science journal style.

Multi-panel figures are essential for scientific publications. cnsplots
provides automatic panel labeling (A, B, C...), flexible layouts, and
precise control over figure dimensions in pixels.
"""

# %%
# Load data
# ~~~~~~~~~
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")
iris = sns.load_dataset("iris")


# %%
# Basic 2x2 multi-panel figure
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create a simple grid layout with different panel sizes.
# Each panel has explicit size: ``mp.panel(label, height, width)``.
# Labels (A, B, C, D) are automatically added in bold, 8pt font.
mp = cns.multipanel(max_width=265)

mp.panel("A", 70, 70)
cns.boxplot(data=tips, x="day", y="total_bill")

mp.panel("B", 100, 100, margin_bottom=20)
cns.barplot(data=tips, x="day", y="total_bill", errorbar="se")

mp.panel("C", 100, 80)
cns.violinplot(data=iris, x="species", y="sepal_width")

mp.panel("D", 120, 80)
cns.stripplot(data=tips, x="day", y="tip", hue="sex")


# %%
# 1x3 horizontal layout with titles
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create a row of panels, useful for comparing related analyses.
mp = cns.multipanel(
    max_width=500,
    title="Distribution Overview",
    loc="left",
    title_fontweight="bold",
)

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
mp = cns.multipanel(max_width=440)

mp.panel("A", 100, 100, margin_bottom=20)
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
mp = cns.multipanel(max_width=440)

mp.panel("A", 100, 100, margin_bottom=30)
cns.boxplot(data=tips, x="day", y="total_bill", pairs="all")

mp.panel("B", 100, 100)
cns.violinplot(data=tips, x="day", y="tip")

mp.panel("C", 100, 100)
cns.stripplot(data=tips, x="day", y="size")

mp.panel(
    "D",
    80,
    80,
    margin_left=10,
    margin_top=0,
    margin_right=20,
    margin_bottom=20,
)
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
mp = cns.multipanel(max_width=480)

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

mp.panel("C", 120, 120, margin_right=0)
cns.boxplot(data=tips, x="day", y="size")
ax_c = mp.get_axes("C")
ax_c.set_ylabel("Party Size")
ax_c.set_xlabel("Day of Week")


# %%
# Using custom color palettes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Apply different palettes to the multi-panel figure.
mp = cns.multipanel(max_width=450)

mp.panel("A", 100, 100, pad_top=5, color_cycle="Tableau")
cns.barplot(data=tips, x="day", y="total_bill")
mp.get_axes("A").set_title("Tableau")

mp.panel("B", 100, 100, pad_top=5, color_cycle="Ecotyper1")
cns.barplot(data=tips, x="day", y="tip")
mp.get_axes("A").set_title("Ecotyper1")

mp.panel("C", 100, 100, pad_top=5, color_cycle="Ecotyper2", margin_right=0)
cns.barplot(data=tips, x="day", y="size")
mp.get_axes("A").set_title("Ecotyper2")
