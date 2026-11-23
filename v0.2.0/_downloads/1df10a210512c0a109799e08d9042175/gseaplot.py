"""
GSEA Plot
---------

Create Gene Set Enrichment Analysis (GSEA) plots.

GSEA plots visualize pathway enrichment results, showing normalized
enrichment scores (NES) and statistical significance. This example uses
precomputed prerank-style results so the gallery stays reproducible
without live network downloads. You can also pass the output of
``cns.methods.prerank`` directly to ``cns.gseaplot``.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import pandas as pd

import cnsplots as cns


def _build_gsea_results(
    prefix: str,
    rows: list[tuple[str, float, float]],
) -> pd.DataFrame:
    """Create a small prerank-style result table for plotting examples."""

    def _term_id(term: str) -> str:
        cleaned = (
            term.upper()
            .replace("&", "AND")
            .replace("/", " ")
            .replace("-", " ")
            .replace("(", " ")
            .replace(")", " ")
        )
        return "_".join(cleaned.split())

    return pd.DataFrame(
        {
            "Term": [f"{prefix}_{_term_id(term)}" for term, _, _ in rows],
            "Clean_Term": [term for term, _, _ in rows],
            "NES": [nes for _, nes, _ in rows],
            "FDR q-val": [fdr for _, _, fdr in rows],
        }
    )


# %%
# Create example GSEA results
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# These tables mirror the columns returned by ``cns.methods.prerank``.
# For a live analysis, replace them with the output of:
#
# ``cns.methods.prerank(de_results, "GO_Biological_Process_2021", "symbol", "rank")``
gsea_res = _build_gsea_results(
    "GO_BIOLOGICAL_PROCESS_2021",
    [
        ("Interferon Gamma Response", 2.7, 0.001),
        ("Chromatin Remodeling", 2.5, 0.002),
        ("Mitotic Spindle Checkpoint", 2.4, 0.004),
        ("DNA Repair", 2.3, 0.006),
        ("T Cell Activation", 2.2, 0.007),
        ("Antigen Presentation", 2.0, 0.010),
        ("Oxidative Stress Response", 1.9, 0.014),
        ("Protein Folding", 1.8, 0.018),
        ("Autophagy Regulation", 1.7, 0.022),
        ("RNA Splicing", -1.7, 0.030),
        ("Mitochondrial Translation", -1.8, 0.026),
        ("Cell Cycle Progression", -2.0, 0.019),
        ("Inflammatory Response", -2.1, 0.015),
        ("Apoptotic Signaling", -2.3, 0.011),
    ],
)

gsea_kegg = _build_gsea_results(
    "KEGG_2021_HUMAN",
    [
        ("Cell Cycle", 2.4, 0.002),
        ("DNA Replication", 2.2, 0.004),
        ("Proteasome", 2.0, 0.009),
        ("Ribosome Biogenesis", 1.8, 0.016),
        ("Spliceosome", 1.7, 0.021),
        ("Oxidative Phosphorylation", -1.7, 0.030),
        ("Lysosome", -1.8, 0.024),
        ("Apoptosis", -2.0, 0.017),
        ("JAK STAT Signaling", -2.1, 0.013),
        ("T Cell Receptor Signaling", -2.3, 0.008),
    ],
)

gsea_reactome = _build_gsea_results(
    "REACTOME_2022",
    [
        ("Innate Immune System", 2.5, 0.002),
        ("Adaptive Immune System", 2.2, 0.004),
        ("Cellular Responses To Stress", 2.0, 0.010),
        ("DNA Double Strand Break Repair", 1.9, 0.015),
        ("mRNA Processing", 1.7, 0.022),
        ("Metabolism Of RNA", -1.7, 0.028),
        ("Mitochondrial Protein Import", -1.8, 0.024),
        ("Respiratory Electron Transport", -2.0, 0.019),
        ("Programmed Cell Death", -2.2, 0.012),
        ("Extracellular Matrix Organization", -2.4, 0.007),
    ],
)

gsea_mf = _build_gsea_results(
    "GO_MOLECULAR_FUNCTION_2021",
    [
        ("DNA Binding", 2.3, 0.003),
        ("ATPase Activity", 2.0, 0.009),
        ("Kinase Regulator Activity", 1.8, 0.017),
        ("Protein Heterodimerization Activity", 1.7, 0.022),
        ("Oxidoreductase Activity", -1.7, 0.030),
        ("GTPase Binding", -1.9, 0.019),
        ("Cytokine Receptor Binding", -2.0, 0.015),
        ("Transcription Coregulator Activity", -2.2, 0.010),
    ],
)

gsea_cc = _build_gsea_results(
    "GO_CELLULAR_COMPONENT_2021",
    [
        ("Chromosomal Region", 2.4, 0.002),
        ("Spindle Pole", 2.2, 0.005),
        ("Nuclear Speck", 1.9, 0.011),
        ("Proteasome Complex", 1.7, 0.020),
        ("Endoplasmic Reticulum Lumen", -1.7, 0.030),
        ("Mitochondrial Matrix", -1.9, 0.019),
        ("Lysosomal Membrane", -2.0, 0.015),
        ("Cell Leading Edge", -2.1, 0.011),
    ],
)

gsea_wiki = _build_gsea_results(
    "WIKIPATHWAY_2023_HUMAN",
    [
        ("Interleukin 6 Signaling", 2.2, 0.004),
        ("Type II Interferon Signaling", 2.0, 0.008),
        ("DNA Damage Response", 1.9, 0.012),
        ("Mitotic G1 G1 S Phases", 1.7, 0.020),
        ("mTOR Signaling", -1.7, 0.029),
        ("Apoptosis Modulation", -1.8, 0.024),
        ("Mitochondrial Biogenesis", -2.0, 0.016),
        ("TGF Beta Receptor Signaling", -2.2, 0.010),
    ],
)

gsea_res.head()


# %%
# Basic GSEA plot - GO Biological Process
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Visualize the strongest enriched terms from prerank-style results.
cns.figure(180, 130)
ax = cns.gseaplot(gsea_res, y="Clean_Term", top_term=12, size=1.5)
ax.set_title("GSEA Plot")


# %%
# Top 8 enriched terms
# ~~~~~~~~~~~~~~~~~~~~
# Display fewer terms for a cleaner plot.
cns.figure(150, 100)
cns.gseaplot(gsea_res, y="Clean_Term", top_term=8, size=1.5)


# %%
# All enriched terms
# ~~~~~~~~~~~~~~~~~~
# Show the complete result table.
cns.figure(200, 180)
cns.gseaplot(gsea_res, y="Clean_Term", top_term=len(gsea_res), size=1.5)


# %%
# KEGG pathway enrichment
# ~~~~~~~~~~~~~~~~~~~~~~~
# Use prerank-style KEGG results for pathway analysis.
cns.figure(150, 100)
ax = cns.gseaplot(gsea_kegg, y="Clean_Term", top_term=10, size=1.5)
ax.set_title("KEGG Pathways")


# %%
# Reactome pathway enrichment
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use prerank-style Reactome results for biological pathways.
cns.figure(180, 120)
ax = cns.gseaplot(gsea_reactome, y="Clean_Term", top_term=10, size=1.5)
ax.set_title("Reactome Pathways")


# %%
# GO Molecular Function
# ~~~~~~~~~~~~~~~~~~~~~
# Enrichment analysis for molecular functions.
cns.figure(250, 100)
ax = cns.gseaplot(gsea_mf, y="Clean_Term", top_term=8, size=1.5)
ax.set_title("GO Molecular Function")


# %%
# GO Cellular Component
# ~~~~~~~~~~~~~~~~~~~~~
# Enrichment analysis for cellular locations.
cns.figure(150, 100)
ax = cns.gseaplot(gsea_cc, y="Clean_Term", top_term=8, size=1.5)
ax.set_title("GO Cellular Component")


# %%
# WikiPathways enrichment
# ~~~~~~~~~~~~~~~~~~~~~~~
# Use prerank-style WikiPathways results.
cns.figure(150, 100)
ax = cns.gseaplot(gsea_wiki, y="Clean_Term", top_term=8, size=1.5)
ax.set_title("WikiPathways")


# %%
# Larger dot size
# ~~~~~~~~~~~~~~~
# Increase dot size for emphasis.
cns.figure(100, 100)
ax = cns.gseaplot(gsea_res, y="Clean_Term", top_term=8, size=1)
ax.set_title("Larger Dots")


# %%
# Smaller dot size
# ~~~~~~~~~~~~~~~~
# Decrease dot size for denser plots.
cns.figure(180, 150)
ax = cns.gseaplot(gsea_res, y="Clean_Term", top_term=12, size=1.2)
ax.set_title("Smaller Dots")


# %%
# Comparing pathway databases
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Side-by-side comparison of different databases.
mp = cns.multipanel(max_width=300)

mp.panel("A", 100, 100, margin_right=0, margin_bottom=20)
cns.gseaplot(gsea_res, y="Clean_Term", top_term=8, size=1.5)
mp.get_axes("A").set_title("GO Biological Process")

mp.newline()

mp.panel("B", 100, 100, margin_right=0)
cns.gseaplot(gsea_kegg, y="Clean_Term", top_term=8, size=1.5)
mp.get_axes("B").set_title("KEGG")


# %%
# GO categories comparison
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Compare different Gene Ontology categories.
mp = cns.multipanel(max_width=300)

mp.panel("A", 100, 100, margin_right=0, margin_bottom=30)
cns.gseaplot(gsea_res, y="Clean_Term", top_term=6, size=1.4)
mp.get_axes("A").set_title("Biological Process")

mp.newline()

mp.panel("B", 100, 100, margin_right=0, margin_bottom=30)
cns.gseaplot(gsea_mf, y="Clean_Term", top_term=6, size=1.4)
mp.get_axes("B").set_title("Molecular Function")

mp.newline()

mp.panel("C", 100, 100, margin_right=0)
cns.gseaplot(gsea_cc, y="Clean_Term", top_term=6, size=1.4)
mp.get_axes("C").set_title("Cellular Component")
