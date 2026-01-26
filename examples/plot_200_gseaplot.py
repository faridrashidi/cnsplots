"""
gseaplot
--------

Create Gene Set Enrichment Analysis (GSEA) plots.

GSEA plots visualize pathway enrichment results, showing normalized
enrichment scores (NES) and statistical significance. cnsplots
integrates with the gseapy library for running prerank analysis.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import numpy as np
import pandas as pd

import cnsplots as cns

# %%
# Load differential expression data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Download example DE results for GSEA analysis.
de = pd.read_csv(
    "https://www.dropbox.com/s/q695jhlaudkcle9/de_result.csv?dl=1", index_col=0
)
de["-log10(adjp)"] = -np.log10(de["padj"])
de["rank"] = de["log2FoldChange"].abs()
de = de.sort_values("rank", ascending=False)
de = de[["symbol", "rank"]]
de.head()


# %%
# Basic GSEA plot - GO Biological Process
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Run prerank analysis and visualize top enriched terms.
gsea_res = cns.methods.prerank(de, "GO_Biological_Process_2021", "symbol", "rank")
cns.figure(250, 130)
cns.gseaplot(gsea_res, y="Clean_Term", top_term=20, size=1.8)


# %%
# Top 10 enriched terms
# ~~~~~~~~~~~~~~~~~~~~~
# Display fewer terms for a cleaner plot.
cns.figure(250, 100)
cns.gseaplot(gsea_res, y="Clean_Term", top_term=10, size=2.0)


# %%
# Top 30 enriched terms
# ~~~~~~~~~~~~~~~~~~~~~
# Show more terms for comprehensive overview.
cns.figure(280, 180)
cns.gseaplot(gsea_res, y="Clean_Term", top_term=30, size=1.5)


# %%
# KEGG pathway enrichment
# ~~~~~~~~~~~~~~~~~~~~~~~
# Use KEGG database for pathway analysis.
gsea_kegg = cns.methods.prerank(de, "KEGG_2021_Human", "symbol", "rank")
cns.figure(250, 100)
ax = cns.gseaplot(gsea_kegg, y="Clean_Term", top_term=15, size=1.8)
ax.set_title("KEGG Pathways")


# %%
# Reactome pathway enrichment
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use Reactome database for biological pathways.
gsea_reactome = cns.methods.prerank(de, "Reactome_2022", "symbol", "rank")
cns.figure(280, 120)
ax = cns.gseaplot(gsea_reactome, y="Clean_Term", top_term=15, size=1.6)
ax.set_title("Reactome Pathways")


# %%
# GO Molecular Function
# ~~~~~~~~~~~~~~~~~~~~~
# Enrichment analysis for molecular functions.
gsea_mf = cns.methods.prerank(de, "GO_Molecular_Function_2021", "symbol", "rank")
cns.figure(250, 100)
ax = cns.gseaplot(gsea_mf, y="Clean_Term", top_term=12, size=1.8)
ax.set_title("GO Molecular Function")


# %%
# GO Cellular Component
# ~~~~~~~~~~~~~~~~~~~~~
# Enrichment analysis for cellular locations.
gsea_cc = cns.methods.prerank(de, "GO_Cellular_Component_2021", "symbol", "rank")
cns.figure(250, 100)
ax = cns.gseaplot(gsea_cc, y="Clean_Term", top_term=12, size=1.8)
ax.set_title("GO Cellular Component")


# %%
# WikiPathways enrichment
# ~~~~~~~~~~~~~~~~~~~~~~~
# Use WikiPathways database.
gsea_wiki = cns.methods.prerank(de, "WikiPathway_2023_Human", "symbol", "rank")
cns.figure(280, 100)
ax = cns.gseaplot(gsea_wiki, y="Clean_Term", top_term=12, size=1.8)
ax.set_title("WikiPathways")


# %%
# Larger dot size
# ~~~~~~~~~~~~~~~
# Increase dot size for emphasis.
cns.figure(250, 100)
ax = cns.gseaplot(gsea_res, y="Clean_Term", top_term=10, size=2.5)
ax.set_title("Larger Dots")


# %%
# Smaller dot size
# ~~~~~~~~~~~~~~~~
# Decrease dot size for denser plots.
cns.figure(280, 150)
ax = cns.gseaplot(gsea_res, y="Clean_Term", top_term=25, size=1.2)
ax.set_title("Smaller Dots")


# %%
# Comparing pathway databases
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Side-by-side comparison of different databases.
mp = cns.multipanel((1, 2), max_width=640, hgap=200)

mp.panel("A", 100, 220, offset_x=-1.1)
cns.gseaplot(gsea_res, y="Clean_Term", top_term=10, size=1.5)
mp.get_axes("A").set_title("GO Biological Process")

mp.panel("B", 100, 220, offset_x=-0.8)
cns.gseaplot(gsea_kegg, y="Clean_Term", top_term=10, size=1.5)
mp.get_axes("B").set_title("KEGG")


# %%
# GO categories comparison
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Compare different Gene Ontology categories.
mp = cns.multipanel((1, 3), max_width=940, hgap=230)

mp.panel("A", 100, 180, offset_x=-1.1)
cns.gseaplot(gsea_res, y="Clean_Term", top_term=8, size=1.4)
mp.get_axes("A").set_title("Biological Process")

mp.panel("B", 100, 180, offset_x=-0.9)
cns.gseaplot(gsea_mf, y="Clean_Term", top_term=8, size=1.4)
mp.get_axes("B").set_title("Molecular Function")

mp.panel("C", 100, 180, offset_x=-1.1)
cns.gseaplot(gsea_cc, y="Clean_Term", top_term=8, size=1.4)
mp.get_axes("C").set_title("Cellular Component")
