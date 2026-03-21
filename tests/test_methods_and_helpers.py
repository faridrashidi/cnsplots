from __future__ import annotations

import types
from typing import Any, cast

import anndata as ad
import matplotlib as mpl
import matplotlib.colorbar  # noqa: F401  # ensure submodule is importable
import matplotlib.legend as mlegend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.transforms import Bbox

import cnsplots as cns
from cnsplots import _utils
from cnsplots.helpers import _cmprsk, _heatmap as helper_heatmap, _phylo, _sankey


def test_competing_risk_helper(competing_risk_df: pd.DataFrame) -> None:
    pvalue = _cmprsk.cuminc(
        competing_risk_df["time"],
        competing_risk_df["event"],
        competing_risk_df["group"],
    )
    assert 0 <= pvalue <= 1


def test_sankey_helpers(sankey_df: pd.DataFrame) -> None:
    _sankey.check_data_matches_labels(
        ["Start", "Middle", "End"], sankey_df["source"], "left"
    )
    with pytest.raises(ValueError, match="left labels and data do not match"):
        _sankey.check_data_matches_labels(["Other"], sankey_df["source"], "left")

    with pytest.warns(DeprecationWarning) as caught:
        ax, left_labels, left_weight, right_labels, right_weight = _sankey.init_values(
            None,
            True,
            (1, 1),
            "name",
            sankey_df["source"].tolist(),
            None,
            None,
            None,
            None,
        )
    assert ax is plt.gca()
    assert left_labels == []
    assert len(left_weight) == len(sankey_df)
    assert len(right_weight) == len(sankey_df)
    messages = [str(warning.message) for warning in caught]
    assert any("deprecated" in message for message in messages)

    data_frame = _sankey._create_dataframe(
        sankey_df["source"],
        np.ones(len(sankey_df)),
        sankey_df["target"],
        np.ones(len(sankey_df)),
    )
    left_labels, right_labels = _sankey.identify_labels(data_frame, [], [])
    ns_l, ns_r = _sankey.determine_widths(data_frame, left_labels, right_labels)
    widths_left, top_edge_left = _sankey._get_positions_and_total_widths(
        data_frame, left_labels, "left"
    )
    widths_right, top_edge_right = _sankey._get_positions_and_total_widths(
        data_frame, right_labels, "right"
    )
    assert top_edge_left > 0
    assert top_edge_right > 0

    colors = _sankey.create_colors(np.array(left_labels + right_labels), None)
    assert colors
    with pytest.raises(ValueError, match="missing values"):
        _sankey.create_colors(np.array(["A"]), {})

    fig, ax_plot = plt.subplots()
    _sankey.draw_vertical_bars(
        ax_plot,
        colors,
        10,
        left_labels,
        widths_left,
        right_labels,
        widths_right,
        np.float64(1.0),
        label_rotation=45,
    )
    assert len(ax_plot.texts) == len(left_labels) + len(right_labels)
    assert all(text.get_rotation() == 45 for text in ax_plot.texts)
    left_texts = ax_plot.texts[: len(left_labels)]
    right_texts = ax_plot.texts[len(left_labels) :]
    assert all(text.get_position()[0] < 0 for text in left_texts)
    assert all(text.get_position()[0] > 0 for text in right_texts)
    _sankey.plot_strips(
        ax_plot,
        colors,
        data_frame,
        left_labels,
        widths_left,
        ns_l,
        ns_r,
        False,
        right_labels,
        widths_right,
        np.float64(1.0),
    )
    assert ax_plot.axison is False

    with pytest.raises(ValueError, match="null values"):
        _sankey._create_dataframe(
            pd.Series(["A", None]),
            pd.Series([1, 1]),
            pd.Series(["B", "C"]),
            pd.Series([1, 1]),
        )

    fig2, ax2 = plt.subplots()
    result_ax = _sankey.sankeyplot(
        sankey_df["source"],
        sankey_df["target"],
        label_rotation=90,
        figureName="figure",
        closePlot=True,
        figSize=(2, 2),
        ax=ax2,
    )
    assert result_ax is ax2
    assert len(ax2.texts) == len(left_labels) + len(right_labels)
    assert all(text.get_rotation() == 90 for text in ax2.texts)
    left_texts = ax2.texts[: len(left_labels)]
    right_texts = ax2.texts[len(left_labels) :]
    assert all(text.get_position()[0] < 0 for text in left_texts)
    assert all(text.get_position()[0] > 0 for text in right_texts)


def test_phylo_helper_functions(phylo_adata: ad.AnnData) -> None:
    cns.figure(150, 120)
    _phylo.phyloplot(phylo_adata)
    assert len(plt.gcf().axes) == 5

    fig, ax = plt.subplots()
    pytest.importorskip("seaborn")
    out_ax, cmap = _phylo._heatmap(
        pd.DataFrame({"group": ["A", "B"]}),
        ax=ax,
        legend=True,
        leg_pos="top",
    )
    assert out_ax is ax
    assert set(cmap) == {"A", "B"}

    with pytest.raises(TypeError, match="Unable to work with data"):
        _phylo._heatmap("bad")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Unable to interpret colormap"):
        _phylo._heatmap(pd.DataFrame({"group": ["A", "B"]}), cmap="bad")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="leg_ax must be matplotlib axes"):
        _phylo._heatmap(pd.DataFrame({"group": ["A", "B"]}), leg_ax="bad")  # type: ignore[arg-type]

    assert _phylo._is_categorical(pd.DataFrame({"a": [1, 2]})) == [False]
    with pytest.raises(TypeError):
        _phylo._is_categorical(pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}))
    assert _phylo._is_categorical(pd.Series([1, 2])) is True
    assert _phylo._is_categorical(pd.Series(["x", "y"])) is False
    assert _phylo._is_categorical(np.array([1, 2])) is False
    assert _phylo._is_categorical(np.array(["x", "y"])) is True
    assert _phylo._is_categorical(np.array([[1, 2], ["x", "y"]], dtype=object)) == [
        True,
        True,
    ]
    with pytest.raises(ValueError, match="1d or 2d arrays"):
        _phylo._is_categorical(np.zeros((1, 1, 1)))

    assert len(_phylo._gen_colors("Set1", 2)) == 2
    assert len(_phylo._gen_colors(cns.palettes("parula"), 2)) == 2
    assert len(_phylo._gen_colors(["red", "blue"], 2)) == 2
    with pytest.raises(ValueError, match="at least as many colors"):
        _phylo._gen_colors(["red"], 2)
    with pytest.raises(TypeError, match="Unable to generate colors"):
        _phylo._gen_colors(1, 2)  # type: ignore[arg-type]


def test_cluster_map_plotter_new_collect_legends() -> None:
    import PyComplexHeatmap as pch

    df = pd.DataFrame([[0, 1], [1, 0]], columns=pd.Index(["A", "B"]))
    cns.figure(120, 120)
    plotter = helper_heatmap.ClusterMapPlotterNew(
        data=df,
        cmap="Set1",
        show_rownames=True,
        show_colnames=True,
        plot=True,
        plot_legend=True,
        legend_anchor="ax_heatmap",
        verbose=0,
    )
    assert plotter.ax_heatmap is not None

    cns.figure(120, 120)
    plotter_cont = helper_heatmap.ClusterMapPlotterNew(
        data=df,
        cmap="viridis",
        show_rownames=True,
        show_colnames=True,
        plot=True,
        plot_legend=True,
        verbose=0,
    )
    assert plotter_cont.legend_list

    top_annotation = pch.HeatmapAnnotation(
        axis=1,
        blobs=pch.anno_simple(pd.Series(["0", "1"], index=df.columns), cmap="Set2"),
    )
    left_annotation = pch.HeatmapAnnotation(
        axis=0,
        Ensemble=pch.anno_simple(
            pd.Series(["ens0", "ens1"], index=df.index), cmap="Set1"
        ),
    )
    cns.figure(120, 120)
    plotter_ordered = helper_heatmap.ClusterMapPlotterNew(
        data=df,
        cmap="viridis",
        label="Z-score",
        top_annotation=top_annotation,
        left_annotation=left_annotation,
        show_rownames=True,
        show_colnames=True,
        plot=True,
        plot_legend=True,
        legend_order=["missing", "Ensemble", "blobs", "Z-score"],
        verbose=0,
    )
    assert [item[1] for item in plotter_ordered.legend_list] == [
        "Ensemble",
        "blobs",
        "Z-score",
    ]


def test_stabilize_detached_legends_guard_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cns.figure(120, 120)
    ax = plt.gca()
    ax.plot([0, 1], [0, 1], label="A")
    removed_legend = ax.legend()
    removed_legend.remove()
    assert removed_legend.axes is None
    helper_heatmap._stabilize_detached_legends([removed_legend])

    cns.figure(120, 120)
    ax2 = plt.gca()
    ax2.plot([0, 1], [0, 1], label="B")
    legend_no_renderer = ax2.legend()
    monkeypatch.setattr(ax2.figure.canvas, "get_renderer", lambda: None)
    helper_heatmap._stabilize_detached_legends([legend_no_renderer])

    cns.figure(120, 120)
    ax3 = plt.gca()
    ax3.plot([0, 1], [0, 1], label="C")
    zero_size_legend = ax3.legend()
    ax3.figure.canvas.draw()
    monkeypatch.setattr(
        ax3,
        "get_window_extent",
        lambda renderer=None: Bbox.from_bounds(0, 0, 0, 1),
    )
    helper_heatmap._stabilize_detached_legends([zero_size_legend])


def test_stabilize_detached_legends_skips_zero_sized_stub_axes() -> None:
    class StubCanvas:
        def get_renderer(self) -> object:
            return object()

    class StubFigure:
        def __init__(self) -> None:
            self.canvas = StubCanvas()

    class StubAxes:
        def __init__(self) -> None:
            self.figure = StubFigure()
            self.transAxes = object()

        def get_window_extent(self, renderer: object | None = None) -> Bbox:
            return Bbox.from_bounds(0, 0, 0, 1)

    class StubLegend(mlegend.Legend):
        def __init__(self, axes: object) -> None:
            self._axes = axes
            self.anchor_args: tuple[object, ...] | None = None
            self.anchor_kwargs: dict[str, object] | None = None

        def get_window_extent(self, renderer: object | None = None) -> Bbox:
            return Bbox.from_bounds(0, 0, 10, 10)

        def set_bbox_to_anchor(self, *args: object, **kwargs: object) -> None:
            self.anchor_args = args
            self.anchor_kwargs = kwargs

    legend = StubLegend(StubAxes())
    helper_heatmap._stabilize_detached_legends([legend])

    assert legend.anchor_args is None
    assert legend.anchor_kwargs is None


def test_stabilize_detached_legends_skips_canvas_without_renderer_method() -> None:
    class StubFigure:
        def __init__(self) -> None:
            self.canvas = object()

    class StubAxes:
        def __init__(self) -> None:
            self.figure = StubFigure()
            self.transAxes = object()

        def get_window_extent(self, renderer: object | None = None) -> Bbox:
            return Bbox.from_bounds(0, 0, 10, 10)

    class StubLegend(mlegend.Legend):
        def __init__(self, axes: object) -> None:
            self._axes = axes
            self.anchor_args: tuple[object, ...] | None = None
            self.anchor_kwargs: dict[str, object] | None = None

        def get_window_extent(self, renderer: object | None = None) -> Bbox:
            return Bbox.from_bounds(0, 0, 10, 10)

        def set_bbox_to_anchor(self, *args: object, **kwargs: object) -> None:
            self.anchor_args = args
            self.anchor_kwargs = kwargs

    legend = StubLegend(StubAxes())
    helper_heatmap._stabilize_detached_legends([legend])

    assert legend.anchor_args is None
    assert legend.anchor_kwargs is None


def test_sync_detached_legend_axes_guard_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cns.figure(120, 120)
    ax = plt.gca()
    fig = plt.gcf()
    legend_ax = fig.add_axes((0.6, 0.2, 0.1, 0.5))
    fig.canvas.draw()
    plotter = cast(
        Any,
        types.SimpleNamespace(
            _legend_anchor_ax=ax,
            legend_axes=[legend_ax],
            legend_delta_x=None,
            legend_side="right",
            right_annotation=None,
            label_max_width=0.0,
            show_rownames=False,
            row_names_side="left",
            legend_hpad=2,
            cbars=[],
        ),
    )

    initial_bounds = legend_ax.get_position().bounds
    monkeypatch.setattr(fig.canvas, "get_renderer", lambda: None)
    helper_heatmap._sync_detached_legend_axes(plotter)
    assert legend_ax.get_position().bounds == pytest.approx(initial_bounds)

    cns.figure(120, 120)
    ax2 = plt.gca()
    fig2 = plt.gcf()
    legend_ax2 = fig2.add_axes((0.6, 0.2, 0.1, 0.5))
    fig2.canvas.draw()
    plotter2 = cast(
        Any,
        types.SimpleNamespace(
            _legend_anchor_ax=ax2,
            legend_axes=[legend_ax2],
            legend_delta_x=None,
            legend_side="right",
            right_annotation=None,
            label_max_width=0.0,
            show_rownames=False,
            row_names_side="left",
            legend_hpad=2,
            cbars=[],
        ),
    )

    initial_bounds2 = legend_ax2.get_position().bounds
    monkeypatch.setattr(
        ax2,
        "get_window_extent",
        lambda renderer=None: Bbox.from_bounds(0, 0, 0, 10),
    )
    helper_heatmap._sync_detached_legend_axes(plotter2)
    assert legend_ax2.get_position().bounds == pytest.approx(initial_bounds2)


def test_sync_detached_legend_axes_skips_canvas_without_renderer_method() -> None:
    class StubLegendAxes:
        def __init__(self) -> None:
            self.position_updates: list[list[float]] = []

        def set_position(self, bounds: list[float]) -> None:
            self.position_updates.append(bounds)

    plotter = cast(
        Any,
        types.SimpleNamespace(
            _legend_anchor_ax=types.SimpleNamespace(
                figure=types.SimpleNamespace(canvas=object())
            ),
            legend_axes=[StubLegendAxes()],
            legend_delta_x=None,
            legend_side="right",
            right_annotation=None,
            label_max_width=0.0,
            show_rownames=False,
            row_names_side="left",
            legend_hpad=2,
            cbars=[],
        ),
    )

    helper_heatmap._sync_detached_legend_axes(plotter)

    assert plotter.legend_axes[0].position_updates == []


def test_sync_detached_legend_axes_uses_label_width_for_right_annotation() -> None:
    cns.figure(120, 120)
    ax = plt.gca()
    fig = plt.gcf()
    legend_ax = fig.add_axes((0.6, 0.2, 0.1, 0.5))
    fig.canvas.draw()
    plotter = cast(
        Any,
        types.SimpleNamespace(
            _legend_anchor_ax=ax,
            legend_axes=[legend_ax],
            legend_delta_x=None,
            legend_side="right",
            right_annotation=object(),
            label_max_width=12.0,
            show_rownames=False,
            row_names_side="left",
            legend_hpad=2,
            cbars=[],
        ),
    )

    helper_heatmap._sync_detached_legend_axes(plotter)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    anchor_bbox = ax.get_window_extent(renderer=renderer)
    expected_x0 = (
        anchor_bbox.x1
        + plotter.label_max_width
        + plotter.legend_hpad * helper_heatmap.mm2inch * fig.dpi
        + ax.yaxis.labelpad * 1.2 * fig.dpi / 72
    )
    assert legend_ax.get_window_extent(renderer=renderer).x0 == pytest.approx(
        expected_x0
    )


def test_sync_detached_legend_axes_respects_explicit_delta_x() -> None:
    cns.figure(120, 120)
    ax = plt.gca()
    fig = plt.gcf()
    legend_ax = fig.add_axes((0.6, 0.2, 0.1, 0.5))
    fig.canvas.draw()
    plotter = cast(
        Any,
        types.SimpleNamespace(
            _legend_anchor_ax=ax,
            legend_axes=[legend_ax],
            legend_delta_x=0.15,
            legend_side="right",
            right_annotation=None,
            label_max_width=0.0,
            show_rownames=False,
            row_names_side="left",
            legend_hpad=2,
            cbars=[],
        ),
    )

    helper_heatmap._sync_detached_legend_axes(plotter)
    assert legend_ax.get_position().x0 == pytest.approx(ax.get_position().x1 + 0.15)


def test_figure_autofit_sync_hooks_deduplicate_callbacks() -> None:
    cns.figure(120, 120)
    fig = plt.gcf()
    manager = getattr(fig, "_cnsplots_autofit_manager")
    ax1 = plt.gca()
    ax2 = fig.add_axes((0.6, 0.2, 0.2, 0.2))
    calls: list[str] = []

    def sync() -> None:
        calls.append("called")

    setattr(ax1, "_sync_test", sync)
    setattr(ax2, "_sync_test", sync)

    manager._run_axes_sync_hooks("_sync_test")

    assert calls == ["called"]


def test_capture_detached_axes_layout_returns_empty_without_new_axes() -> None:
    cns.figure(120, 120)
    host_ax = plt.gca()

    layouts = _utils._capture_detached_axes_layout(host_ax, [host_ax])

    assert layouts == []
    assert not hasattr(host_ax, "_cnsplots_detached_axes_layout")
    assert not hasattr(host_ax, "_cnsplots_sync_embedded_axes")


def test_capture_detached_axes_layout_chains_existing_sync_hook() -> None:
    cns.figure(120, 120)
    host_ax = plt.gca()
    detached_ax = plt.gcf().add_axes((0.75, 0.2, 0.1, 0.4))
    initial_detached_box = detached_ax.get_position().frozen()
    calls: list[str] = []

    setattr(host_ax, "_cnsplots_sync_embedded_axes", lambda: calls.append("existing"))
    layouts = _utils._capture_detached_axes_layout(host_ax, [host_ax])

    assert len(layouts) == 1

    host_ax.set_position((0.2, 0.3, 0.4, 0.5))
    sync = getattr(host_ax, "_cnsplots_sync_embedded_axes")
    assert callable(sync)
    sync()

    host_box = host_ax.get_position().frozen()
    detached_box = detached_ax.get_position().frozen()

    assert calls == ["existing"]
    assert detached_box.bounds != pytest.approx(initial_detached_box.bounds)
    assert detached_box.x0 == pytest.approx(
        host_box.x0 + host_box.width * layouts[0]["x0"]
    )
    assert detached_box.y0 == pytest.approx(
        host_box.y0 + host_box.height * layouts[0]["y0"]
    )
    assert detached_box.width == pytest.approx(host_box.width * layouts[0]["width"])
    assert detached_box.height == pytest.approx(host_box.height * layouts[0]["height"])


def test_capture_detached_axes_layout_appends_specific_axes_without_duplicates() -> (
    None
):
    cns.figure(120, 120)
    host_ax = plt.gca()
    fig = plt.gcf()
    detached_ax1 = fig.add_axes((0.75, 0.2, 0.1, 0.4))

    first_layouts = _utils._capture_detached_axes_layout(
        host_ax,
        detached_axes=[detached_ax1],
    )
    assert len(first_layouts) == 1

    detached_ax2 = fig.add_axes((0.82, 0.2, 0.05, 0.3))
    second_layouts = _utils._capture_detached_axes_layout(
        host_ax,
        detached_axes=[detached_ax1, detached_ax2],
    )

    assert len(second_layouts) == 1
    tracked_layouts = getattr(host_ax, "_cnsplots_detached_axes_layout")
    assert len(tracked_layouts) == 2
    assert tracked_layouts[0]["ax"] is detached_ax1
    assert tracked_layouts[1]["ax"] is detached_ax2


def test_capture_detached_axes_layout_skips_foreign_axes_and_sync_guard() -> None:
    cns.figure(120, 120)
    host_ax = plt.gca()
    other_fig = plt.figure()
    try:
        other_ax = other_fig.add_axes((0.1, 0.2, 0.2, 0.3))
        assert (
            _utils._capture_detached_axes_layout(host_ax, detached_axes=[other_ax])
            == []
        )

        detached_ax = host_ax.figure.add_axes((0.75, 0.2, 0.1, 0.4))
        _utils._capture_detached_axes_layout(host_ax, detached_axes=[detached_ax])
        layouts = getattr(host_ax, "_cnsplots_detached_axes_layout")
        layouts[0]["ax"] = other_ax

        sync = getattr(host_ax, "_cnsplots_sync_embedded_axes")
        assert callable(sync)
        sync()
    finally:
        plt.close(other_fig)


def test_capture_detached_colorbar_layout_guard_branches() -> None:
    plotter = cast(Any, types.SimpleNamespace(legend_axes=[], cbars=[]))
    helper_heatmap._capture_detached_colorbar_layout(plotter)
    assert plotter._detached_colorbar_layout == []

    stub_plotter = cast(
        Any,
        types.SimpleNamespace(
            legend_axes=[
                types.SimpleNamespace(
                    figure=types.SimpleNamespace(bbox=Bbox.from_bounds(0, 0, 0, 1)),
                    get_position=lambda: types.SimpleNamespace(
                        bounds=(0.0, 0.0, 0.1, 0.5)
                    ),
                )
            ],
            cbars=[],
        ),
    )
    helper_heatmap._capture_detached_colorbar_layout(stub_plotter)
    assert not hasattr(stub_plotter, "_detached_colorbar_layout")

    legend_ax = types.SimpleNamespace(
        figure=types.SimpleNamespace(bbox=Bbox.from_bounds(0, 0, 100, 100)),
        get_position=lambda: types.SimpleNamespace(bounds=(0.6, 0.2, 0.1, 0.5)),
    )
    cbar1 = object.__new__(mpl.colorbar.Colorbar)
    cbar1.ax = None
    cbar2 = object.__new__(mpl.colorbar.Colorbar)
    cbar2.ax = types.SimpleNamespace(
        get_position=lambda: types.SimpleNamespace(bounds=(0.0, 0.0, 0.0, 0.2))
    )
    plotter2 = cast(
        Any,
        types.SimpleNamespace(legend_axes=[legend_ax], cbars=[cbar1, cbar2]),
    )
    helper_heatmap._capture_detached_colorbar_layout(plotter2)
    assert plotter2._detached_colorbar_layout == []


def test_sync_detached_legend_axes_skips_invalid_colorbar_layout_entries() -> None:
    cns.figure(120, 120)
    ax = plt.gca()
    fig = plt.gcf()
    legend_ax = fig.add_axes((0.6, 0.2, 0.1, 0.5))
    fig.canvas.draw()
    plotter = cast(
        Any,
        types.SimpleNamespace(
            _legend_anchor_ax=ax,
            legend_axes=[legend_ax],
            legend_delta_x=None,
            legend_side="right",
            right_annotation=None,
            label_max_width=0.0,
            show_rownames=False,
            row_names_side="left",
            legend_hpad=2,
            cbars=[],
            _detached_colorbar_layout=[
                {
                    "legend_ax_idx": 5,
                    "cbar": types.SimpleNamespace(ax=legend_ax),
                    "x_offset_px": 0.0,
                    "top_offset_px": 0.0,
                    "width_px": 10.0,
                    "height_px": 20.0,
                },
                {
                    "legend_ax_idx": 0,
                    "cbar": types.SimpleNamespace(ax=None),
                    "x_offset_px": 0.0,
                    "top_offset_px": 0.0,
                    "width_px": 10.0,
                    "height_px": 20.0,
                },
            ],
        ),
    )

    helper_heatmap._sync_detached_legend_axes(plotter)
