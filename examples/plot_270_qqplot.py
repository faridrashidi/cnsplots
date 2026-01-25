"""
qqplot
------

create qqplot
"""

# %%
# load data
import scipy.stats as stats
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")


# %%
# plot qqplot using :func:`cnsplots.qqplot`
cns.figure(150, 150)
cns.qqplot(tips, x="total_bill", dist=stats.t, fit=True, line="45")
