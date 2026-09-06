from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest
import seaborn as sns

import cnsplots as cns


@pytest.mark.parametrize("plot_name", ["boxplot", "violinplot", "stripplot"])
@pytest.mark.parametrize("horizontal", [False, True])
@pytest.mark.parametrize("numeric", [False, True])
def test_counts_use_category_axis_and_complete_values(
    plot_name: str, horizontal: bool, numeric: bool
) -> None:
    levels = [0, 1] if numeric else ["A", "B"]
    data = pd.DataFrame(
        {
            "group": np.repeat(levels, 4),
            "value": [1.0, 1.2, 1.4, np.nan, 2.0, 2.2, 2.4, 2.6],
        }
    )
    kwargs: dict[str, Any] = {"orient": "h"} if horizontal and numeric else {}
    ax = getattr(cns, plot_name)(
        data,
        x="value" if horizontal else "group",
        y="group" if horizontal else "value",
        add_count=True,
        **kwargs,
    )

    category_ticks = ax.get_yticklabels() if horizontal else ax.get_xticklabels()
    value_ticks = ax.get_xticklabels() if horizontal else ax.get_yticklabels()
    assert [tick.get_text() for tick in category_ticks] == [
        f"{levels[0]}\n(n=3)",
        f"{levels[1]}\n(n=4)",
    ]
    assert all("(n=" not in tick.get_text() for tick in value_ticks)


@pytest.mark.parametrize("plot_name", ["boxplot", "violinplot", "stripplot"])
@pytest.mark.parametrize("horizontal", [False, True])
@pytest.mark.parametrize("subset_hue", [False, True])
def test_counts_pool_displayed_hues_and_share_rendered_rows(
    plot_name: str,
    horizontal: bool,
    subset_hue: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = pd.DataFrame(
        {
            "group": ["A"] * 6 + ["B"] * 6 + ["C", None, "empty"],
            "value": [
                1,
                1.2,
                1.4,
                np.nan,
                1.8,
                9,
                2,
                2.2,
                2.4,
                2.6,
                2.8,
                9,
                3,
                4,
                np.nan,
            ],
            "hue": ["H1", "H1", "H2", "H1", None, "H3"]
            + ["H1", "H2", "H2", "H1", None, "H3", "H1", "H1", "H1"],
            "unrelated": np.nan,
        }
    )
    original = data.copy(deep=True)
    rendered = []

    def capture(name: str) -> None:
        plot = getattr(sns, name)

        def draw(*args: Any, **kwargs: Any) -> Any:
            rendered.append(kwargs.copy())
            return plot(*args, **kwargs)

        monkeypatch.setattr(sns, name, draw)

    for name in {plot_name, "boxplot"}:
        capture(name)
    ax = getattr(cns, plot_name)(
        data,
        x="value" if horizontal else "group",
        y="group" if horizontal else "value",
        hue="hue",
        order=["B", "A", "empty"],
        hue_order=["H2", "H1"] if subset_hue else None,
        add_count=True,
    )

    ticks = ax.get_yticklabels() if horizontal else ax.get_xticklabels()
    assert [tick.get_text() for tick in ticks] == [
        f"B\n(n={4 if subset_hue else 5})",
        f"A\n(n={3 if subset_hue else 4})",
        "empty\n(n=0)",
    ]
    indices = [0, 1, 2, 6, 7, 8, 9] if subset_hue else [0, 1, 2, 5, 6, 7, 8, 9, 11]
    for call in rendered:
        pd.testing.assert_frame_equal(call["data"], data.loc[indices])
        assert call["orient"] == ("h" if horizontal else "v")
        assert call["order"] == ["B", "A", "empty"]
    pd.testing.assert_frame_equal(data, original)
    if plot_name == "stripplot":
        values = np.concatenate(
            [
                collection.get_offsets()[:, 0 if horizontal else 1]
                for collection in ax.collections
            ]
        )
        np.testing.assert_allclose(np.sort(values), np.sort(data.loc[indices, "value"]))


@pytest.mark.parametrize("plot_name", ["boxplot", "violinplot", "stripplot"])
@pytest.mark.parametrize("horizontal", [False, True])
def test_repeated_plot_calls_replace_counts(plot_name: str, horizontal: bool) -> None:
    data = pd.DataFrame({"group": ["A"] * 4, "value": [1, 2, 3, 4]})
    kwargs = {
        "x": "value" if horizontal else "group",
        "y": "group" if horizontal else "value",
    }
    plot = getattr(cns, plot_name)
    ax = plot(data, add_count=True, **kwargs)
    plot(data.iloc[:3], ax=ax, add_count=True, **kwargs)
    ticks = ax.get_yticklabels() if horizontal else ax.get_xticklabels()
    assert [tick.get_text() for tick in ticks] == ["A\n(n=3)"]


@pytest.mark.parametrize("axis", ["x", "y"])
def test_repeated_count_helper_updates_suffix(axis: str) -> None:
    import matplotlib.pyplot as plt

    _, ax = plt.subplots()
    set_ticks = ax.set_xticks if axis == "x" else ax.set_yticks
    set_ticks([0, 1, 2], ["A", "empty", "label\n(n=5)"])
    data = pd.DataFrame({"group": ["A", "A", "label\n(n=5)"]})
    cns.utils._add_count_helper(data, "group", ax, axis=axis)
    cns.utils._add_count_helper(data.iloc[1:], "group", ax, axis=axis)
    ticks = ax.get_xticklabels() if axis == "x" else ax.get_yticklabels()
    assert [tick.get_text() for tick in ticks] == [
        "A\n(n=1)",
        "empty\n(n=0)",
        "label\n(n=5)\n(n=1)",
    ]


@pytest.mark.parametrize("horizontal", [False, True])
def test_stackplot_counts_keep_raw_totals(horizontal: bool) -> None:
    data = pd.DataFrame(
        {"group": ["A", "A", "A", "B", "B"], "stack": ["yes", "no", None, "yes", "no"]}
    )
    ax = cns.stackplot(
        data,
        x=None if horizontal else "group",
        y="group" if horizontal else None,
        stack="stack",
        add_count=True,
    )
    ticks = ax.get_yticklabels() if horizontal else ax.get_xticklabels()
    assert [tick.get_text() for tick in ticks] == ["A\n(n=3)", "B\n(n=2)"]


@pytest.mark.parametrize("plot_name", ["boxplot", "violinplot", "stripplot"])
def test_empty_category_keeps_default_position(plot_name: str) -> None:
    data = pd.DataFrame({"group": ["empty", "A", "A"], "value": [np.nan, 1, 2]})
    ax = getattr(cns, plot_name)(data, x="group", y="value", add_count=True)
    assert [tick.get_text() for tick in ax.get_xticklabels()] == [
        "empty\n(n=0)",
        "A\n(n=2)",
    ]


@pytest.mark.parametrize("plot_name", ["boxplot", "violinplot", "stripplot"])
def test_order_selecting_no_complete_rows_raises(plot_name: str) -> None:
    data = pd.DataFrame({"group": ["empty", "A", "A"], "value": [np.nan, 1, 2]})
    with pytest.raises(ValueError, match="No complete observations remain"):
        getattr(cns, plot_name)(
            data, x="group", y="value", order=["empty"], add_count=True
        )
