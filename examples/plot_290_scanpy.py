"""
scanpy
------

Integrate cnsplots with scanpy for single-cell RNA-seq visualization.

cnsplots provides ``setup_scanpy()`` to apply publication-ready styling
to scanpy plots including UMAP, dotplots, matrixplots, and violin plots.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import matplotlib.pyplot as plt
import numpy as np
import scanpy as sc

import cnsplots as cns

# %%
# Generate sample data
# ~~~~~~~~~~~~~~~~~~~~
# Create synthetic single-cell data with clusters.
blobs = sc.datasets.blobs()
blobs.obs["mitf"] = np.random.random(blobs.shape[0])
blobs.obs["axl"] = np.random.random(blobs.shape[0])
blobs.obs["sox10"] = np.random.random(blobs.shape[0])
blobs.obs["ngfr"] = np.random.random(blobs.shape[0])

sc.pp.neighbors(blobs)
sc.tl.umap(blobs)


# %%
# UMAP colored by cluster
# ~~~~~~~~~~~~~~~~~~~~~~~
# Basic UMAP visualization with cnsplots styling.
cns.figure(150, 150)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.umap(blobs, color="blobs", size=10, ax=ax, show=False)
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")
plt.title("")


# %%
# UMAP with larger points
# ~~~~~~~~~~~~~~~~~~~~~~~
# Increase point size for presentations.
cns.figure(150, 150)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.umap(blobs, color="blobs", size=20, ax=ax, show=False)
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")
plt.title("Larger Points")


# %%
# UMAP colored by continuous variable
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Show gene expression on UMAP.
cns.figure(150, 150)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.umap(blobs, color="mitf", size=10, ax=ax, show=False, cmap="gnuplot")
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")
plt.title("MITF Expression")


# %%
# UMAP with different colormap
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(150, 150)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.umap(blobs, color="axl", size=10, ax=ax, show=False, cmap="hot")
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")
plt.title("AXL Expression")


# %%
# Dotplot of marker genes
# ~~~~~~~~~~~~~~~~~~~~~~~
# Show expression patterns across clusters.
cns.figure(150, 150)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.dotplot(
    blobs, ["mitf", "axl"], groupby="blobs", ax=ax, show=False, return_fig=True
).style(dot_edge_color=None, largest_dot=90, cmap="gnuplot").show()


# %%
# Dotplot with more genes
# ~~~~~~~~~~~~~~~~~~~~~~~
# Add additional markers.
cns.figure(180, 150)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.dotplot(
    blobs,
    ["mitf", "axl", "sox10", "ngfr"],
    groupby="blobs",
    ax=ax,
    show=False,
    return_fig=True,
).style(dot_edge_color=None, largest_dot=80, cmap="gnuplot").show()


# %%
# Matrix plot
# ~~~~~~~~~~~
# Heatmap-style visualization of expression.
cns.figure(100, 100)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.matrixplot(blobs, ["mitf", "axl"], groupby="blobs", ax=ax, show=False)


# %%
# Matrix plot with more genes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(150, 100)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.matrixplot(
    blobs, ["mitf", "axl", "sox10", "ngfr"], groupby="blobs", ax=ax, show=False
)


# %%
# Stacked violin plot
# ~~~~~~~~~~~~~~~~~~~
# Compare distributions across clusters.
cns.figure(150, 150)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.stacked_violin(blobs, ["mitf", "axl"], groupby="blobs", ax=ax, show=False)


# %%
# Stacked violin with more genes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(180, 180)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.stacked_violin(
    blobs, ["mitf", "axl", "sox10", "ngfr"], groupby="blobs", ax=ax, show=False
)


# %%
# Single violin plot
# ~~~~~~~~~~~~~~~~~~
# Distribution of one gene across clusters.
cns.figure(150, 150)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.violin(
    blobs,
    keys="mitf",
    groupby="blobs",
    ax=ax,
    show=False,
    edgecolor=None,
    stripplot=False,
)


# %%
# Violin with stripplot
# ~~~~~~~~~~~~~~~~~~~~~
# Add individual points to violin.
cns.figure(150, 150)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.violin(
    blobs,
    keys="axl",
    groupby="blobs",
    ax=ax,
    show=False,
    edgecolor=None,
    stripplot=True,
    jitter=0.4,
    size=1,
)


# %%
# Scatter plot
# ~~~~~~~~~~~~
# Gene-gene scatter plot colored by cluster.
cns.figure(150, 150)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.scatter(blobs, x="mitf", y="axl", color="blobs", size=10, ax=ax, show=False)


# %%
# Scatter with different genes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(150, 150)
cns.setup_scanpy()
ax = plt.gca()
sc.pl.scatter(blobs, x="sox10", y="ngfr", color="blobs", size=10, ax=ax, show=False)


# %%
# Comparing expression with multipanel
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Side-by-side UMAP plots for different genes.
mp = cns.multipanel((1, 2), max_width=350, hgap=40)
cns.setup_scanpy()

mp.panel("A", 120, 120)
ax_a = mp.get_axes("A")
sc.pl.umap(blobs, color="mitf", size=8, ax=ax_a, show=False, cmap="gnuplot")
ax_a.set_xlabel("UMAP-1")
ax_a.set_ylabel("UMAP-2")
ax_a.set_title("MITF")

mp.panel("B", 120, 120)
ax_b = mp.get_axes("B")
sc.pl.umap(blobs, color="axl", size=8, ax=ax_b, show=False, cmap="gnuplot")
ax_b.set_xlabel("UMAP-1")
ax_b.set_ylabel("UMAP-2")
ax_b.set_title("AXL")


# %%
# Four gene comparison
# ~~~~~~~~~~~~~~~~~~~~
# Grid of UMAP plots for multiple markers.
mp = cns.multipanel((2, 2), max_width=350, hgap=35, vgap=35)
cns.setup_scanpy()

genes = ["mitf", "axl", "sox10", "ngfr"]
labels = ["A", "B", "C", "D"]

for gene, label in zip(genes, labels):
    mp.panel(label, 100, 100)
    ax = mp.get_axes(label)
    sc.pl.umap(blobs, color=gene, size=6, ax=ax, show=False, cmap="gnuplot")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title(gene.upper())


# %%
# Cluster vs expression multipanel
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Show cluster assignments alongside gene expression.
mp = cns.multipanel((1, 3), max_width=480, hgap=30)
cns.setup_scanpy()

mp.panel("A", 110, 110)
ax_a = mp.get_axes("A")
sc.pl.umap(blobs, color="blobs", size=8, ax=ax_a, show=False)
ax_a.set_xlabel("UMAP-1")
ax_a.set_ylabel("UMAP-2")
ax_a.set_title("Clusters")

mp.panel("B", 110, 110)
ax_b = mp.get_axes("B")
sc.pl.umap(blobs, color="mitf", size=8, ax=ax_b, show=False, cmap="gnuplot")
ax_b.set_xlabel("UMAP-1")
ax_b.set_ylabel("UMAP-2")
ax_b.set_title("MITF")

mp.panel("C", 110, 110)
ax_c = mp.get_axes("C")
sc.pl.umap(blobs, color="axl", size=8, ax=ax_c, show=False, cmap="gnuplot")
ax_c.set_xlabel("UMAP-1")
ax_c.set_ylabel("UMAP-2")
ax_c.set_title("AXL")
