"""
histplot
--------

create histplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")
tips = sns.load_dataset("tips")

# %%
# plot histplot using :func:`cnsplots.histplot`
cns.figure(150, 150)
sns.histplot(data=iris, x="sepal_length", y="sepal_width", cbar=True, cmap="gnuplot")

# %%
# plot histplot using :func:`cnsplots.histplot`
cns.figure(150, 150)
sns.histplot(
    data=iris, x="sepal_length", y="sepal_width", cbar=True, cmap="parula"
)  # TODO: bring to the module
