"""
Dumbbell Plot
-------------

Create dumbbell plots that compare two numeric values per category. Each
category is drawn as a horizontal line with two colored endpoints, making
before/after and two-group comparisons easy to scan.
"""

# %%
# Load data
# ~~~~~~~~~
import cnsplots as cns

tips = cns.datasets.load_dataset("tips")

dumbbell_data = tips.groupby(
    ["day", "sex"],
    as_index=False,
    observed=True,
)["total_bill"].mean()
dumbbell_data = dumbbell_data.rename(columns={"sex": "condition"})

# %%
# Basic dumbbell plot
# ~~~~~~~~~~~~~~~~~~~
# Compare mean total bills by sex across days.
cns.figure(180, 120)
ax = cns.dumbbellplot(
    dumbbell_data,
    x="total_bill",
    y="day",
    hue="condition",
)

# %%
# Custom order and endpoint order
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(180, 120)
ax = cns.dumbbellplot(
    dumbbell_data,
    x="total_bill",
    y="day",
    hue="condition",
    order=["Thur", "Fri", "Sat", "Sun"],
    hue_order=["Female", "Male"],
    markersize=40,
    linewidth=2,
)

# %%
# Multipanel dumbbell plot
# ~~~~~~~~~~~~~~~~~~~~~~~~~
mp = cns.multipanel(max_width=420)

mp.panel("A", 160, 120)
cns.dumbbellplot(
    dumbbell_data,
    x="total_bill",
    y="day",
    hue="condition",
)

mp.panel("B", 160, 120)
weekend = dumbbell_data[dumbbell_data["day"].isin(["Sat", "Sun"])]
cns.dumbbellplot(
    weekend,
    x="total_bill",
    y="day",
    hue="condition",
)
