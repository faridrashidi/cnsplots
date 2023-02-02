"""
violinplot
----------

create violinplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")

# %%
# plot violinplot using :func:`cnsplots.violinplot`
cns.figure(150, 100)
cns.violinplot(data=tips, x="day", y="total_bill", pairs="all")
