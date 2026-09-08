from __future__ import annotations

from typing import Any, cast

import anndata as ad
import matplotlib as mpl
from matplotlib.collections import QuadMesh
from matplotlib.colorbar import Colorbar
from matplotlib.colors import LogNorm
from matplotlib.legend import Legend
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import PyComplexHeatmap as pch
import pytest

import cnsplots as cns
from cnsplots.helpers._heatmap import ClusterMapPlotterNew


def _plot_heatmap(
    values: np.ndarray, split: bool, **kwargs: Any
) -> ClusterMapPlotterNew:
    cns.figure(180, 180)
    if split:
        data = ad.AnnData(np.repeat(np.repeat(values, 2, axis=0), 2, axis=1))
        data.obs["group"] = ["A", "A", "B", "B"]
        data.var["group"] = ["A", "A", "B", "B"]
        plotter = cns.heatmapplot(
            data,
            row_split="group",
            col_split="group",
            row_split_order=["A", "B"],
            col_split_order=["A", "B"],
            **kwargs,
        )
    else:
        plotter = cns.heatmapplot(pd.DataFrame(values), **kwargs)
    plotter.ax.figure.canvas.draw()
    assert plotter.heatmap_axes.shape == ((2, 2) if split else (1, 1))
    return plotter


@pytest.mark.parametrize("split", [False, True], ids=["unsplit", "split"])
@pytest.mark.parametrize(
    ("values", "kwargs", "limits"),
    [
        ([[0.001, 0.002], [0.003, 0.004]], {}, (0.001, 0.004)),
        ([[1, 2], [3, 4]], {"cmap": "viridis"}, (1, 4)),
        ([[-1, 0], [1, 10]], {"cmap": "bwr", "center": 0}, (-1, 10)),
        (
            [[1, 10], [100, 1000]],
            {"cmap": "viridis", "norm": LogNorm(1, 1000)},
            (1, 1000),
        ),
        (
            [[0.1, 0.4], [0.7, 0.9]],
            {"cmap": "viridis", "vmin": -0.1234, "vmax": 1.2345},
            (-0.1234, 1.2345),
        ),
        (
            [[-1, 0], [1, 10]],
            {
                "cmap": "bwr",
                "center": 0,
                "legend_kws": {"center": 5, "vmin": -10, "vmax": 20},
            },
            (-1, 10),
        ),
    ],
    ids=[
        "small",
        "ordinary",
        "centered",
        "logarithmic",
        "explicit-limits",
        "conflicting-legend-mapping",
    ],
)
def test_heatmap_colorbar_matches_rendered_cells(
    values: list[list[float]],
    kwargs: dict[str, Any],
    limits: tuple[float, float],
    split: bool,
) -> None:
    plotter = _plot_heatmap(np.asarray(values), split, **kwargs)
    colorbar = next(item for item in plotter.cbars if isinstance(item, Colorbar))

    assert (colorbar.norm.vmin, colorbar.norm.vmax) == pytest.approx(limits)
    for ax in plotter.heatmap_axes.flat:
        mesh = next(item for item in ax.collections if isinstance(item, QuadMesh))
        assert (mesh.norm.vmin, mesh.norm.vmax) == pytest.approx(limits)
        cell_values = np.asarray(mesh.get_array()).ravel()
        np.testing.assert_allclose(
            colorbar.mappable.to_rgba(cell_values), mesh.get_facecolors()
        )


@pytest.mark.parametrize("split", [False, True], ids=["unsplit", "split"])
def test_heatmap_constant_cells_match_colorbar(split: bool) -> None:
    plotter = _plot_heatmap(np.ones((2, 2)), split)
    colorbar = next(item for item in plotter.cbars if isinstance(item, Colorbar))
    assert colorbar.norm.vmin < 1 < colorbar.norm.vmax

    for ax in plotter.heatmap_axes.flat:
        mesh = next(item for item in ax.collections if isinstance(item, QuadMesh))
        assert (mesh.norm.vmin, mesh.norm.vmax) == pytest.approx(
            (colorbar.norm.vmin, colorbar.norm.vmax)
        )
        np.testing.assert_allclose(
            colorbar.mappable.to_rgba(np.asarray(mesh.get_array()).ravel()),
            mesh.get_facecolors(),
        )


@pytest.mark.parametrize("split", [False, True], ids=["unsplit", "split"])
@pytest.mark.parametrize("codes", [[2, 10, 20], [2, 3, 20]])
def test_heatmap_categorical_legend_matches_rendered_cells(
    codes: list[int], split: bool
) -> None:
    values = np.array([[codes[0], codes[1]], [codes[1], codes[2]]])
    plotter = _plot_heatmap(values, split, cmap="Set1")
    legend = next(item for item in plotter.cbars if isinstance(item, Legend))
    legend_colors = {}
    for label, handle in zip(legend.get_texts(), legend.legend_handles):
        assert isinstance(handle, Patch)
        legend_colors[int(label.get_text())] = handle.get_facecolor()

    assert set(legend_colors) == set(codes)
    for ax in plotter.heatmap_axes.flat:
        mesh = next(item for item in ax.collections if isinstance(item, QuadMesh))
        cell_values = np.asarray(mesh.get_array()).ravel()
        np.testing.assert_allclose(
            [legend_colors[value] for value in cell_values], mesh.get_facecolors()
        )


@pytest.mark.parametrize(
    ("values", "kwargs", "ticks", "labels"),
    [
        (
            [[-1, 0], [1, 10]],
            {"cmap": "bwr", "center": 0},
            [-1, 0, 10],
            ["-1.0", "0.0", "10.0"],
        ),
        (
            [[1, 10], [100, 1000]],
            {"cmap": "viridis", "norm": LogNorm(1, 1000)},
            [1, 10, 1000],
            ["1.0", "10.0", "1000.0"],
        ),
    ],
    ids=["centered", "logarithmic"],
)
def test_heatmap_colorbar_preserves_explicit_ticks_and_format(
    values: list[list[float]],
    kwargs: dict[str, Any],
    ticks: list[int],
    labels: list[str],
) -> None:
    plotter = _plot_heatmap(
        np.asarray(values),
        False,
        legend_kws={"ticks": ticks, "format": "%.1f"},
        **kwargs,
    )
    colorbar = next(item for item in plotter.cbars if isinstance(item, Colorbar))

    np.testing.assert_array_equal(colorbar.get_ticks(), ticks)
    assert [label.get_text() for label in colorbar.ax.get_yticklabels()] == labels


def test_heatmap_preserves_annotation_colorbar_with_shared_colormap() -> None:
    cns.figure(180, 180)
    cmap = mpl.colormaps["viridis"]
    annotation = pch.HeatmapAnnotation(
        score=pch.anno_simple(pd.Series([10.0, 20.0]), cmap=cmap),
        verbose=0,
    )
    plotter = ClusterMapPlotterNew(
        pd.DataFrame([[1.0, 2.0], [3.0, 4.0]]),
        cmap=cast(Any, cmap),
        top_annotation=annotation,
        row_cluster=False,
        col_cluster=False,
        label="value",
        verbose=0,
    )
    plotter.ax.figure.canvas.draw()
    colorbars = {
        item.ax.get_ylabel(): item
        for item in plotter.cbars
        if isinstance(item, Colorbar)
    }

    assert set(colorbars) == {"score", "value"}
    annotation_bar = colorbars["score"]
    assert (annotation_bar.norm.vmin, annotation_bar.norm.vmax) == (10, 20)
    for label, ax in [
        ("score", annotation.axes[0, 0]),
        ("value", plotter.heatmap_axes[0, 0]),
    ]:
        mesh = next(item for item in ax.collections if isinstance(item, QuadMesh))
        cell_values = np.asarray(mesh.get_array()).ravel()
        np.testing.assert_allclose(
            colorbars[label].mappable.to_rgba(cell_values), mesh.get_facecolors()
        )
