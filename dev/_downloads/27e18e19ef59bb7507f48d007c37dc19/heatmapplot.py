"""
Heatmap
-------

Create complex clustered heatmaps with annotations and dendrograms.

Heatmaps are essential for visualizing matrix data, gene expression patterns,
and correlation matrices. cnsplots provides publication-ready heatmaps with
hierarchical clustering, row/column annotations, and customizable colormaps.
"""

# %%
# Load data
# ~~~~~~~~~
import numpy as np
import pandas as pd
import scanpy as sc

import cnsplots as cns

# Create synthetic expression data
np.random.seed(42)
blobs = sc.datasets.blobs()
blobs.obs["mitf"] = np.random.random(blobs.shape[0])
blobs.var["ensemble"] = [f"ens{x}" for x in np.random.randint(0, 3, blobs.shape[1])]
blobs.obs["selected"] = np.where(blobs.obs["mitf"] > 0.95, "o", None)
blobs.obs["cluster"] = pd.Categorical(
    [f"C{x}" for x in np.random.randint(0, 4, blobs.shape[0])]
)
blobs_full = blobs[:24, :].copy()
blobs_annot = blobs[:120, :].copy()


# %%
# Full-featured clustered heatmap
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Complete heatmap with clustering, annotations, and dendrograms.
# Use a display subset to keep the gallery image readable and stable to render.
cns.figure(250, 300)
cmp = cns.heatmapplot(
    blobs_full,
    label="Expression",
    xlabel="Genes",
    ylabel="Samples",
    row_annotation=["selected", "mitf", "blobs"],
    col_annotation=["ensemble"],
    row_split=5,
    row_cluster=True,
    col_cluster=True,
    row_cluster_method="ward",
    row_cluster_metric="euclidean",
    col_cluster_method="ward",
    col_cluster_metric="euclidean",
    show_rownames=True,
    show_colnames=True,
    xticklabels_fontsize=7,
    yticklabels_fontsize=7,
    row_dendrogram=True,
    col_dendrogram=True,
    row_split_gap=1,
    col_split_gap=1,
    legend_hpad=-2,
    legend_vpad=1,
    legend_width=15,
    xlabel_labelpad=-3,
)
cmp.ax.set_title("Basic Heatmapplot")
print(f"Row clusters: {len(cmp.row_order)}, Col clusters: {len(cmp.col_order)}")


# %%
# Heatmap from a DataFrame
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Pass a numeric DataFrame directly without converting it to AnnData. Its index and
# columns become the heatmap labels. A two-dimensional NumPy array can be passed in
# the same way and uses integer labels.
expression_df = pd.DataFrame(
    np.random.default_rng(42).normal(size=(12, 8)),
    index=pd.Index([f"Sample {index + 1}" for index in range(12)]),
    columns=pd.Index([f"Feature {index + 1}" for index in range(8)]),
)

cns.figure(200, 220)
cmp = cns.heatmapplot(
    expression_df,
    label="Value",
    xlabel="Features",
    ylabel="Samples",
    row_cluster=True,
    col_cluster=True,
    show_rownames=True,
    show_colnames=True,
    yticklabels_fontsize=6,
    legend_hpad=5,
)


# %%
# Simple heatmap without clustering
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Basic heatmap showing raw data without reordering.
cns.figure(200, 250)
cmp = cns.heatmapplot(
    blobs[:20, :],  # Subset for readable row labels
    label="Expression",
    xlabel="Genes",
    ylabel="Samples",
    row_cluster=False,
    col_cluster=False,
    show_rownames=True,
    show_colnames=True,
    yticklabels_fontsize=6,
    legend_hpad=5,
    xlabel_labelpad=-20,
    ylabel_labelpad=10,
)


# %%
# Heatmap with row clustering only
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Cluster samples but keep gene order fixed.
cns.figure(200, 250)
cmp = cns.heatmapplot(
    blobs[:20, :],
    label="Expression",
    xlabel="Genes",
    ylabel="Samples",
    row_cluster=True,
    col_cluster=False,
    row_dendrogram=True,
    show_rownames=True,
    show_colnames=True,
    legend_hpad=5,
    xlabel_labelpad=-20,
    yticklabels_fontsize=6,
)


# %%
# Heatmap with categorical split
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Split rows by a categorical variable using a subset with readable dendrograms.
cns.figure(220, 300)
cmp = cns.heatmapplot(
    blobs[:200, :],
    label="Expression",
    xlabel="Genes",
    ylabel="Samples",
    row_annotation=["blobs"],
    row_split="blobs",
    row_cluster=True,
    col_cluster=True,
    row_dendrogram=True,
    col_dendrogram=True,
    show_rownames=False,
    show_colnames=True,
    legend_hpad=5,
    xlabel_labelpad=-20,
)


# %%
# Heatmap with multiple annotations
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Add both categorical and continuous annotations.
# Use a display subset to keep the gallery image readable and stable to render.
cns.figure(280, 320)
cmp = cns.heatmapplot(
    blobs_annot,
    label="Expression",
    xlabel="Genes",
    ylabel="Samples",
    row_annotation=["blobs", "mitf", "cluster"],
    col_annotation=["ensemble"],
    row_cluster=True,
    col_cluster=True,
    row_dendrogram=True,
    col_dendrogram=True,
    show_rownames=False,
    show_colnames=True,
    legend_hpad=5,
    legend_vpad=1,
    legend_width=10,
)


# %%
# Heatmap with different colormaps
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Showcase different colormap options.
cns.figure(200, 250)
cmp = cns.heatmapplot(
    blobs[:50, :],
    label="Expression",
    xlabel="Genes",
    ylabel="Samples",
    cmap="gnuplot",
    row_cluster=True,
    col_cluster=True,
    show_rownames=False,
    show_colnames=True,
    legend_hpad=5,
    xlabel_labelpad=-20,
)


# %%
# Diverging colormap for centered data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use BuRd_custom for data centered around zero.
# First center the data
centered_data = blobs.copy()
centered_data.X = centered_data.X - centered_data.X.mean()

cns.figure(200, 250)
cmp = cns.heatmapplot(
    centered_data[:50, :],
    label="Z-score",
    xlabel="Genes",
    ylabel="Samples",
    cmap="BuRd_custom",
    row_cluster=True,
    col_cluster=True,
    show_rownames=False,
    show_colnames=True,
    legend_hpad=5,
    xlabel_labelpad=-20,
)


# %%
# Discrete/categorical heatmap
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Heatmap for discrete values with categorical coloring.
discrete = sc.AnnData(pd.DataFrame(np.random.randint(0, 3, size=(20, 8))))
discrete.var["ensemble"] = [
    f"ens{x}" for x in np.random.randint(0, 3, discrete.shape[1])
]
discrete.obs["group"] = [f"G{x}" for x in np.random.randint(0, 3, discrete.shape[0])]

cns.figure(240, 250)
cmp = cns.heatmapplot(
    discrete,
    label="Category",
    xlabel="Features",
    ylabel="Samples",
    row_annotation=["group"],
    col_annotation=["ensemble"],
    show_rownames=True,
    show_colnames=True,
    linewidth=1,
    legend_hpad=-3,
    legend_vpad=1,
    legend_width=15,
)


# %%
# Heatmap with custom annotation colors
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Specify exact colors for annotation categories.
custom_colors = {
    "blobs": {0: "#e41a1c", 1: "#377eb8", 2: "#4daf4a"},
}

cns.figure(220, 280)
cmp = cns.heatmapplot(
    blobs[:60, :],
    label="Expression",
    xlabel="Genes",
    ylabel="Samples",
    row_annotation=["blobs"],
    row_cluster=True,
    col_cluster=True,
    row_dendrogram=True,
    show_rownames=False,
    show_colnames=True,
    colors=custom_colors,
    legend_hpad=5,
    xlabel_labelpad=-20,
)


# %%
# Heatmap with value range limits
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set explicit vmin/vmax for consistent coloring.
cns.figure(200, 250)
cmp = cns.heatmapplot(
    blobs[:50, :],
    label="Expression",
    xlabel="Genes",
    ylabel="Samples",
    row_cluster=True,
    col_cluster=True,
    show_rownames=False,
    show_colnames=True,
    vmin=-2,
    vmax=2,
    legend_hpad=5,
    xlabel_labelpad=-20,
)


# %%
# Heatmap with cell borders
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Add borders between cells with ``linewidth``.
small_data = sc.AnnData(pd.DataFrame(np.random.randn(15, 10)))
small_data.var["type"] = [f"T{x}" for x in np.random.randint(0, 2, 10)]
small_data.obs["group"] = [f"G{x}" for x in np.random.randint(0, 3, 15)]

cns.figure(180, 200)
cmp = cns.heatmapplot(
    small_data,
    label="Value",
    xlabel="Features",
    ylabel="Samples",
    row_annotation=["group"],
    col_annotation=["type"],
    show_rownames=True,
    show_colnames=True,
    linewidth=0.5,
    legend_vpad=4,
    legend_hpad=5,
    xlabel_labelpad=-10,
)


# %%
# Large heatmap with rasterization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``rasterized=True`` for large datasets to reduce file size.
cns.figure(250, 300)
cmp = cns.heatmapplot(
    blobs,
    label="Expression",
    xlabel="Genes",
    ylabel="Samples",
    row_annotation=["blobs"],
    row_cluster=True,
    col_cluster=True,
    show_rownames=False,
    show_colnames=True,
    rasterized=True,  # Reduces SVG file size
    legend_hpad=5,
    xlabel_labelpad=-20,
)


# %%
# Heatmap with different clustering methods
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare different linkage methods.
cns.figure(200, 250)
cmp = cns.heatmapplot(
    blobs[:60, :],
    label="Expression",
    xlabel="Genes",
    ylabel="Samples",
    row_cluster=True,
    col_cluster=True,
    row_cluster_method="average",  # Options: ward, complete, average, single
    col_cluster_method="complete",
    row_cluster_metric="correlation",  # Options: euclidean, correlation, cosine
    col_cluster_metric="euclidean",
    row_dendrogram=True,
    col_dendrogram=True,
    show_rownames=False,
    show_colnames=True,
    legend_hpad=5,
    xlabel_labelpad=-20,
)
