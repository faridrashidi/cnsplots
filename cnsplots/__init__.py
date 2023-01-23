"""CNSPlots Module."""

from cnsplots._altair import setup_altair
from cnsplots._matplotlib import figure, setup_matplotlib, barplot
from cnsplots._common import colors

__version__ = "0.0.0"
__all__ = (setup_altair, setup_matplotlib, figure, barplot)
