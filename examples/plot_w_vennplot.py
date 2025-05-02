"""
vennplot
--------

create vennplot
"""

# %%
# load data
import cnsplots as cns

set1 = {"A", "B", "C", "D"}
set2 = {"B", "C", "D", "E"}
set3 = {"C", "D", " E", "F", "G"}
labels = ["Set1", "Set2", "Set3"]


# %%
# plot vennplot using :func:`cnsplots.vennplot`
cns.figure(100, 100)
cns.vennplot([set1, set2, set3], labels)


# %%
# plot vennplot using :func:`cnsplots.vennplot`
cns.figure(100, 100)
cns.vennplot([set1, set3], labels[:2])
