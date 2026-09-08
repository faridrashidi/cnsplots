from __future__ import annotations

from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
import pytest
from matplotlib.artist import Artist
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path

import cnsplots as cns


@pytest.mark.parametrize("explicit_ax", [False, True])
@pytest.mark.parametrize("existing_artist", [False, True])
def test_boxplot_without_boxes_returns_target_axes(
    categorical_df: pd.DataFrame, explicit_ax: bool, existing_artist: bool
) -> None:
    _, (target_ax, other_ax) = plt.subplots(1, 2)
    artist = Artist()
    artist.set_alpha(0.6)
    if existing_artist:
        target_ax.add_artist(artist)
    plt.sca(other_ax if explicit_ax else target_ax)

    result = cns.boxplot(
        categorical_df,
        x="group",
        y="value",
        showbox=False,
        add_count=True,
        **({"ax": target_ax} if explicit_ax else {}),
    )

    assert result is target_ax
    assert not target_ax.patches
    assert len(target_ax.lines) == 9
    if existing_artist:
        assert artist in target_ax.artists
    assert artist.get_alpha() == 0.6
    assert target_ax.get_xticklabels()[0].get_text() == "A\n(n=4)"
    assert not other_ax.lines
    assert not other_ax.patches
    target_ax.figure.canvas.draw()


def test_boxplot_preserves_existing_artists(categorical_df: pd.DataFrame) -> None:
    _, ax = plt.subplots()
    cns.boxplot(categorical_df, x="group", y="value", color="red", ax=ax)
    ax.plot([0, 1], [1, 2], color="purple", marker="o", mfc="yellow", mec="green")
    patch = PathPatch(
        Path([(0, 0), (1, 0), (1, 1), (0, 0)]),
        facecolor="orange",
        edgecolor="purple",
        label="Existing path",
    )
    ax.add_patch(patch)
    ax.add_patch(
        Rectangle(
            (0, 0), 1, 1, facecolor="yellow", edgecolor="green", label="Existing area"
        )
    )
    ax.legend()
    existing_lines = [
        (
            item,
            item.get_color(),
            item.get_markerfacecolor(),
            item.get_markeredgecolor(),
        )
        for item in ax.lines
    ]
    existing_patches = [
        (item, item.get_facecolor(), item.get_edgecolor()) for item in ax.patches
    ]

    cns.boxplot(categorical_df, x="group", y="value", color="blue", ax=ax)

    for item, color, mfc, mec in existing_lines:
        assert item in ax.lines
        assert item.get_color() == color
        assert item.get_markerfacecolor() == mfc
        assert item.get_markeredgecolor() == mec
    for item, facecolor, edgecolor in existing_patches:
        assert item in ax.patches
        assert item.get_facecolor() == facecolor
        assert item.get_edgecolor() == edgecolor
    legend = ax.get_legend()
    assert legend is not None
    legend_handles = dict(
        zip([text.get_text() for text in legend.get_texts()], legend.legend_handles)
    )
    for label, color in [("Existing path", "purple"), ("Existing area", "green")]:
        handle = legend_handles[label]
        assert isinstance(handle, Rectangle)
        assert handle.get_edgecolor() == to_rgba(color)


@pytest.mark.parametrize("horizontal", [False, True])
@pytest.mark.parametrize("showcaps", [False, True])
def test_filled_boxplot_colors_follow_each_hue(
    categorical_df: pd.DataFrame, horizontal: bool, showcaps: bool
) -> None:
    _, ax = plt.subplots()
    palette = {"H1": "#d95f02", "H2": "#1b9e77"}

    cns.boxplot(
        categorical_df,
        x="value" if horizontal else "group",
        y="group" if horizontal else "value",
        hue="hue",
        hue_order=["H2", "H1"],
        palette=palette,
        saturation=1,
        showcaps=showcaps,
        showmeans=showcaps,
        showoutliers=True,
        ax=ax,
    )

    assert len(ax.containers) == 2
    for container, hue in zip(ax.containers, ["H2", "H1"]):
        container = cast(Any, container)
        color = to_rgba(palette[hue])
        assert len(container.boxes) == 3
        for box in container.boxes:
            assert isinstance(box, PathPatch)
            assert box.get_fill()
            assert box.get_facecolor() == pytest.approx(color)
            assert box.get_edgecolor()[-1] == 0
        for line in [
            *container.whiskers,
            *container.caps,
            *container.fliers,
            *container.means,
        ]:
            assert to_rgba(line.get_color()) == pytest.approx(color)
            assert to_rgba(line.get_mfc()) == pytest.approx(color)
            assert to_rgba(line.get_mec()) == pytest.approx(color)
        for median in container.medians:
            assert to_rgba(median.get_color()) == to_rgba("white")


@pytest.mark.parametrize("boxprops", [None, {"color": "red"}])
def test_unfilled_boxplot_keeps_visible_line_boxes(
    categorical_df: pd.DataFrame, boxprops: dict[str, Any] | None
) -> None:
    _, ax = plt.subplots()

    result = cns.boxplot(
        categorical_df,
        x="group",
        y="value",
        fill=False,
        ax=ax,
        **({"boxprops": boxprops} if boxprops is not None else {}),
    )

    assert result is ax
    boxes = [box for container in ax.containers for box in cast(Any, container).boxes]
    assert len(boxes) == 3
    for box in boxes:
        assert isinstance(box, Line2D)
        assert to_rgba(box.get_color())[-1] > 0
        if boxprops is not None:
            assert to_rgba(box.get_color()) == to_rgba("red")
    ax.figure.canvas.draw()


def test_unfilled_boxplot_keeps_hue_legend_outlines(
    categorical_df: pd.DataFrame,
) -> None:
    _, ax = plt.subplots()

    cns.boxplot(categorical_df, x="group", y="value", hue="hue", fill=False, ax=ax)

    legend = ax.get_legend()
    assert legend is not None
    assert [text.get_text() for text in legend.get_texts()] == ["H1", "H2"]
    for handle in legend.legend_handles:
        assert isinstance(handle, Rectangle)
        assert to_rgba(handle.get_facecolor())[-1] == 0
        assert to_rgba(handle.get_edgecolor())[-1] > 0


@pytest.mark.parametrize("edgecolor", [None, "red"])
def test_boxplot_preserves_unfilled_patch_outlines(
    categorical_df: pd.DataFrame, edgecolor: str | None
) -> None:
    _, ax = plt.subplots()
    boxprops: dict[str, Any] = {"fill": False}
    if edgecolor is not None:
        boxprops["edgecolor"] = edgecolor

    cns.boxplot(categorical_df, x="group", y="value", boxprops=boxprops, ax=ax)

    assert len(ax.patches) == 3
    for box in ax.patches:
        assert not box.get_fill()
        assert to_rgba(box.get_edgecolor())[-1] > 0
        if edgecolor is not None:
            assert box.get_edgecolor() == to_rgba(edgecolor)
    ax.figure.canvas.draw()
