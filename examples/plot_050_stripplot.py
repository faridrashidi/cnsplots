"""
stripplot
---------

create stripplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")


# %%
# plot stripplot using :func:`cnsplots.stripplot`
cns.figure(120, 100)
cns.stripplot(data=tips, x="day", y="total_bill", size=2, rasterized=True)


# %%
# plot stripplot using :func:`cnsplots.stripplot`
cns.figure(120, 100)
cns.stripplot(data=tips, x="total_bill", y="day", size=2)
