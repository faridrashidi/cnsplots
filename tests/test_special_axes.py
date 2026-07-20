from __future__ import annotations

import inspect
import sys
import types
import warnings

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.axes import Axes
from matplotlib.transforms import Bbox

import cnsplots as cns
import cnsplots._utils as plot_utils


SPECIAL_PLOT_NAMES = [
    "placeholderplot",
    "sankeyplot",
    "phyloplot",
    "forestplot",
    "rocplot",
    "heatmapplot",
    "dotplot",
    "confusionplot",
    "volcanoplot",
    "gseaplot",
    "survivalplot",
    "cumulativeincidenceplot",
    "upsetplot",
    "vennplot",
]


def _artist_count(ax: Axes) -> int:
    return len(ax.lines) + len(ax.collections) + len(ax.patches) + len(ax.texts)


def _assert_within(host_box: Bbox, axes: list[Axes]) -> None:
    eps = 1e-9
    for ax in axes:
        box = ax.get_position()
        assert box.x0 >= host_box.x0 - eps
        assert box.y0 >= host_box.y0 - eps
        assert box.x1 <= host_box.x1 + eps
        assert box.y1 <= host_box.y1 + eps


def test_host_relative_axes_locator_handles_non_layout_axes() -> None:
    fig, host_ax = plt.subplots()
    host_ax.set_position((0.1, 0.1, 0, 0.5))
    plot_utils._anchor_axes_to_host(host_ax, [])

    host_ax.set_position((0.1, 0.1, 0.5, 0.5))
    other_fig, other_ax = plt.subplots()
    plot_utils._anchor_axes_to_host(host_ax, [host_ax, other_ax])
    assert not hasattr(host_ax, "_cnsplots_sync_embedded_axes")

    child_ax = fig.add_axes((0.2, 0.2, 0.2, 0.2))
    plot_utils._anchor_axes_to_host(host_ax, [child_ax])
    child_ax.remove()

    sync = getattr(host_ax, "_cnsplots_sync_embedded_axes")
    sync()

    zero_child_ax = fig.add_axes((0.2, 0.2, 0, 0))
    plot_utils._anchor_axes_to_host(host_ax, [zero_child_ax])

    free_host_ax = fig.add_axes((0.1, 0.1, 0.5, 0.5))
    free_child_ax = fig.add_axes((0.2, 0.2, 0.2, 0.2))
    plot_utils._anchor_axes_to_host(free_host_ax, [free_child_ax])
    assert free_child_ax.get_subplotspec() is None
    assert not free_child_ax.get_in_layout()
    plt.close(other_fig)


def test_special_plot_axes_are_explicit_keyword_only_parameters() -> None:
    for name in SPECIAL_PLOT_NAMES:
        parameter = inspect.signature(getattr(cns, name)).parameters["ax"]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is None


def test_single_axes_special_plots_use_supplied_axes(
    sankey_df: pd.DataFrame,
    roc_df: pd.DataFrame,
    volcano_df: pd.DataFrame,
    survival_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "adjustText",
        types.SimpleNamespace(adjust_text=lambda *args, **kwargs: None),
    )
    plotters = [
        lambda ax: cns.placeholderplot("Reserved", ax=ax),
        lambda ax: cns.sankeyplot(sankey_df, x="source", y="target", ax=ax),
        lambda ax: cns.rocplot(roc_df, "truth", "model_a", ax=ax),
        lambda ax: cns.volcanoplot(volcano_df, n_show=1, ax=ax),
        lambda ax: cns.survivalplot(
            survival_df,
            "time",
            "event",
            "group",
            ax=ax,
        ),
    ]

    for plotter in plotters:
        _, (target_ax, current_ax) = plt.subplots(1, 2)
        plt.sca(current_ax)

        result = plotter(target_ax)

        assert result is target_ax
        assert _artist_count(target_ax) > 0
        assert _artist_count(current_ax) == 0
        plt.close(target_ax.figure)


def test_forestplot_appends_pvalue_panel_to_supplied_axes() -> None:
    model = types.SimpleNamespace(
        name="cox",
        hue=None,
        results=pd.DataFrame(
            {
                "display_label": ["Age", "Stage"],
                "exp(coef)": [1.2, 0.9],
                "log10_pvalue": [1.1, 0.7],
                "exp(coef) lower_err": [0.1, 0.1],
                "exp(coef) upper_err": [0.2, 0.15],
                "hue_group": ["All", "All"],
            }
        ),
    )
    fig, (target_ax, current_ax) = plt.subplots(1, 2)
    host_box = target_ax.get_position().frozen()
    plt.sca(current_ax)

    result = cns.forestplot(model, ax=target_ax)
    fig.canvas.draw()

    assert result is target_ax
    assert _artist_count(current_ax) == 0
    pvalue_ax = fig.axes[-1]
    assert pvalue_ax is not current_ax
    assert pvalue_ax.figure is fig
    assert pvalue_ax.get_position().x0 > target_ax.get_position().x1
    _assert_within(host_box, [target_ax, pvalue_ax])


def test_confusionplot_anchors_stats_overlay_to_supplied_axes(
    confusion_df: pd.DataFrame,
) -> None:
    fig, (target_ax, current_ax) = plt.subplots(1, 2)
    plt.sca(current_ax)

    result = cns.confusionplot(
        confusion_df,
        x="pred",
        y="truth",
        add_pvalue=True,
        ax=target_ax,
    )
    fig.canvas.draw()

    assert result is target_ax
    assert _artist_count(current_ax) == 0
    stats_ax = fig.axes[-1]
    assert stats_ax is not current_ax
    assert stats_ax.get_position().bounds == pytest.approx(
        target_ax.get_position().bounds
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig.tight_layout()
    assert not any("not compatible with tight_layout" in str(w.message) for w in caught)
    fig.canvas.draw()
    assert stats_ax.get_position().bounds == pytest.approx(
        target_ax.get_position().bounds
    )


def test_heatmap_backends_use_supplied_host_axes(
    heatmap_adata: ad.AnnData,
    dotplot_df: pd.DataFrame,
) -> None:
    fig, (heatmap_ax, current_ax) = plt.subplots(1, 2, layout="constrained")
    layout_engine = fig.get_layout_engine()
    plt.sca(current_ax)

    heatmap = cns.heatmapplot(
        heatmap_adata,
        row_annotation=["score"],
        row_cluster=False,
        col_cluster=False,
        ax=heatmap_ax,
    )
    fig.canvas.draw()

    assert heatmap.ax is heatmap_ax
    assert heatmap.cbars
    assert fig.get_layout_engine() is layout_engine
    assert _artist_count(current_ax) == 0
    _assert_within(
        heatmap_ax.get_position(original=True).frozen(),
        [ax for ax in fig.axes if ax not in (heatmap_ax, current_ax)],
    )
    plt.close(fig)

    fig, (dot_ax, current_ax) = plt.subplots(1, 2, layout="constrained")
    layout_engine = fig.get_layout_engine()
    plt.sca(current_ax)
    dot = cns.dotplot(
        dotplot_df,
        x="sample",
        y="gene",
        color="mean_expr",
        size="pct_expr",
        value="score",
        ax=dot_ax,
    )
    fig.canvas.draw()

    assert dot.ax is dot_ax
    assert dot.cbars
    assert fig.get_layout_engine() is layout_engine
    assert _artist_count(current_ax) == 0
    _assert_within(
        dot_ax.get_position(original=True).frozen(),
        [ax for ax in fig.axes if ax not in (dot_ax, current_ax)],
    )

    normal_fig, normal_ax = plt.subplots()
    assert normal_fig.get_layout_engine() is None
    normal_heatmap = cns.heatmapplot(
        heatmap_adata,
        row_annotation=["score"],
        row_cluster=False,
        col_cluster=False,
        ax=normal_ax,
    )
    normal_fig.canvas.draw()

    assert normal_fig.get_layout_engine() is None
    _assert_within(
        normal_ax.get_position().frozen(), list(normal_heatmap.heatmap_axes.flat)
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        normal_fig.tight_layout()
    assert not any("not compatible with tight_layout" in str(w.message) for w in caught)


def test_gseaplot_uses_supplied_axes_and_figure(
    gsea_plot_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_dotplot(
        data: pd.DataFrame,
        cmap: object,
        y: str,
        x: str,
        cutoff: float,
        column: str,
        ax: Axes,
        top_term: int,
        size: float,
    ) -> None:
        scatter = ax.scatter(data[x], np.arange(len(data)), c=data[column])
        ax.figure.colorbar(scatter, ax=ax)
        handle = plt.Line2D([], [], marker="o", linestyle="none", color="black")
        ax.legend([handle], ["20"], title="size")

    monkeypatch.setitem(
        sys.modules,
        "gseapy",
        types.SimpleNamespace(dotplot=fake_dotplot),
    )
    fig, (target_ax, current_ax) = plt.subplots(1, 2)
    plt.sca(current_ax)

    result = cns.gseaplot(gsea_plot_df, y="Clean_Term", ax=target_ax)

    assert result is target_ax
    assert _artist_count(target_ax) > 0
    assert _artist_count(current_ax) == 0
    assert fig.axes[-1].figure is fig


def test_cumulativeincidence_risk_table_uses_supplied_axes_figure(
    competing_risk_df: pd.DataFrame,
) -> None:
    fig, (target_ax, current_ax) = plt.subplots(1, 2)
    plt.sca(current_ax)

    result = cns.cumulativeincidenceplot(
        competing_risk_df,
        "time",
        "event",
        "group",
        show_risk_table=True,
        ax=target_ax,
    )

    assert result is target_ax
    assert _artist_count(current_ax) == 0
    assert fig.axes[-1].figure is fig
    assert fig.axes[-1] is not current_ax


def test_phyloplot_uses_and_returns_supplied_heatmap_axes(
    phylo_adata: ad.AnnData,
) -> None:
    fig, (target_ax, current_ax) = plt.subplots(1, 2)
    host_box = target_ax.get_position().frozen()
    plt.sca(current_ax)

    result = cns.phyloplot(phylo_adata, ax=target_ax)
    fig.canvas.draw()

    assert result is target_ax
    assert _artist_count(target_ax) > 0
    assert _artist_count(current_ax) == 0
    phylo_axes = [ax for ax in fig.axes if ax is not current_ax]
    assert len(phylo_axes) == 5
    _assert_within(host_box, phylo_axes)


def test_set_plots_use_supplied_axes(
    sets_fixture: dict[str, set[int]],
) -> None:
    fig, (upset_ax, current_ax) = plt.subplots(1, 2)
    initial_size = fig.get_size_inches().copy()
    initial_facecolor = fig.patch.get_facecolor()
    initial_alpha = fig.patch.get_alpha()
    plt.sca(current_ax)

    axes = cns.upsetplot(sets_fixture, ax=upset_ax, min_subset_size=1)
    fig.canvas.draw()

    assert all(ax is None or ax.figure is fig for ax in axes.values())
    assert _artist_count(current_ax) == 0
    np.testing.assert_allclose(fig.get_size_inches(), initial_size)
    assert fig.patch.get_facecolor() == initial_facecolor
    assert fig.patch.get_alpha() == initial_alpha
    _assert_within(
        upset_ax.get_position().frozen(),
        [ax for ax in axes.values() if ax is not None],
    )

    venn_fig, (venn_ax, current_ax) = plt.subplots(1, 2)
    plt.sca(current_ax)
    diagram = cns.vennplot(
        list(sets_fixture.values())[:2],
        labels=["A", "B"],
        ax=venn_ax,
    )

    assert diagram.get_label_by_id("A").get_text() == "A"
    assert _artist_count(venn_ax) > 0
    assert _artist_count(current_ax) == 0
    plt.close(venn_fig)


def test_upsetplot_rejects_conflicting_embedding_options(
    sets_fixture: dict[str, set[int]],
) -> None:
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="either 'ax' or 'fig'"):
        cns.upsetplot(sets_fixture, ax=ax, fig=fig)
    with pytest.raises(ValueError, match="element_size"):
        cns.upsetplot(sets_fixture, ax=ax, element_size=17)


def test_upsetplot_tracks_constrained_layout_host(
    sets_fixture: dict[str, set[int]],
) -> None:
    fig, (host_ax, other_ax) = plt.subplots(1, 2, layout="constrained")
    layout_engine = fig.get_layout_engine()

    axes = cns.upsetplot(sets_fixture, ax=host_ax, min_subset_size=1)
    fig.canvas.draw()

    assert fig.get_layout_engine() is layout_engine
    _assert_within(
        host_ax.get_position().frozen(),
        [ax for ax in axes.values() if ax is not None],
    )

    initial_host_box = host_ax.get_position().frozen()
    fig.set_size_inches(9, 4)
    fig.canvas.draw()

    assert host_ax.get_position().bounds != pytest.approx(initial_host_box.bounds)
    _assert_within(
        host_ax.get_position().frozen(),
        [ax for ax in axes.values() if ax is not None],
    )
