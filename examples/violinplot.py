"""
Construct lienage tree using Trisicell-Boost
--------------------------------------------

This example shows how to construct a lineage tree using Trisicell-Boost on a binary
single-cell genotype matrix.
"""

# sphinx_gallery_thumbnail_path = "_static/thumbnails/trisicell-boost.png"

import matplotlib.pyplot as plt
import seaborn as sns

import cnsplots as cns

cns.setup_matplotlib()

# %%
# First, we load a binary test single-cell genotype data.
tips = sns.load_dataset("tips")

# %%
# Next, using :func:`trisicell.tl.booster` we remove the single-cell noises from the
# input.
cns.figure(150, 100)
cns.violinplot(data=tips, x="day", y="total_bill", pairs="all")
plt.savefig("test.pdf")
