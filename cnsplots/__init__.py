"""CNSPlots Module."""

import palettable

from cnsplots._common import colors
from cnsplots._plots import (
    barplot,
    boxplot,
    distplot,
    heatmap,
    piechart,
    regplot,
    stackplot,
    survivalplot,
    violinplot,
    volcanoplot,
)
from cnsplots._setup import setup_altair, setup_matplotlib
from cnsplots._utils import _p_value_helper, figure, take_legend_out

__version__ = "0.0.0"
__all__ = (
    palettable,
    setup_altair,
    setup_matplotlib,
    colors,
    figure,
    take_legend_out,
    _p_value_helper,
    barplot,
    boxplot,
    distplot,
    heatmap,
    piechart,
    regplot,
    stackplot,
    survivalplot,
    violinplot,
    volcanoplot,
)
