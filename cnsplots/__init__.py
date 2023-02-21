"""CNSPlots Module."""

from cnsplots._plots import (
    barplot,
    boxplot,
    confusionplot,
    distplot,
    heatmapplot,
    histplot,
    lineplot,
    pieplot,
    regplot,
    scatterplot,
    stackplot,
    stripplot,
    survivalplot,
    upsetplot,
    vennplot,
    violinplot,
    volcanoplot,
)
from cnsplots._setup import setup_altair, setup_matplotlib
from cnsplots._utils import _p_value_helper, figure, palettes, take_legend_out

__version__ = "0.0.0"
__all__ = (
    setup_altair,
    setup_matplotlib,
    _p_value_helper,
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
    pieplot,
    regplot,
    scatterplot,
    stackplot,
    stripplot,
    survivalplot,
    upsetplot,
    vennplot,
    violinplot,
    volcanoplot,
)
