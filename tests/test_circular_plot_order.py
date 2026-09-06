from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.colors import to_rgba
from matplotlib.patches import Wedge

import cnsplots as cns


@pytest.mark.parametrize("plot_name", ["pieplot", "donutplot"])
@pytest.mark.parametrize("categorical", [False, True])
@pytest.mark.parametrize(
    ("order", "labels", "counts"),
    [
        (None, ["C", "A", "B"], [3, 2, 1]),
        (["B", "C", "A"], ["B", "C", "A"], [1, 3, 2]),
        (["A"], ["A"], [2]),
        (["B", "A"], ["B", "A"], [1, 2]),
        (["A", "B", "C", "D"], ["A", "B", "C", "D"], [2, 1, 3, 0]),
        (["D", "B", "A"], ["D", "B", "A"], [0, 1, 2]),
        (["B", "D", "A"], ["B", "D", "A"], [1, 0, 2]),
    ],
)
def test_circular_plot_slice_alignment(
    plot_name: str,
    categorical: bool,
    order: list[str] | None,
    labels: list[str],
    counts: list[int],
) -> None:
    data = pd.DataFrame({"group": ["A", "A", "B", "C", "C", "C", None]})
    if categorical:
        data["group"] = pd.Categorical(data["group"], categories=["A", "B", "C"])
    original = data.copy(deep=True)
    colors = ["#111111", "#eeeeee", "#222222", "#dddddd"]
    _, ax = plt.subplots()
    with plt.rc_context({"axes.prop_cycle": plt.cycler(color=colors)}):
        result = getattr(cns, plot_name)(data, x="group", order=order, ax=ax)

    assert result is ax
    wedges = [patch for patch in ax.patches if isinstance(patch, Wedge)]
    proportions = np.asarray(counts) / sum(counts)
    assert len(wedges) == len(counts)
    np.testing.assert_allclose(
        [wedge.theta2 - wedge.theta1 for wedge in wedges],
        proportions * 360,
        atol=1e-5,
    )
    np.testing.assert_allclose(
        [wedge.get_facecolor() for wedge in wedges],
        [to_rgba(color) for color in colors[: len(counts)]],
    )
    legend = ax.get_legend()
    assert legend is not None
    assert [text.get_text() for text in legend.get_texts()] == labels
    np.testing.assert_allclose(
        [handle.get_facecolor() for handle in legend.legend_handles],
        [wedge.get_facecolor() for wedge in wedges],
    )
    if plot_name == "pieplot":
        percentages = [text for text in ax.texts if text.get_text().endswith("%")]
        assert [text.get_text() for text in percentages] == [
            f"{value * 100:.0f}%" for value in proportions
        ]
        assert [text.get_color() for text in percentages] == [
            "white",
            "black",
            "white",
            "black",
        ][: len(counts)]
    else:
        assert [wedge.width for wedge in wedges] == pytest.approx([0.4] * len(counts))
        assert [text.get_text() for text in ax.texts] == ["group"]
    pd.testing.assert_frame_equal(data, original)


@pytest.mark.parametrize("plot_name", ["pieplot", "donutplot"])
def test_circular_plot_retains_unused_categorical_levels(plot_name: str) -> None:
    data = pd.DataFrame(
        {"group": pd.Categorical(["A", "A", "B"], categories=["A", "B", "C"])}
    )
    ax = getattr(cns, plot_name)(data, x="group")
    legend = ax.get_legend()
    assert legend is not None
    assert [text.get_text() for text in legend.get_texts()] == ["A", "B", "C"]
    wedges = [patch for patch in ax.patches if isinstance(patch, Wedge)]
    np.testing.assert_allclose(
        [wedge.theta2 - wedge.theta1 for wedge in wedges], [240, 120, 0]
    )


@pytest.mark.parametrize("plot_name", ["pieplot", "donutplot"])
@pytest.mark.parametrize("order", [["A", "A"], ["D", "D", "A"]])
def test_circular_plot_rejects_duplicate_order(
    plot_name: str, order: list[str]
) -> None:
    data = pd.DataFrame({"group": ["A", "A", "B"]})
    _, ax = plt.subplots()
    with pytest.raises(ValueError, match=rf"\[{plot_name}\].*order.*duplicate"):
        getattr(cns, plot_name)(data, x="group", order=order, ax=ax)
    assert not ax.patches
    assert ax.get_legend() is None


@pytest.mark.parametrize("plot_name", ["pieplot", "donutplot"])
@pytest.mark.parametrize(
    ("values", "order"),
    [
        (["A", "A", "B"], []),
        (["A", "A", "B"], ["D"]),
        (["A", "A", "B"], ["D", "E"]),
        ([None, None], None),
        ([None, None], ["A"]),
        (pd.Categorical([None, None], categories=["A", "B"]), None),
        (pd.Categorical(["A", "A"], categories=["A", "B"]), ["B"]),
    ],
)
def test_circular_plot_requires_remaining_counts(
    plot_name: str, values: list[str | None] | pd.Categorical, order: list[str] | None
) -> None:
    data = pd.DataFrame({"group": values})
    _, ax = plt.subplots()
    with pytest.raises(
        ValueError, match=rf"\[{plot_name}\].*No non-missing observations.*group"
    ):
        getattr(cns, plot_name)(data, x="group", order=order, ax=ax)
    assert not ax.patches
    assert ax.get_legend() is None
