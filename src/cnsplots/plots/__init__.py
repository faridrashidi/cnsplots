"""Plot functions for cnsplots."""

from importlib import import_module

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
