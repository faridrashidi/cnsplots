"""
violinplot
----------

create violinplot
"""

import matplotlib.pyplot as plt
import seaborn as sns

import cnsplots as cns

cns.setup_matplotlib()

# %%
# load the data
tips = sns.load_dataset("tips")

# %%
# then using :func:`cnsplots.violinplot` you can create violinplot
cns.figure(150, 100)
cns.violinplot(data=tips, x="day", y="total_bill", pairs="all")
# plt.savefig("test.pdf")
