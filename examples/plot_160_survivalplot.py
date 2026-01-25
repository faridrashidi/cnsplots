"""
survivalplot
------------

create survivalplot
"""

# %%
# load data
import lifelines as ll
import matplotlib.pyplot as plt
import numpy as np

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
ax = cns.cumulativeincidenceplot(
    data=waltons,
    duration="T",
    event="E",
    hue="group",
    hue_order=["miR-137", "control"],
    xticks=np.arange(0, waltons["T"].max() + 2, 12),
    show_risk_table=True,
    risk_table_ypos=-0.2,
)
ax.set_xlabel("Time (Months)")
_ = plt.legend(loc="upper left")
