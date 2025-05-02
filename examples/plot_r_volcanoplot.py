"""
volcanoplot
-----------

create volcanoplot
"""

# %%
# load data
import numpy as np
import pandas as pd

import cnsplots as cns

de = pd.read_csv(
    "https://www.dropbox.com/s/q695jhlaudkcle9/de_result.csv?dl=1", index_col=0
)
de["-log10(adjp)"] = -np.log10(de["padj"])
de.head()


# %%
# plot volcanoplot using :func:`cnsplots.volcanoplot`
cns.figure(200, 200)
cns.volcanoplot(de, x="log2FoldChange", y="-log10(adjp)", symbol="symbol")
