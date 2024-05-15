"""
distplot
--------

create distplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")

# %%
# plot distplot using :func:`cnsplots.distplot`
cns.figure(150, 150)
cns.distplot(data=tips, x="total_bill", hue="sex")
