"""Plot functions for cnsplots."""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._categorical import barplot as barplot
    from ._categorical import donutplot as donutplot
    from ._categorical import dumbbellplot as dumbbellplot
    from ._categorical import lollipopplot as lollipopplot
    from ._categorical import pieplot as pieplot
    from ._categorical import stackplot as stackplot
    from ._categorical import stripplot as stripplot
    from ._distribution import boxplot as boxplot
    from ._distribution import distplot as distplot
    from ._distribution import histplot as histplot
    from ._distribution import kdeplot as kdeplot
    from ._distribution import qqplot as qqplot
    from ._distribution import ridgeplot as ridgeplot
    from ._distribution import violinplot as violinplot
    from ._genomics import gseaplot as gseaplot
    from ._genomics import volcanoplot as volcanoplot
    from ._heatmap import confusionplot as confusionplot
    from ._heatmap import dotplot as dotplot
    from ._heatmap import heatmapplot as heatmapplot
    from ._regression import lineplot as lineplot
    from ._regression import regplot as regplot
    from ._regression import scatterplot as scatterplot
    from ._regression import slopeplot as slopeplot
    from ._sets import upsetplot as upsetplot
    from ._sets import vennplot as vennplot
    from ._specialized import forestplot as forestplot
    from ._specialized import phyloplot as phyloplot
    from ._specialized import placeholderplot as placeholderplot
    from ._specialized import rocplot as rocplot
    from ._specialized import sankeyplot as sankeyplot
    from ._survival import cumulativeincidenceplot as cumulativeincidenceplot
    from ._survival import survivalplot as survivalplot

_LAZY_IMPORTS = {
    "barplot": ("cnsplots.plots._categorical", "barplot"),
    "boxplot": ("cnsplots.plots._distribution", "boxplot"),
    "confusionplot": ("cnsplots.plots._heatmap", "confusionplot"),
    "cumulativeincidenceplot": (
        "cnsplots.plots._survival",
        "cumulativeincidenceplot",
    ),
    "distplot": ("cnsplots.plots._distribution", "distplot"),
    "donutplot": ("cnsplots.plots._categorical", "donutplot"),
    "dotplot": ("cnsplots.plots._heatmap", "dotplot"),
    "dumbbellplot": ("cnsplots.plots._categorical", "dumbbellplot"),
    "forestplot": ("cnsplots.plots._specialized", "forestplot"),
    "gseaplot": ("cnsplots.plots._genomics", "gseaplot"),
    "heatmapplot": ("cnsplots.plots._heatmap", "heatmapplot"),
    "histplot": ("cnsplots.plots._distribution", "histplot"),
    "kdeplot": ("cnsplots.plots._distribution", "kdeplot"),
    "lineplot": ("cnsplots.plots._regression", "lineplot"),
    "lollipopplot": ("cnsplots.plots._categorical", "lollipopplot"),
    "phyloplot": ("cnsplots.plots._specialized", "phyloplot"),
    "placeholderplot": ("cnsplots.plots._specialized", "placeholderplot"),
    "pieplot": ("cnsplots.plots._categorical", "pieplot"),
    "qqplot": ("cnsplots.plots._distribution", "qqplot"),
    "regplot": ("cnsplots.plots._regression", "regplot"),
    "ridgeplot": ("cnsplots.plots._distribution", "ridgeplot"),
    "rocplot": ("cnsplots.plots._specialized", "rocplot"),
    "sankeyplot": ("cnsplots.plots._specialized", "sankeyplot"),
    "scatterplot": ("cnsplots.plots._regression", "scatterplot"),
    "slopeplot": ("cnsplots.plots._regression", "slopeplot"),
    "stackplot": ("cnsplots.plots._categorical", "stackplot"),
    "stripplot": ("cnsplots.plots._categorical", "stripplot"),
    "survivalplot": ("cnsplots.plots._survival", "survivalplot"),
    "upsetplot": ("cnsplots.plots._sets", "upsetplot"),
    "vennplot": ("cnsplots.plots._sets", "vennplot"),
    "violinplot": ("cnsplots.plots._distribution", "violinplot"),
    "volcanoplot": ("cnsplots.plots._genomics", "volcanoplot"),
}

__all__ = list(_LAZY_IMPORTS)


def __getattr__(name: str):
    """Load a plot function on first access."""
    try:
        module_name, attribute_name = _LAZY_IMPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None

    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return eager and lazy module attributes."""
    return sorted(set(globals()) | set(__all__))
