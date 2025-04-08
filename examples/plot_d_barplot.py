"""
barplot
-------

create barplot
"""

# %%
# load data
import matplotlib.pyplot as plt
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")
tips = sns.load_dataset("tips")

# %%
# plot barplot using :func:`cnsplots.barplot`
cns.figure(150, 100)
cns.barplot(data=tips, x="day", y="total_bill")

# %%
# plot barplot using :func:`cnsplots.barplot`
mean_bills = tips.groupby("day")["total_bill"].mean()
cols = ["grey" if x < 21.0 else "orange" for x in mean_bills]
cns.figure(150, 100)
cns.barplot(data=tips, x="day", y="total_bill", palette=cols)

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

# %%
# plot barplot using :func:`cnsplots.barplot`
tips["total_bill"] = tips["total_bill"] - tips["total_bill"].mean()
cns.figure(100, 150, "Tableau")
cns.barplot(data=tips, x="day", y="total_bill")
ax = plt.gca()
ax.axhline(0, color="k", clip_on=False, lw=0.8)
ax.spines["bottom"].set_visible(False)

# %%
# plot barplot using :func:`cnsplots.barplot`
cns.figure(150, 100, "Tableau")
cns.barplot(data=tips, y="day", x="total_bill")
ax = plt.gca()
ax.axvline(0, color="k", clip_on=False, lw=0.8)
ax.spines["left"].set_visible(False)
