"""Packaged datasets used by the documentation gallery."""

from cnsplots.datasets import gallery
from cnsplots.datasets._loader import load_dataset
from cnsplots.datasets.gallery import get_showcase_data

__all__ = ("gallery", "get_showcase_data", "load_dataset")
