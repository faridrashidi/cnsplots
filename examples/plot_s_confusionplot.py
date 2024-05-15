"""
confusionplot
-------------

create confusionplot
"""

# %%
# load data
import pandas as pd

import cnsplots as cns

data = pd.DataFrame(
    {"x": [0, 1, 1, 0, 1, 1, 1, 0, 0, 0], "y": [0, 1, 0, 0, 1, 1, 0, 0, 0, 0]}
)

# %%
# plot confusionplot using :func:`cnsplots.confusionplot`
cns.figure(80, 80)
cns.confusionplot(data=data, x="x", y="y")

# %%
# plot confusionplot using :func:`cnsplots.confusionplot`
cns.figure(100, 100)
cns.confusionplot(data=data, x="x", y="y", add_pvalue=True)
