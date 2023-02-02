"""
distplot
--------

create distplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")

# %%
# plot distplot using :func:`cnsplots.distplot`
cns.figure(150, 150)
cns.distplot(data=iris, x="sepal_width")
