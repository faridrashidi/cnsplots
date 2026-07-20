"""CNSPlots public API."""

from importlib import import_module

__version__ = "0.4.0"

_LAZY_IMPORTS = {
    "utils": ("cnsplots._utils", None),
    "datasets": ("cnsplots.datasets", None),
    "settings": ("cnsplots._settings", "settings"),
    "validation": ("cnsplots._validation", None),
    "BLUE": ("cnsplots._utils", "BLUE"),
    "BROWN": ("cnsplots._utils", "BROWN"),
    "CHOCOLATE": ("cnsplots._utils", "CHOCOLATE"),
    "GRAY": ("cnsplots._utils", "GRAY"),
    "GREEN": ("cnsplots._utils", "GREEN"),
    "ORANGE": ("cnsplots._utils", "ORANGE"),
    "PINK": ("cnsplots._utils", "PINK"),
    "PURPLE": ("cnsplots._utils", "PURPLE"),
    "RED": ("cnsplots._utils", "RED"),
    "VIOLET": ("cnsplots._utils", "VIOLET"),
    "YELLOW": ("cnsplots._utils", "YELLOW"),
    "methods": ("cnsplots._methods", None),
    "CoxModel": ("cnsplots._methods", "CoxModel"),
    "LogisticModel": ("cnsplots._methods", "LogisticModel"),
    "prerank": ("cnsplots._methods", "prerank"),
    "setup_ax": ("cnsplots._setup", "setup_ax"),
    "setup_ggplot": ("cnsplots._setup", "setup_ggplot"),
    "setup_matplotlib": ("cnsplots._setup", "setup_matplotlib"),
    "setup_scanpy": ("cnsplots._setup", "setup_scanpy"),
    "add_panel_label": ("cnsplots._utils", "add_panel_label"),
    "apply_unicode_font": ("cnsplots._utils", "apply_unicode_font"),
    "figure": ("cnsplots._utils", "figure"),
    "multipanel": ("cnsplots._multipanels", "multipanel"),
    "save": ("cnsplots._utils", "savefig"),
    "savefig": ("cnsplots._utils", "savefig"),
    "palettes": ("cnsplots._utils", "palettes"),
    "take_legend_out": ("cnsplots._utils", "take_legend_out"),
    "get_hexcolors_from_apalette": (
        "cnsplots._utils",
        "get_hexcolors_from_apalette",
    ),
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

__all__ = tuple(_LAZY_IMPORTS)


def __getattr__(name: str):
    """Load a public attribute on first access."""
    try:
        module_name, attribute_name = _LAZY_IMPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None

    module = import_module(module_name)
    value = module if attribute_name is None else getattr(module, attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return eager and lazy module attributes."""
    return sorted(set(globals()) | set(__all__))
