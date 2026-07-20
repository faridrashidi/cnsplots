"""
Survival Analysis
-----------------

Create Kaplan-Meier survival curves and cumulative incidence plots.

Survival plots are essential for time-to-event analysis in clinical and
biological research. cnsplots provides automatic statistical testing
(log-rank test) and hazard ratio calculation.
"""

# %%
# Load data
# ~~~~~~~~~
import lifelines as ll
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import cnsplots as cns

waltons = ll.datasets.load_waltons()


# %%
# Basic survival plot (two groups)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Kaplan-Meier survival curves with automatic log-rank test.
cns.figure(150, 150)
cns.survivalplot(
    data=waltons, duration="T", event="E", hue="group", hue_order=["miR-137", "control"]
)
_ = plt.legend(loc="upper right")
plt.title("Kaplan-Meier Survival Curves")


# %%
# Survival plot with legend outside
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Move legend to avoid overlapping curves.
cns.figure(150, 180)
cns.survivalplot(
    data=waltons, duration="T", event="E", hue="group", hue_order=["miR-137", "control"]
)
cns.take_legend_out()
plt.title("Survival with External Legend")


# %%
# Cumulative incidence plot
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Show cumulative incidence instead of survival probability.
cns.figure(150, 150)
ax = cns.cumulativeincidenceplot(
    data=waltons,
    duration="T",
    event="E",
    hue="group",
    hue_order=["miR-137", "control"],
    xticks=np.arange(0, waltons["T"].max() + 2, 12),
    show_risk_table=True,
    risk_table_ypos=-0.2,
)
ax.set_xlabel("Time (Months)")
_ = plt.legend(loc="upper left")
plt.title("Cumulative Incidence")


# %%
# Cumulative incidence without risk table
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Cleaner plot without the risk table.
cns.figure(150, 150)
ax = cns.cumulativeincidenceplot(
    data=waltons,
    duration="T",
    event="E",
    hue="group",
    hue_order=["miR-137", "control"],
    show_risk_table=False,
)
ax.set_xlabel("Time (Months)")
_ = plt.legend(loc="upper left")
plt.title("Cumulative Incidence (No Risk Table)")


# %%
# Survival plot with custom colors
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use different color palettes.
cns.figure(150, 150, "BlueRed")
cns.survivalplot(data=waltons, duration="T", event="E", hue="group")
cns.take_legend_out()
plt.title("BlueRed Palette")


# %%
# Simulated clinical trial data (multiple groups)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create synthetic data with multiple treatment groups.
np.random.seed(42)
n_patients = 150

# Simulate different survival characteristics for each group
survival_data = []

# Control group - baseline survival
control_times = np.random.exponential(scale=24, size=n_patients // 3)
control_events = np.random.binomial(1, 0.7, n_patients // 3)
for t, e in zip(control_times, control_events):
    survival_data.append({"time": t, "event": e, "group": "Control"})

# Treatment A - moderate improvement
treatment_a_times = np.random.exponential(scale=36, size=n_patients // 3)
treatment_a_events = np.random.binomial(1, 0.6, n_patients // 3)
for t, e in zip(treatment_a_times, treatment_a_events):
    survival_data.append({"time": t, "event": e, "group": "Treatment A"})

# Treatment B - strong improvement
treatment_b_times = np.random.exponential(scale=48, size=n_patients // 3)
treatment_b_events = np.random.binomial(1, 0.5, n_patients // 3)
for t, e in zip(treatment_b_times, treatment_b_events):
    survival_data.append({"time": t, "event": e, "group": "Treatment B"})

clinical_df = pd.DataFrame(survival_data)


# %%
# Survival plot with three groups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare multiple treatment arms.
cns.figure(150, 180)
cns.survivalplot(
    data=clinical_df,
    duration="time",
    event="event",
    hue="group",
    hue_order=["Control", "Treatment A", "Treatment B"],
)
cns.take_legend_out()
plt.title("Three-Arm Clinical Trial")
plt.xlabel("Time (Months)")


# %%
# Cumulative incidence with three groups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Show cumulative events for multiple groups.
cns.figure(150, 180)
ax = cns.cumulativeincidenceplot(
    data=clinical_df,
    duration="time",
    event="event",
    hue="group",
    hue_order=["Control", "Treatment A", "Treatment B"],
    show_risk_table=True,
    risk_table_ypos=-0.25,
)
ax.set_xlabel("Time (Months)")
cns.take_legend_out()
plt.title("Cumulative Incidence - Three Arms")


# %%
# Side-by-side survival comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare survival vs cumulative incidence.
mp = cns.multipanel(max_width=450)

mp.panel("A", 160, 120)
cns.survivalplot(
    data=waltons,
    duration="T",
    event="E",
    hue="group",
)
mp.get_axes("A").legend().remove()
mp.get_axes("A").set_title("Survival Probability")

mp.panel("B", 160, 120)
cns.cumulativeincidenceplot(
    data=waltons,
    duration="T",
    event="E",
    hue="group",
    show_risk_table=False,
)
mp.get_axes("B").legend().remove()
mp.get_axes("B").set_title("Cumulative Incidence")


# %%
# Survival with biomarker stratification
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Stratify patients by biomarker expression.
np.random.seed(123)
n = 200

# Simulate biomarker data
biomarker_data = []
for _ in range(n // 2):
    # Low expression - worse survival
    time = np.random.exponential(scale=20)
    event = np.random.binomial(1, 0.8)
    biomarker_data.append({"time": time, "event": event, "biomarker": "Low"})

for _ in range(n // 2):
    # High expression - better survival
    time = np.random.exponential(scale=40)
    event = np.random.binomial(1, 0.5)
    biomarker_data.append({"time": time, "event": event, "biomarker": "High"})

biomarker_df = pd.DataFrame(biomarker_data)

cns.figure(150, 150)
cns.survivalplot(
    data=biomarker_df,
    duration="time",
    event="event",
    hue="biomarker",
    hue_order=["High", "Low"],
)
cns.take_legend_out()
plt.title("Survival by Biomarker Expression")
plt.xlabel("Time (Months)")


# %%
# Cumulative incidence with custom x-axis ticks
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Control the time axis display.
cns.figure(150, 180)
ax = cns.cumulativeincidenceplot(
    data=waltons,
    duration="T",
    event="E",
    hue="group",
    hue_order=["miR-137", "control"],
    xticks=np.arange(0, 80, 10),
    show_risk_table=True,
    risk_table_ypos=-0.2,
)
ax.set_xlabel("Time (Months)")
_ = plt.legend(loc="upper left")
plt.title("Custom X-Axis Ticks")


# %%
# Survival analysis with censoring visualization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# The curves automatically handle censored observations (shown as vertical marks).
cns.figure(150, 150)
cns.survivalplot(
    data=clinical_df,
    duration="time",
    event="event",
    hue="group",
    hue_order=["Control", "Treatment B"],
)
cns.take_legend_out()
plt.title("Survival with Censoring Marks")
plt.xlabel("Time (Months)")
