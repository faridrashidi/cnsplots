from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd
import pytest

import cnsplots as cns


@pytest.fixture
def annotations(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    instances = []
    original = cns.utils.Annotator

    def capture(*args: Any, **kwargs: Any) -> Any:
        annotator = original(*args, **kwargs)
        instances.append(annotator)
        return annotator

    monkeypatch.setattr(cns.utils, "Annotator", capture)
    return instances


@pytest.mark.parametrize("plot_name", ["boxplot", "violinplot", "barplot"])
@pytest.mark.parametrize("numeric", [False, True])
@pytest.mark.parametrize("orient", [None, "v", "h", "x", "y"])
@pytest.mark.parametrize("selector", ["explicit", "all", "hue"])
def test_annotations_match_category_axis(
    plot_name: str,
    numeric: bool,
    orient: str | None,
    selector: str,
    annotations: list[Any],
) -> None:
    levels = [2, 0, 1] if numeric else ["C", "A", "B"]
    data = pd.DataFrame(
        {
            "group": np.repeat(levels, 6),
            "value": np.arange(18, dtype=float) + 0.5,
            "hue": [1, 1, 1, 0, 0, 0] * 3,
        }
    )
    horizontal = orient in {"h", "y"}
    order = levels[::-1]
    pairs = [(order[0], order[1])] if selector == "explicit" else selector
    kwargs: dict[str, Any] = {"order": order, "orient": orient}
    if selector == "hue":
        kwargs.update(hue="hue", hue_order=[0, 1])
    if plot_name == "barplot":
        kwargs.update(add_tip=True, errorbar=None)

    ax = getattr(cns, plot_name)(
        data,
        x="value" if horizontal else "group",
        y="group" if horizontal else "value",
        pairs=pairs,
        **kwargs,
    )

    annotator = annotations[0]
    assert annotator.orient == ("h" if horizontal else "v")
    ticks = ax.get_yticklabels() if horizontal else ax.get_xticklabels()
    assert [tick.get_text() for tick in ticks] == [str(level) for level in order]
    expected_groups = (
        [(level, hue) for level in order for hue in [0, 1]]
        if selector == "hue"
        else [(level,) for level in order]
    )
    assert [item["group"] for item in annotator._plotter.structs] == expected_groups
    for item in annotator._plotter.structs:
        group = item["group"]
        selected = data[data["group"] == group[0]]
        if selector == "hue":
            selected = selected[selected["hue"] == group[1]]
        np.testing.assert_array_equal(item["group_data"], selected["value"])
    expected_pairs = (
        [((level, 0), (level, 1)) for level in order]
        if selector == "hue"
        else list(combinations(order, 2))
        if selector == "all"
        else pairs
    )
    assert annotator.pairs == expected_pairs
    assert len(ax.texts) >= len(expected_pairs)


@pytest.mark.parametrize(
    ("plot_name", "categorical"),
    [
        (name, categorical)
        for name in ["boxplot", "violinplot", "barplot"]
        for categorical in [False, True]
    ]
    + [("lollipopplot", False)],
)
def test_default_annotation_order_matches_drawn_order(
    plot_name: str, categorical: bool, annotations: list[Any]
) -> None:
    data = pd.DataFrame(
        {"group": [2, 2, 0, 0, 1, 1], "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]}
    )
    if categorical:
        data["group"] = pd.Categorical(
            data["group"], categories=[1, 2, 0], ordered=True
        )
    expected = (
        [2, 0, 1]
        if plot_name == "lollipopplot"
        else [1, 2, 0]
        if categorical
        else [0, 1, 2]
    )

    ax = getattr(cns, plot_name)(data, x="group", y="value", pairs="all")

    assert [tick.get_text() for tick in ax.get_xticklabels()] == list(
        map(str, expected)
    )
    assert annotations[0].pairs == list(combinations(expected, 2))
    assert [str(item["group"][0]) for item in annotations[0]._plotter.structs] == list(
        map(str, expected)
    )
    for item, level in zip(annotations[0]._plotter.structs, expected):
        np.testing.assert_array_equal(
            item["group_data"], data.loc[data["group"] == level, "value"]
        )
    if plot_name == "lollipopplot":
        offsets = ax.collections[1].get_offsets()
        np.testing.assert_allclose(offsets[:, 0], range(3))
        means = data.groupby("group", observed=True)["value"].mean().reindex(expected)
        np.testing.assert_allclose(offsets[:, 1], means)


@pytest.mark.parametrize("horizontal", [False, True])
@pytest.mark.parametrize("numeric", [False, True])
@pytest.mark.parametrize("selector", ["explicit", "all"])
@pytest.mark.parametrize("ordered", [False, True])
def test_stackplot_annotation_orientation(
    horizontal: bool,
    numeric: bool,
    selector: str,
    ordered: bool,
    annotations: list[Any],
) -> None:
    levels = [0, 1] if numeric else ["A", "B"]
    data = pd.DataFrame(
        {"group": np.repeat(levels, [4, 6]), "outcome": ["yes", "no"] * 5}
    )
    expected_order = levels[::-1] if ordered else levels
    pairs = [tuple(expected_order)] if selector == "explicit" else "all"

    kwargs: dict[str, Any] = {
        "y" if horizontal else "x": "group",
        "order": expected_order if ordered else None,
        "pairs": pairs,
    }
    ax = cns.stackplot(data, stack="outcome", **kwargs)

    assert annotations[0].orient == ("h" if horizontal else "v")
    assert annotations[0].pairs == [tuple(expected_order)]
    assert [item["group"] for item in annotations[0]._plotter.structs] == [
        (level,) for level in expected_order
    ]
    ticks = ax.get_yticklabels() if horizontal else ax.get_xticklabels()
    assert [tick.get_text() for tick in ticks] == list(map(str, expected_order))


@pytest.mark.parametrize(
    "plot_name", ["boxplot", "violinplot", "barplot", "lollipopplot"]
)
@pytest.mark.parametrize("horizontal", [False, True])
def test_inferred_orientation_with_hue(
    plot_name: str, horizontal: bool, annotations: list[Any]
) -> None:
    levels = ["B", "A"] if horizontal else [1, 0]
    data = pd.DataFrame(
        {
            "group": np.repeat(levels, 6),
            "value": np.arange(12, dtype=float),
            "hue": [1, 1, 1, 0, 0, 0] * 2,
        }
    )
    ax = getattr(cns, plot_name)(
        data,
        x="value" if horizontal else "group",
        y="group" if horizontal else "value",
        hue="hue",
        pairs="hue",
    )
    expected_order = (
        levels if horizontal or plot_name == "lollipopplot" else levels[::-1]
    )
    hue_order = [1, 0] if plot_name == "lollipopplot" else [0, 1]
    assert annotations[0].orient == ("h" if horizontal else "v")
    assert annotations[0].pairs == [
        ((level, hue_order[0]), (level, hue_order[1])) for level in expected_order
    ]
    ticks = ax.get_yticklabels() if horizontal else ax.get_xticklabels()
    assert [tick.get_text() for tick in ticks] == list(map(str, expected_order))
    for item in annotations[0]._plotter.structs:
        level, hue = item["group"]
        selected = data.loc[(data["group"] == level) & (data["hue"] == hue), "value"]
        np.testing.assert_array_equal(item["group_data"], selected)
