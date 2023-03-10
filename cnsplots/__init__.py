"""CNSPlots Module."""

from cnsplots._plots import (
    barplot,
    boxplot,
    confusionplot,
    distplot,
    heatmapplot,
    histplot,
    lineplot,
    phyloplot,
    pieplot,
    regplot,
    sankeyplot,
    scatterplot,
    stackplot,
    stripplot,
    survivalplot,
    upsetplot,
    vennplot,
    violinplot,
    volcanoplot,
)
from cnsplots._setup import setup_matplotlib
from cnsplots._utils import figure, palettes, take_legend_out

__version__ = "0.0.1"
__all__ = (
    setup_matplotlib,
    figure,
    palettes,
    take_legend_out,
    barplot,
    boxplot,
    confusionplot,
    distplot,
    heatmapplot,
    histplot,
    lineplot,
    phyloplot,
    pieplot,
    regplot,
    sankeyplot,
    scatterplot,
    stackplot,
    stripplot,
    survivalplot,
    upsetplot,
    vennplot,
    violinplot,
    volcanoplot,
)
