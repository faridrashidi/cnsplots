from __future__ import annotations

import logging
import sys
import types
from typing import Any, cast

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar
from matplotlib.legend import Legend

import cnsplots as cns


def _bivariate_hist_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "x": [4.5, 4.7, 4.9, 5.1, 5.3, 5.7, 5.9, 6.1, 6.3, 6.8, 7.1, 7.4],
            "y": [2.2, 2.4, 3.1, 3.3, 3.6, 4.0, 4.2, 2.9, 2.7, 3.0, 3.5, 2.8],
        }
    )


def _linked_colorbar(ax: Axes) -> Colorbar | None:
    for artist in (*ax.collections, *ax.images):
        colorbar = getattr(artist, "colorbar", None)
        if isinstance(colorbar, Colorbar):
            return colorbar
    return None


def _relative_axes_bounds(
    host_ax: Axes, helper_ax: Axes
) -> tuple[float, float, float, float]:
    host_box = host_ax.get_position().frozen()
    helper_box = helper_ax.get_position().frozen()
    return (
        float((helper_box.x0 - host_box.x0) / host_box.width),
        float((helper_box.y0 - host_box.y0) / host_box.height),
        float(helper_box.width / host_box.width),
        float(helper_box.height / host_box.height),
    )


def _bbox_is_within(fig_bbox, artist_bbox, *, pad: float = 0.8) -> bool:
    return (
        artist_bbox.x0 >= fig_bbox.x0 - pad
        and artist_bbox.y0 >= fig_bbox.y0 - pad
        and artist_bbox.x1 <= fig_bbox.x1 + pad
        and artist_bbox.y1 <= fig_bbox.y1 + pad
    )


@pytest.fixture(scope="module")
def scanpy_blobs() -> tuple[Any, ad.AnnData]:
    sc = pytest.importorskip("scanpy")
    blobs = sc.datasets.blobs()
    rng = np.random.default_rng(0)
    blobs.obs["mitf"] = rng.random(blobs.shape[0])
    blobs.obs["axl"] = rng.random(blobs.shape[0])
    sc.pp.neighbors(blobs)
    sc.tl.umap(blobs, random_state=0)
    return sc, blobs


def test_slopeplot_autofit_keeps_axes_within_figure() -> None:
    slope_df = pd.DataFrame(
        {
            "site": ["site1", "site1", "site2", "site2", "site3", "site3"] * 5,
            "value": [
                1.0,
                2.0,
                2.0,
                1.0,
                1.5,
                1.7,
                1.2,
                1.8,
                2.1,
                1.4,
                1.1,
                2.2,
                0.8,
                1.4,
                2.2,
                1.6,
                0.7,
                2.3,
                0.2,
                1.5,
                2.5,
                1.7,
                0.9,
                2.6,
                -0.2,
                1.1,
                3.0,
                1.8,
                0.3,
                2.8,
            ],
            "label": ["healthy", "disease"] * 15,
        }
    )

    with cns.settings.context(figure_autofit=True):
        cns.figure(150, 150)
        ax = cns.slopeplot(slope_df, x="site", y="value", hue="label")
        ax.set_title("Basic Slope Plot", pad=15)

        fig = plt.gcf()
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()

        assert _bbox_is_within(fig.bbox, ax.get_window_extent(renderer=renderer))


def test_survival_plots(
    survival_df: pd.DataFrame,
    survival_three_group_df: pd.DataFrame,
    competing_risk_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    cns.figure(120, 120)
    with caplog.at_level(logging.INFO, logger="cnsplots"):
        ax = cns.survivalplot(
            survival_df, "time", "event", "group", hue_order=["Treatment", "Control"]
        )
    assert ax.get_ylabel() == "Overall survival probability"
    assert "HR =" in ax.texts[0].get_text()
    assert "multivariate log-rank test" in caplog.text

    cns.figure(120, 120)
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="cnsplots"):
        ax2 = cns.survivalplot(survival_three_group_df, "time", "event", "group")
    assert ax2.get_xlabel() == "Time (Years)"
    assert "trend" in caplog.text

    added: dict[str, object] = {}
    import lifelines.plotting as lifelines_plotting

    monkeypatch.setattr(
        lifelines_plotting,
        "add_at_risk_counts",
        lambda *fitters, **kwargs: added.update({"fitters": fitters, **kwargs}),
    )
    cns.figure(120, 120)
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="cnsplots"):
        ax3 = cns.cumulativeincidenceplot(
            competing_risk_df,
            "time",
            "event",
            "group",
            show_risk_table=True,
            xticks=[0, 2, 4, 6, 8],
        )
    assert list(ax3.get_xticks()) == [0, 2, 4, 6, 8]
    assert added["rows_to_show"] == ["At risk"]
    assert "Gray's test" in caplog.text

    cns.figure(120, 120)
    single_group = competing_risk_df[competing_risk_df["group"] == "A"].copy()
    ax4 = cns.cumulativeincidenceplot(single_group, "time", "event", "group")
    assert ax4 is plt.gca()


def test_confusionplot_metrics_and_errors(confusion_df: pd.DataFrame) -> None:
    cns.figure(120, 120)
    ax = cns.confusionplot(
        confusion_df,
        x="pred",
        y="truth",
        add_pvalue=True,
        x_order=["neg", "pos"],
        y_order=["neg", "pos"],
        positive_x="pos",
        positive_y="pos",
    )
    assert ax.get_xlabel() == "pred"
    assert len(plt.gcf().axes) == 2
    stats_ax = plt.gcf().axes[1]
    assert len(stats_ax.texts) == 1
    assert stats_ax.texts[0].get_position() == pytest.approx((-0.25, -1.5))

    cns.figure(120, 120)
    cns.confusionplot(
        confusion_df,
        x="pred",
        y="truth",
        add_pvalue=True,
        x_order=["neg", "pos"],
        y_order=["neg", "pos"],
        pvalue_x_pad=0.4,
        pvalue_y_pad=2.2,
    )
    custom_stats_ax = plt.gcf().axes[1]
    assert custom_stats_ax.texts[0].get_position() == pytest.approx((-0.4, -2.2))

    cns.figure(120, 120)
    ax2 = cns.confusionplot(confusion_df, x="pred", y="truth", annot=False)
    assert ax2 is plt.gca()

    legacy_confusionplot = cast(Any, cns.confusionplot)
    with pytest.raises(TypeError, match="pvalue_pad"):
        legacy_confusionplot(
            confusion_df,
            x="pred",
            y="truth",
            add_pvalue=True,
            pvalue_pad=1.5,
        )

    with pytest.raises(ValueError, match="2x2 confusion matrix"):
        cns.confusionplot(
            pd.DataFrame({"pred": ["a", "b", "c"], "truth": ["a", "b", "c"]}),
            x="pred",
            y="truth",
            add_pvalue=True,
        )

    with pytest.raises(ValueError, match="Could not find negative label in y_order"):
        cns.confusionplot(
            confusion_df,
            x="pred",
            y="truth",
            add_pvalue=True,
            x_order=["neg", "pos"],
            y_order=["pos"],
            positive_y="pos",
        )

    with pytest.raises(ValueError, match="2x2 confusion matrix"):
        cns.confusionplot(
            confusion_df,
            x="pred",
            y="truth",
            add_pvalue=True,
            x_order=["pos"],
            y_order=["neg", "pos"],
            positive_x="pos",
        )

    with pytest.raises(ValueError, match="Categorical categories cannot be null"):
        cns.confusionplot(
            pd.DataFrame({"pred": ["neg", "pos"], "truth": ["neg", np.nan]}),
            x="pred",
            y="truth",
        )


def test_heatmap_and_dotplot(
    heatmap_adata: ad.AnnData,
    dotplot_df: pd.DataFrame,
) -> None:
    cns.figure(180, 180)
    cmp = cns.heatmapplot(
        heatmap_adata,
        layer="scaled",
        row_annotation=["cluster", "score"],
        col_annotation=["pathway", "importance"],
        row_split="cluster",
        col_split="pathway",
        row_cluster=True,
        col_cluster=True,
        colors={"cluster": {"A": "#111111", "B": "#222222"}},
        cmap="parula",
    )
    assert cmp.ax_heatmap is not None
    heatmap_colorbars = [cbar for cbar in cmp.cbars if isinstance(cbar, Colorbar)]
    heatmap_legends = [obj for obj in cmp.cbars if isinstance(obj, Legend)]
    assert len(heatmap_colorbars) == 3
    assert {legend.get_title().get_text() for legend in heatmap_legends} == {
        "cluster",
        "pathway",
    }

    cns.figure(180, 180)
    cmp2 = cns.heatmapplot(
        heatmap_adata,
        row_annotation=["cluster"],
        col_annotation=["pathway"],
        colors={"cluster": {"missing": "#111111"}},
        cmap="Set1",
    )
    assert cmp2.ax_heatmap is not None

    cns.figure(160, 160)
    dp = cns.dotplot(
        dotplot_df,
        x="sample",
        y="gene",
        color="mean_expr",
        size="pct_expr",
        value="score",
    )
    assert dp.ax_heatmap is not None
    assert dp.hm_ax is dp.heatmap_axes[-1, 0]
    assert dp.legend_ax is not None
    assert dp.cbar_ax is not None

    cns.figure(160, 160)
    with pytest.raises(ValueError, match="Length mismatch"):
        cns.dotplot(
            dotplot_df[["sample", "gene", "mean_expr", "pct_expr"]],
            x="sample",
            y="gene",
            color="mean_expr",
            size="pct_expr",
        )

    with cns.settings.context(fontsize_legend=13, ytick_color="#cc2233"):
        cns.figure(180, 180)
        cmp3 = cns.heatmapplot(
            heatmap_adata,
            layer="scaled",
            row_annotation=["cluster"],
            col_annotation=["pathway"],
            cmap="parula",
        )
        heatmap_cbar = next(cbar for cbar in cmp3.cbars if isinstance(cbar, Colorbar))
        assert {tick.get_fontsize() for tick in heatmap_cbar.ax.get_yticklabels()} == {
            13
        }
        assert {tick.get_color() for tick in heatmap_cbar.ax.get_yticklabels()} == {
            "#cc2233"
        }

        cns.figure(160, 160)
        dp2 = cns.dotplot(
            dotplot_df,
            x="sample",
            y="gene",
            color="mean_expr",
            size="pct_expr",
            value="score",
        )
        dotplot_cbar = next(cbar for cbar in dp2.cbars if isinstance(cbar, Colorbar))
        assert {tick.get_fontsize() for tick in dotplot_cbar.ax.get_yticklabels()} == {
            13
        }
        assert {tick.get_color() for tick in dotplot_cbar.ax.get_yticklabels()} == {
            "#cc2233"
        }


def test_dotplot_respects_multipanel_bounds(dotplot_df: pd.DataFrame) -> None:
    mp = cns.multipanel(max_width=180)
    host_ax = mp.panel("A", height=80, width=80, pad_left=5, pad_top=5)
    host_box = host_ax.get_position().frozen()

    dp = cns.dotplot(
        dotplot_df,
        x="sample",
        y="gene",
        color="mean_expr",
        size="pct_expr",
        value="score",
        legend=False,
        xlabel="",
        ylabel="",
        xticklabels_rotation=0,
    )

    assert dp.ax_heatmap is not None
    assert len(dp.cbars) == 0
    assert dp.legend_ax is None
    assert dp.cbar_ax is None

    eps = 1e-9
    for ax in dp.heatmap_axes.flat:
        box = ax.get_position()
        assert box.x0 >= host_box.x0 - eps
        assert box.y0 >= host_box.y0 - eps
        assert box.x1 <= host_box.x1 + eps
        assert box.y1 <= host_box.y1 + eps

    for ax in plt.gcf().axes:
        box = ax.get_position()
        assert box.x0 >= host_box.x0 - eps
        assert box.y0 >= host_box.y0 - eps
        assert box.x1 <= host_box.x1 + eps
        assert box.y1 <= host_box.y1 + eps


def test_dotplot_tracks_multipanel_relayout(dotplot_df: pd.DataFrame) -> None:
    mp = cns.multipanel(max_width=220)
    host_ax = mp.panel("A", height=80, width=80, pad_left=5, pad_top=5)
    initial_host_box = host_ax.get_position().frozen()

    dp = cns.dotplot(
        dotplot_df,
        x="sample",
        y="gene",
        color="mean_expr",
        size="pct_expr",
        value="score",
        legend=False,
        xlabel="",
        ylabel="",
        xticklabels_rotation=0,
    )

    assert dp.ax_heatmap is not None

    mp.newline()
    mp.panel("B", height=200, width=100)

    resized_host_box = host_ax.get_position().frozen()
    heatmap_box = dp.ax_heatmap.get_position().frozen()

    assert resized_host_box.y0 != pytest.approx(initial_host_box.y0)
    assert heatmap_box.bounds == pytest.approx(resized_host_box.bounds)


def test_heatmapplot_tracks_multipanel_relayout(heatmap_adata: ad.AnnData) -> None:
    mp = cns.multipanel(max_width=220)
    host_ax = mp.panel("A", height=80, width=80, pad_left=5, pad_top=5)
    initial_host_box = host_ax.get_position().frozen()

    cmp = cns.heatmapplot(
        heatmap_adata[:, :5].copy(),
        row_cluster=False,
        col_cluster=False,
    )

    assert cmp.ax_heatmap is not None

    mp.newline()
    mp.panel("B", height=200, width=100)

    resized_host_box = host_ax.get_position().frozen()
    heatmap_box = cmp.ax_heatmap.get_position().frozen()

    assert resized_host_box.y0 != pytest.approx(initial_host_box.y0)
    assert heatmap_box.bounds == pytest.approx(resized_host_box.bounds)


def test_histplot_colorbars_align_in_multipanel() -> None:
    data = _bivariate_hist_df()
    mp = cns.multipanel(max_width=400)

    ax_a = mp.panel("A", 120, 140)
    cns.histplot(data=data, x="x", y="y", cbar=True, cmap="hot")
    ax_a.set_title("hot colormap")

    ax_b = mp.panel("B", 120, 140)
    cns.histplot(data=data, x="x", y="y", cbar=True, cmap="BuRd_custom")
    ax_b.set_title("BuRd_custom colormap")

    fig = mp.fig
    assert fig is not None
    fig.canvas.draw()

    for host_ax in (ax_a, ax_b):
        colorbar = host_ax.collections[0].colorbar
        assert colorbar is not None

        host_box = host_ax.get_position().frozen()
        cbar_box = colorbar.ax.get_position().frozen()

        assert cbar_box.y0 == pytest.approx(host_box.y0)
        assert cbar_box.height == pytest.approx(host_box.height)
        assert cbar_box.x0 >= host_box.x1 - 1e-9


def test_histplot_colorbar_tracks_multipanel_relayout() -> None:
    data = _bivariate_hist_df()
    mp = cns.multipanel(max_width=220)
    host_ax = mp.panel("A", height=80, width=80, pad_left=5, pad_top=5)
    cns.histplot(data=data, x="x", y="y", cbar=True, cmap="hot")

    colorbar = host_ax.collections[0].colorbar
    assert colorbar is not None

    fig = mp.fig
    assert fig is not None
    fig.canvas.draw()

    initial_host_box = host_ax.get_position().frozen()
    initial_cbar_box = colorbar.ax.get_position().frozen()

    mp.newline()
    mp.panel("B", height=200, width=100)
    fig.canvas.draw()

    resized_host_box = host_ax.get_position().frozen()
    resized_cbar_box = colorbar.ax.get_position().frozen()

    assert resized_host_box.y0 != pytest.approx(initial_host_box.y0)
    assert resized_cbar_box.y0 != pytest.approx(initial_cbar_box.y0)
    assert resized_cbar_box.y0 == pytest.approx(resized_host_box.y0)
    assert resized_cbar_box.height == pytest.approx(resized_host_box.height)
    assert resized_cbar_box.x0 >= resized_host_box.x1 - 1e-9


def test_histplot_with_explicit_cbar_ax_leaves_it_untouched() -> None:
    data = _bivariate_hist_df()
    mp = cns.multipanel(max_width=220)
    host_ax = mp.panel("A", height=80, width=80, pad_left=5, pad_top=5)
    fig = mp.fig
    assert fig is not None
    cbar_ax = fig.add_axes((0.8, 0.2, 0.05, 0.5))
    initial_cbar_box = cbar_ax.get_position().frozen()

    cns.histplot(
        data=data,
        x="x",
        y="y",
        ax=host_ax,
        cbar=True,
        cbar_ax=cbar_ax,
        cmap="hot",
    )

    mp.newline()
    mp.panel("B", height=200, width=100)
    fig.canvas.draw()

    assert host_ax.collections[0].colorbar is not None
    assert host_ax.collections[0].colorbar.ax is cbar_ax
    assert cbar_ax.get_position().bounds == pytest.approx(initial_cbar_box.bounds)
    assert not hasattr(host_ax, "_cnsplots_detached_axes_layout")


def test_scanpy_umap_colorbars_preserve_linked_geometry_in_multipanel(
    scanpy_blobs: tuple[Any, ad.AnnData],
) -> None:
    sc, blobs = scanpy_blobs
    mp = cns.multipanel(max_width=350)
    cns.setup_scanpy()

    ax_a = mp.panel("A", 120, 120)
    sc.pl.umap(blobs, color="mitf", size=8, ax=ax_a, show=False, cmap="gnuplot")
    ax_a.set_xlabel("UMAP-1")
    ax_a.set_ylabel("UMAP-2")
    ax_a.set_title("MITF")
    colorbar_a = _linked_colorbar(ax_a)
    assert colorbar_a is not None

    ax_b = mp.panel("B", 120, 120)
    sc.pl.umap(blobs, color="axl", size=8, ax=ax_b, show=False, cmap="gnuplot")
    ax_b.set_xlabel("UMAP-1")
    ax_b.set_ylabel("UMAP-2")
    ax_b.set_title("AXL")
    colorbar_b = _linked_colorbar(ax_b)
    assert colorbar_b is not None

    fig = mp.fig
    assert fig is not None
    fig.canvas.draw()

    rendered_a = _relative_axes_bounds(ax_a, colorbar_a.ax)
    rendered_b = _relative_axes_bounds(ax_b, colorbar_b.ax)
    for host_ax, colorbar in ((ax_a, colorbar_a), (ax_b, colorbar_b)):
        host_box = host_ax.get_position().frozen()
        cbar_box = colorbar.ax.get_position().frozen()
        assert cbar_box.y0 == pytest.approx(host_box.y0)
        assert cbar_box.height == pytest.approx(host_box.height)
        assert cbar_box.x0 >= host_box.x1 - 1e-9

    mp.newline()
    mp.panel("C", 120, 120)
    fig.canvas.draw()

    assert _relative_axes_bounds(ax_a, colorbar_a.ax) == pytest.approx(rendered_a)
    assert _relative_axes_bounds(ax_b, colorbar_b.ax) == pytest.approx(rendered_b)
    assert hasattr(ax_a, "_cnsplots_detached_axes_layout")
    assert hasattr(ax_b, "_cnsplots_detached_axes_layout")


def test_scanpy_violin_autofit_keeps_axes_within_figure(
    scanpy_blobs: tuple[Any, ad.AnnData],
) -> None:
    sc, blobs = scanpy_blobs

    with cns.settings.context(figure_autofit=True):
        cns.figure(150, 150)
        cns.setup_scanpy()
        ax = plt.gca()
        sc.pl.violin(
            blobs,
            keys="mitf",
            groupby="blobs",
            ax=ax,
            show=False,
            edgecolor=None,
            stripplot=False,
        )

        fig = plt.gcf()
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()

        assert _bbox_is_within(fig.bbox, ax.get_window_extent(renderer=renderer))


def test_scanpy_umap_colorbar_tracks_multipanel_relayout(
    scanpy_blobs: tuple[Any, ad.AnnData],
) -> None:
    sc, blobs = scanpy_blobs
    mp = cns.multipanel(max_width=220)
    cns.setup_scanpy()
    host_ax = mp.panel("A", height=90, width=90, pad_left=5, pad_top=5)
    sc.pl.umap(blobs, color="mitf", size=8, ax=host_ax, show=False, cmap="gnuplot")

    colorbar = _linked_colorbar(host_ax)
    assert colorbar is not None

    fig = mp.fig
    assert fig is not None
    fig.canvas.draw()
    rendered_relative_box = _relative_axes_bounds(host_ax, colorbar.ax)

    host_box = host_ax.get_position().frozen()
    cbar_box = colorbar.ax.get_position().frozen()
    assert cbar_box.y0 == pytest.approx(host_box.y0)
    assert cbar_box.height == pytest.approx(host_box.height)
    assert cbar_box.x0 >= host_box.x1 - 1e-9

    mp.newline()
    mp.panel("B", height=160, width=100)
    fig.canvas.draw()

    assert _relative_axes_bounds(host_ax, colorbar.ax) == pytest.approx(
        rendered_relative_box
    )


def test_scanpy_categorical_umap_does_not_capture_detached_axes(
    scanpy_blobs: tuple[Any, ad.AnnData],
) -> None:
    sc, blobs = scanpy_blobs
    mp = cns.multipanel(max_width=220)
    cns.setup_scanpy()
    host_ax = mp.panel("A", height=90, width=90)
    sc.pl.umap(blobs, color="blobs", size=8, ax=host_ax, show=False)

    fig = mp.fig
    assert fig is not None
    fig.canvas.draw()

    assert _linked_colorbar(host_ax) is None
    assert not hasattr(host_ax, "_cnsplots_detached_axes_layout")


def test_multipanel_linked_colorbar_tracks_relayout() -> None:
    mp = cns.multipanel(max_width=220)
    host_ax = mp.panel("A", height=90, width=90)
    fig = mp.fig
    assert fig is not None

    scatter = host_ax.scatter([1, 2, 3], [1, 2, 3], c=[0.1, 0.2, 0.3])
    colorbar = fig.colorbar(scatter, ax=host_ax)

    mp.newline()
    mp.panel("B", height=160, width=100)
    fig.canvas.draw()
    rendered_relative_box = _relative_axes_bounds(host_ax, colorbar.ax)

    host_box = host_ax.get_position().frozen()
    cbar_box = colorbar.ax.get_position().frozen()
    assert cbar_box.y0 == pytest.approx(host_box.y0)
    assert cbar_box.height == pytest.approx(host_box.height)
    assert cbar_box.x0 >= host_box.x1 - 1e-9

    mp.newline()
    mp.panel("C", height=120, width=80)
    fig.canvas.draw()

    assert _relative_axes_bounds(host_ax, colorbar.ax) == pytest.approx(
        rendered_relative_box
    )
    assert hasattr(host_ax, "_cnsplots_detached_axes_layout")


def test_multipanel_linked_colorbar_ignores_explicit_cbar_axes() -> None:
    mp = cns.multipanel(max_width=220)
    host_ax = mp.panel("A", height=90, width=90)
    fig = mp.fig
    assert fig is not None

    cbar_ax = fig.add_axes((0.8, 0.2, 0.05, 0.5))
    scatter = host_ax.scatter([1, 2, 3], [1, 2, 3], c=[0.1, 0.2, 0.3])
    colorbar = fig.colorbar(scatter, cax=cbar_ax)
    initial_cbar_box = colorbar.ax.get_position().frozen()

    mp.newline()
    mp.panel("B", height=160, width=100)
    fig.canvas.draw()

    assert colorbar.ax.get_position().bounds == pytest.approx(initial_cbar_box.bounds)
    assert not hasattr(host_ax, "_cnsplots_detached_axes_layout")


def test_gseaplot_colorbar_aligns_with_host_axes_in_multipanel(
    gsea_plot_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_dotplot(
        data: pd.DataFrame,
        cmap: str,
        y: str,
        x: str,
        cutoff: float,
        column: str,
        ax: Axes,
        top_term: int,
        size: float,
    ) -> None:
        scatter = ax.scatter(data[x], np.arange(len(data)), c=data[column], s=20)
        fig = plt.gcf()
        cbar = fig.colorbar(scatter, ax=ax)
        cbar.set_label(column)
        handles = [plt.Line2D([], [], marker="o", linestyle="none", color="black")]
        ax.legend(handles, ["20"], title="size")

    monkeypatch.setitem(
        sys.modules, "gseapy", types.SimpleNamespace(dotplot=fake_dotplot)
    )

    mp = cns.multipanel(max_width=240)
    host_ax = mp.panel("A", height=90, width=100)
    plt.sca(host_ax)
    cns.gseaplot(gsea_plot_df, y="Clean_Term", color="NES", top_term=2)

    colorbar = _linked_colorbar(host_ax)
    assert colorbar is not None

    fig = mp.fig
    assert fig is not None
    fig.canvas.draw()

    rendered_relative_box = _relative_axes_bounds(host_ax, colorbar.ax)
    host_box = host_ax.get_position().frozen()
    cbar_box = colorbar.ax.get_position().frozen()

    assert cbar_box.y0 == pytest.approx(host_box.y0)
    assert cbar_box.height == pytest.approx(host_box.height)
    assert cbar_box.x0 >= host_box.x1 - 1e-9
    assert cbar_box.x0 - host_box.x1 < host_box.width * 0.2

    mp.newline()
    mp.panel("B", height=120, width=100)
    fig.canvas.draw()

    assert _relative_axes_bounds(host_ax, colorbar.ax) == pytest.approx(
        rendered_relative_box
    )
    assert hasattr(host_ax, "_cnsplots_detached_axes_layout")


def test_genomics_plots(
    volcano_df: pd.DataFrame,
    gsea_plot_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_adjust = types.SimpleNamespace(adjust_text=lambda *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "adjustText", fake_adjust)

    cns.figure(120, 120)
    ax = cns.volcanoplot(volcano_df)
    assert ax.get_xlabel() == "log2(fold change)"
    assert {text.get_text() for text in ax.texts} == {
        "GENE1",
        "GENE2",
        "GENE5",
        "GENE6",
    }

    cns.figure(120, 120)
    ax2 = cns.volcanoplot(volcano_df, n_show=1)
    assert ax2.get_ylabel() == "–log10(adjusted p-value)"
    assert {text.get_text() for text in ax2.texts} == {"GENE1", "GENE6"}

    cns.figure(120, 120)
    ax3 = cns.volcanoplot(volcano_df, n_show=0)
    assert len(ax3.texts) == 0

    cns.figure(120, 120)
    ax4 = cns.volcanoplot(volcano_df, show_list=["GENE1", "GENE6"], n_show=1)
    assert ax4.get_ylabel() == "–log10(adjusted p-value)"
    assert {text.get_text() for text in ax4.texts} == {"GENE1", "GENE6"}

    with pytest.raises(TypeError, match="Parameter 'n_show' must be an integer"):
        cns.volcanoplot(volcano_df, n_show=1.5)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Parameter 'n_show' must be non-negative"):
        cns.volcanoplot(volcano_df, n_show=-1)

    with pytest.raises(TypeError, match="Parameter 'n_show' must be an integer"):
        cns.volcanoplot(volcano_df, n_show=True)

    def fake_dotplot(
        data: pd.DataFrame,
        cmap: str,
        y: str,
        x: str,
        cutoff: float,
        column: str,
        ax: Axes,
        top_term: int,
        size: float,
    ) -> None:
        scatter = ax.scatter(data[x], np.arange(len(data)), c=data[column], s=20)
        fig = plt.gcf()
        cbar = fig.colorbar(scatter, ax=ax)
        cbar.set_label(column)
        handles = [plt.Line2D([], [], marker="o", linestyle="none", color="black")]
        ax.legend(handles, ["20"], title="size")

    monkeypatch.setitem(
        sys.modules, "gseapy", types.SimpleNamespace(dotplot=fake_dotplot)
    )
    cns.figure(160, 140)
    ax5 = cns.gseaplot(gsea_plot_df, y="Clean_Term", color="NES", top_term=2)
    assert ax5.get_xlabel() == "Normalized Enrichment Score (NES)"


def test_sets_validation_errors(sets_fixture: dict[str, set[int]]) -> None:
    with pytest.raises(TypeError, match="must be a dictionary"):
        cns.upsetplot([])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cannot be empty"):
        cns.upsetplot({})
    with pytest.raises(TypeError, match="must be a list"):
        cns.vennplot(tuple(sets_fixture.values()), labels=["A", "B"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must contain 2 or 3 sets"):
        cns.vennplot([set()], labels=["A"])
    with pytest.raises(ValueError, match="Length of 'labels'"):
        cns.vennplot([set(), set()], labels=["A"])
