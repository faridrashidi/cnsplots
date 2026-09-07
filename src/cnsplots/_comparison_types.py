"""Shared input types for categorical statistical comparisons."""

from collections.abc import Sequence
from typing import Literal, TypeAlias

CategoryLabel: TypeAlias = str | int | float
CategoryPair: TypeAlias = tuple[CategoryLabel, CategoryLabel]
HuePair: TypeAlias = tuple[
    tuple[CategoryLabel, CategoryLabel], tuple[CategoryLabel, CategoryLabel]
]
CategoryComparisons: TypeAlias = Literal["all"] | Sequence[CategoryPair]
HueComparisons: TypeAlias = Literal["all", "hue"] | Sequence[CategoryPair | HuePair]
