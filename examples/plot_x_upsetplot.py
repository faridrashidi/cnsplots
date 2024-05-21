"""
upsetplot
---------

create upsetplot
"""

# %%
# load data
import upsetplot as usp

import cnsplots as cns

example = usp.generate_counts()

# %%
# plot upsetplot using :func:`cnsplots.upsetplot`
cns.upsetplot(example, element_size=30, show_counts=True)
