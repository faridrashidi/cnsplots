from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from cnsplots.helpers import _sankey


def _weighted_sankey_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "left": pd.Categorical(
                ["B", "A", "B", "C", "A", "B", "C"],
                categories=["A", "B", "C", "unused"],
            ),
            "right": pd.Categorical(
                ["Y", "X", "X", "Y", "Y", "Y", "Z"],
                categories=["X", "Y", "Z", "unused"],
            ),
            "leftWeight": [1.5, 2.0, 0.0, 4.25, -1.0, 0.5, 0.0],
            "rightWeight": [3.0, 1.0, 5.0, 2.0, 1.0, -1.0, 0.0],
        }
    )


def test_grouped_sankey_widths_preserve_weighted_results() -> None:
    data_frame = _weighted_sankey_data()
    left_labels = ["C", "A", "B"]
    right_labels = ["Y", "X", "Z"]

    actual_left, actual_right = _sankey.determine_widths(
        data_frame, left_labels, right_labels
    )
    assert actual_left == {
        "C": {"Y": 4.25, "X": 0, "Z": 0},
        "A": {"Y": -1.0, "X": 2.0, "Z": 0},
        "B": {"Y": 2.0, "X": 0.0, "Z": 0},
    }
    assert actual_right == {
        "C": {"Y": 2.0, "X": 0, "Z": 0.0},
        "A": {"Y": 1.0, "X": 1.0, "Z": 0},
        "B": {"Y": 2.0, "X": 5.0, "Z": 0},
    }

    left_widths, left_top = _sankey._get_positions_and_total_widths(
        data_frame, left_labels, "left"
    )
    right_widths, right_top = _sankey._get_positions_and_total_widths(
        data_frame, right_labels, "right"
    )
    assert left_widths["C"] == pytest.approx({"left": 4.25, "bottom": 0, "top": 4.25})
    assert left_widths["A"] == pytest.approx(
        {"left": 1.0, "bottom": 4.395, "top": 5.395}
    )
    assert left_widths["B"] == pytest.approx({"left": 2.0, "bottom": 5.54, "top": 7.54})
    assert left_top == pytest.approx(7.54)
    assert right_widths["Y"] == pytest.approx({"right": 5.0, "bottom": 0, "top": 5.0})
    assert right_widths["X"] == pytest.approx(
        {"right": 6.0, "bottom": 5.22, "top": 11.22}
    )
    assert right_widths["Z"] == pytest.approx(
        {"right": 0.0, "bottom": 11.44, "top": 11.44}
    )
    assert right_top == pytest.approx(11.44)


def test_sankey_hot_path_avoids_boolean_dataframe_scans(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_frame = _weighted_sankey_data()
    left_labels = ["C", "A", "B"]
    right_labels = ["Y", "X", "Z"]
    boolean_mask_lookups = 0
    original_getitem = pd.DataFrame.__getitem__

    def track_getitem(self: pd.DataFrame, key: Any) -> Any:
        nonlocal boolean_mask_lookups
        if isinstance(key, pd.Series) and pd.api.types.is_bool_dtype(key.dtype):
            boolean_mask_lookups += 1
        return original_getitem(self, key)

    monkeypatch.setattr(pd.DataFrame, "__getitem__", track_getitem)
    left_strips, right_strips = _sankey.determine_widths(
        data_frame, left_labels, right_labels
    )
    left_widths, _ = _sankey._get_positions_and_total_widths(
        data_frame, left_labels, "left"
    )
    right_widths, _ = _sankey._get_positions_and_total_widths(
        data_frame, right_labels, "right"
    )

    fig, ax = plt.subplots()
    _sankey.plot_strips(
        ax,
        {
            "A": "red",
            "B": "blue",
            "C": "green",
            "X": "gray",
            "Y": "black",
            "Z": "pink",
        },
        data_frame,
        left_labels,
        left_widths,
        left_strips,
        right_strips,
        False,
        right_labels,
        right_widths,
        np.float64(1.0),
    )
    assert boolean_mask_lookups == 0
    assert len(ax.collections) == 6
    plt.close(fig)
