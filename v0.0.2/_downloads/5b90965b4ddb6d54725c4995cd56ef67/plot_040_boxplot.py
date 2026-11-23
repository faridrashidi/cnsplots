"""
boxplot
-------

Create publication-ready boxplots with statistical annotations.

This example demonstrates the full range of boxplot customization options
including statistical testing, outlier display, grouping, and styling.
"""

# %%
# Load data
# ~~~~~~~~~
# We'll use classic datasets for demonstration.
import matplotlib.pyplot as plt
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")
tips = sns.load_dataset("tips")


# %%
# Basic boxplot
# ~~~~~~~~~~~~~
# Simple boxplot showing distribution of total bills across days.
cns.figure(150, 100)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)
ax.set_title("Basic Boxplot")


# %%
# Boxplot with Stripplot Overlay
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Overlay a stripplot to show individual observations on top of the boxplot.
# Use one palette so both boxes and points share the same group colors.
day_order = ["Thur", "Fri", "Sat", "Sun"]
overlay_palette = dict(zip(day_order, sns.color_palette("NEJM", len(day_order))))
cns.figure(150, 100)
ax = cns.boxplot(
    data=tips,
    x="day",
    y="total_bill",
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
if ax.get_legend() is not None:
    ax.get_legend().remove()
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)
ax.set_title("Boxplot with Stripplot Overlay")


# %%
# Boxplot with rotated and colored labels
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Customize x-axis tick labels with rotation and conditional coloring.
cns.figure(150, 100)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)

xtick_labels = ax.get_xticklabels()
for index in range(tips["day"].nunique()):
    if xtick_labels[index].get_text() in ["Thur", "Fri"]:
        xtick_labels[index].set_color("red")
    else:
        xtick_labels[index].set_color("blue")


# %%
# Boxplot with statistical comparisons (all pairs)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``pairs="all"`` to perform Mann-Whitney U tests between all groups.
# The ``addcount=True`` parameter adds sample sizes below each box.
cns.figure(150, 100)
ax = cns.boxplot(
    data=iris,
    x="species",
    y="sepal_width",
    pairs="all",
    addcount=True,
)
ax.set_title("All Pairwise Comparisons with Sample Counts")


# %%
# Boxplot with specific pair comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Test only specific pairs by providing a list of tuples.
cns.figure(150, 100)
ax = cns.boxplot(
    data=iris,
    x="species",
    y="sepal_width",
    pairs=[("setosa", "virginica"), ("versicolor", "virginica")],
)
ax.set_title("Selected Pair Comparisons")


# %%
# Grouped boxplot with hue
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``hue`` parameter to create side-by-side boxes for subgroups.
# Statistical testing works across hue groups as well.
cns.figure(180, 100)
ax = cns.boxplot(
    data=tips,
    x="day",
    y="total_bill",
    hue="sex",
    pairs=[(("Thur", "Male"), ("Fri", "Male"))],
)
cns.take_legend_out()
ax.set_title("Grouped Boxplot with Cross-Group Comparison")


# %%
# Horizontal boxplot with custom order
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create horizontal boxplots by swapping x and y.
# Use ``order`` to specify the display order of categories.
cns.figure(100, 150)
ax = cns.boxplot(
    data=iris,
    x="sepal_width",
    y="species",
    pairs="all",
    order=["versicolor", "setosa", "virginica"],
)
ax.set_title("Horizontal Boxplot")


# %%
# Boxplot with outliers displayed
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``showoutliers=True`` to display outlier points.
cns.figure(150, 100)
ax = cns.boxplot(
    data=tips,
    x="day",
    y="total_bill",
    showoutliers=True,
)
ax.set_title("Boxplot with Outliers")


# %%
# Boxplot with custom whisker range
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# The ``whis`` parameter controls whisker extent.
# Default is 1.5 (1.5×IQR). Use larger values for fewer outliers.
mp = cns.multipanel(max_width=350)

mp.panel("A", 80, 120)
cns.boxplot(data=tips, x="day", y="total_bill", whis=1.0, showoutliers=True)
mp.get_axes("A").set_title("whis=1.0 (more outliers)")

mp.panel("B", 80, 120)
cns.boxplot(data=tips, x="day", y="total_bill", whis=3.0, showoutliers=True)
mp.get_axes("B").set_title("whis=3.0 (fewer outliers)")


# %%
# Boxplot with custom palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``palette`` parameter for custom colors.
cns.figure(150, 100, "Tableau")
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Tableau Palette")


# %%
# Boxplot with custom list of colors
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Pass a list of colors to ``palette``.
custom_colors = [cns.RED, cns.BLUE, cns.GREEN, cns.ORANGE]
cns.figure(150, 100)
ax = cns.boxplot(data=tips, x="day", y="total_bill", palette=custom_colors)
ax.set_title("Custom Color List")


# %%
# Boxplot comparing multiple variables
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Melt the data to compare distributions across variables.
iris_melted = iris.melt(
    id_vars=["species"],
    value_vars=["sepal_length", "sepal_width", "petal_length", "petal_width"],
    var_name="measurement",
    value_name="value",
)

cns.figure(200, 120)
ax = cns.boxplot(
    data=iris_melted,
    x="measurement",
    y="value",
    hue="species",
)
cns.take_legend_out()
ax.set_title("Multi-Variable Comparison")
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)
plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")


# %%
# Boxplot with grouped hue and all comparisons within groups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# When using hue, you can compare all subgroups within a category.
cns.figure(180, 120)
ax = cns.boxplot(
    data=tips,
    x="day",
    y="total_bill",
    hue="smoker",
    pairs=[
        (("Sat", "Yes"), ("Sat", "No")),
        (("Sun", "Yes"), ("Sun", "No")),
    ],
)
cns.take_legend_out()
ax.set_title("Within-Group Comparisons")
