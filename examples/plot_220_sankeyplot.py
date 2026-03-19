"""
sankeyplot
----------

Create Sankey diagrams for visualizing flows between categories.

Sankey diagrams show how quantities flow from one set of categories
to another, useful for visualizing transitions, migrations, or
relationships between categorical variables.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import numpy as np
import pandas as pd

import cnsplots as cns

# %%
# Create sample data
# ~~~~~~~~~~~~~~~~~~
data = pd.DataFrame(
    {
        "x": ["A", "A", "B", "B", "C", "C"],
        "y": ["X", "Y", "Y", "Z", "X", "Z"],
    }
)


# %%
# Basic Sankey diagram
# ~~~~~~~~~~~~~~~~~~~~
# Show flows from categories A, B, C to X, Y, Z.
cns.figure(100, 80)
ax = cns.sankeyplot(data=data, x="x", y="y")
ax.set_title("Basic Sankey")


# %%
# Rotated labels for narrow layouts
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Rotate Sankey labels to improve readability in compact panels.
rotated_label_data = pd.DataFrame(
    {
        "source": [
            "Baseline visit",
            "Baseline visit",
            "Follow-up visit",
            "Follow-up visit",
            "Extended monitoring",
            "Extended monitoring",
        ],
        "target": [
            "Complete response",
            "Stable disease",
            "Stable disease",
            "Progressive disease",
            "Complete response",
            "Progressive disease",
        ],
    }
)

cns.figure(90, 110)
ax = cns.sankeyplot(data=rotated_label_data, x="source", y="target", label_rotation=45)
ax.set_title("Rotated Labels")


# %%
# Treatment to outcome flow
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Visualize patient flow from treatment to outcome.
np.random.seed(42)
n = 150
treatment_data = pd.DataFrame(
    {
        "treatment": np.random.choice(
            ["Drug A", "Drug B", "Placebo"], n, p=[0.4, 0.35, 0.25]
        ),
        "outcome": np.random.choice(
            ["Improved", "Stable", "Worsened"], n, p=[0.5, 0.3, 0.2]
        ),
    }
)

cns.figure(120, 100)
ax = cns.sankeyplot(data=treatment_data, x="treatment", y="outcome")
ax.set_title("Treatment to Outcome")


# %%
# Disease stage progression
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Show how patients transition between stages.
stage_data = pd.DataFrame(
    {
        "baseline": np.random.choice(
            ["Stage I", "Stage II", "Stage III"], 100, p=[0.4, 0.35, 0.25]
        ),
        "followup": np.random.choice(
            ["Stage I", "Stage II", "Stage III", "Stage IV"],
            100,
            p=[0.25, 0.3, 0.25, 0.2],
        ),
    }
)

cns.figure(140, 100)
ax = cns.sankeyplot(data=stage_data, x="baseline", y="followup")
ax.set_title("Disease Stage Progression")


# %%
# Cell type transition
# ~~~~~~~~~~~~~~~~~~~~
# Visualize cell differentiation patterns.
cell_transition = pd.DataFrame(
    {
        "initial": np.random.choice(
            ["Stem", "Progenitor", "Precursor"], 80, p=[0.3, 0.4, 0.3]
        ),
        "final": np.random.choice(
            ["T cell", "B cell", "NK cell", "Monocyte"], 80, p=[0.3, 0.25, 0.2, 0.25]
        ),
    }
)

cns.figure(120, 100)
ax = cns.sankeyplot(data=cell_transition, x="initial", y="final")
ax.set_title("Cell Differentiation")


# %%
# Cluster assignment comparison
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare clustering results between methods.
cluster_comparison = pd.DataFrame(
    {
        "method_A": np.random.choice(
            ["Cluster 1", "Cluster 2", "Cluster 3"], 120, p=[0.35, 0.35, 0.3]
        ),
        "method_B": np.random.choice(
            ["Group A", "Group B", "Group C", "Group D"], 120, p=[0.25, 0.3, 0.25, 0.2]
        ),
    }
)

cns.figure(140, 100)
ax = cns.sankeyplot(data=cluster_comparison, x="method_A", y="method_B")
ax.set_title("Clustering Comparison")


# %%
# Response to treatment over time
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Track patient responses at different timepoints.
response_flow = pd.DataFrame(
    {
        "week_0": np.random.choice(["Responder", "Non-responder"], 80, p=[0.6, 0.4]),
        "week_12": np.random.choice(
            ["Complete", "Partial", "None"], 80, p=[0.4, 0.35, 0.25]
        ),
    }
)

cns.figure(120, 100)
ax = cns.sankeyplot(data=response_flow, x="week_0", y="week_12")
ax.set_title("Response at Week 0 to Week 12")


# %%
# Simple binary flow
# ~~~~~~~~~~~~~~~~~~
# Two-category to two-category flow.
binary_data = pd.DataFrame(
    {
        "before": np.random.choice(["Control", "Treatment"], 60, p=[0.5, 0.5]),
        "after": np.random.choice(["Success", "Failure"], 60, p=[0.6, 0.4]),
    }
)

cns.figure(100, 80)
ax = cns.sankeyplot(data=binary_data, x="before", y="after")
ax.set_title("Treatment Success")


# %%
# Biomarker to phenotype
# ~~~~~~~~~~~~~~~~~~~~~~
# Link molecular markers to clinical phenotypes.
biomarker_data = pd.DataFrame(
    {
        "biomarker": np.random.choice(["High", "Medium", "Low"], 90, p=[0.3, 0.4, 0.3]),
        "phenotype": np.random.choice(["Aggressive", "Indolent"], 90, p=[0.45, 0.55]),
    }
)

cns.figure(120, 90)
ax = cns.sankeyplot(data=biomarker_data, x="biomarker", y="phenotype")
ax.set_title("Biomarker to Phenotype")
