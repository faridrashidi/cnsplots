"""
forestplot
----------

Create forest plots for visualizing regression results.

Forest plots display effect sizes (hazard ratios, odds ratios) with
confidence intervals, commonly used in survival analysis, meta-analysis,
and epidemiological studies. cnsplots integrates with lifelines for
Cox proportional hazards and logistic regression models.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import lifelines as ll
import numpy as np
import pandas as pd

import cnsplots as cns

# %%
# Generate synthetic survival data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create a realistic clinical dataset for demonstration.
np.random.seed(42)
n_patients = 300
liver = {
    "Survival": np.random.exponential(scale=50, size=n_patients),
    "Event": np.random.binomial(1, 0.5, n_patients),
    "Predictor": np.random.choice(
        ["low risk", "high risk"], size=n_patients, p=[0.6, 0.4]
    ),
    "AFP": np.random.lognormal(mean=5, sigma=1, size=n_patients),
    "Cirrhosis": np.random.choice(["no", "yes"], size=n_patients, p=[0.55, 0.45]),
    "TNM_staging": np.random.choice(["I", "I-II"], size=n_patients, p=[0.5, 0.5]),
    "BCLC_staging": np.random.choice(["A-0", "B-C"], size=n_patients, p=[0.6, 0.4]),
    "Group": np.random.choice(["CCA", "HCC"], size=n_patients, p=[0.6, 0.4]),
}
liver = pd.DataFrame(liver)
liver["AFP_cat"] = liver["AFP"].apply(
    lambda x: ">300 ng/mL" if x > 300 else "<=300 ng/mL"
)
liver.head()


# %%
# Cox regression with multiple covariates and hue
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Display hazard ratios stratified by a grouping variable.
model = cns.methods.CoxModel(
    data=liver,
    duration="Event",
    event="Survival",
    variates=[
        "C(Predictor, levels=['low risk', 'high risk'])",
        "C(AFP_cat, levels=['<=300 ng/mL', '>300 ng/mL'])",
        "C(Cirrhosis, levels=['no', 'yes'])",
        "C(TNM_staging, levels=['I', 'I-II'])",
        "Predictor + AFP_cat + Cirrhosis + C(TNM_staging, levels=['I', 'I-II'])",
        "AFP_cat + Predictor + Cirrhosis + C(TNM_staging, levels=['I', 'I-II'])",
    ],
    hue="Group",
)
model.fit()
cns.figure(150, 210)
cns.forestplot(model)
model.results.head()


# %%
# Load GBSG2 breast cancer data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use lifelines' built-in dataset for breast cancer survival.
gbsg2 = ll.datasets.load_gbsg2()
gbsg2["estrec_cat"] = np.where(gbsg2["estrec"] <= 36, "Low", "High")
gbsg2["estrec_cat"] = pd.Categorical(
    gbsg2["estrec_cat"], categories=["Low", "High"], ordered=True
)
bins = [-float("inf"), 20, 50, float("inf")]
labels = ["<=20", "20<x<=50", ">50"]
gbsg2["progrec_cat"] = pd.cut(
    gbsg2["progrec"], bins=bins, labels=labels, include_lowest=True
)
gbsg2["progrec_cat"] = pd.Categorical(
    gbsg2["progrec_cat"], categories=labels, ordered=True
)
gbsg2.head()


# %%
# Cox regression with continuous and categorical variables
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Combine log-transformed continuous variables with categorical factors.
model = cns.methods.CoxModel(
    data=gbsg2,
    duration="time",
    event="cens",
    variates=[
        "np.log(age)",
        "pnodes",
        "age + pnodes",
        "C(tgrade) + C(menostat)",
        'C(tgrade) + C(menostat, Treatment(reference="Pre"))',
        "C(estrec_cat)",
        "C(progrec_cat)",
    ],
)
model.fit()
cns.figure(120, 210, ["black"])
cns.forestplot(model)
model.results.head()


# %%
# Logistic regression forest plot
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Display odds ratios from logistic regression.
model = cns.methods.LogisticModel(
    data=gbsg2,
    event="cens",
    variates=[
        "horTh",
        "age",
        "tsize",
        "tgrade",
        "pnodes",
        "progrec",
        "estrec",
        "estrec_cat",
        "progrec_cat",
        "pnodes + progrec",
    ],
    hue="menostat",
)
model.fit()
cns.figure(150, 150)
cns.forestplot(model)
model.results.head()


# %%
# Univariate Cox analysis
# ~~~~~~~~~~~~~~~~~~~~~~~
# Test individual covariates one at a time.
model = cns.methods.CoxModel(
    data=gbsg2,
    duration="time",
    event="cens",
    variates=[
        "age",
        "tsize",
        "pnodes",
        "progrec",
        "estrec",
    ],
)
model.fit()
cns.figure(90, 150, ["black"])
ax = cns.forestplot(model)
ax.set_title("Univariate Cox Regression")


# %%
# Multivariate Cox model
# ~~~~~~~~~~~~~~~~~~~~~~
# Include all covariates in a single model.
model = cns.methods.CoxModel(
    data=gbsg2,
    duration="time",
    event="cens",
    variates=[
        "age + tsize + pnodes + progrec + estrec",
    ],
)
model.fit()
cns.figure(40, 150, ["black"])
ax = cns.forestplot(model)
ax.set_title("Multivariate Cox Regression")


# %%
# Categorical variables with reference levels
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Specify reference categories for factor variables.
model = cns.methods.CoxModel(
    data=gbsg2,
    duration="time",
    event="cens",
    variates=[
        'C(tgrade, Treatment(reference="I"))',
        'C(menostat, Treatment(reference="Pre"))',
        'C(horTh, Treatment(reference="no"))',
    ],
)
model.fit()
cns.figure(80, 150, ["black"])
ax = cns.forestplot(model)
ax.set_title("Categorical Covariates")


# %%
# Stratified by hormone therapy
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare hazard ratios between treatment groups.
model = cns.methods.CoxModel(
    data=gbsg2,
    duration="time",
    event="cens",
    variates=[
        "age",
        "pnodes",
        "C(tgrade)",
    ],
    hue="horTh",
)
model.fit()
cns.figure(100, 150)
ax = cns.forestplot(model)
ax.set_title("Stratified by Hormone Therapy")


# %%
# Interaction terms
# ~~~~~~~~~~~~~~~~~
# Test interactions between covariates.
model = cns.methods.CoxModel(
    data=gbsg2,
    duration="time",
    event="cens",
    variates=[
        "age",
        "pnodes",
        "age + pnodes",
        "age * pnodes",
    ],
)
model.fit()
cns.figure(80, 150, ["black"])
ax = cns.forestplot(model)
ax.set_title("With Interaction Term")


# %%
# Logistic regression - single covariate
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Simple univariate logistic regression.
model = cns.methods.LogisticModel(
    data=gbsg2,
    event="cens",
    variates=[
        "age",
        "tsize",
        "pnodes",
    ],
)
model.fit()
cns.figure(80, 150, ["black"])
ax = cns.forestplot(model)
ax.set_title("Univariate Logistic Regression")


# %%
# Custom color for forest plot
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use different colors for effect estimates.
model = cns.methods.CoxModel(
    data=liver,
    duration="Event",
    event="Survival",
    variates=[
        "C(Predictor, levels=['low risk', 'high risk'])",
        "C(AFP_cat, levels=['<=300 ng/mL', '>300 ng/mL'])",
        "C(Cirrhosis, levels=['no', 'yes'])",
    ],
)
model.fit()
cns.figure(80, 150, [cns.BLUE])
ax = cns.forestplot(model)
ax.set_title("Custom Color")


# %%
# Comparing Cox models side by side
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use multipanel to compare different model specifications.
mp = cns.multipanel(max_width=400)

model1 = cns.methods.CoxModel(
    data=gbsg2,
    duration="time",
    event="cens",
    variates=["age", "pnodes", "tsize"],
)
model1.fit()

model2 = cns.methods.CoxModel(
    data=gbsg2,
    duration="time",
    event="cens",
    variates=["age + pnodes + tsize"],
)
model2.fit()

mp.panel("A", 80, 140, color_cycle=["black"])
cns.forestplot(model1)
mp.get_axes("A").set_title("Univariate")

mp.panel("B", 80, 140, color_cycle=["black"])
cns.forestplot(model2)
mp.get_axes("B").set_title("Multivariate")


# %%
# Subgroup analysis visualization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare effects across patient subgroups.
mp = cns.multipanel(max_width=400)

pre_meno = gbsg2[gbsg2["menostat"] == "Pre"]
post_meno = gbsg2[gbsg2["menostat"] == "Post"]

model_pre = cns.methods.CoxModel(
    data=pre_meno,
    duration="time",
    event="cens",
    variates=["age", "pnodes", "C(tgrade)"],
)
model_pre.fit()

model_post = cns.methods.CoxModel(
    data=post_meno,
    duration="time",
    event="cens",
    variates=["age", "pnodes", "C(tgrade)"],
)
model_post.fit()

mp.panel("A", 80, 140, color_cycle=[cns.BLUE])
cns.forestplot(model_pre)
mp.get_axes("A").set_title("Premenopausal")

mp.panel("B", 80, 140, color_cycle=[cns.RED])
cns.forestplot(model_post)
mp.get_axes("B").set_title("Postmenopausal")
