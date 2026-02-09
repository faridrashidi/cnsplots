"""Plot functions for cnsplots."""

from cnsplots.plots._categorical import (
    barplot,
    donutplot,
    pieplot,
    stackplot,
    stripplot,
)
from cnsplots.plots._distribution import (
    boxplot,
    distplot,
    histplot,
    kdeplot,
    qqplot,
    ridgeplot,
    violinplot,
)
from cnsplots.plots._genomics import gseaplot, volcanoplot
from cnsplots.plots._heatmap import confusionplot, dotplot, heatmapplot
from cnsplots.plots._regression import lineplot, regplot, scatterplot, slopeplot
from cnsplots.plots._sets import upsetplot, vennplot
from cnsplots.plots._specialized import forestplot, phyloplot, rocplot, sankeyplot
from cnsplots.plots._survival import cumulativeincidenceplot, survivalplot

__all__ = [
    "barplot",
    "boxplot",
    "confusionplot",
    "cumulativeincidenceplot",
    "distplot",
    "donutplot",
    "dotplot",
    "forestplot",
    "gseaplot",
    "heatmapplot",
    "histplot",
    "kdeplot",
    "lineplot",
    "phyloplot",
    "pieplot",
    "qqplot",
    "regplot",
    "ridgeplot",
    "rocplot",
    "sankeyplot",
    "scatterplot",
    "slopeplot",
    "stackplot",
    "stripplot",
    "survivalplot",
    "upsetplot",
    "vennplot",
    "violinplot",
    "volcanoplot",
]
