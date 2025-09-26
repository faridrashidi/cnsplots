"""
upsetplot
---------

create upsetplot
"""

# %%
# load data
import upsetplot as usp

import cnsplots as cns

example1 = usp.generate_counts()
sets = {
    "A": {"a", "b", "c", "d"},
    "B": {"c", "d", "e", "f"},
    "C": {"b", "d", "f", "g"},
    "D": {"a", "e", "g", "h"},
}
memberships = []
for item in set.union(*sets.values()):
    membership = [name for name, s in sets.items() if item in s]
    memberships.append(membership)
example2 = usp.from_memberships(memberships)


# %%
# plot upsetplot using :func:`cnsplots.upsetplot`
cns.upsetplot(example1, element_size=30, show_counts="{:,}", totals_plot_elements=0)


# %%
# plot upsetplot using :func:`cnsplots.upsetplot`
cns.upsetplot(example2, element_size=30, show_counts="{:,}", subset_size="count")
