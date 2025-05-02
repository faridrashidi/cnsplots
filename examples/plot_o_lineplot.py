"""
lineplot
--------

create lineplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

fmri = sns.load_dataset("fmri")


# %%
# plot lineplot using :func:`cnsplots.lineplot`
cns.figure(150, 150)
cns.lineplot(data=fmri, x="timepoint", y="signal", hue="event", err_style="bars")
