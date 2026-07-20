"""
Stacked Bar Plot
----------------

Create stacked bar plots showing proportions with optional statistical testing.

Stacked bar plots are ideal for visualizing how a whole is divided into parts
across different categories. They support Fisher's exact test for comparing
proportions between groups.
"""

# %%
# Load data
# ~~~~~~~~~
import numpy as np
import pandas as pd

import cnsplots as cns

tips = cns.datasets.load_dataset("tips")


# %%
# Basic stacked bar plot (normalized)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Shows proportions that sum to 100% within each bar.
# Use ``addcount=True`` to display total counts in the tick labels.
cns.figure(120, 100)
ax = cns.stackplot(
    data=tips, x="sex", stack="day", width=0.4, normalize=True, addcount=True
)
ax.set_title("Basic Stacked Plot")


# %%
# Stacked bar plot with absolute counts
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set ``normalize=False`` to show actual counts instead of proportions.
cns.figure(120, 100)
ax = cns.stackplot(
    data=tips,
    x="day",
    stack="sex",
    stack_order=["Female", "Male"],
    normalize=False,
)
ax.set_title("Stacked Bar with Counts")


# %%
# Stacked bar plot with Fisher's exact test
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``pairs`` to test if proportions differ significantly between groups.
# Fisher's exact test is used for 2x2 contingency tables.
cns.figure(120, 100)
ax = cns.stackplot(
    data=tips,
    x="day",
    stack="sex",
    normalize=True,
    pairs=[("Thur", "Fri"), ("Fri", "Sat")],
)
ax.set_title("With Selected Statistical Comparisons")


# %%
# Stacked bar plot with custom stack order
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Control the order of stacked segments with ``stack_order``.
cns.figure(120, 100)
ax = cns.stackplot(
    data=tips,
    x="sex",
    stack="day",
    normalize=True,
    stack_order=["Sun", "Sat", "Fri", "Thur"],
    pairs=[("Male", "Female")],
)
ax.set_title("Custom Stack Order")


# %%
# Stacked bar plot with all pairwise comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``pairs="all"`` to test all possible pairs.
cns.figure(150, 100, "Tableau")
ax = cns.stackplot(data=tips, x="day", stack="sex", normalize=True, pairs="all")
ax.set_title("All Pairwise Comparisons")


# %%
# Horizontal stacked bar plot
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Pass the bar variable to ``y`` for horizontal orientation.
cns.figure(100, 120)
ax = cns.stackplot(
    data=tips,
    y="day",
    stack="sex",
    normalize=True,
    pairs=[("Thur", "Fri"), ("Fri", "Sat")],
    bar_order=["Fri", "Sat", "Sun", "Thur"],
)
ax.set_title("Horizontal Stacked Bar")


# %%
# Stacked bar plot with custom bar order
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``bar_order`` to specify the order of bars on the axis.
cns.figure(120, 100)
ax = cns.stackplot(
    data=tips,
    x="day",
    stack="sex",
    normalize=True,
    bar_order=["Sun", "Sat", "Fri", "Thur"],
)
ax.set_title("Custom Bar Order")


# %%
# Stacked bar plot with custom width
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Adjust bar width with the ``width`` parameter.
mp = cns.multipanel(max_width=250)

mp.panel("A", 80, 100)
cns.stackplot(data=tips, x="day", stack="sex", normalize=True, width=0.3)
mp.get_axes("A").set_title("width=0.3 (narrow)")

mp.panel("B", 80, 100, margin_right=0)
cns.stackplot(data=tips, x="day", stack="sex", normalize=True, width=0.8)
mp.get_axes("B").set_title("width=0.8 (wide)")


# %%
# Stacked bar plot with custom palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use different color palettes for visual variety.
cns.figure(120, 100, "Set2")
ax = cns.stackplot(data=tips, x="day", stack="sex", normalize=True)
ax.set_title("Set2 Palette")


# %%
# Stacked bar plot with different palettes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Showcase multiple palette options.
mp = cns.multipanel(max_width=250)

mp.panel("A", 80, 100, color_cycle="Bold")
cns.stackplot(data=tips, x="day", stack="sex", normalize=True)
mp.get_axes("A").set_title("Bold")

mp.panel("B", 80, 100, color_cycle="BlueRed", margin_right=0)
cns.stackplot(data=tips, x="day", stack="sex", normalize=True)
mp.get_axes("B").set_title("BlueRed")


# %%
# Stacked bar plot with more than two categories
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Stack plots work with multiple categories in the stack variable.
cns.figure(150, 100, "Ecotyper1")
ax = cns.stackplot(data=tips, x="sex", stack="time", normalize=True, addcount=True)
ax.set_title("Multiple Stack Categories")


# %%
# Complex stacked bar plot example
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create a more realistic biological example with multiple groups.
np.random.seed(42)
n_samples = 200
cell_data = pd.DataFrame(
    {
        "sample": np.repeat(
            ["Control", "Treatment A", "Treatment B", "Treatment C"], n_samples // 4
        ),
        "cell_type": np.random.choice(
            ["CD4+ T", "CD8+ T", "B cell", "NK cell", "Monocyte"],
            size=n_samples,
            p=[0.25, 0.2, 0.2, 0.15, 0.2],
        ),
    }
)

cns.figure(180, 120, "Ecotyper2")
ax = cns.stackplot(
    data=cell_data,
    x="sample",
    stack="cell_type",
    normalize=True,
    pairs=[("Control", "Treatment A"), ("Control", "Treatment B")],
    stack_order=["CD4+ T", "CD8+ T", "B cell", "NK cell", "Monocyte"],
)
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)
ax.set_title("Cell Type Composition")
ax.set_ylabel("Proportion")


# %%
# Horizontal stacked bar with count labels
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Combine horizontal orientation with count labels on the category axis.
cns.figure(120, 100, "Pastel1")
ax = cns.stackplot(
    data=tips,
    y="day",
    stack="sex",
    normalize=True,
    addcount=True,
    width=0.6,
)
ax.set_title("Horizontal with Labels")


# %%
# Stacked bar plot with counts vs proportions comparison
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare the same data shown as counts vs proportions.
mp = cns.multipanel(max_width=160)

mp.panel("A", 80, 130)
cns.stackplot(data=tips, x="day", stack="sex", normalize=False)
mp.get_axes("A").set_title("Absolute Counts")
mp.get_axes("A").set_ylabel("Count")

mp.newline()

mp.panel("B", 80, 130, margin_top=10)
cns.stackplot(data=tips, x="day", stack="sex", normalize=True, addcount=True)
mp.get_axes("B").set_title("Normalized Proportions")
mp.get_axes("B").set_ylabel("Proportion")
