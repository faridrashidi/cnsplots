"""
upsetplot
---------

Create UpSet plots for visualizing set intersections.

UpSet plots are an alternative to Venn diagrams that scale better
for many sets (>3). They show all possible intersections as a
matrix with bar charts indicating intersection sizes.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import random

import cnsplots as cns

# %%
# Create sample sets
# ~~~~~~~~~~~~~~~~~~
sets = {
    "A": ["a", "b", "c", "d"],
    "B": ["c", "d", "e", "f"],
    "C": ["b", "d", "f", "g"],
    "D": ["a", "e", "g", "h"],
}


# %%
# Basic UpSet plot
# ~~~~~~~~~~~~~~~~
# Show all set intersections.
cns.upsetplot(sets, subset_size="count")


# %%
# UpSet plot without totals
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Hide the set totals bar on the left.
cns.upsetplot(sets, totals_plot_elements=0, facecolor=cns.VIOLET)


# %%
# UpSet plot with custom color
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Change the bar color.
cns.upsetplot(sets, facecolor=cns.BLUE)


# %%
# Sort by cardinality
# ~~~~~~~~~~~~~~~~~~~
# Sort intersections by size (largest first).
cns.upsetplot(sets, sort_by="cardinality")


# %%
# Sort by degree
# ~~~~~~~~~~~~~~
# Sort by number of sets in intersection.
cns.upsetplot(sets, sort_by="degree")


# %%
# Gene set intersection example
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Common use case: finding genes shared across conditions.
gene_sets = {
    "Treatment_A": ["TP53", "BRCA1", "MYC", "EGFR", "KRAS", "PIK3CA"],
    "Treatment_B": ["TP53", "KRAS", "APC", "BRAF", "NRAS", "PTEN"],
    "Treatment_C": ["BRCA1", "EGFR", "TP53", "CDKN2A", "MLH1"],
    "Control": ["TP53", "MYC", "KRAS", "APC", "RB1"],
}

cns.upsetplot(gene_sets, sort_by="cardinality", facecolor=cns.GREEN)


# %%
# Larger dataset example
# ~~~~~~~~~~~~~~~~~~~~~~
# UpSet plots handle many sets better than Venn diagrams.
random.seed(42)
all_items = [f"item_{i}" for i in range(100)]

large_sets = {
    "Set_1": random.sample(all_items, 40),
    "Set_2": random.sample(all_items, 35),
    "Set_3": random.sample(all_items, 45),
    "Set_4": random.sample(all_items, 30),
    "Set_5": random.sample(all_items, 38),
}

cns.upsetplot(large_sets, sort_by="cardinality")


# %%
# Filter by minimum size
# ~~~~~~~~~~~~~~~~~~~~~~
# Show only intersections with at least N elements.
cns.upsetplot(large_sets, min_subset_size=3, sort_by="cardinality")


# %%
# Limit number of intersections shown
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Show only top N intersections.
cns.upsetplot(large_sets, max_subset_rank=10, sort_by="cardinality")


# %%
# Sample overlap analysis
# ~~~~~~~~~~~~~~~~~~~~~~~
# Compare which samples pass different quality filters.
sample_filters = {
    "High_Quality": [f"S{i}" for i in [1, 2, 3, 5, 7, 8, 10, 12, 15]],
    "High_Coverage": [f"S{i}" for i in [1, 3, 4, 5, 6, 8, 9, 11, 12]],
    "Low_Duplication": [f"S{i}" for i in [2, 3, 5, 6, 7, 8, 10, 13, 14]],
    "Clean_Data": [f"S{i}" for i in [1, 2, 5, 8, 9, 10, 11, 15]],
}

cns.upsetplot(sample_filters, sort_by="cardinality", facecolor=cns.ORANGE)


# %%
# Pathway membership
# ~~~~~~~~~~~~~~~~~~
# Analyze gene membership across biological pathways.
pathways = {
    "Apoptosis": ["CASP3", "CASP9", "BAX", "BCL2", "TP53", "BID", "CYCS"],
    "Cell_Cycle": ["CDK1", "CDK2", "CCNA", "CCNB", "TP53", "RB1", "E2F1"],
    "DNA_Repair": ["BRCA1", "BRCA2", "ATM", "ATR", "TP53", "RAD51"],
    "PI3K_Signaling": ["PIK3CA", "AKT1", "PTEN", "MTOR", "TSC1", "TSC2"],
    "MAPK_Signaling": ["KRAS", "BRAF", "MEK1", "ERK1", "RAF1"],
}

cns.upsetplot(pathways, sort_by="cardinality", facecolor=cns.PURPLE)


# %%
# Clinical trial cohorts
# ~~~~~~~~~~~~~~~~~~~~~~
# Compare patient inclusion across different trials.
clinical_cohorts = {
    "Trial_1": [f"P{i}" for i in range(1, 51)],
    "Trial_2": [f"P{i}" for i in range(30, 80)],
    "Trial_3": [f"P{i}" for i in range(60, 100)],
}

cns.upsetplot(clinical_cohorts, sort_by="cardinality", facecolor=cns.RED)


# %%
# UpSet with different colors
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Showcase color options.
cns.upsetplot(sets, facecolor=cns.CHOCOLATE)
