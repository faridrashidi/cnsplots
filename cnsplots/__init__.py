"""CNSPlots Module."""

from cnsplots._altair import setup_altair
from cnsplots._common import colors
from cnsplots._matplotlib import figure, setup_matplotlib
from cnsplots._seaborn import (
    plt_piechart,
    sns_barplot,
    sns_boxplot,
    sns_histplot,
    sns_regplot,
    sns_stackplot,
)

__version__ = "0.0.0"
__all__ = (
    setup_altair,
    setup_matplotlib,
    figure,
    colors,
    plt_piechart,
    sns_barplot,
    sns_boxplot,
    sns_histplot,
    sns_regplot,
    sns_stackplot,
)
