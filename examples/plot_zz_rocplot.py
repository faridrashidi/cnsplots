"""
rocplot
-------

create rocplot
"""

# %%
# load data
import numpy as np
import seaborn as sns

import cnsplots as cns

np.random.seed(42)
iris = sns.load_dataset("iris")
iris["true_labels"] = (iris["species"] == "setosa").astype(int)
n_samples = len(iris)
iris["model1_prob"] = np.clip(
    iris["true_labels"] + np.random.normal(0, 0.2, n_samples), 0, 1
)
iris["model2_prob"] = np.clip(
    iris["true_labels"] + np.random.normal(0, 0.4, n_samples), 0, 1
)
iris["model3_prob"] = np.random.uniform(0, 1, n_samples)


# %%
# plot rocplot using :func:`cnsplots.rocplot`
cns.figure(150, 150)
cns.rocplot(
    iris,
    "true_labels",
    ["model1_prob", "model2_prob", "model3_prob"],
)
cns.take_legend_out()
