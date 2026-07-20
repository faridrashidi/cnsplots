from __future__ import annotations

from collections.abc import Iterable
from typing import cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection

import cnsplots as cns


def test_regplot_uses_only_finite_plotted_pairs_for_pearson() -> None:
    data = pd.DataFrame(
        {
            "x": [0.0, 1.0, 2.0, np.nan, np.inf],
            "y": [0.0, 2.0, 1.0, 100.0, -100.0],
        }
    )

    cns.figure(120, 120)
    ax = cns.regplot(data, x="x", y="y")

    assert ax.texts[0].get_text().startswith(r"$r$=0.50,")
    assert r"\rho" not in ax.texts[0].get_text()
    scatter = next(
        collection
        for collection in ax.collections
        if isinstance(collection, PathCollection)
    )
    np.testing.assert_allclose(
        np.asarray(scatter.get_offsets(), dtype=float),
        data.loc[:2, ["x", "y"]].to_numpy(),
    )


@pytest.mark.parametrize("hue", [None, "group"])
def test_regplot_requires_two_finite_pairs_before_drawing(hue: str | None) -> None:
    data = pd.DataFrame(
        {
            "x": [0.0, np.nan, 1.0],
            "y": [0.0, 1.0, np.inf],
            "group": ["A", "A", "A"],
        }
    )

    cns.figure(120, 120)
    with pytest.raises(ValueError, match="at least 2 finite paired observations"):
        cns.regplot(data, x="x", y="y", hue=hue)
    assert not plt.gca().collections
    assert not plt.gca().lines


def test_slopeplot_aligns_values_by_pair_key() -> None:
    data = pd.DataFrame(
        {
            "site": ["A"] * 4,
            "subject": ["one", "two", "two", "one"],
            "condition": ["before", "before", "after", "after"],
            "value": [1.0, 10.0, 20.0, 2.0],
        }
    )

    cns.figure(120, 120)
    ax = cns.slopeplot(
        data,
        x="site",
        y="value",
        hue="condition",
        pair="subject",
    )

    paired_values = sorted(
        tuple(cast(Iterable[float], line.get_ydata())) for line in ax.lines
    )
    assert paired_values == [(1.0, 2.0), (10.0, 20.0)]


def test_regplot_and_slopeplot_respect_hue_order() -> None:
    regression_data = pd.DataFrame(
        {
            "x": [0.0, 1.0, 0.0, 1.0],
            "y": [0.0, 1.0, 1.0, 2.0],
            "condition": ["before", "before", "after", "after"],
        }
    )
    hue_order = ["after", "before"]

    cns.figure(120, 120)
    regression_ax = cns.regplot(
        regression_data,
        x="x",
        y="y",
        hue="condition",
        hue_order=hue_order,
    )
    regression_legend = regression_ax.get_legend()
    assert regression_legend is not None
    assert [text.get_text() for text in regression_legend.get_texts()] == hue_order

    slope_data = regression_data.assign(site="A", subject=["one", "two"] * 2)
    cns.figure(120, 120)
    slope_ax = cns.slopeplot(
        slope_data,
        x="site",
        y="y",
        hue="condition",
        pair="subject",
        hue_order=hue_order,
    )
    slope_legend = slope_ax.get_legend()
    assert slope_legend is not None
    assert [text.get_text() for text in slope_legend.get_texts()] == hue_order


def test_slopeplot_rejects_incomplete_hue_order() -> None:
    data = pd.DataFrame(
        {
            "site": ["A"] * 4,
            "subject": ["one", "two"] * 2,
            "condition": ["before", "before", "after", "after"],
            "value": [1.0, 10.0, 2.0, 20.0],
        }
    )

    with pytest.raises(ValueError, match="hue_order.*both observed"):
        cns.slopeplot(
            data,
            x="site",
            y="value",
            hue="condition",
            pair="subject",
            hue_order=["before", "missing"],
        )


@pytest.mark.parametrize(
    "conditions",
    [
        ["before", "before"],
        ["before", "after", "follow-up"],
    ],
)
def test_slopeplot_requires_exactly_two_hue_levels(conditions: list[str]) -> None:
    data = pd.DataFrame(
        {
            "site": ["A"] * len(conditions),
            "subject": list(range(len(conditions))),
            "condition": conditions,
            "value": np.arange(len(conditions), dtype=float),
        }
    )

    with pytest.raises(ValueError, match="exactly 2 unique values"):
        cns.slopeplot(
            data,
            x="site",
            y="value",
            hue="condition",
            pair="subject",
        )


@pytest.mark.parametrize("invalid_kind", ["duplicate", "missing"])
def test_slopeplot_requires_one_value_per_pair_and_condition(
    invalid_kind: str,
) -> None:
    data = pd.DataFrame(
        {
            "site": ["A"] * 4,
            "subject": ["one", "one", "two", "two"],
            "condition": ["before", "after"] * 2,
            "value": [1.0, 2.0, 10.0, 20.0],
        }
    )
    if invalid_kind == "duplicate":
        data = pd.concat([data, data.iloc[[0]]], ignore_index=True)
    else:
        data = data.drop(index=0)

    with pytest.raises(ValueError, match="exactly one .* value for each"):
        cns.slopeplot(
            data,
            x="site",
            y="value",
            hue="condition",
            pair="subject",
        )


def test_slopeplot_requires_each_pair_to_belong_to_one_x_group() -> None:
    data = pd.DataFrame(
        {
            "site": ["A", "A", "B", "B"],
            "subject": ["one"] * 4,
            "condition": ["before", "after"] * 2,
            "value": [1.0, 2.0, 3.0, 4.0],
        }
    )

    with pytest.raises(ValueError, match="belong to exactly one"):
        cns.slopeplot(
            data,
            x="site",
            y="value",
            hue="condition",
            pair="subject",
        )
