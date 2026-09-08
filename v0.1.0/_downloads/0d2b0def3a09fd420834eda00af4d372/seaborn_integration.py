"""
Seaborn Integration
-------------------

Use native seaborn plotting with cnsplots sizing, styling, and export helpers.

These examples intentionally stick to seaborn's plotting API and only use
``cns.figure()`` and ``cns.save()`` from cnsplots.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
from pathlib import Path
import tempfile

import matplotlib.pyplot as plt
import seaborn as sns

import cnsplots as cns


# %%
# Load example datasets
# ~~~~~~~~~~~~~~~~~~~~~
tips = sns.load_dataset("tips")
penguins = sns.load_dataset("penguins").dropna(
    subset=["bill_length_mm", "bill_depth_mm", "species", "sex"]
)
flights = sns.load_dataset("flights")


# %%
# Scatter plot with seaborn
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# cnsplots prepares the canvas while seaborn handles the plot.
cns.figure(160, 220)
ax = plt.gca()
sns.scatterplot(
    data=penguins,
    x="bill_length_mm",
    y="bill_depth_mm",
    hue="species",
    style="sex",
    s=45,
    ax=ax,
)
ax.set_xlabel("Bill length (mm)")
ax.set_ylabel("Bill depth (mm)")
ax.set_title("Seaborn with cns.figure")


# %%
# Two seaborn plots on one cnsplots canvas
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Axes-level seaborn functions work naturally with matplotlib subplots.
cns.figure(170, 320)
fig = plt.gcf()
ax_left, ax_right = fig.subplots(1, 2)

sns.boxplot(
    data=tips,
    x="day",
    y="total_bill",
    hue="sex",
    ax=ax_left,
)
ax_left.set_xlabel("")
ax_left.set_ylabel("Total bill")
ax_left.set_title("Box plot")

sns.histplot(
    data=tips,
    x="tip",
    hue="sex",
    element="step",
    stat="density",
    common_norm=False,
    ax=ax_right,
)
ax_right.set_xlabel("Tip")
ax_right.set_ylabel("Density")
ax_right.set_title("Histogram")

fig.tight_layout()


# %%
# Save a seaborn figure with cns.save
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Export the current seaborn figure using the cnsplots save helper.
monthly_passengers = (
    flights.groupby("year", as_index=False)["passengers"]
    .mean()
    .rename(columns={"passengers": "mean_passengers"})
)
export_dir = Path(tempfile.gettempdir()) / "cnsplots-gallery"
export_dir.mkdir(parents=True, exist_ok=True)

cns.figure(150, 200)
ax = plt.gca()
sns.lineplot(
    data=monthly_passengers,
    x="year",
    y="mean_passengers",
    marker="o",
    linewidth=2,
    ax=ax,
)
ax.set_xlabel("Year")
ax.set_ylabel("Mean passengers")
ax.set_title("Saved with cns.save")

export_path = export_dir / "seaborn_with_cns.pdf"
cns.save(export_path)
print(f"Saved demo figure to {export_path}")
