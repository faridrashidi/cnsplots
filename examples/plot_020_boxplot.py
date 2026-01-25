"""
boxplot
-------

create boxplot
"""

# %%
# load data
import matplotlib.pyplot as plt
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")
tips = sns.load_dataset("tips")


# %%
# plot boxplot using :func:`cnsplots.boxplot`
cns.figure(150, 100)
cns.boxplot(data=tips, x="day", y="total_bill")

_ = plt.xticks(rotation=40, ha="right", rotation_mode="anchor")

xtick_labels = plt.gca().get_xticklabels()
for index in range(tips["day"].nunique()):
    if xtick_labels[index].get_text() in ["Thur", "Fri"]:
        xtick_labels[index].set_color("red")
    else:
        xtick_labels[index].set_color("blue")


# %%
# plot boxplot using :func:`cnsplots.boxplot`
cns.figure(150, 100)
cns.boxplot(
    data=iris,
    x="species",
    y="sepal_width",
    pairs="all",
    addcount=True,
)


# %%
# plot boxplot using :func:`cnsplots.boxplot`
cns.figure(150, 100)
cns.boxplot(
    data=tips,
    x="day",
    y="total_bill",
    hue="sex",
    pairs=[(("Thur", "Male"), ("Fri", "Male"))],
)
cns.take_legend_out()


# %%
# plot boxplot using :func:`cnsplots.boxplot`
cns.figure(100, 150)
cns.boxplot(
    data=iris,
    x="sepal_width",
    y="species",
    pairs="all",
    order=["versicolor", "setosa", "virginica"],
)
