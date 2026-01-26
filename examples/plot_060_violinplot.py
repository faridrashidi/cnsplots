"""
violinplot
----------

Create violin plots showing distribution shapes with optional statistical testing.

Violin plots combine box plots with kernel density estimation to show
the full distribution shape, making them ideal for comparing distributions
across categories.
"""

# %%
# Load data
# ~~~~~~~~~
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")
iris = sns.load_dataset("iris")


# %%
# Basic violin plot
# ~~~~~~~~~~~~~~~~~
# Simple violin plot with embedded box plot (default).
cns.figure(150, 100)
ax = cns.violinplot(data=tips, x="day", y="total_bill")
ax.set_title("Basic Violin Plot")


# %%
# Violin plot with statistical testing
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``pairs="all"`` for Mann-Whitney U tests between all groups.
cns.figure(150, 100, "Tableau")
ax = cns.violinplot(data=tips, x="day", y="total_bill", pairs="all")
ax.set_title("Violin Plot with All Pairwise Comparisons")


# %%
# Violin plot with specific pair comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Test only selected pairs.
cns.figure(150, 100)
ax = cns.violinplot(
    data=iris,
    x="species",
    y="sepal_length",
    pairs=[("setosa", "versicolor"), ("setosa", "virginica")],
)
ax.set_title("Selected Pair Comparisons")


# %%
# Violin plot without embedded box plot
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set ``add_box=False`` for cleaner violin shapes.
cns.figure(150, 100)
ax = cns.violinplot(data=tips, x="day", y="total_bill", add_box=False)
ax.set_title("Violin Plot without Box")


# %%
# Violin plot with custom width
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Adjust violin body width with the ``width`` parameter.
mp = cns.multipanel((1, 2), max_width=350, hgap=40)

mp.panel("A", 80, 120)
cns.violinplot(data=tips, x="day", y="total_bill", width=0.4)
mp.get_axes("A").set_title("width=0.4 (narrow)")

mp.panel("B", 80, 120)
cns.violinplot(data=tips, x="day", y="total_bill", width=0.9)
mp.get_axes("B").set_title("width=0.9 (wide)")


# %%
# Grouped violin plot with hue
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``hue`` for side-by-side violins within each category.
cns.figure(180, 120)
ax = cns.violinplot(
    data=tips,
    x="day",
    y="total_bill",
    hue="sex",
)
cns.take_legend_out()
ax.set_title("Grouped Violin Plot")


# %%
# Split violin plot
# ~~~~~~~~~~~~~~~~~
# Use ``split=True`` to show two hue levels as halves of the same violin.
# This is useful for direct comparison of two groups.
cns.figure(150, 100)
ax = cns.violinplot(
    data=tips,
    x="day",
    y="total_bill",
    hue="sex",
    split=True,
)
cns.take_legend_out()
ax.set_title("Split Violin Plot")


# %%
# Violin plot with different inner representations
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# The ``inner`` parameter controls what's shown inside the violin.
# Options: "box" (default), "quart", "point", "stick", None
mp = cns.multipanel((1, 3), max_width=450, hgap=35)

mp.panel("A", 80, 110)
cns.violinplot(data=tips, x="day", y="total_bill", inner="quart", add_box=False)
mp.get_axes("A").set_title("inner='quart'")

mp.panel("B", 80, 110)
cns.violinplot(data=tips, x="day", y="total_bill", inner="point", add_box=False)
mp.get_axes("B").set_title("inner='point'")

mp.panel("C", 80, 110)
cns.violinplot(data=tips, x="day", y="total_bill", inner="stick", add_box=False)
mp.get_axes("C").set_title("inner='stick'")


# %%
# Horizontal violin plot
# ~~~~~~~~~~~~~~~~~~~~~~
# Swap x and y for horizontal orientation.
cns.figure(100, 150)
ax = cns.violinplot(
    data=iris,
    x="sepal_width",
    y="species",
    order=["virginica", "versicolor", "setosa"],
)
ax.set_title("Horizontal Violin Plot")


# %%
# Violin plot with custom palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use built-in palettes or custom colors.
cns.figure(150, 100, "Bold")
ax = cns.violinplot(data=tips, x="day", y="total_bill")
ax.set_title("Bold Palette")


# %%
# Violin plot comparing multiple measurements
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Melt data to compare distributions across variables.
iris_melted = iris.melt(
    id_vars=["species"],
    value_vars=["sepal_length", "sepal_width", "petal_length", "petal_width"],
    var_name="measurement",
    value_name="value",
)

cns.figure(200, 120, "Set2")
ax = cns.violinplot(
    data=iris_melted[iris_melted["species"] == "setosa"],
    x="measurement",
    y="value",
)
ax.tick_params(axis="x", rotation=40)
ax.set_title("Setosa Measurements Distribution")


# %%
# Violin plot with grouped comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Statistical testing across hue groups.
cns.figure(180, 120)
ax = cns.violinplot(
    data=tips,
    x="day",
    y="total_bill",
    hue="smoker",
    pairs=[(("Sat", "Yes"), ("Sat", "No"))],
)
cns.take_legend_out()
ax.set_title("Grouped Violin with Statistical Testing")
