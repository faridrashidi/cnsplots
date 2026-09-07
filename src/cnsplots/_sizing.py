"""Shared conversion of physical sizes to the legacy point-based layout."""

from __future__ import annotations

import math
from numbers import Real
from typing import Literal

_SizeUnit = Literal["pt", "in", "mm"]
_POINTS_PER_UNIT = {"pt": 1, "in": 72, "mm": 72 / 25.4}


def _validate_positive_finite_dimension(
    name: str,
    value: int | float,
) -> int | float:
    """Validate a dimension used to construct a matplotlib figure or axes."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a number")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return value


def _dimension_to_points(
    name: str,
    value: int | float | None,
    unit: _SizeUnit,
    *,
    default: int | float,
) -> int | float:
    """Convert an explicit size, keeping omitted settings-based sizes in points."""
    if not isinstance(unit, str) or unit not in _POINTS_PER_UNIT:
        raise ValueError("unit must be one of: 'pt', 'in', or 'mm'")
    if value is None:
        return _validate_positive_finite_dimension(name, default)
    value = _validate_positive_finite_dimension(name, value)
    return _validate_positive_finite_dimension(name, value * _POINTS_PER_UNIT[unit])
