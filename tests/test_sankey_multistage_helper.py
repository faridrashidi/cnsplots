from __future__ import annotations

from typing import Any, cast

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
import numpy as np
import pandas as pd
import pytest

from cnsplots.helpers import _sankey


def _capture_fill_between(
    monkeypatch: pytest.MonkeyPatch, ax: Axes
) -> list[tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]]:
    calls: list[tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]] = []
    original_fill_between = ax.fill_between

    def capture(x: Any, y1: Any, y2: Any, *args: Any, **kwargs: Any) -> Any:
        calls.append(
            (
                np.asarray(x),
                np.asarray(y1),
                np.asarray(y2),
                kwargs,
            )
        )
        return original_fill_between(x, y1, y2, *args, **kwargs)

    monkeypatch.setattr(ax, "fill_between", capture)
    return calls


def test_multistage_sankeyplot_stacks_sparse_links_and_nodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = pd.DataFrame(
        {
            "first": ["B", "A", "B", "A", "B"],
            "second": ["Y", "Y", "X", "Y", "X"],
            "third": ["Q", "P", "Q", "P", "Q"],
        }
    )
    colors = {
        "A": "blue",
        "B": "red",
        "X": "purple",
        "Y": "green",
        "P": "black",
        "Q": "orange",
    }
    fig, ax = plt.subplots()
    fill_calls = _capture_fill_between(monkeypatch, ax)

    result = _sankey.multistage_sankeyplot(
        data,
        ["first", "second", "third"],
        colorDict=colors,
        fontsize=11,
        label_rotation=30,
        ax=ax,
    )

    assert result is ax
    assert ax.axison is False
    assert len(fill_calls) == 12
    assert len(ax.collections) == 12

    ribbon_calls = fill_calls[:6]
    node_calls = fill_calls[6:]
    assert all(len(call[0]) == 62 for call in ribbon_calls)
    assert all(len(call[0]) == 2 for call in node_calls)
    assert [call[3]["alpha"] for call in ribbon_calls] == [0.65] * 6
    assert [call[3]["alpha"] for call in node_calls] == [1] * 6

    assert [to_rgba(call[3]["color"]) for call in ribbon_calls] == [
        to_rgba(colors[label]) for label in ["B", "B", "A", "Y", "Y", "X"]
    ]
    ribbon_edges = [
        (call[1][0], call[1][-1], call[2][0], call[2][-1]) for call in ribbon_calls
    ]
    np.testing.assert_allclose(
        ribbon_edges,
        [
            (0.0, 0.0, 1.0, 1.0),
            (1.0, 3.1, 3.0, 5.1),
            (3.1, 1.0, 5.1, 3.0),
            (0.0, 0.0, 1.0, 1.0),
            (1.0, 3.1, 3.0, 5.1),
            (3.1, 1.0, 5.1, 3.0),
        ],
    )
    np.testing.assert_allclose(
        [(call[0][0], call[0][-1]) for call in ribbon_calls],
        [(0.0, 1.275)] * 3 + [(1.275, 2.55)] * 3,
    )

    assert [text.get_text() for text in ax.texts] == ["B", "A", "Y", "X", "Q", "P"]
    assert [text.get_rotation() for text in ax.texts] == [30] * 6
    assert [text.get_fontsize() for text in ax.texts] == [11] * 6
    assert [text.get_horizontalalignment() for text in ax.texts] == [
        "right",
        "right",
        "center",
        "center",
        "left",
        "left",
    ]
    assert [cast(Any, text).xy[0] for text in ax.texts] == pytest.approx(
        [-0.06375, -0.06375, 1.275, 1.275, 2.61375, 2.61375]
    )
    np.testing.assert_allclose(
        [(call[1][0], call[2][0]) for call in node_calls],
        [(0.0, 3.0), (3.1, 5.1)] * 3,
    )


def test_multistage_sankeyplot_uses_current_axes_and_observed_categories() -> None:
    data = pd.DataFrame(
        {
            "one": pd.Categorical(["same", "same"], categories=["same", "unused1"]),
            "two": pd.Categorical(["same", "same"], categories=["same", "unused2"]),
            "three": pd.Categorical(["C", "C"], categories=["C", "unused3"]),
            "four": pd.Categorical(["D", "D"], categories=["D", "unused4"]),
        }
    )
    fig, ax = plt.subplots()
    plt.sca(ax)

    result = _sankey.multistage_sankeyplot(
        data,
        ["one", "two", "three", "four"],
        label_rotation=45,
        aspect=2,
    )

    assert result is ax
    assert len(ax.collections) == 7
    assert [text.get_text() for text in ax.texts] == ["same", "same", "C", "D"]
    assert all(text.get_rotation() == 45 for text in ax.texts)
    first_node_color = ax.collections[3].get_facecolor()[0]
    second_node_color = ax.collections[4].get_facecolor()[0]
    assert first_node_color == pytest.approx(second_node_color)


def test_multistage_sankeyplot_requires_three_columns() -> None:
    with pytest.raises(ValueError, match="at least three columns"):
        _sankey.multistage_sankeyplot(
            pd.DataFrame({"one": ["A"], "two": ["B"]}),
            ["one", "two"],
        )
