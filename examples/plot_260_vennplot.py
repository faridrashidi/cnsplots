"""
vennplot
--------

Create Venn diagrams for visualizing set overlaps.

Venn diagrams show the relationships between 2-3 sets, displaying
the number of elements in each region (unique and shared).
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import matplotlib.pyplot as plt

import cnsplots as cns

# %%
# Create sample sets
# ~~~~~~~~~~~~~~~~~~
set1 = {"A", "B", "C", "D"}
set2 = {"B", "C", "D", "E"}
set3 = {"C", "D", "E", "F", "G"}
labels = ["Set1", "Set2", "Set3"]


# %%
# Basic three-set Venn diagram
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Visualize overlap between three sets.
cns.figure(100, 100)
cns.vennplot([set1, set2, set3], labels)
plt.title("Three-Set Venn Diagram")


# %%
# Two-set Venn diagram
# ~~~~~~~~~~~~~~~~~~~~
# Simpler diagram for comparing two sets.
cns.figure(100, 100)
cns.vennplot([set1, set3], ["Set1", "Set3"])
plt.title("Two-Set Venn Diagram")


# %%
# Gene set overlap example
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Common use case in genomics: comparing gene lists.
upregulated_genes = {"TP53", "BRCA1", "MYC", "EGFR", "KRAS", "PIK3CA", "PTEN"}
mutated_genes = {"TP53", "KRAS", "PIK3CA", "APC", "BRAF", "NRAS"}
methylated_genes = {"BRCA1", "CDKN2A", "MLH1", "TP53", "MGMT"}

cns.figure(120, 100)
cns.vennplot(
    [upregulated_genes, mutated_genes, methylated_genes],
    ["Upregulated", "Mutated", "Methylated"],
)
plt.title("Gene Set Overlaps")


# %%
# Differentially expressed genes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare DEGs across conditions.
condition_a_degs = set(["gene" + str(i) for i in range(1, 51)])  # 50 genes
condition_b_degs = set(["gene" + str(i) for i in range(30, 80)])  # 50 genes
condition_c_degs = set(["gene" + str(i) for i in range(45, 95)])  # 50 genes

cns.figure(120, 100)
cns.vennplot(
    [condition_a_degs, condition_b_degs, condition_c_degs],
    ["Condition A", "Condition B", "Condition C"],
)
plt.title("DEG Overlap Across Conditions")


# %%
# Two-set comparison: Treatment vs Control
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
treatment_responsive = set(["gene" + str(i) for i in range(1, 101)])
control_baseline = set(["gene" + str(i) for i in range(50, 150)])

cns.figure(100, 100)
cns.vennplot([treatment_responsive, control_baseline], ["Treatment", "Control"])
plt.title("Treatment vs Control Genes")


# %%
# Sample overlap example
# ~~~~~~~~~~~~~~~~~~~~~~
# Compare samples passing different QC criteria.
high_coverage = {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"}
low_duplication = {"S1", "S3", "S4", "S6", "S7", "S9", "S10"}
clean_data = {"S1", "S2", "S4", "S5", "S7", "S8", "S10", "S11"}

cns.figure(120, 100)
cns.vennplot(
    [high_coverage, low_duplication, clean_data], ["High Cov", "Low Dup", "Clean"]
)
plt.title("Sample QC Criteria")


# %%
# Comparing classifier predictions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# See which samples are classified by each model.
model_a_positive = {"sample_" + str(i) for i in [1, 2, 3, 5, 8, 13, 21]}
model_b_positive = {"sample_" + str(i) for i in [1, 3, 5, 7, 9, 11, 13]}

cns.figure(100, 100)
cns.vennplot([model_a_positive, model_b_positive], ["Model A", "Model B"])
plt.title("Classifier Agreement")


# %%
# Pathway overlap
# ~~~~~~~~~~~~~~~
# Compare genes in different pathways.
apoptosis_genes = {"BAX", "BCL2", "CASP3", "CASP9", "CYCS", "TP53", "BID"}
cell_cycle_genes = {"CDK1", "CDK2", "CCNA", "CCNB", "TP53", "RB1", "E2F1"}
dna_repair_genes = {"BRCA1", "BRCA2", "ATM", "ATR", "TP53", "RAD51", "CHEK2"}

cns.figure(120, 100)
cns.vennplot(
    [apoptosis_genes, cell_cycle_genes, dna_repair_genes],
    ["Apoptosis", "Cell Cycle", "DNA Repair"],
)
plt.title("Pathway Gene Overlap")


# %%
# Side-by-side Venn comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare different analyses.
mp = cns.multipanel((1, 2), max_width=280, hgap=30)

mp.panel("A", 100, 100)
setA = set(range(1, 51))
setB = set(range(30, 80))
cns.vennplot([setA, setB], ["Set A", "Set B"])
mp.get_axes("A").set_title("Analysis 1")

mp.panel("B", 100, 100)
setC = set(range(1, 41))
setD = set(range(35, 75))
cns.vennplot([setC, setD], ["Set C", "Set D"])
mp.get_axes("B").set_title("Analysis 2")
