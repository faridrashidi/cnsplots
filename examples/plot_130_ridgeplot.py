"""
ridgeplot
---------

create ridgeplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")


# %%
# plot ridgeplot using :func:`cnsplots.ridgeplot`
cns.figure(150, 150)
cns.ridgeplot(data=tips, x="total_bill", y="day")
