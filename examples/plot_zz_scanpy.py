"""
scanpy
------

create scanpy
"""

# %%
# load data
import matplotlib.pyplot as plt
import numpy as np
import scanpy as sc

import cnsplots as cns

blobs = sc.datasets.blobs()
blobs.obs["mitf"] = np.random.random(blobs.shape[0])
blobs.obs["axl"] = np.random.random(blobs.shape[0])

sc.pp.neighbors(blobs)
sc.tl.umap(blobs)

# %%
# plot scanpy umap
cns.figure(150, 150)
ax = plt.gca()
sc.pl.umap(blobs, color="blobs", size=10, ax=ax, show=False)
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")
plt.title("")

# %%
# plot scanpy dotplot
cns.figure(150, 150)
ax = plt.gca()
sc.pl.dotplot(blobs, ["mitf", "axl"], groupby="blobs", ax=ax, show=False)

# %%
# plot scanpy matrixplot
cns.figure(100, 100)
ax = plt.gca()
sc.pl.matrixplot(blobs, ["mitf", "axl"], groupby="blobs", ax=ax, show=False)

# %%
# plot scanpy matrixplot
cns.figure(150, 150)
ax = plt.gca()
sc.pl.stacked_violin(blobs, ["mitf", "axl"], groupby="blobs", ax=ax, show=False)

# %%
# plot scanpy violin
cns.figure(150, 150)
ax = plt.gca()
sc.pl.violin(blobs, keys="mitf", groupby="blobs", ax=ax, show=False)

# %%
# plot scanpy violin
cns.figure(150, 150)
ax = plt.gca()
sc.pl.scatter(blobs, x="mitf", y="axl", color="blobs", size=10, ax=ax, show=False)

# %%
# plot scanpy heatmap, tracksplot and clustermap
# TODO: handle multiple axes
