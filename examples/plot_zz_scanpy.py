"""
scanpy
------

create scanpy
"""

# %%
# load data
import matplotlib.pyplot as plt
import scanpy as sc

import cnsplots as cns

blobs = sc.datasets.blobs()
sc.pp.neighbors(blobs)
sc.tl.umap(blobs)

# %%
# plot scanpy
cns.figure(150, 150)
ax = plt.gca()
sc.pl.umap(blobs, color="blobs", size=10, ax=ax, show=False)
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")
plt.title("")
