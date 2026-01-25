"""
upsetplot
---------

create upsetplot
"""

# %%
# load data
import cnsplots as cns

sets = {
    "A": ["a", "b", "c", "d"],
    "B": ["c", "d", "e", "f"],
    "C": ["b", "d", "f", "g"],
    "D": ["a", "e", "g", "h"],
}


# %%
# plot upsetplot using :func:`cnsplots.upsetplot`
cns.upsetplot(sets, totals_plot_elements=0, facecolor=cns.VIOLET)


# %%
# plot upsetplot using :func:`cnsplots.upsetplot`
cns.upsetplot(sets, subset_size="count")
