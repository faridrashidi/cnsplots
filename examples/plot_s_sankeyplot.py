"""
sankeyplot
----------

create sankeyplot
"""

# %%
# load data
import pandas as pd

import cnsplots as cns

data = pd.DataFrame(
    {
        "x": ["A", "A", "B", "B", "C", "C"],
        "y": ["X", "Y", "Y", "Z", "X", "Z"],
    }
)


# %%
# plot sankeyplot using :func:`cnsplots.sankeyplot`
cns.figure(100, 80)
cns.sankeyplot(data=data, x="x", y="y")
