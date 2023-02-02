"""
upsetplot
---------

create upsetplot
"""

# %%
# load data
from upsetplot import generate_counts, plot

example = generate_counts()

# %%
# plot upsetplot using :func:`cnsplots.upsetplot`
plot(example, element_size=30, show_counts=True)  # TODO: bring to the module
