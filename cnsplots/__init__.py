"""CNSPlots Module."""

from cnsplots._common import colors
from cnsplots._plots import (
    barplot,
    boxplot,
    distplot,
    figure,
    heatmap,
    piechart,
    regplot,
    stackplot,
    survivalplot,
)
from cnsplots._setup import setup_altair, setup_matplotlib

__version__ = "0.0.0"
__all__ = (
    setup_altair,
    setup_matplotlib,
    colors,
    figure,
    piechart,
    barplot,
    boxplot,
    distplot,
    regplot,
    stackplot,
    survivalplot,
    heatmap,
)
