"""
Ridge Plot
----------

Create ridge plots (joy plots) for comparing distributions across categories.

Ridge plots stack density curves vertically, making them ideal for comparing
how distributions change across ordered categories like time periods or
experimental conditions.
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
# Basic ridge plot
# ~~~~~~~~~~~~~~~~
# Compare distributions across days.
cns.figure(150, 150)
ax = cns.ridgeplot(data=tips, x="total_bill", y="day")
ax.set_title("Total Bill by Day")

# %%
# Ridge plot with custom colormap
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use the ``cmap`` parameter to change the colormap.
cns.figure(150, 150)
ax = cns.ridgeplot(data=tips, x="total_bill", y="day", cmap="plasma")
ax.set_title("Total Bill by Day (plasma cmap)")


# %%
# Ridge plot for iris data
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Compare species distributions.
cns.figure(120, 150)
ax = cns.ridgeplot(data=iris, x="sepal_length", y="species")
ax.set_title("Sepal Length by Species")


# %%
# Ridge plot with different measurements
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare petal measurements.
cns.figure(120, 150)
ax = cns.ridgeplot(data=iris, x="petal_length", y="species")
ax.set_title("Petal Length by Species")


# %%
# Ridge plot comparing multiple variables
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Side-by-side comparison.
mp = cns.multipanel(max_width=400)

mp.panel("A", 150, 100, pad_left=100, margin_right=20)
cns.ridgeplot(data=iris, x="sepal_length", y="species")
mp.get_axes("A").set_title("Sepal Length")

mp.panel("B", 150, 100, pad_left=100, margin_right=0)
cns.ridgeplot(data=iris, x="sepal_width", y="species")
mp.get_axes("B").set_title("Sepal Width")


# %%
# Ridge plot with tips by time
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare lunch and dinner distributions.
cns.figure(100, 150)
ax = cns.ridgeplot(data=tips, x="tip", y="time")
ax.set_title("Tip by Time")


# %%
# Ridge plot for simulated temporal data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Demonstrate distributions changing over time.
np.random.seed(42)
temporal_data = []
for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]:
    shift = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"].index(month) * 2
    values = np.random.normal(20 + shift, 5, 200)
    for v in values:
        temporal_data.append({"month": month, "value": v})

temporal_df = pd.DataFrame(temporal_data)

cns.figure(180, 150)
ax = cns.ridgeplot(data=temporal_df, x="value", y="month")
ax.set_title("Value Distribution Over Months")


# %%
# Ridge plot for experimental conditions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare treatment effects.
np.random.seed(42)
treatment_data = []
for treatment in ["Control", "Low Dose", "Medium Dose", "High Dose"]:
    if treatment == "Control":
        values = np.random.normal(50, 10, 150)
    elif treatment == "Low Dose":
        values = np.random.normal(55, 12, 150)
    elif treatment == "Medium Dose":
        values = np.random.normal(65, 8, 150)
    else:
        values = np.random.normal(80, 15, 150)
    for v in values:
        treatment_data.append({"treatment": treatment, "response": v})

treatment_df = pd.DataFrame(treatment_data)

cns.figure(150, 150)
ax = cns.ridgeplot(data=treatment_df, x="response", y="treatment")
ax.set_title("Treatment Response Distribution")
