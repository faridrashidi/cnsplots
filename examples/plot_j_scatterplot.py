"""
scatterplot
-----------

create scatterplot
"""

# %%
# load data
import matplotlib.pyplot as plt
import seaborn as sns

import cnsplots as cns

iris = sns.load_dataset("iris")

# %%
# plot scatterplot using :func:`cnsplots.scatterplot`
cns.figure(120, 120)
cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", s=7, hue="species")
plt.title("title")
plt.xlabel("xlabel")
plt.ylabel("ylabel")
cns.take_legend_out()
