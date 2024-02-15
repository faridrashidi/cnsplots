"""
survivalplot
------------

create survivalplot
"""

# %%
# load data
import matplotlib.pyplot as plt
from lifelines.datasets import load_waltons

import cnsplots as cns

waltons = load_waltons()

# %%
# plot survivalplot using :func:`cnsplots.survivalplot`
cns.figure(150, 150)
cns.survivalplot(
    data=waltons, duration="T", event="E", hue="group", hue_order=["miR-137", "control"]
)
plt.legend(loc="upper right")
