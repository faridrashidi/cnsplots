"""
piechart
--------

create piechart
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")

# %%
# plot piechart using :func:`cnsplots.piechart`
cns.figure(100, 100)
cns.piechart(iris, "species")
