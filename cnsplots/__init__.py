"""CNSPlots Module."""

from cnsplots._altair import setup_altair
from cnsplots._matplotlib import figure, setup_matplotlib
from cnsplots._common import colors
from cnsplots._seaborn import sns_barplot, sns_boxplot, sns_distplot, sns_regplot

__version__ = "0.0.0"
__all__ = (
    setup_altair,
    setup_matplotlib,
    figure,
    colors,
    sns_barplot,
    sns_boxplot,
    sns_distplot,
    sns_regplot,
)
