"""
volcanoplot
-----------

create volcanoplot
"""

# %%
# load data
import pandas as pd

import cnsplots as cns

de = pd.read_csv(
    "https://www.dropbox.com/s/q695jhlaudkcle9/de_result.csv?dl=1", index_col=0
)

# %%
# plot volcanoplot using :func:`cnsplots.volcanoplot`
cns.figure(200, 200)
cns.volcanoplot(de, symbol="symbol")
