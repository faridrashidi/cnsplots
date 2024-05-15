"""
pieplot
-------

create pieplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")

# %%
# plot pieplot using :func:`cnsplots.pieplot`
cns.figure(100, 100)
cns.pieplot(iris, "species")
