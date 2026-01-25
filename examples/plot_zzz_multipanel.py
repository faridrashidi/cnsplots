"""
multipanel
----------

Create multi-panel figures in Cell, Nature, Science journal style.
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")
tips = sns.load_dataset("tips")


# %%
# Create a simple 2x2 multi-panel figure using :class:`cnsplots.multipanel`
# Each panel has explicit size: mp.panel(label, height, width)
# Labels A, B, C, D are automatically added in bold, 8pt font.
# Figure size is calculated from panel sizes + gaps.

mp = cns.multipanel((2, 2), max_width=540, hgap=50, vgap=40)

mp.panel("A", 100, 150)
cns.boxplot(data=tips, x="day", y="total_bill")

mp.panel("B", 100, 150)
cns.barplot(data=tips, x="day", y="total_bill", errorbar="se")

mp.panel("C", 100, 150)
cns.violinplot(data=iris, x="species", y="sepal_width")

mp.panel("D", 100, 150)
cns.stripplot(data=tips, x="day", y="tip", hue="sex")


# %%
# Create panels with different sizes in the same figure.
# Row height = max height of panels in that row.
# Column width = max width of panels in that column.
# Example: A(50x100), B(100x100), C(50x100), D(120x80)
# Row 0: max(50, 100) = 100, Row 1: max(50, 120) = 120
# Col 0: max(100, 100) = 100, Col 1: max(100, 80) = 100
# Total content: 100+50+100 = 250 wide, 100+40+120 = 260 tall
# Figure is max_width=540 wide with blank space on right.

mp = cns.multipanel((2, 2), max_width=540, hgap=50, vgap=40)

mp.panel("A", 50, 100)
cns.boxplot(data=tips, x="day", y="total_bill")

mp.panel("B", 100, 100)
cns.barplot(data=tips, x="day", y="total_bill", errorbar="se")

mp.panel("C", 50, 100)
cns.violinplot(data=iris, x="species", y="sepal_width")

mp.panel("D", 120, 80)
cns.stripplot(data=tips, x="day", y="tip", hue="sex")


# %%
# Create a 1x3 multi-panel figure

mp = cns.multipanel((1, 3), max_width=540, hgap=40)

mp.panel("A", 120, 150, offset_x=-0.15)
cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", hue="species")

mp.panel("B", 120, 150, offset_x=-0.15)
cns.histplot(data=tips, x="total_bill", bins=15)

mp.panel("C", 120, 150, offset_x=-0.15)
cns.kdeplot(data=iris, x="petal_length", hue="species")

mp.get_axes("A").set_title("Scatter Plot")
mp.get_axes("B").set_title("Hist Plot")
mp.get_axes("C").set_title("KDE Plot")


# %%
# Create a 3x2 multi-panel figure with uniform panel sizes

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

# Save first figure to test
mp.fig.savefig("test_multipanel.png", dpi=150, bbox_inches="tight")
print(f"Figure saved! Size: {mp.fig.get_size_inches()} inches")
