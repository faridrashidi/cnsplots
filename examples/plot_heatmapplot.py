"""
heatmapplot
-----------

create heatmapplot
"""

# %%
# load data
import numpy as np
import pandas as pd
import scanpy as sc

import cnsplots as cns

blobs = sc.datasets.blobs()
blobs.obs["mitf"] = np.random.random(blobs.shape[0])
blobs.var["ensemble"] = [f"ens{x}" for x in np.random.randint(0, 3, blobs.shape[1])]
blobs.obs["selected"] = np.where(
    blobs.obs["mitf"] > 0.95, blobs.obs["mitf"].index, None
)

discrete = sc.AnnData(pd.DataFrame(np.random.randint(0, 3, size=(20, 8))))
discrete.var["ensemble"] = [
    f"ens{x}" for x in np.random.randint(0, 3, discrete.shape[1])
]
discrete.obs["mitf"] = [f"gene{x}" for x in np.random.randint(0, 3, discrete.shape[0])]

# %%
# plot heatmapplot using :func:`cnsplots.heatmapplot`
cns.figure(300, 250)
cmp = cns.heatmapplot(
    blobs,
    row_annotation=["selected", "mitf", "blobs"],
    col_annotation=["ensemble"],
    row_split=5,
    # col_split=2,
    # row_split="blobs",
    # col_split=["ensemble"],
    row_cluster=True,
    col_cluster=True,
    row_cluster_method="ward",
    row_cluster_metric="euclidean",
    col_cluster_method="ward",
    col_cluster_metric="euclidean",
    show_rownames=True,
    show_colnames=True,
    row_dendrogram=False,
    col_dendrogram=False,
    row_split_gap=1,
    col_split_gap=1,
    legend_hpad=-2,
    legend_vpad=6,
    # vmin=0,
    # vmax=1,
)
print(len(cmp.row_order), cmp.row_order[0][:5])
print(len(cmp.col_order), cmp.col_order[0][:5])

# %%
# plot heatmapplot using :func:`cnsplots.heatmapplot`
cns.figure(300, 200)
cns.heatmapplot(
    discrete,
    row_annotation=["mitf"],
    col_annotation=["ensemble"],
    show_rownames=True,
    show_colnames=True,
    linewidth=1,
    legend_hpad=-3,
    cmap=["blue", "red"],
    # cmap="Set1",
    # cmap={"0": "#e41a1c", "1": "#ff7f00"},
)
