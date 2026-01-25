"""
donutplot
---------

create donutplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")


# %%
# plot donutplot using :func:`cnsplots.donutplot`
cns.figure(100, 100)
cns.donutplot(iris, "species")
