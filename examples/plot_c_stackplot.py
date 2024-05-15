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

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100)
cns.stackplot(data=tips, x="sex", y="day", width=0.4, normalize=True, addtip=True)

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100)
cns.stackplot(
    data=tips, x="day", y="sex", stack_order=["Female", "Male"], normalize=False
)

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100)
cns.stackplot(
    data=tips,
    x="day",
    y="sex",
    normalize=True,
    pairs=[("Thur", "Fri"), ("Fri", "Sat")],
)

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100)
cns.stackplot(
    data=tips,
    x="sex",
    y="day",
    normalize=True,
    stack_order=["Sun", "Sat", "Fri", "Thur"],
    pairs=[("Male", "Female")],
)

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100, "Tableau")
cns.stackplot(data=tips, x="day", y="sex", normalize=True, pairs="all")

# %%
# plot stackplot using :func:`cnsplots.stackplot`
cns.figure(120, 100)
cns.stackplot(
    data=tips,
    x="sex",
    y="day",
    horizontal=True,
    normalize=True,
    pairs=[("Thur", "Fri"), ("Fri", "Sat")],
    bar_order=["Fri", "Sat", "Sun", "Thur"],
)
