"""Regression tests for violin and box overlay keyword routing."""

from copy import deepcopy
from typing import Any
from unittest.mock import patch

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.patches import PathPatch
import numpy as np
import pandas as pd
import pytest
import seaborn as sns

import cnsplots as cns


@pytest.mark.parametrize("add_box", [False, True])
@pytest.mark.parametrize(
    "options",
    [
        {"bw_adjust": 0.5},
        {"cut": 0},
        {"gridsize": 32},
        {"bw_method": "silverman"},
        {"density_norm": "count", "common_norm": True},
        {"density_norm": "width"},
        {"inner": "quart", "inner_kws": {"linewidth": 2}},
        {"linewidth": 2, "linecolor": "red", "alpha": 0.4},
        {"fill": False},
    ],
)
def test_violin_options_only_reach_violin_layer(
    categorical_df: pd.DataFrame, add_box: bool, options: dict[str, Any]
) -> None:
    with (
        patch("seaborn.violinplot", wraps=sns.violinplot) as violin,
        patch("seaborn.boxplot", wraps=sns.boxplot) as box,
    ):
        ax = cns.violinplot(
            categorical_df, x="group", y="value", add_box=add_box, **options
        )

    assert ax.collections
    for key, value in options.items():
        assert violin.call_args.kwargs[key] == value
    boxes = [artist for artist in ax.patches if isinstance(artist, PathPatch)]
    assert len(boxes) == (3 if add_box else 0)
    if add_box:
        assert box.call_args.kwargs["linewidth"] == 0.4
        assert not (options.keys() - {"linewidth"}) & box.call_args.kwargs.keys()
        assert all(artist.get_facecolor() == to_rgba("white") for artist in boxes)
    else:
        box.assert_not_called()


@pytest.mark.parametrize("add_box", [False, True])
@pytest.mark.parametrize("facecolor", [None, "green"])
def test_box_options_are_isolated_and_do_not_mutate_input(
    categorical_df: pd.DataFrame, add_box: bool, facecolor: str | None
) -> None:
    box_kws: dict[str, Any] = {
        "width": 0.1,
        "whis": (0, 100),
        "boxprops": {"edgecolor": "red"},
        "medianprops": {"color": "blue", "linewidth": 2},
    }
    if facecolor is not None:
        box_kws["boxprops"]["facecolor"] = facecolor
    original = deepcopy(box_kws)
    _, (ax, reference) = plt.subplots(1, 2)
    cns.violinplot(
        categorical_df,
        x="group",
        y="value",
        inner=None,
        box_color="yellow",
        box_kws=box_kws,
        add_box=add_box,
        ax=ax,
    )
    cns.violinplot(
        categorical_df, x="group", y="value", inner=None, add_box=False, ax=reference
    )

    for actual, expected in zip(ax.collections, reference.collections, strict=True):
        np.testing.assert_array_equal(
            actual.get_paths()[0].vertices, expected.get_paths()[0].vertices
        )
    boxes = [artist for artist in ax.patches if isinstance(artist, PathPatch)]
    assert len(boxes) == (3 if add_box else 0)
    for artist in boxes:
        assert artist.get_facecolor() == to_rgba(facecolor or "yellow")
        assert artist.get_edgecolor() == to_rgba("red")
        assert np.ptp(artist.get_path().vertices[:, 0]) == pytest.approx(0.1)
    assert box_kws == original


@pytest.mark.parametrize("add_box", [False, True])
@pytest.mark.parametrize("horizontal", [False, True])
def test_split_violin_comparisons_share_category_semantics(
    categorical_df: pd.DataFrame, add_box: bool, horizontal: bool
) -> None:
    palette = {"H1": "red", "H2": "blue"}
    comparison_options: dict[str, Any] = {"pairs": "hue", "p_adjust": "holm"}
    with (
        patch("seaborn.violinplot", wraps=sns.violinplot) as violin,
        patch("seaborn.boxplot", wraps=sns.boxplot) as box,
        patch.object(cns.utils, "Annotator", wraps=cns.utils.Annotator) as annotate,
    ):
        ax = cns.violinplot(
            categorical_df,
            x="value" if horizontal else "group",
            y="group" if horizontal else "value",
            orient="y" if horizontal else "x",
            hue="hue",
            order=["B", "A"],
            hue_order=["H2", "H1"],
            palette=palette,
            saturation=1,
            box_color=None,
            dodge=True,
            split=True,
            inner=None,
            bw_adjust=0.5,
            cut=0,
            add_box=add_box,
            **comparison_options,
            box_kws={"whis": (0, 100)},
        )

    assert len(ax.texts) == 2
    expected_data = categorical_df[categorical_df["group"].isin(["A", "B"])]
    calls = [violin.call_args.kwargs, annotate.call_args.kwargs]
    if add_box:
        calls.append(box.call_args.kwargs)
        boxes = [artist for artist in ax.patches if isinstance(artist, PathPatch)]
        assert [artist.get_facecolor() for artist in boxes] == [
            to_rgba("blue"),
            to_rgba("blue"),
            to_rgba("red"),
            to_rgba("red"),
        ]
    for call in calls:
        pd.testing.assert_frame_equal(call["data"], expected_data)
        assert call["orient"] == ("h" if horizontal else "v")
        assert call["order"] == ["B", "A"]
        assert call["hue_order"] == ["H2", "H1"]
        assert call["dodge"] is True
    assert not {"bw_adjust", "cut", "split", "inner", "whis", "boxprops"} & (
        annotate.call_args.kwargs.keys()
    )
