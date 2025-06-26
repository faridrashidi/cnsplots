"""
forestplot
----------

create forestplot
"""

# %%
# load packages
import lifelines as ll
import numpy as np
import pandas as pd

import cnsplots as cns

# %%
# load data
np.random.seed(42)
n_patients = 242
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
}
liver = pd.DataFrame(liver)
liver["AFP_cat"] = liver["AFP"].apply(
    lambda x: ">300 ng/mL" if x > 300 else "<=300 ng/mL"
)
liver.head()


# %%
# plot forestplot using :func:`cnsplots.forestplot`
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
    ],
)
model.fit()
cns.figure(150, 210, ["black"])
cns.forestplot(model)
model.results.head()


# %%
# load another data
gbsg2 = ll.datasets.load_gbsg2()

gbsg2["estrec_cat"] = np.where(gbsg2["estrec"] <= 36, "Low", "High")
gbsg2["estrec_cat"] = pd.Categorical(
    gbsg2["estrec_cat"], categories=["Low", "High"], ordered=True
)

bins = [-float("inf"), 20, 50, float("inf")]
labels = ["<=20", "20<x<=50", "<50"]
gbsg2["progrec_cat"] = pd.cut(
    gbsg2["progrec"], bins=bins, labels=labels, include_lowest=True
)
gbsg2["progrec_cat"] = pd.Categorical(
    gbsg2["progrec_cat"], categories=labels, ordered=True
)

gbsg2.head()


# %%
# plot forestplot using :func:`cnsplots.forestplot`
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
cns.figure(200, 210, ["black"])
cns.forestplot(model)
model.results.head()


# %%
# plot forestplot using :func:`cnsplots.forestplot`
model = cns.methods.LogisticModel(
    data=gbsg2,
    event="cens",
    variates=[
        "horTh",
        "age",
        "menostat",
        "tsize",
        "tgrade",
        "pnodes",
        "progrec",
        "estrec",
        "estrec_cat",
        "progrec_cat",
        "pnodes + progrec",
    ],
)
model.fit()
cns.figure(150, 150, ["black"])
cns.forestplot(model)
model.results.head()
