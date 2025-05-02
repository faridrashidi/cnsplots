"""
regplot
-------

create regplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")


# %%
# plot regplot using :func:`cnsplots.regplot`
cns.figure(150, 150)
cns.regplot(data=tips, x="tip", y="total_bill")
