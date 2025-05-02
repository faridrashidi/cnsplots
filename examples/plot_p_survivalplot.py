"""
survivalplot
------------

create survivalplot
"""

# %%
# load data
import lifelines as ll
import matplotlib.pyplot as plt

import cnsplots as cns

waltons = ll.datasets.load_waltons()


# %%
# plot survivalplot using :func:`cnsplots.survivalplot`
cns.figure(150, 150)
cns.survivalplot(
    data=waltons, duration="T", event="E", hue="group", hue_order=["miR-137", "control"]
)
_ = plt.legend(loc="upper right")


# %%
# plot cumulativeincidenceplot using :func:`cnsplots.cumulativeincidenceplot`
cns.figure(150, 150)
cns.cumulativeincidenceplot(
    data=waltons, duration="T", event="E", hue="group", hue_order=["miR-137", "control"]
)
plt.xlabel("Time (Months)")
_ = plt.legend(loc="upper left")
