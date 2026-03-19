from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
import sys
import types

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import cnsplots as cns
from cnsplots import _methods
from cnsplots.helpers import _cmprsk, _heatmap as helper_heatmap, _phylo, _sankey


def test_cox_model_fit_and_forestplot(survival_df: pd.DataFrame) -> None:
    model = cns.CoxModel(
        survival_df,
        duration="time",
        event="event",
        variates=["age", "C(stage)"],
    )
    model.fit()
    assert set(model.results.columns) == {
        "display_label",
        "exp(coef)",
        "exp(coef) lower_err",
        "exp(coef) upper_err",
        "exp(coef) lower 95%",
        "exp(coef) upper 95%",
        "log10_pvalue",
        "analysis",
        "covariate",
        "hue_group",
        "p",
    }

    model_hue = cns.CoxModel(
        survival_df,
        duration="time",
        event="event",
        variates=["age"],
        hue="group",
    )
    model_hue.fit()
    cns.figure(120, 120)
    ax = cns.forestplot(model_hue)
    assert ax.get_xlabel() == "Hazard ratio (95% CI)"


def test_logistic_model_paths(
    monkeypatch: pytest.MonkeyPatch,
    roc_df: pd.DataFrame,
    capsys: pytest.CaptureFixture[str],
) -> None:
    data = pd.concat(
        [
            roc_df.rename(
                columns={"truth": "event", "model_a": "score", "model_b": "other"}
            )
        ]
        * 4,
        ignore_index=True,
    )
    data["group"] = ["A"] * 12 + ["B"] * 12

    model = cns.LogisticModel(data, event="event", variates=["score"])
    auc, lower, upper = model._compute_auc_ci(
        data["event"].values, data["score"].values, n_bootstrap=10
    )
    assert lower <= auc <= upper

    monkeypatch.setattr(
        cns.LogisticModel,
        "_compute_auc_ci",
        lambda self, y_true, y_pred_proba, n_bootstrap=1000, alpha=0.05: (
            0.8,
            0.7,
            0.9,
        ),
    )
    model.fit()
    assert list(model.results.columns) == [
        "predictor",
        "auc",
        "lower_ci",
        "upper_ci",
        "hue_group",
    ]

    data_bad = data.copy()
    data_bad.loc[data_bad["group"] == "A", "event"] = 1
    model_hue = cns.LogisticModel(
        data_bad, event="event", variates=["score", "missing_col"], hue="group"
    )
    model_hue.fit()
    out = capsys.readouterr().out
    assert "Warning: No variance in outcome" in out
    assert "Error fitting missing_col" in out

    model_empty = cns.LogisticModel(
        data_bad[data_bad["group"] == "A"],
        event="event",
        variates=["score"],
        hue="group",
    )
    model_empty.fit()
    assert "No successful model fits" in capsys.readouterr().out

    cns.figure(120, 120)
    ax = cns.forestplot(model, add_pvalue=False)
    assert ax.get_xlabel() == "AUC (95% CI)"


def test_forestplot_validation_errors() -> None:
    with pytest.raises(ValueError, match="results"):
        cns.forestplot(types.SimpleNamespace(name="cox"))
    with pytest.raises(ValueError, match="name"):
        cns.forestplot(types.SimpleNamespace(results=pd.DataFrame({"a": [1]})))
    with pytest.raises(ValueError, match="Data is empty"):
        cns.forestplot(types.SimpleNamespace(name="cox", results=pd.DataFrame()))


def test_prerank_with_mocked_gseapy(
    fake_gseapy_result: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = pd.DataFrame({"gene": ["a", "b", "c"], "rank": [3, 2, 1]})
    fake_gp = types.SimpleNamespace(prerank=lambda **kwargs: fake_gseapy_result)
    monkeypatch.setitem(sys.modules, "gseapy", fake_gp)
    res = _methods.prerank(
        data, {"set": ["A", "B"]}, "gene", "rank", permutation_num=10
    )
    assert list(res["Clean_Term"]) == [
        "NF-κB Signaling",
        "DNA Repair",
        "Reactome IL-6 and TGF Signaling",
    ]


def test_prerank_import_error_prints(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> object:
        if name == "gseapy":
            raise ImportError("missing")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(UnboundLocalError):
        _methods.prerank(
            pd.DataFrame({"gene": ["a"], "rank": [1]}), {"set": ["A"]}, "gene", "rank"
        )
    assert "pip install gseapy" in capsys.readouterr().out


def test_competing_risk_helper(competing_risk_df: pd.DataFrame) -> None:
    pvalue = _cmprsk.cuminc(
        competing_risk_df["time"],
        competing_risk_df["event"],
        competing_risk_df["group"],
    )
    assert 0 <= pvalue <= 1


def test_sankey_helpers(
    sankey_df: pd.DataFrame, capsys: pytest.CaptureFixture[str]
) -> None:
    _sankey.check_data_matches_labels(
        ["Start", "Middle", "End"], sankey_df["source"], "left"
    )
    with pytest.raises(ValueError, match="left labels and data do not match"):
        _sankey.check_data_matches_labels(["Other"], sankey_df["source"], "left")

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
    out = capsys.readouterr().out
    assert "deprecated" in out

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
    ax3.set_position([0.1, 0.1, 0, 0])
    ax3.figure.canvas.draw()
    helper_heatmap._stabilize_detached_legends([zero_size_legend])
