"""Packaged datasets used by the documentation gallery."""

from cnsplots.datasets import gallery
from cnsplots.datasets._loader import get_dataset_names, load_dataset
from cnsplots.datasets.gallery import (
    ShowcaseData,
    ShowcaseDataWithImages,
    get_showcase_data,
)

__all__ = (
    "ShowcaseData",
    "ShowcaseDataWithImages",
    "gallery",
    "get_dataset_names",
    "get_showcase_data",
    "load_dataset",
)
