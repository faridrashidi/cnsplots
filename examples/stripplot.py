"""
Strip Plot
----------

Create strip plots showing individual data points with summary statistics.

Strip plots display all individual observations, making them ideal for
small-to-medium datasets where you want to show the actual data distribution.
"""

# %%
# Load data
# ~~~~~~~~~

import cnsplots as cns

tips = cns.datasets.load_dataset("tips")
iris = cns.datasets.load_dataset("iris")


# %%
# Basic strip plot
# ~~~~~~~~~~~~~~~~
# Shows individual points with median line (default).
cns.figure(100, 120)
ax = cns.stripplot(data=tips, x="day", y="total_bill", size=2, rasterized=True)
ax.set_title("Basic Strip Plot with Median")


# %%
# Horizontal strip plot
# ~~~~~~~~~~~~~~~~~~~~~
# Swap x and y for horizontal orientation.
cns.figure(120, 100)
ax = cns.stripplot(data=tips, x="total_bill", y="day", size=2)
ax.set_title("Horizontal Strip Plot")


# %%
# Strip plot without median line
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set ``showmedian=False`` for points only.
cns.figure(100, 120)
ax = cns.stripplot(data=tips, x="day", y="total_bill", size=2, showmedian=False)
ax.set_title("Strip Plot without Median")


# %%
# Strip plot with mean marker
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``showmeans=True`` to show mean instead of median.
cns.figure(100, 120)
ax = cns.stripplot(
    data=tips, x="day", y="total_bill", size=2, showmedian=False, showmeans=True
)
ax.set_title("Strip Plot with Mean Marker")


# %%
# Strip plot with both median and mean
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Show both summary statistics.
cns.figure(100, 120)
ax = cns.stripplot(
    data=tips, x="day", y="total_bill", size=2, showmedian=True, showmeans=True
)
ax.set_title("Strip Plot with Median and Mean")


# %%
# Strip plot with sample counts
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``add_count=True`` to display sample sizes.
cns.figure(100, 120)
ax = cns.stripplot(data=tips, x="day", y="total_bill", size=2, add_count=True)
ax.set_title("Strip Plot with Sample Counts")


# %%
# Grouped strip plot with hue
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``hue`` for color-coded subgroups.
cns.figure(100, 180)
ax = cns.stripplot(data=tips, x="day", y="total_bill", size=2, hue="sex")
cns.take_legend_out()
ax.set_title("Grouped Strip Plot")


# %%
# Strip plot with dodging
# ~~~~~~~~~~~~~~~~~~~~~~~
# Points are automatically dodged when using hue.
cns.figure(100, 180)
ax = cns.stripplot(data=tips, x="day", y="total_bill", size=3, hue="smoker", dodge=True)
cns.take_legend_out()
ax.set_title("Strip Plot with Dodging")


# %%
# Strip plot with varying point sizes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Adjust point size for visibility.
mp = cns.multipanel(max_width=330)

mp.panel("A", 120, 80)
cns.stripplot(data=iris, x="species", y="sepal_width", size=1)
mp.get_axes("A").set_title("size=1 (small)")

mp.panel("B", 120, 80, margin_right=0)
cns.stripplot(data=iris, x="species", y="sepal_width", size=5)
mp.get_axes("B").set_title("size=5 (large)")


# %%
# Strip plot with custom palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use built-in color palettes.
cns.figure(100, 120, "Tableau")
ax = cns.stripplot(data=tips, x="day", y="total_bill", size=2)
ax.set_title("Tableau Palette")


# %%
# Strip plot with custom jitter
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Control the amount of horizontal jitter with the ``jitter`` parameter.
mp = cns.multipanel(max_width=350)

mp.panel("A", 120, 80)
cns.stripplot(data=tips, x="day", y="total_bill", size=2, jitter=0.1)
mp.get_axes("A").set_title("jitter=0.1 (tight)")

mp.panel("B", 120, 80)
cns.stripplot(data=tips, x="day", y="total_bill", size=2, jitter=0.4)
mp.get_axes("B").set_title("jitter=0.4 (spread)")


# %%
# Strip plot with custom alpha
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Adjust transparency for overlapping points.
mp = cns.multipanel(max_width=330)

mp.panel("A", 120, 80)
cns.stripplot(data=tips, x="day", y="total_bill", size=4, alpha=1.0)
mp.get_axes("A").set_title("alpha=1.0 (opaque)")

mp.panel("B", 120, 80, margin_right=0)
cns.stripplot(data=tips, x="day", y="total_bill", size=4, alpha=0.3)
mp.get_axes("B").set_title("alpha=0.3 (transparent)")


# %%
# Strip plot with custom order
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Specify category order with the ``order`` parameter.
cns.figure(100, 120)
ax = cns.stripplot(
    data=tips,
    x="day",
    y="total_bill",
    size=2,
    order=["Sun", "Sat", "Fri", "Thur"],
)
ax.set_title("Custom Category Order")


# %%
# Strip plot comparing multiple measurements
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Melt data to compare distributions across variables.
iris_melted = iris.melt(
    id_vars=["species"],
    value_vars=["sepal_length", "sepal_width", "petal_length", "petal_width"],
    var_name="measurement",
    value_name="value",
)

cns.figure(200, 120)
ax = cns.stripplot(
    data=iris_melted,
    x="measurement",
    y="value",
    hue="species",
    size=2,
    dodge=True,
    alpha=0.7,
)
cns.take_legend_out()
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)
ax.set_title("Multi-Variable Comparison")


# %%
# Strip plot with all options combined
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Comprehensive example showing multiple features.
cns.figure(150, 150, "Set2")
ax = cns.stripplot(
    data=tips,
    x="day",
    y="total_bill",
    size=3,
    showmedian=True,
    showmeans=True,
    add_count=True,
    order=["Thur", "Fri", "Sat", "Sun"],
    alpha=0.6,
)
ax.set_title("Strip Plot with All Options")
ax.set_ylabel("Total Bill ($)")
