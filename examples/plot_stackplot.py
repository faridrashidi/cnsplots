"""
stackplot
---------

create stackplot
"""

# %%
# load data
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")
df = tips.value_counts(["sex", "day"]).reset_index().rename(columns={0: "value"})

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100)
cns.stackplot(data=df, x="sex", y="value", hue="day", width=0.4, normalize=True)

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100)
cns.stackplot(
    data=df,
    x="day",
    y="value",
    hue="sex",
    hue_order=["Female", "Male"],
    normalize=False,
)

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100)
cns.stackplot(
    data=df,
    x="day",
    y="value",
    hue="sex",
    normalize=True,
    pairs=[("Thur", "Fri"), ("Fri", "Sat")],
)

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100)
cns.stackplot(
    data=df, x="sex", y="value", hue="day", normalize=True, pairs=[("Male", "Female")]
)

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100, "Tableau")
cns.stackplot(data=df, x="day", y="value", hue="sex", normalize=True, pairs="all")

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100)
cns.stackplot(
    data=df,
    x="value",
    y="day",
    hue="sex",
    normalize=True,
    pairs=[("Thur", "Fri"), ("Fri", "Sat")],
    order=["Fri", "Sat", "Sun", "Thur"],
)
