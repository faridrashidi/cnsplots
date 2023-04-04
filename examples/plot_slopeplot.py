"""
slopeplot
---------

create slopeplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")

# %%
# plot slopeplot using :func:`cnsplots.slopeplot`
cns.figure(150, 100)
cns.slopeplot(data=iris, x1="sepal_length", x2="sepal_width")
