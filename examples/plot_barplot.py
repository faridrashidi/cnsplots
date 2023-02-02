"""
barplot
-------

create barplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")
tips = sns.load_dataset("tips")

# %%
# plot barplot using :func:`cnsplots.barplot`
cns.figure(150, 100, "Tableau")
cns.barplot(data=tips, x="day", y="total_bill", pairs="all", addtip=True)

# %%
# plot barplot using :func:`cnsplots.barplot`
cns.figure(150, 100, "Bold")
cns.barplot(data=iris, x="species", y="sepal_width", pairs="all", addtip=True)

# %%
# plot barplot using :func:`cnsplots.barplot`
cns.figure(150, 100, "BlueRed")
cns.barplot(
    data=tips,
    x="day",
    y="total_bill",
    hue="sex",
    pairs=[(("Thur", "Male"), ("Fri", "Male"))],
)
cns.take_legend_out()

# %%
# plot barplot using :func:`cnsplots.barplot`
cns.figure(100, 180, "Set1")
cns.barplot(
    data=tips,
    x="total_bill",
    y="day",
    order=["Sun", "Fri", "Thur", "Sat"],
    pairs=[("Sun", "Fri")],
)
