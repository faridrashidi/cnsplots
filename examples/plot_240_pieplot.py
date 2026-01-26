"""
pieplot
-------

Create pie charts for visualizing proportions.

Pie charts show how a whole is divided into parts, useful for
displaying composition or market share data. Best used with
a small number of categories (2-6).
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
# Basic pie chart
# ~~~~~~~~~~~~~~~
# Show species distribution in the iris dataset.
cns.figure(100, 100)
ax = cns.pieplot(iris, "species")
ax.set_title("Species Distribution")


# %%
# Pie chart with tips dataset
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Visualize distribution by day.
cns.figure(100, 100)
ax = cns.pieplot(tips, "day")
ax.set_title("Meals by Day")


# %%
# Pie chart by sex
# ~~~~~~~~~~~~~~~~
# Two-category pie chart.
cns.figure(100, 100)
ax = cns.pieplot(tips, "sex")
ax.set_title("Customers by Sex")


# %%
# Pie chart with custom order
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Control the order of categories.
cns.figure(100, 100)
ax = cns.pieplot(tips, "day", hue_order=["Thur", "Fri", "Sat", "Sun"])
ax.set_title("Custom Order")


# %%
# Pie chart for smoker status
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(100, 100)
ax = cns.pieplot(tips, "smoker")
ax.set_title("Smoker vs Non-Smoker")


# %%
# Pie chart with different palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use different color palettes.
cns.figure(100, 100, "Tableau")
ax = cns.pieplot(tips, "day")
ax.set_title("Tableau Palette")


# %%
# Pie chart with Set2 palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(100, 100, "Set2")
ax = cns.pieplot(iris, "species")
ax.set_title("Set2 Palette")


# %%
# Comparing pie charts side-by-side
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare composition across conditions.
mp = cns.multipanel((1, 2), max_width=270, hgap=70)

mp.panel("A", 100, 100)
cns.pieplot(tips[tips["sex"] == "Male"], "day")
mp.get_axes("A").set_title("Male Customers")

mp.panel("B", 100, 100)
cns.pieplot(tips[tips["sex"] == "Female"], "day")
mp.get_axes("B").set_title("Female Customers")


# %%
# Biological sample composition
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Common use case: cell type proportions.
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

cns.figure(100, 100, "Ecotyper1")
ax = cns.pieplot(cell_data, "cell_type")
ax.set_title("Cell Type Composition")


# %%
# Treatment response pie chart
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Visualize outcome proportions.
response_data = pd.DataFrame(
    {
        "response": np.random.choice(
            [
                "Complete Response",
                "Partial Response",
                "Stable Disease",
                "Progressive Disease",
            ],
            size=100,
            p=[0.2, 0.35, 0.3, 0.15],
        )
    }
)

cns.figure(100, 100, "Bold")
ax = cns.pieplot(response_data, "response")
ax.set_title("Treatment Response")
