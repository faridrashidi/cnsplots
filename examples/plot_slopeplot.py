"""
slopeplot
---------

create slopeplot
"""

# %%
# load data
import numpy as np
import pandas as pd

import cnsplots as cns

# %%
# generate data
data = np.concatenate(
    [
        [np.random.normal(loc=1, size=15), 15 * ["site1"], 15 * ["healthy"]],
        [np.random.normal(loc=3, size=15), 15 * ["site2"], 15 * ["healthy"]],
        [np.random.normal(loc=0, size=15), 15 * ["site3"], 15 * ["healthy"]],
        [np.random.normal(loc=1, size=15), 15 * ["site1"], 15 * ["disease"]],
        [np.random.normal(loc=1, size=15), 15 * ["site2"], 15 * ["disease"]],
        [np.random.normal(loc=3, size=15), 15 * ["site3"], 15 * ["disease"]],
    ],
    axis=1,
)
data = pd.DataFrame(columns=["value", "site", "label"], data=data.T)
data["value"] = data["value"].astype(float)

# %%
# plot slopeplot using :func:`cnsplots.slopeplot`
cns.figure(150, 150)
cns.slopeplot(data=data, x="site", y="value", hue="label")
