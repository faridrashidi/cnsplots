"""
donutplot
---------

Create donut charts for visualizing proportions.

Donut charts are pie charts with a hole in the center, providing
a more modern look while maintaining the same proportional
visualization. The center can be used for additional information.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import numpy as np
import pandas as pd
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")
tips = sns.load_dataset("tips")


# %%
# Basic donut chart
# ~~~~~~~~~~~~~~~~~
# Show species distribution with center hole.
cns.figure(100, 100)
ax = cns.donutplot(iris, "species")
ax.set_title("Species Distribution")


# %%
# Donut chart with tips dataset
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Visualize distribution by day.
cns.figure(100, 100)
ax = cns.donutplot(tips, "day")
ax.set_title("Meals by Day")


# %%
# Donut chart by sex
# ~~~~~~~~~~~~~~~~~~
# Two-category donut chart.
cns.figure(100, 100)
ax = cns.donutplot(tips, "sex")
ax.set_title("Customers by Sex")


# %%
# Donut chart with custom order
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Control the order of categories.
cns.figure(100, 100)
ax = cns.donutplot(tips, "day", hue_order=["Thur", "Fri", "Sat", "Sun"])
ax.set_title("Custom Order")


# %%
# Donut chart for smoker status
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(100, 100)
ax = cns.donutplot(tips, "smoker")
ax.set_title("Smoker vs Non-Smoker")


# %%
# Donut chart with different palettes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use different color palettes.
cns.figure(100, 100, "Tableau")
ax = cns.donutplot(tips, "day")
ax.set_title("Tableau Palette")


# %%
# Donut chart with Set2 palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(100, 100, "Set2")
ax = cns.donutplot(iris, "species")
ax.set_title("Set2 Palette")


# %%
# Comparing donut charts
# ~~~~~~~~~~~~~~~~~~~~~~
# Compare composition across conditions.
mp = cns.multipanel((1, 2), max_width=300, hgap=100)

mp.panel("A", 100, 100)
cns.donutplot(tips[tips["sex"] == "Male"], "day")
mp.get_axes("A").set_title("Male Customers")

mp.panel("B", 100, 100)
cns.donutplot(tips[tips["sex"] == "Female"], "day")
mp.get_axes("B").set_title("Female Customers")


# %%
# Cell type composition donut
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Biological use case: cell type proportions.
np.random.seed(42)
cell_data = pd.DataFrame(
    {
        "cell_type": np.random.choice(
            ["T cells", "B cells", "NK cells", "Monocytes"],
            size=200,
            p=[0.35, 0.25, 0.15, 0.25],
        )
    }
)

cns.figure(100, 100, "Ecotyper2")
ax = cns.donutplot(cell_data, "cell_type")
ax.set_title("Cell Type Composition")


# %%
# Treatment response donut chart
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Visualize clinical outcome proportions.
response_data = pd.DataFrame(
    {
        "response": np.random.choice(
            ["Complete", "Partial", "Stable", "Progressive"],
            size=100,
            p=[0.2, 0.35, 0.3, 0.15],
        )
    }
)

cns.figure(100, 100, "Bold")
ax = cns.donutplot(response_data, "response")
ax.set_title("Treatment Response")


# %%
# Mutation status donut chart
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Common in cancer genomics.
mutation_data = pd.DataFrame(
    {"status": np.random.choice(["Wild Type", "Mutant"], size=150, p=[0.6, 0.4])}
)

cns.figure(100, 100, "BlueRed")
ax = cns.donutplot(mutation_data, "status")
ax.set_title("TP53 Mutation Status")


# %%
# Pie vs Donut comparison
# ~~~~~~~~~~~~~~~~~~~~~~~
# Compare the two visualization styles.
mp = cns.multipanel((1, 2), max_width=300, hgap=100)

mp.panel("A", 100, 100)
cns.pieplot(iris, "species")
mp.get_axes("A").set_title("Pie Chart")

mp.panel("B", 100, 100)
cns.donutplot(iris, "species")
mp.get_axes("B").set_title("Donut Chart")
