"""
forestplot
----------

create forestplot
"""

# %%
# load data
import lifelines as ll
import numpy as np
import pandas as pd

import cnsplots as cns

rossi = ll.datasets.load_rossi()
rossi.head()

# %%
# plot forestplot using :func:`cnsplots.forestplot`
cns.figure(150, 210, ["black"])
cns.forestplot(
    rossi,
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
cns.figure(200, 210, ["black"])
cns.forestplot(
    gbsg2,
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
