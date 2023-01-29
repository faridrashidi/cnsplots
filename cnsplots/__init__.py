"""CNSPlots Module."""

import palettable

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
    volcanoplot,
)
from cnsplots._setup import setup_altair, setup_matplotlib

__version__ = "0.0.0"
__all__ = (
    palettable,
    setup_altair,
    setup_matplotlib,
    colors,
    figure,
    barplot,
    boxplot,
    distplot,
    heatmap,
    piechart,
    regplot,
    stackplot,
    survivalplot,
    volcanoplot,
)
