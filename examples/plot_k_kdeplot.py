"""
kdeplot
-------

create kdeplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")

# %%
# plot kdeplot using :func:`cnsplots.kdeplot`
cns.figure(150, 150)
cns.kdeplot(data=tips, x="total_bill", add_mode=True)


# %%
# plot kdeplot using :func:`cnsplots.kdeplot`
cns.figure(150, 150)
cns.kdeplot(data=tips, x="total_bill", hue="sex")
