"""CNSPlots Module."""

import cnsplots._methods as methods
from cnsplots._plots import (
    barplot,
    boxplot,
    confusionplot,
    cumulativeincidenceplot,
    distplot,
    donutplot,
    dotplot,
    forestplot,
    heatmapplot,
    histplot,
    kdeplot,
    lineplot,
    phyloplot,
    pieplot,
    qqplot,
    regplot,
    ridgeplot,
    rocplot,
    sankeyplot,
    scatterplot,
    slopeplot,
    stackplot,
    stripplot,
    survivalplot,
    upsetplot,
    vennplot,
    violinplot,
    volcanoplot,
)
from cnsplots._setup import setup_ax, setup_matplotlib, setup_scanpy
from cnsplots._utils import (
    BLUE,
    BROWN,
    GRAY,
    GREEN,
    ORANGE,
    PINK,
    PURPLE,
    RED,
    YELLOW,
    figure,
    get_hexcolors_from_apalette,
    palettes,
    savefig,
    take_legend_out,
)

__version__ = "0.0.1"
__all__ = (
    methods,
    setup_matplotlib,
    setup_scanpy,
    figure,
    savefig,
    palettes,
    take_legend_out,
    get_hexcolors_from_apalette,
    barplot,
    boxplot,
    confusionplot,
    cumulativeincidenceplot,
    distplot,
    donutplot,
    dotplot,
    forestplot,
    heatmapplot,
    histplot,
    kdeplot,
    lineplot,
    phyloplot,
    pieplot,
    qqplot,
    regplot,
    ridgeplot,
    rocplot,
    sankeyplot,
    scatterplot,
    slopeplot,
    stackplot,
    stripplot,
    survivalplot,
    upsetplot,
    vennplot,
    violinplot,
    volcanoplot,
)

import warnings

warnings.filterwarnings("ignore", message="findfont: Font family 'Helvetica' not found")

import logging

mpl_logger = logging.getLogger("matplotlib")
mpl_logger.setLevel(logging.ERROR)
