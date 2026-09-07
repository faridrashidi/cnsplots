"""
Enrichment Significance Bars
----------------------------

Display computed pathway or GO enrichment results as horizontal -log10(FDR)
bars, with optional overlapping-gene count labels. The data below are synthetic
and require no downloads or enrichment analysis. Significance values are
already adjusted; the plot never computes or adjusts p-values.
"""

# %%
# Supply a complete results table
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import pandas as pd

import cnsplots as cns

results = pd.DataFrame(
    {
        "Term": [
            "DNA repair",
            "Cell cycle",
            "Immune response",
            "RNA processing",
            "Metabolism",
            "Cell adhesion",
        ],
        "FDR q-val": [0.001, 0.0001, 0.01, 0.01, 0.05, 0.2],
        "Count": [12, 18, 9, None, 7, 4],
    }
)
original = results.copy(deep=True)

# %%
# Select significant terms and annotate counts
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# The cutoff is inclusive: FDR = 0.05 is retained. Top-term selection always
# takes the smallest FDR values; ties keep their input order. Larger bars mean
# smaller FDR. Missing counts omit labels without dropping their pathway.
cns.figure(width=250, height=150)
ax = cns.enrichmentbarplot(results, y="Term", count="Count", cutoff=0.05, top_term=5)
ax.set_title("Pathway enrichment")

# %%
# Compose views from explicitly selected results
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set cutoff=None to skip significance filtering and top_term=None to show all
# supplied rows. order="input" controls display order after significance-based
# selection. Duplicate term labels would remain separate bars.
selected = results.loc[results["FDR q-val"] <= 0.01].copy()
mp = cns.multipanel(max_width=650)
ranked_ax = mp.panel("A", width=200, height=140)
cns.enrichmentbarplot(
    selected,
    y="Term",
    count="Count",
    cutoff=None,
    top_term=None,
    ax=ranked_ax,
)
ranked_ax.set_title("Ranked by significance")
input_ax = mp.panel("B", width=200, height=140)
cns.enrichmentbarplot(
    selected,
    y="Term",
    cutoff=None,
    top_term=None,
    order="input",
    ax=input_ax,
)
input_ax.set_title("Input order")
pd.testing.assert_frame_equal(results, original)

# %%
# Obtain every summary row from prerank
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# For your own ranked genes, request all computed results with
# ``cns.prerank(ranked_genes, gene_sets, "gene", "rank", fdr_cutoff=None,
# min_abs_nes=None)`` and then choose rows for this plot or ``cns.gseaplot``.
# The prerank defaults remain strict FDR < 0.25 and abs(NES) > 1.5.
#
# Missing/nonfinite FDR values or values outside [0, 1] are rejected. Exact
# zeros use the smallest positive normal float for plotting, giving a finite
# length of about 307.65; this display convention does not estimate their true
# significance. Positive FDR values are unchanged. Empty selections return
# labeled axes without bars. A supplied raw p-value column is used as-is and
# named on the axis; it is never relabeled as adjusted significance.
