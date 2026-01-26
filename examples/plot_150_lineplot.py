"""
lineplot
--------

Create line plots for visualizing trends and time series data.

Line plots connect data points to show continuous trends,
useful for time series, experimental measurements over time,
and any sequential data.
"""

# %%
# Load data
# ~~~~~~~~~
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

import cnsplots as cns

fmri = sns.load_dataset("fmri")


# %%
# Basic line plot
# ~~~~~~~~~~~~~~~
# Plot signal over time with confidence intervals.
cns.figure(150, 100)
cns.lineplot(data=fmri, x="timepoint", y="signal")
plt.title("Basic Line Plot")


# %%
# Line plot with error bars
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``err_style="bars"`` for discrete error bars.
cns.figure(150, 100)
cns.lineplot(data=fmri, x="timepoint", y="signal", err_style="bars")
plt.title("With Error Bars")


# %%
# Grouped line plot with hue
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare trends across groups.
cns.figure(150, 100)
cns.lineplot(data=fmri, x="timepoint", y="signal", hue="event")
cns.take_legend_out()
plt.title("Grouped by Event")


# %%
# Line plot with hue and error bars
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Combine grouping with error visualization.
cns.figure(180, 100)
cns.lineplot(data=fmri, x="timepoint", y="signal", hue="event", err_style="bars")
cns.take_legend_out()
plt.title("Grouped with Error Bars")


# %%
# Line plot with style differentiation
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use different line styles for groups.
cns.figure(180, 100)
cns.lineplot(data=fmri, x="timepoint", y="signal", hue="event", style="event")
cns.take_legend_out()
plt.title("Different Line Styles")


# %%
# Multiple grouping levels
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Use both hue and style for complex comparisons.
cns.figure(180, 120)
cns.lineplot(data=fmri, x="timepoint", y="signal", hue="event", style="region")
cns.take_legend_out()
plt.title("Multiple Grouping Levels")


# %%
# Line plot without confidence interval
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set ``errorbar=None`` for clean lines.
cns.figure(150, 100)
cns.lineplot(data=fmri, x="timepoint", y="signal", hue="event", errorbar=None)
cns.take_legend_out()
plt.title("Without Confidence Interval")


# %%
# Custom time series data
# ~~~~~~~~~~~~~~~~~~~~~~~
# Create synthetic time series.
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=30, freq="D")
ts_data = pd.DataFrame(
    {
        "date": np.tile(dates, 2),
        "value": np.concatenate(
            [
                np.cumsum(np.random.randn(30)) + 100,
                np.cumsum(np.random.randn(30)) + 95,
            ]
        ),
        "group": ["A"] * 30 + ["B"] * 30,
    }
)

cns.figure(180, 100)
cns.lineplot(data=ts_data, x="date", y="value", hue="group")
cns.take_legend_out()
plt.title("Time Series Data")
_ = plt.xticks(rotation=30, ha="right")


# %%
# Line plot with markers
# ~~~~~~~~~~~~~~~~~~~~~~
# Add markers at data points.
cns.figure(150, 100)
cns.lineplot(
    data=fmri, x="timepoint", y="signal", hue="event", marker="o", markersize=3
)
cns.take_legend_out()
plt.title("With Markers")


# %%
# Line plot with custom palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use different color palettes.
cns.figure(150, 100, "Tableau")
cns.lineplot(data=fmri, x="timepoint", y="signal", hue="event")
cns.take_legend_out()
plt.title("Tableau Palette")


# %%
# Dose-response curve
# ~~~~~~~~~~~~~~~~~~~
# Common in pharmacology and biology.
np.random.seed(123)
doses = [0.1, 0.5, 1, 5, 10, 50, 100]
dose_response = []
for dose in doses:
    for replicate in range(5):
        response = 100 * dose / (dose + 10) + np.random.randn() * 5
        dose_response.append(
            {"dose": dose, "response": response, "replicate": replicate}
        )

dose_df = pd.DataFrame(dose_response)

cns.figure(150, 100)
cns.lineplot(data=dose_df, x="dose", y="response", marker="o")
plt.xscale("log")
plt.xlabel("Dose (log scale)")
plt.ylabel("Response (%)")
plt.title("Dose-Response Curve")


# %%
# Comparing multiple conditions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Side-by-side line plot comparison.
mp = cns.multipanel((1, 2), max_width=400, hgap=40)

mp.panel("A", 80, 140)
cns.lineplot(
    data=fmri[fmri["region"] == "parietal"], x="timepoint", y="signal", hue="event"
)
mp.get_axes("A").legend().remove()
mp.get_axes("A").set_title("Parietal Region")

mp.panel("B", 80, 140)
cns.lineplot(
    data=fmri[fmri["region"] == "frontal"], x="timepoint", y="signal", hue="event"
)
mp.get_axes("B").legend().remove()
mp.get_axes("B").set_title("Frontal Region")
