"""Stable category and example ordering for the Sphinx gallery."""

from pathlib import Path

GALLERY_CATEGORIES = [
    {
        "title": "Getting Started",
        "description": (
            "Start here for the core cnsplots workflow: overview figures, global "
            "settings, figure setup, color palettes, and publication-style "
            "multipanel layouts."
        ),
        "examples": [
            "showcase",
            "settings",
            "figure_setup",
            "palettes",
            "multipanel",
        ],
    },
    {
        "title": "Comparison & Categories",
        "description": (
            "Examples in this section focus on comparing groups and compositions "
            "with categorical plots, proportion charts, and flow-based visual "
            "summaries."
        ),
        "examples": [
            "boxplot",
            "stackplot",
            "barplot",
            "lollipopplot",
            "dumbbellplot",
            "stripplot",
            "violinplot",
            "dotplot",
            "pieplot",
            "donutplot",
            "sankeyplot",
        ],
    },
    {
        "title": "Distributions & Trends",
        "description": (
            "These examples highlight continuous data, distribution shapes, "
            "relationships, and trend-oriented visualizations for exploratory "
            "and publication figures."
        ),
        "examples": [
            "histplot",
            "kdeplot",
            "distplot",
            "ridgeplot",
            "qqplot",
            "scatterplot",
            "regplot",
            "lineplot",
            "slopeplot",
        ],
    },
    {
        "title": "Analysis & Evaluation",
        "description": (
            "This section collects analysis-driven examples including "
            "enrichment, survival, classification, overlap, and evaluation "
            "plots commonly used in scientific workflows."
        ),
        "examples": [
            "heatmapplot",
            "survivalplot",
            "forestplot",
            "gseaplot",
            "volcanoplot",
            "confusionplot",
            "rocplot",
            "vennplot",
            "upsetplot",
        ],
    },
    {
        "title": "Integrations",
        "description": (
            "These examples show how to combine cnsplots styling, sizing, and "
            "export helpers with native matplotlib, seaborn, and scanpy "
            "workflows."
        ),
        "examples": [
            "matplotlib_integration",
            "seaborn_integration",
            "scanpy_integration",
        ],
    },
]

_GALLERY_EXAMPLE_ORDER = [
    f"{example}.py"
    for category in GALLERY_CATEGORIES
    for example in category["examples"]
]


class GalleryExampleOrder:
    """Keep gallery examples in a stable, curated order."""

    def __init__(self, src_dir: str):
        del src_dir
        self.positions = {
            name: index for index, name in enumerate(_GALLERY_EXAMPLE_ORDER)
        }

    def __call__(self, filename: str) -> tuple[int, str]:
        name = Path(filename).name
        return (self.positions.get(name, len(self.positions)), name)

    def __repr__(self) -> str:
        return "<GalleryExampleOrder>"
