"""
Lollipop Plot
-------------

Create lollipop plots for comparing categorical data.

Lollipop plots are a cleaner alternative to bar plots, using a stem (line)
topped with a dot to represent aggregated values for each category. They
reduce visual clutter while clearly conveying the same information.
"""

# %%
# Load data
# ~~~~~~~~~
import numpy as np
import pandas as pd

import cnsplots as cns

tips = cns.datasets.load_dataset("tips")
iris = cns.datasets.load_dataset("iris")


# %%
# Basic lollipop plot
# ~~~~~~~~~~~~~~~~~~~
# Simple vertical lollipop plot showing mean values per category.
cns.figure(150, 100)
ax = cns.lollipopplot(data=tips, x="day", y="total_bill")
ax.set_title("Basic Lollipop Plot")


# %%
# Horizontal lollipop plot
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Swap x and y to create a horizontal layout automatically.
cns.figure(100, 180)
ax = cns.lollipopplot(data=tips, x="total_bill", y="day")
ax.set_title("Horizontal Lollipop")


# %%
# With error bars
# ~~~~~~~~~~~~~~~
# Add standard error bars to show variability.
cns.figure(150, 100)
ax = cns.lollipopplot(data=tips, x="day", y="total_bill", errorbar="se")
ax.set_title("With Standard Error")


# %%
# With standard deviation
# ~~~~~~~~~~~~~~~~~~~~~~~
# Show variability with standard deviation error bars.
cns.figure(150, 100)
ax = cns.lollipopplot(data=tips, x="day", y="total_bill", errorbar="sd")
ax.set_title("With Standard Deviation")


# %%
# Grouped lollipop plot with hue
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Split lollipops by a secondary categorical variable.
cns.figure(180, 100, "BlueRed")
ax = cns.lollipopplot(data=tips, x="day", y="total_bill", hue="sex")
cns.take_legend_out()


# %%
# Grouped with error bars
# ~~~~~~~~~~~~~~~~~~~~~~~
# Combine hue grouping with error bars.
cns.figure(180, 100, "BlueRed")
ax = cns.lollipopplot(data=tips, x="day", y="total_bill", hue="sex", errorbar="se")
cns.take_legend_out()


# %%
# Statistical comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~
# Add significance annotations for specific pairs.
cns.figure(150, 100, "Set1")
cns.lollipopplot(
    data=tips,
    x="day",
    y="total_bill",
    pairs=[("Thur", "Fri"), ("Sat", "Sun")],
)


# %%
# With value labels
# ~~~~~~~~~~~~~~~~~
# Display the mean value at each dot.
cns.figure(150, 100, "Tableau")
cns.lollipopplot(data=tips, x="day", y="total_bill", addtip=True)


# %%
# Custom order
# ~~~~~~~~~~~~
# Specify the order of categories.
cns.figure(150, 100, "Tableau")
cns.lollipopplot(
    data=tips,
    x="day",
    y="total_bill",
    order=["Thur", "Fri", "Sat", "Sun"],
)


# %%
# Custom styling
# ~~~~~~~~~~~~~~
# Adjust marker size, line width, and marker shape.
cns.figure(150, 100, "Bold")
cns.lollipopplot(
    data=tips,
    x="day",
    y="total_bill",
    markersize=60,
    linewidth=2.5,
    marker="D",
)


# %%
# Horizontal with hue
# ~~~~~~~~~~~~~~~~~~~~
# Horizontal grouped lollipop plot.
cns.figure(120, 180, "BlueRed")
ax = cns.lollipopplot(
    data=tips,
    x="total_bill",
    y="day",
    hue="sex",
    order=["Thur", "Fri", "Sat", "Sun"],
)
cns.take_legend_out()


# %%
# Species comparison
# ~~~~~~~~~~~~~~~~~~
# Compare measurements across species with value labels.
cns.figure(150, 100, "Bold")
ax = cns.lollipopplot(
    data=iris, x="species", y="sepal_width", addtip=True, errorbar="se"
)
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)


# %%
# Gene expression comparison
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Biological example: gene expression by condition.
np.random.seed(42)
gene_data = pd.DataFrame(
    {
        "gene": ["TP53"] * 30 + ["BRCA1"] * 30 + ["MYC"] * 30,
        "expression": np.concatenate(
            [
                np.random.normal(5, 1, 30),
                np.random.normal(3, 0.8, 30),
                np.random.normal(7, 1.5, 30),
            ]
        ),
        "condition": (["Control"] * 15 + ["Treatment"] * 15) * 3,
    }
)

cns.figure(180, 100)
ax = cns.lollipopplot(
    data=gene_data,
    x="gene",
    y="expression",
    hue="condition",
    errorbar="se",
)
ax.set_ylabel("Expression (log2 TPM)")
cns.take_legend_out()


# %%
# Median estimator
# ~~~~~~~~~~~~~~~~
# Use median instead of mean for robust estimation.
cns.figure(150, 100)
ax = cns.lollipopplot(
    data=tips, x="day", y="total_bill", estimator="median", addtip=True
)
ax.set_title("Median Total Bill")
