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
de["DEG"] = "NS"
de.loc[de["pvalue"] < 0.05, "DEG"] = "p < 0.05"
up = (de["pvalue"] < 0.05) & (de["log2FoldChange"] > 0)
de.loc[de.loc[up].nlargest(10, "-log10(adjp)").index, "DEG"] = "Up"
down = (de["pvalue"] < 0.05) & (de["log2FoldChange"] < 0)
de.loc[de.loc[down].nlargest(10, "-log10(adjp)").index, "DEG"] = "Down"

# %%
# plot volcanoplot using :func:`cnsplots.volcanoplot`
cns.figure(200, 200)
cns.volcanoplot(de, x="log2FoldChange", y="-log10(adjp)", hue="DEG", symbol="symbol")
