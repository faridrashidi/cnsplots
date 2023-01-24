"""CNSPlots Module."""

from cnsplots._common import colors
from cnsplots._plots import (
    figure,
    plt_piechart,
    sns_barplot,
    sns_boxplot,
    sns_distplot,
    sns_regplot,
    sns_stackplot,
)
from cnsplots._setup import setup_altair, setup_matplotlib

__version__ = "0.0.0"
__all__ = (
    setup_altair,
    setup_matplotlib,
    colors,
    figure,
    plt_piechart,
    sns_barplot,
    sns_boxplot,
    sns_distplot,
    sns_regplot,
    sns_stackplot,
)
