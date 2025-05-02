"""
dotplot
-------

create dotplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")
tips = tips.groupby(["day", "sex"]).agg({"total_bill": ["min", "size"]})
tips.columns = ["min", "size"]
tips = tips.reset_index()


# %%
# plot dotplot using :func:`cnsplots.dotplot`
cns.figure(150, 50)
cns.dotplot(tips, x="sex", y="day", color="size", size="min", value="size", max_s=60)
