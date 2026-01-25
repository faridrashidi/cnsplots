"""
confusionplot
-------------

create confusionplot
"""

# %%
# load data
import pandas as pd

import cnsplots as cns

data1 = pd.DataFrame(
    {"x": [0, 1, 1, 0, 1, 1, 1, 0, 0, 0], "y": [0, 1, 0, 0, 1, 1, 0, 0, 0, 0]}
)
data2 = pd.DataFrame(
    {
        "truth": [0, 0, 0, 1, 1, 1, 1, 0, 1, 0],
        "pred": ["dog", "dog", "cat", "cat", "cat", "dog", "dog", "dog", "cat", "dog"],
    }
)


# %%
# plot confusionplot using :func:`cnsplots.confusionplot`
cns.figure(80, 80)
cns.confusionplot(data=data1, x="x", y="y")


# %%
# plot confusionplot using :func:`cnsplots.confusionplot`
cns.figure(80, 80)
cns.confusionplot(
    data=data2,
    x="truth",
    y="pred",
    add_pvalue=True,
    pvalue_pad=1.5,
    positive_x=1,
    positive_y="dog",
    x_order=[0, 1],
    y_order=["cat", "dog"],
)
