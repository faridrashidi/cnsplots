"""
gseaplot
--------

create gseaplot
"""

# %%
# load data
import gseapy as gp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import cnsplots as cns

de = pd.read_csv(
    "https://www.dropbox.com/s/q695jhlaudkcle9/de_result.csv?dl=1", index_col=0
)
de["-log10(adjp)"] = -np.log10(de["padj"])
de["rank"] = de["log2FoldChange"].abs()
de = de.sort_values("rank", ascending=False)
de = de[["symbol", "rank"]]
de.head()


# %%
# plot volcanoplot using :func:`cnsplots.volcanoplot`
gsea_res = cns.methods.prerank(de, "GO_Biological_Process_2021", "symbol", "rank")
cns.figure(250, 130)
cns.gseaplot(gsea_res, y="Clean_Term", top_term=20, size=1.8)
