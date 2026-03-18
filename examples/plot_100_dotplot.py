"""
dotplot
-------

Create dot plots for visualizing grouped data with size and color encoding.

Dot plots display data points where both size and color can encode
different variables, making them ideal for showing multiple dimensions
of grouped categorical data.
"""

# %%
# Load data
# ~~~~~~~~~
import numpy as np
import pandas as pd
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")
iris = sns.load_dataset("iris")


# %%
# Basic dotplot
# ~~~~~~~~~~~~~
# Aggregate data and display with size and color encoding.
tips_agg = tips.groupby(["day", "sex"]).agg({"total_bill": ["mean", "count"]})
tips_agg.columns = ["mean_bill", "count"]
tips_agg = tips_agg.reset_index()

cns.figure(80, 50)
dp = cns.dotplot(
    tips_agg,
    x="sex",
    y="day",
    color="mean_bill",
    size="count",
    value="count",
    max_s=60,
)
dp.ax_heatmap.set_title("Basic Dotplot")


# %%
# Dotplot with min values
# ~~~~~~~~~~~~~~~~~~~~~~~
# Display minimum values instead of counts.
tips_minmax = tips.groupby(["day", "sex"]).agg({"total_bill": ["min", "size"]})
tips_minmax.columns = ["min", "size"]
tips_minmax = tips_minmax.reset_index()

cns.figure(80, 50)
cns.dotplot(
    tips_minmax,
    x="sex",
    y="day",
    color="size",
    size="min",
    value="size",
    max_s=60,
)


# %%
# Gene expression dotplot
# ~~~~~~~~~~~~~~~~~~~~~~~
# Biological example: gene expression across cell types.
np.random.seed(42)
genes = ["TP53", "BRCA1", "MYC", "EGFR", "KRAS"]
cell_types = ["T cells", "B cells", "Macrophages", "NK cells"]
gene_expr = []
for gene in genes:
    for cell in cell_types:
        pct = np.random.uniform(20, 100)
        expr = np.random.uniform(0.5, 3)
        gene_expr.append(
            {"gene": gene, "cell_type": cell, "pct_expressed": pct, "mean_expr": expr}
        )
gene_df = pd.DataFrame(gene_expr)

cns.figure(120, 100)
dp = cns.dotplot(
    gene_df,
    x="gene",
    y="cell_type",
    color="pct_expressed",
    size="pct_expressed",
    value="pct_expressed",
    max_s=80,
    ylabel_kws={"labelpad": 50},
)
dp.ax_heatmap.set_title("Gene Expression by Cell Type")


# %%
# Larger dotplot with more categories
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Expanded grid with many genes and cell types.
np.random.seed(42)
genes = ["TP53", "BRCA1", "MYC", "EGFR", "KRAS", "PIK3CA", "PTEN", "RB1"]
cell_types = [
    "T cells",
    "B cells",
    "Macrophages",
    "NK cells",
    "Fibroblasts",
    "Epithelial",
]
gene_expr = []
for gene in genes:
    for cell in cell_types:
        pct = np.random.uniform(10, 100)
        expr = np.random.uniform(0, 4)
        gene_expr.append(
            {"gene": gene, "cell_type": cell, "pct_expressed": pct, "mean_expr": expr}
        )
gene_df = pd.DataFrame(gene_expr)

cns.figure(150, 120)
cns.dotplot(
    gene_df,
    x="gene",
    y="cell_type",
    color="pct_expressed",
    size="pct_expressed",
    value="pct_expressed",
    max_s=100,
    ylabel_kws={"labelpad": 50},
)


# %%
# Dotplot with custom colormap
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use a different colormap for color encoding.
cns.figure(150, 100)
cns.dotplot(
    gene_df,
    x="gene",
    y="cell_type",
    color="pct_expressed",
    size="mean_expr",
    value="pct_expressed",
    max_s=80,
    cmap="gnuplot",
    xlabel_kws={"labelpad": 20},
    ylabel_kws={"labelpad": 50},
)


# %%
# Dotplot with size encoding only
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Display dots with size encoding.
cns.figure(150, 100)
cns.dotplot(
    gene_df,
    x="gene",
    y="cell_type",
    color="pct_expressed",
    size="mean_expr",
    value="pct_expressed",
    max_s=80,
    ylabel_kws={"labelpad": 50},
)


# %%
# Survival analysis summary dotplot
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Display hazard ratios and p-values as a dotplot.
np.random.seed(42)
cox_summary = pd.DataFrame(
    {
        "covariate": ["Age", "Stage", "Grade", "Treatment", "Biomarker"],
        "group": ["Clinical"] * 3 + ["Treatment"] * 2,
        "HR": [1.2, 2.5, 1.8, 0.6, 1.5],
        "neg_log_p": [2.5, 4.0, 3.2, 3.8, 2.0],
    }
)

cns.figure(80, 100)
dp = cns.dotplot(
    cox_summary,
    x="covariate",
    y="group",
    color="HR",
    size="neg_log_p",
    value="HR",
    max_s=100,
    xlabel_kws={"labelpad": 20},
    ylabel_kws={"labelpad": 20},
)
dp.ax_heatmap.set_title("Cox Regression Summary")


# %%
# Pathway enrichment dotplot
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Display pathway analysis results.
np.random.seed(42)
pathways = pd.DataFrame(
    {
        "pathway": [
            "Cell cycle",
            "Apoptosis",
            "DNA repair",
            "Immune response",
            "Metabolism",
            "Signaling",
        ],
        "category": ["Proliferation"] * 2
        + ["DNA"] * 1
        + ["Immune"] * 1
        + ["Metabolic"] * 2,
        "enrichment": [3.5, 2.8, 4.1, 2.2, 1.8, 2.5],
        "neg_log_fdr": [5.2, 3.8, 6.5, 2.5, 1.5, 3.0],
        "gene_count": [25, 18, 32, 15, 12, 20],
    }
)

cns.figure(100, 100)
dp = cns.dotplot(
    pathways,
    x="pathway",
    y="category",
    color="gene_count",
    size="enrichment",
    value="gene_count",
    max_s=120,
    cmap="hot",
    xlabel_kws={"labelpad": 30},
    ylabel_kws={"labelpad": 25},
)
dp.ax_heatmap.set_title("Pathway Enrichment")


# %%
# Time series summary dotplot
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Summarize measurements across time points.
np.random.seed(42)
timepoints = ["Day 0", "Day 7", "Day 14", "Day 21"]
markers = ["CD4", "CD8", "CD19", "CD56"]
time_data = []
for tp in timepoints:
    for marker in markers:
        mean_val = np.random.uniform(5, 50)
        cv = np.random.uniform(10, 40)
        time_data.append(
            {"timepoint": tp, "marker": marker, "mean": mean_val, "cv": cv}
        )
time_df = pd.DataFrame(time_data)

cns.figure(100, 80)
dp = cns.dotplot(
    time_df,
    x="timepoint",
    y="marker",
    color="mean",
    size="cv",
    value="mean",
    max_s=80,
    ylabel_kws={"labelpad": 20},
)
dp.ax_heatmap.set_title("Marker Expression Over Time")
