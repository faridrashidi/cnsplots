"""
qqplot
------

Create quantile-quantile (Q-Q) plots for distribution comparison.

Q-Q plots compare the distribution of data against a theoretical
distribution, commonly used to assess normality and identify
outliers or distribution deviations.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import numpy as np
import pandas as pd
import scipy.stats as stats
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")
iris = sns.load_dataset("iris")


# %%
# Basic Q-Q plot against t-distribution
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare sample quantiles against t-distribution.
cns.figure(150, 150)
ax = cns.qqplot(tips, x="total_bill", dist=stats.t, fit=True, line="45")
ax.set_title("Basic Q-Q Plot")


# %%
# Q-Q plot against normal distribution
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Test normality assumption.
cns.figure(150, 150)
ax = cns.qqplot(tips, x="total_bill", dist=stats.norm, fit=True, line="45")
ax.set_title("Normal Q-Q Plot")


# %%
# Q-Q plot for tip amounts
# ~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(150, 150)
ax = cns.qqplot(tips, x="tip", dist=stats.norm, fit=True, line="45")
ax.set_title("Tip Amount Q-Q Plot")


# %%
# Q-Q plot for iris sepal length
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(150, 150)
ax = cns.qqplot(iris, x="sepal_length", dist=stats.norm, fit=True, line="45")
ax.set_title("Sepal Length Q-Q Plot")


# %%
# Q-Q plot for iris sepal width
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(150, 150)
ax = cns.qqplot(iris, x="sepal_width", dist=stats.norm, fit=True, line="45")
ax.set_title("Sepal Width Q-Q Plot")


# %%
# Q-Q plot for petal length
# ~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(150, 150)
ax = cns.qqplot(iris, x="petal_length", dist=stats.norm, fit=True, line="45")
ax.set_title("Petal Length Q-Q Plot")


# %%
# Q-Q plot for petal width
# ~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(150, 150)
ax = cns.qqplot(iris, x="petal_width", dist=stats.norm, fit=True, line="45")
ax.set_title("Petal Width Q-Q Plot")


# %%
# Comparing against uniform distribution
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Test for uniform distribution.
np.random.seed(42)
uniform_data = pd.DataFrame({"values": np.random.uniform(0, 10, 200)})
cns.figure(150, 150)
ax = cns.qqplot(uniform_data, x="values", dist=stats.uniform, fit=True, line="45")
ax.set_title("Uniform Q-Q Plot")


# %%
# Exponential distribution
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Compare against exponential distribution.
np.random.seed(42)
exp_data = pd.DataFrame({"values": np.random.exponential(2, 200)})
cns.figure(150, 150)
ax = cns.qqplot(exp_data, x="values", dist=stats.expon, fit=True, line="45")
ax.set_title("Exponential Q-Q Plot")


# %%
# Normally distributed synthetic data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Generate data that follows normal distribution.
np.random.seed(42)
normal_data = pd.DataFrame({"values": np.random.normal(50, 10, 200)})
cns.figure(150, 150)
ax = cns.qqplot(normal_data, x="values", dist=stats.norm, fit=True, line="45")
ax.set_title("Normal Data Q-Q Plot")


# %%
# Skewed distribution
# ~~~~~~~~~~~~~~~~~~~
# Data with positive skew.
np.random.seed(42)
skewed_data = pd.DataFrame({"values": np.random.lognormal(0, 0.5, 200)})
cns.figure(150, 150)
ax = cns.qqplot(skewed_data, x="values", dist=stats.norm, fit=True, line="45")
ax.set_title("Skewed Data Q-Q Plot")


# %%
# Heavy-tailed distribution
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Data with more extreme values than normal.
np.random.seed(42)
heavy_tailed = pd.DataFrame({"values": np.random.standard_t(3, 200)})
cns.figure(150, 150)
ax = cns.qqplot(heavy_tailed, x="values", dist=stats.norm, fit=True, line="45")
ax.set_title("Heavy-Tailed Q-Q Plot")


# %%
# Bimodal distribution
# ~~~~~~~~~~~~~~~~~~~~
# Data with two modes.
np.random.seed(42)
bimodal_data = pd.DataFrame(
    {
        "values": np.concatenate(
            [np.random.normal(30, 5, 100), np.random.normal(70, 5, 100)]
        )
    }
)
cns.figure(150, 150)
ax = cns.qqplot(bimodal_data, x="values", dist=stats.norm, fit=True, line="45")
ax.set_title("Bimodal Q-Q Plot")


# %%
# Comparing distributions with multipanel
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Side-by-side Q-Q plots for different variables.
mp = cns.multipanel((2, 2), max_width=350, hgap=40, vgap=40)

mp.panel("A", 100, 100)
cns.qqplot(iris, x="sepal_length", dist=stats.norm, fit=True, line="45")
mp.get_axes("A").set_title("Sepal Length")

mp.panel("B", 100, 100)
cns.qqplot(iris, x="sepal_width", dist=stats.norm, fit=True, line="45")
mp.get_axes("B").set_title("Sepal Width")

mp.panel("C", 100, 100)
cns.qqplot(iris, x="petal_length", dist=stats.norm, fit=True, line="45")
mp.get_axes("C").set_title("Petal Length")

mp.panel("D", 100, 100)
cns.qqplot(iris, x="petal_width", dist=stats.norm, fit=True, line="45")
mp.get_axes("D").set_title("Petal Width")


# %%
# Comparing by species
# ~~~~~~~~~~~~~~~~~~~~
# Q-Q plots for each species subset.
mp = cns.multipanel((1, 3), max_width=450, hgap=35)

setosa = iris[iris["species"] == "setosa"]
versicolor = iris[iris["species"] == "versicolor"]
virginica = iris[iris["species"] == "virginica"]

mp.panel("A", 100, 100)
cns.qqplot(setosa, x="sepal_length", dist=stats.norm, fit=True, line="45")
mp.get_axes("A").set_title("Setosa")

mp.panel("B", 100, 100)
cns.qqplot(versicolor, x="sepal_length", dist=stats.norm, fit=True, line="45")
mp.get_axes("B").set_title("Versicolor")

mp.panel("C", 100, 100)
cns.qqplot(virginica, x="sepal_length", dist=stats.norm, fit=True, line="45")
mp.get_axes("C").set_title("Virginica")


# %%
# Gene expression normality check
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Simulate gene expression data and check distribution.
np.random.seed(42)
gene_expr = pd.DataFrame(
    {
        "raw_counts": np.random.negative_binomial(10, 0.3, 500),
        "log_counts": np.log1p(np.random.negative_binomial(10, 0.3, 500)),
    }
)

mp = cns.multipanel((1, 2), max_width=350, hgap=40)

mp.panel("A", 120, 120)
cns.qqplot(gene_expr, x="raw_counts", dist=stats.norm, fit=True, line="45")
mp.get_axes("A").set_title("Raw Counts")

mp.panel("B", 120, 120)
cns.qqplot(gene_expr, x="log_counts", dist=stats.norm, fit=True, line="45")
mp.get_axes("B").set_title("Log Counts")
