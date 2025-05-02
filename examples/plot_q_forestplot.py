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
# create models
class CoxModel:
    def __init__(self, data, duration, event, variates):
        self.data = data
        self.duration = duration
        self.event = event
        self.variates = variates
        self.results = None
        self.name = "cox"

    def fit(self):
        df = self.data.copy()
        all_results = []
        for var in self.variates:
            cph = ll.CoxPHFitter()
            cph.fit(df, duration_col=self.duration, event_col=self.event, formula=var)
            summary = cph.summary.reset_index()
            summary["analysis"] = var
            all_results.append(summary)
        df = pd.concat(all_results, ignore_index=True)
        df = df.sort_values("exp(coef)").copy()
        df["exp(coef) lower 95%"] = df["exp(coef)"] - df["exp(coef) lower 95%"]
        df["exp(coef) upper 95%"] = df["exp(coef) upper 95%"] - df["exp(coef)"]
        df["log10_pvalue"] = -np.log10(df["p"])

        def display_label_helper(x):
            if "+" in x["analysis"]:
                return x["analysis"] + " (" + x["covariate"] + ")"
            else:
                return x["analysis"]

        df["display_label"] = df.apply(display_label_helper, axis=1)
        self.results = df[
            [
                "display_label",
                "exp(coef)",
                "exp(coef) lower 95%",
                "exp(coef) upper 95%",
                "log10_pvalue",
            ]
        ]


# %%
# load data
rossi = ll.datasets.load_rossi()
rossi.head()

# %%
# plot forestplot using :func:`cnsplots.forestplot`
model = CoxModel(
    data=rossi,
    duration="week",
    event="arrest",
    variates=[
        "age",
        "race",
        "fin + age",
        "mar + paro + prio",
        "fin + age + race + wexp",
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
model = CoxModel(
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
