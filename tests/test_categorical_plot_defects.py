from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd
import pytest

import cnsplots as cns


def _dumbbell_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "pathway": ["A", "A", "B", "B", "C", "C"],
            "score": [1.0, 3.0, 2.0, 5.0, 4.0, 6.0],
            "condition": ["before", "after"] * 3,
        }
    )


def test_dumbbellplot_requires_dataframe() -> None:
    with pytest.raises(TypeError, match="must be a pandas DataFrame"):
        cns.dumbbellplot(
            cast(Any, []),
            x="score",
            y="pathway",
            hue="condition",
        )


def test_dumbbellplot_requires_all_columns() -> None:
    with pytest.raises(ValueError, match="not found in data"):
        cns.dumbbellplot(
            _dumbbell_data(),
            x="missing",
            y="pathway",
            hue="condition",
        )


def test_dumbbellplot_requires_nonempty_data() -> None:
    with pytest.raises(ValueError, match="Data is empty"):
        cns.dumbbellplot(
            _dumbbell_data().iloc[0:0],
            x="score",
            y="pathway",
            hue="condition",
        )


def test_dumbbellplot_requires_numeric_x_axis() -> None:
    data = _dumbbell_data().assign(score=_dumbbell_data()["condition"])
    with pytest.raises(ValueError, match="must be numeric"):
        cns.dumbbellplot(
            data,
            x="score",
            y="pathway",
            hue="condition",
        )


def test_dumbbellplot_rejects_null_values() -> None:
    data = _dumbbell_data().assign(score=[1.0, None, 2.0, 3.0, 4.0, 5.0])
    with pytest.raises(ValueError, match="Null values found"):
        cns.dumbbellplot(
            data,
            x="score",
            y="pathway",
            hue="condition",
        )


@pytest.mark.parametrize(
    "conditions",
    [
        ["before"],
        ["before", "after", "follow-up"],
    ],
)
def test_dumbbellplot_requires_exactly_two_hue_levels(
    conditions: list[str],
) -> None:
    data = pd.DataFrame(
        {
            "pathway": [f"P{i}" for i in range(len(conditions))],
            "score": np.arange(len(conditions), dtype=float),
            "condition": conditions,
        }
    )

    with pytest.raises(ValueError, match="exactly 2 unique values"):
        cns.dumbbellplot(
            data,
            x="score",
            y="pathway",
            hue="condition",
        )


def test_dumbbellplot_rejects_incomplete_hue_order() -> None:
    with pytest.raises(ValueError, match="hue_order.*both observed"):
        cns.dumbbellplot(
            _dumbbell_data(),
            x="score",
            y="pathway",
            hue="condition",
            hue_order=["before", "missing"],
        )


def test_dumbbellplot_rejects_empty_order() -> None:
    with pytest.raises(ValueError, match="at least one category"):
        cns.dumbbellplot(
            _dumbbell_data(),
            x="score",
            y="pathway",
            hue="condition",
            order=[],
        )


def test_dumbbellplot_rejects_duplicate_order() -> None:
    with pytest.raises(ValueError, match="duplicate categories"):
        cns.dumbbellplot(
            _dumbbell_data(),
            x="score",
            y="pathway",
            hue="condition",
            order=["A", "A", "B"],
        )


def test_dumbbellplot_rejects_order_categories_not_in_data() -> None:
    with pytest.raises(ValueError, match="not present in data"):
        cns.dumbbellplot(
            _dumbbell_data(),
            x="score",
            y="pathway",
            hue="condition",
            order=["A", "D"],
        )


@pytest.mark.parametrize(
    ("invalid_kind", "expected"),
    [
        ("duplicate", "exactly one 'score' value for each"),
        ("missing", "missing an 'score' value"),
    ],
)
def test_dumbbellplot_requires_one_value_per_category_and_condition(
    invalid_kind: str,
    expected: str,
) -> None:
    data = _dumbbell_data()
    if invalid_kind == "duplicate":
        data = pd.concat([data, data.iloc[[0]]], ignore_index=True)
    else:
        data = data.drop(index=3)

    with pytest.raises(ValueError, match=expected):
        cns.dumbbellplot(
            data,
            x="score",
            y="pathway",
            hue="condition",
        )
