from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
import sys
import types
from pathlib import Path
from typing import Any

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.patches import PathPatch

import cnsplots as cns
from cnsplots import _methods, _setup, _svg, _utils, _validation
from cnsplots.helpers import _heatmap as helper_heatmap, _phylo, _sankey
from cnsplots.plots import _distribution as dist_mod
from cnsplots.plots import _genomics as genomics_mod
from cnsplots.plots import _heatmap as heatmap_mod
from cnsplots.plots import _specialized as specialized_mod


def test_methods_gap_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCoxPHFitter:
        def __init__(self) -> None:
            self.summary = pd.DataFrame(
                {
                    "exp(coef)": [1.0],
                    "exp(coef) lower 95%": [0.9],
                    "exp(coef) upper 95%": [1.1],
                    "p": [0.5],
                    "covariate": ["123"],
                },
                index=pd.Index(["123"]),
            )

        def fit(
            self, data: pd.DataFrame, duration_col: str, event_col: str, formula: str
        ) -> None:
            return None

    monkeypatch.setattr(_methods.ll, "CoxPHFitter", FakeCoxPHFitter)
    model = cns.CoxModel(
        pd.DataFrame({"time": [1, 2], "event": [1, 0], "x": [0, 1]}),
        duration="time",
        event="event",
        variates=["123"],
    )
    model.fit()
    assert model.results is not None
    assert model.results["display_label"].isna().all()

    samples = [np.array([0, 0, 0, 0]), np.array([0, 1, 2, 3])]

    def fake_choice(n: int, size: int, replace: bool = True) -> np.ndarray:
        return samples.pop(0)

    monkeypatch.setattr(_methods.np.random, "choice", fake_choice)
    logistic = cns.LogisticModel(
        pd.DataFrame({"event": [0, 0, 1, 1]}), event="event", variates=["1"]
    )
    auc, lower, upper = logistic._compute_auc_ci(
        np.array([0, 0, 1, 1]),
        np.array([0.1, 0.2, 0.8, 0.9]),
        n_bootstrap=2,
    )
    assert lower <= auc <= upper


def test_multipanel_gap_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    mp = cns.multipanel()
    mp._panels = [{"label": "A", "_below": "missing"}]
    assert mp._get_panel_position(0) == (0, 0)

    mp2 = cns.multipanel()
    mp2._panels = [
        {
            "label": "A",
            "width": 10,
            "height": 10,
            "label_left": 0,
            "label_top": 0,
            "pad_left": 0,
            "pad_top": 0,
            "margin_left": 0,
            "margin_top": 0,
            "margin_right": 0,
            "margin_bottom": 0,
        }
    ]
    assert mp2._get_panel_position(0) == (0, 0)

    mp3 = cns.multipanel(max_width=200)
    mp3.panel(None, width=40, height=20)
    mp3.panel("B", width=40, height=20)
    assert mp3._get_panel_position(1)[0] > 0

    mp4 = cns.multipanel()
    monkeypatch.setattr(mp4, "_create_or_update_figure", lambda: None)
    with pytest.raises(RuntimeError, match="axes was not created"):
        mp4.panel("A", width=10, height=10)


def test_setup_gap_coverage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    real_import = builtins.__import__
    real_exists = Path.exists

    def fake_exists(self: Path) -> bool:
        if str(self) == "/System/Library/Fonts/Helvetica.ttc":
            return True
        if str(self).endswith("Helvetica-Bold.ttf"):
            return False
        return real_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(_setup, "_HELVETICA_BOLD_REGISTERED", False)
    monkeypatch.setattr(_setup.sys, "platform", "darwin")
    monkeypatch.setattr(_setup.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        _setup.fm,
        "fontManager",
        types.SimpleNamespace(ttflist=[], addfont=lambda path: None),
    )

    def missing_fonttools(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> object:
        if name == "fontTools.ttLib":
            raise ImportError("missing")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", missing_fonttools)
    _setup._ensure_helvetica_bold()

    class FakeNameTable:
        def __init__(self, family: str, subfamily: str) -> None:
            self.family = family
            self.subfamily = subfamily

        def getDebugName(self, index: int) -> str:
            return self.family if index == 1 else self.subfamily

    class FakeRegularFace(dict):
        def __init__(self) -> None:
            super().__init__(name=FakeNameTable("Helvetica", "Regular"))

        def save(self, path: str) -> None:
            raise AssertionError("regular face should not be saved")

    class NoBoldCollection:
        def __init__(self, path: str) -> None:
            self.fonts = [FakeRegularFace()]

    def import_fonttools_without_bold(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> object:
        if name == "fontTools.ttLib":
            return types.SimpleNamespace(TTCollection=NoBoldCollection)
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_fonttools_without_bold)
    _setup._ensure_helvetica_bold()

    class FakeFace(dict):
        def __init__(self) -> None:
            super().__init__(name=FakeNameTable("Helvetica", "Bold"))
            self.saved = False

        def save(self, path: str) -> None:
            self.saved = True

    face = FakeFace()

    class FakeCollection:
        def __init__(self, path: str) -> None:
            self.fonts = [face]

    font_manager = types.SimpleNamespace(
        ttflist=[],
        addfont=lambda path: font_manager.ttflist.append(
            types.SimpleNamespace(name="Helvetica", weight=700)
        ),
    )
    monkeypatch.setattr(_setup.fm, "fontManager", font_manager)

    def import_fonttools(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> object:
        if name == "fontTools.ttLib":
            return types.SimpleNamespace(TTCollection=FakeCollection)
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_fonttools)
    _setup._ensure_helvetica_bold()
    assert _setup._HELVETICA_BOLD_REGISTERED is True
    assert face.saved is True

    monkeypatch.setattr(_setup, "_HELVETICA_BOLD_REGISTERED", False)
    bad_font_manager = types.SimpleNamespace(
        ttflist=[], addfont=lambda path: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    monkeypatch.setattr(_setup.fm, "fontManager", bad_font_manager)
    _setup._ensure_helvetica_bold()


def test_svg_gap_coverage() -> None:
    class FakeText:
        def getparent(self) -> None:
            return None

        def xpath(self, pattern: str, namespaces: dict[str, str]) -> list[object]:
            return []

    class FakeRoot:
        def xpath(self, pattern: str, namespaces: dict[str, str]) -> list[object]:
            return [FakeText()]

    _svg._process_text_elements_lxml(FakeRoot(), {"svg": "http://www.w3.org/2000/svg"})

    class FakeGroup:
        def getparent(self) -> None:
            return None

    class FakeGroupRoot:
        def xpath(self, pattern: str, namespaces: dict[str, str]) -> list[object]:
            return [FakeGroup()]

    _svg._flatten_groups(FakeGroupRoot(), {"svg": "http://www.w3.org/2000/svg"})
    _svg._restore_bold_fonts(
        types.SimpleNamespace(), {"svg": "http://www.w3.org/2000/svg"}, set()
    )


def test_utils_gap_coverage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cns.figure(100, 100)
    plt.plot([0, 1], [0, 1])
    nested_path = tmp_path / "nested" / "plot.png"
    cns.savefig(str(nested_path))
    assert nested_path.exists()

    monkeypatch.chdir(tmp_path)
    cns.figure(100, 100)
    plt.plot([0, 1], [0, 1])
    cns.savefig("plot.png")
    assert Path("plot.png").exists()

    fig, ax = plt.subplots()
    plt.sca(ax)
    _utils.take_legend_out()
    assert ax.get_legend().get_title().get_text() == ""

    assert _utils._is_qualitative_cmap(["a"]) is True
    assert _utils._is_qualitative_cmap({"a": "#111111"}) is True

    plt.figure()
    plt.title("β")
    _utils.apply_unicode_font()

    class DummyResult:
        test_short_name = "T"
        significance_suffix = ""

        def __init__(self, pvalue: float) -> None:
            self.pvalue = pvalue

    class DummyAnnotator:
        def __init__(self, ax: object, pairs: object, **plotting: object) -> None:
            self._pvalue_format = None

        def configure(self, **kwargs: object) -> None:
            return None

        def apply_and_annotate(self) -> None:
            return None

        def set_pvalues(self, pvalues: list[float]) -> None:
            return None

        def annotate(self) -> None:
            return None

    monkeypatch.setattr(_utils, "Annotator", DummyAnnotator)
    formatter_ax = plt.subplots()[1]
    _utils._p_value_helper(
        "Mann-Whitney",
        pd.DataFrame({"g": ["A", "B"], "v": [1, 2]}),
        formatter_ax,
        {"x": "g", "y": "v"},
        "all",
        format="full",
    )
    formatter = DummyAnnotator(formatter_ax, [])._pvalue_format
    formatter = formatter or _utils.Annotator(formatter_ax, [])._pvalue_format

    class CaptureAnnotator(DummyAnnotator):
        last = None

        def __init__(self, ax: object, pairs: object, **plotting: object) -> None:
            super().__init__(ax, pairs, **plotting)
            CaptureAnnotator.last = self

    monkeypatch.setattr(_utils, "Annotator", CaptureAnnotator)
    fig2, ax2 = plt.subplots()
    _utils._p_value_helper(
        "Mann-Whitney",
        pd.DataFrame({"g": ["A", "B"], "v": [1, 2]}),
        ax2,
        {"x": "g", "y": "v"},
        "all",
        format="full",
    )
    formatted = CaptureAnnotator.last._pvalue_format.format_data(DummyResult(0.2))
    assert formatted == "ns"

    with pytest.raises(ValueError, match="requires a hue column"):
        _utils._p_value_helper(
            "Mann-Whitney",
            pd.DataFrame({"group": ["A", "B"], "value": [1, 2]}),
            ax2,
            {"x": "value", "y": "group"},
            "hue",
        )

    for name in ["Set3", "Pastel1", "Pastel2", "Paired", "Dark2", "Accent", "Bold"]:
        assert _utils.palettes(name)


def test_validation_gap_coverage(heatmap_adata: ad.AnnData) -> None:
    wide_df = pd.DataFrame(
        np.zeros((1, 11)), columns=pd.Index([f"c{i}" for i in range(11)])
    )
    with pytest.raises(ValueError, match="11 total columns"):
        _validation.validate_column_exists(wide_df, "missing", "x", "func")
    with pytest.raises(ValueError, match="11 total columns"):
        _validation.validate_columns_exist(wide_df, ["missing"], "func")

    adata = heatmap_adata.copy()
    for i in range(11):
        adata.obs[f"obs{i}"] = i
        adata.var[f"var{i}"] = i
    with pytest.raises(ValueError, match="13 total columns"):
        _validation.validate_adata_obs_columns(adata, "missing", "func")
    with pytest.raises(ValueError, match="13 total columns"):
        _validation.validate_adata_var_columns(adata, "missing", "func")
    with pytest.raises(ValueError, match="Null values found"):
        _validation.validate_no_nulls(pd.DataFrame({"a": [1, None]}), "a", "func")


def test_helper_heatmap_gap_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def fake_plot(self: object) -> None:
        self.ax = plt.gca()
        self.ax_heatmap = plt.gca()
        self.yticklabels = []

    monkeypatch.setattr(helper_heatmap.ClusterMapPlotterNew, "plot", fake_plot)
    monkeypatch.setattr(
        helper_heatmap.ClusterMapPlotterNew, "post_processing", lambda self: None
    )
    monkeypatch.setattr(
        helper_heatmap.ClusterMapPlotterNew,
        "plot_legends",
        lambda self, ax=None: calls.append(ax),
    )

    annotation = types.SimpleNamespace(
        plot_legend=False,
        legend_list=[],
        label_max_width=0,
        collect_legends=lambda: None,
    )
    cns.figure(100, 100)
    plotter = helper_heatmap.ClusterMapPlotterNew(
        data=pd.DataFrame([[1]]),
        right_annotation=annotation,
        plot=True,
        plot_legend=True,
        legend_anchor="auto",
        verbose=0,
    )
    assert calls[-1] is plotter.ax

    cns.figure(100, 100)
    plotter2 = helper_heatmap.ClusterMapPlotterNew(
        data=pd.DataFrame([[1]]),
        plot=True,
        plot_legend=True,
        legend_anchor="auto",
        verbose=0,
    )
    assert calls[-1] is plotter2.ax_heatmap

    cns.figure(100, 100)
    plotter3 = helper_heatmap.ClusterMapPlotterNew(
        data=pd.DataFrame([[0, 1], [1, 0]]),
        cmap=["red", "blue"],
        plot=False,
        verbose=1,
    )
    plotter3.data = np.array([[0, 1], [1, 0]])
    plotter3.ax = plt.gca()
    plotter3.yticklabels = []
    plotter3.collect_legends()
    assert plotter3.legend_list

    cns.figure(100, 100)
    plotter4 = helper_heatmap.ClusterMapPlotterNew(
        data=pd.DataFrame([[0, 1], [1, 0]]),
        cmap={"0": "red", "1": "blue"},
        plot=False,
        verbose=0,
    )
    plotter4.data = np.array([[0, 1], [1, 0]])
    plotter4.ax = plt.gca()
    plotter4.yticklabels = []
    plotter4.collect_legends()
    assert plotter4.legend_list

    cns.figure(100, 100)
    plotter5 = helper_heatmap.ClusterMapPlotterNew(
        data=pd.DataFrame([[0, 1], [1, 0]]),
        plot=False,
        verbose=0,
    )
    plotter5.ax = plt.gca()
    plotter5.widths = [1, 1, 1]
    plotter5.heights = [1, 1, 1]
    gs = plt.gcf().add_gridspec(1, 1)
    plotter5._define_axes(gs[0])


def test_phylo_and_sankey_gap_coverage() -> None:
    fig, ax = plt.subplots()
    out_ax, cmap = _phylo._heatmap(
        np.array([["A"], ["B"]]),
        cmap={"A": "red"},
        ax=ax,
        leg_pos="right",
    )
    assert out_ax is ax
    assert set(cmap) == {"A", "B"}

    assert len(_phylo._gen_colors(["red", "blue"], 2)) == 2
    assert _phylo._is_categorical(np.array([[1, 2], [3, 4]])) == [False, False]
    assert _phylo._is_categorical("plain text") is False

    def fail_palette(name: str, n: int) -> list[object]:
        raise ValueError("fallback")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(_phylo.sns, "color_palette", fail_palette)
    try:
        assert len(_phylo._gen_colors("viridis", 2)) == 2
    finally:
        monkeypatch.undo()

    _sankey.check_data_matches_labels({"A", "B"}, {"A", "B"}, "left")
    _sankey.check_data_matches_labels(["A", "B"], ["A", "B"], "left")
    data_frame = pd.DataFrame(
        {
            "left": ["A", "B"],
            "right": ["C", "D"],
            "leftWeight": [1, 1],
            "rightWeight": [1, 1],
        }
    )
    _sankey.identify_labels(data_frame, ["A", "B"], ["C", "D"])
    fig2, ax2 = plt.subplots()
    widths_left, _ = _sankey._get_positions_and_total_widths(
        data_frame, ["A", "B"], "left"
    )
    widths_right, _ = _sankey._get_positions_and_total_widths(
        data_frame, ["C", "D"], "right"
    )
    assert set(widths_left) == {"A", "B"}
    assert set(widths_right) == {"C", "D"}
    _sankey.plot_strips(
        ax2,
        {"A": "red", "B": "blue", "C": "green", "D": "black"},
        data_frame,
        ["A", "B"],
        {"A": {"bottom": 0, "left": 1}, "B": {"bottom": 1.04, "left": 1}},
        {"A": {"C": 1, "D": 0}, "B": {"C": 0, "D": 1}},
        {"A": {"C": 1, "D": 0}, "B": {"C": 0, "D": 1}},
        True,
        ["C", "D"],
        {"C": {"bottom": 0, "right": 1}, "D": {"bottom": 1.04, "right": 1}},
        np.float64(1.0),
    )


def test_plot_gap_coverage(
    categorical_df: pd.DataFrame,
    stack_df: pd.DataFrame,
    heatmap_adata: ad.AnnData,
    confusion_df: pd.DataFrame,
    survival_df: pd.DataFrame,
    phylo_adata: ad.AnnData,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cns.figure(120, 120)
    cns.lollipopplot(categorical_df, x="group", y="value", addtip=True, errorbar="bad")

    cns.figure(120, 120)
    cns.lollipopplot(
        categorical_df,
        x="group",
        y="value",
        hue="hue",
        color="black",
        order=["A", "B", "C"],
        hue_order=["H1", "H2"],
        pairs=[(("A", "H1"), ("A", "H2"))],
    )

    cns.figure(120, 120)
    cns.lollipopplot(
        categorical_df.rename(columns={"group": "cat", "value": "num"}),
        x="num",
        y="cat",
        hue="hue",
        addtip=True,
        errorbar="se",
    )

    cns.figure(120, 120)
    cns.stackplot(
        stack_df,
        x="treatment",
        y="response",
        horizontal=True,
        normalize=True,
        addtip=True,
        bar_order=["A", "B", "C"],
    )

    class SizeHandle:
        def __init__(self) -> None:
            self.sizes = None

        def set_sizes(self, sizes: list[float]) -> None:
            self.sizes = sizes

    fake_legend = types.SimpleNamespace(legend_handles=[SizeHandle()])
    monkeypatch.setattr(
        type(plt.gca()),
        "get_legend",
        lambda self: fake_legend,
        raising=False,
    )

    cns.figure(120, 120)
    cns.stripplot(categorical_df, x="group", y="value", hue="hue")
    cns.figure(120, 120)
    cns.scatterplot(
        categorical_df.rename(columns={"value": "x"}).assign(y=lambda df: df["x"] * 2),
        x="x",
        y="y",
        hue="hue",
    )
    cns.figure(120, 120)
    cns.regplot(
        categorical_df.rename(columns={"value": "x"}).assign(
            y=lambda df: df["x"] * 2, color_col=["A"] * 12
        ),
        x="x",
        y="y",
        color="color_col",
    )

    monkeypatch.undo()

    cns.figure(120, 120)
    cns.pieplot(categorical_df, x="group")
    cns.figure(120, 120)
    cns.donutplot(categorical_df, x="group")

    class FakeAxes:
        def __init__(self) -> None:
            self.patches: list[PathPatch] = []
            self.artists = [
                types.SimpleNamespace(
                    get_facecolor=lambda: (1, 0, 0, 1),
                    set_edgecolor=lambda x: None,
                    set_facecolor=lambda x: None,
                )
            ]
            self.lines = [
                types.SimpleNamespace(
                    set_color=lambda x: None,
                    set_mfc=lambda x: None,
                    set_mec=lambda x: None,
                )
            ] * 5

        def get_legend_handles_labels(self) -> tuple[list[object], list[str]]:
            return [], []

        def legend(self, handles: list[object], labels: list[str]) -> None:
            return None

    monkeypatch.setattr(dist_mod.sns, "boxplot", lambda **kwargs: FakeAxes())
    monkeypatch.setattr(cns.utils, "_remove_edge_from_legend_items", lambda ax: None)
    cns.boxplot(categorical_df, x="group", y="value")

    cns.figure(120, 120)
    cns.histplot(
        data=categorical_df.rename(columns={"value": "x", "group": "y"}), y="x"
    )

    adata_nan = heatmap_adata.copy()
    adata_nan.obs["cluster"] = pd.Series(
        ["A", None, "B"], index=adata_nan.obs_names, dtype=object
    )
    cns.figure(120, 120)
    cns.heatmapplot(adata_nan, row_annotation=["cluster"], cmap=None)

    with pytest.raises(ValueError, match="required cell for stats"):
        cns.confusionplot(
            confusion_df,
            x="pred",
            y="truth",
            add_pvalue=True,
            x_order=["neg", "pos"],
            y_order=["neg", "pos"],
            positive_x="missing",
        )

    original_crosstab = heatmap_mod.pd.crosstab
    monkeypatch.setattr(
        heatmap_mod.pd,
        "crosstab",
        lambda *args, **kwargs: pd.DataFrame(
            [[np.nan, 1], [1, 1]],
            index=pd.Index(["neg", "pos"]),
            columns=pd.Index(["neg", "pos"]),
        ),
    )
    with pytest.raises(ValueError, match="TN cell contains NaN"):
        cns.confusionplot(
            confusion_df,
            x="pred",
            y="truth",
            add_pvalue=True,
            annot=False,
            x_order=["neg", "pos"],
            y_order=["neg", "pos"],
        )
    monkeypatch.setattr(heatmap_mod.pd, "crosstab", original_crosstab)

    monkeypatch.setattr(
        heatmap_mod,
        "fisher_exact",
        lambda table: (_ for _ in ()).throw(ValueError("bad")),
    )
    with pytest.raises(ValueError, match="Fisher's exact test failed"):
        cns.confusionplot(
            confusion_df,
            x="pred",
            y="truth",
            add_pvalue=True,
            x_order=["neg", "pos"],
            y_order=["neg", "pos"],
        )

    bad_survival = survival_df.copy()
    bad_survival["time"] = bad_survival["time"] * 20
    cns.figure(120, 120)
    ax = cns.survivalplot(bad_survival, "time", "event", "group")
    assert ax.get_xlabel() == "Time (Months)"

    import lifelines

    original_logrank_test = lifelines.statistics.multivariate_logrank_test

    monkeypatch.setattr(
        lifelines.statistics,
        "multivariate_logrank_test",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("bad")),
    )
    with pytest.raises(RuntimeError, match="Log-rank test failed"):
        cns.survivalplot(survival_df, "time", "event", "group")
    monkeypatch.setattr(
        lifelines.statistics,
        "multivariate_logrank_test",
        original_logrank_test,
    )

    class BadCox:
        def fit(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("bad")

    monkeypatch.setattr(lifelines, "CoxPHFitter", BadCox)
    with pytest.raises(RuntimeError, match="Cox proportional hazards model failed"):
        cns.survivalplot(
            pd.DataFrame(
                {
                    "time": [1, 2, 3, 4, 5, 6],
                    "event": [1, 0, 1, 0, 1, 0],
                    "group": ["A", "A", "B", "B", "C", "C"],
                }
            ),
            "time",
            "event",
            "group",
        )
    with pytest.raises(RuntimeError, match="Could not compute hazard ratios"):
        cns.survivalplot(survival_df, "time", "event", "group")

    cns.figure(120, 120)
    cns.phyloplot(phylo_adata)

    fake_venn_obj = types.SimpleNamespace(
        get_label_by_id=lambda area: (_ for _ in ()).throw(AttributeError())
        if area in {"100", "110"}
        else types.SimpleNamespace(set_fontsize=lambda size: None),
        get_patch_by_id=lambda area: (_ for _ in ()).throw(AttributeError())
        if area in {"100", "110"}
        else types.SimpleNamespace(
            set_edgecolor=lambda color: None, set_linewidth=lambda width: None
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "matplotlib_venn",
        types.SimpleNamespace(
            venn2=lambda *args, **kwargs: fake_venn_obj,
            venn3=lambda *args, **kwargs: fake_venn_obj,
        ),
    )
    cns.figure(120, 120)
    assert (
        cns.vennplot([{1, 2}, {2, 3}, {3, 4}], labels=["A", "B", "C"]) is fake_venn_obj
    )


def test_remaining_visual_gap_coverage(
    confusion_df: pd.DataFrame,
    heatmap_adata: ad.AnnData,
    numeric_df: pd.DataFrame,
    volcano_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_isinstance = builtins.isinstance

    def fake_isinstance(obj: object, typ: Any) -> bool:
        if typ is object and getattr(obj, "kind", None) in {"b", "i", "u", "f"}:
            return False
        return real_isinstance(obj, typ)

    monkeypatch.setattr(heatmap_mod, "isinstance", fake_isinstance, raising=False)
    cns.figure(180, 180)
    cmp = cns.heatmapplot(
        heatmap_adata,
        row_annotation=["score"],
        col_annotation=["importance"],
        cmap="parula",
    )
    assert cmp.ax_heatmap is not None

    monkeypatch.setattr(
        heatmap_mod.pd,
        "crosstab",
        lambda *args, **kwargs: pd.DataFrame(
            [[np.nan, 1], [1, 1]],
            index=pd.Index(["neg", "pos"]),
            columns=pd.Index(["neg", "pos"]),
        ),
    )
    with pytest.raises(ValueError, match="contains NaN at position \\[0,0\\]"):
        cns.confusionplot(
            confusion_df,
            x="pred",
            y="truth",
            x_order=["neg", "pos"],
            y_order=["neg", "pos"],
            annot=True,
        )

    monkeypatch.setattr(
        heatmap_mod.pd,
        "Categorical",
        lambda values, categories, ordered: values,
    )
    monkeypatch.setattr(
        heatmap_mod.pd,
        "crosstab",
        lambda *args, **kwargs: pd.DataFrame(
            [[1, 0], [0, 1]],
            index=pd.Index(["neg", "pos"]),
            columns=pd.Index(["pos1", "pos2"]),
        ),
    )
    with pytest.raises(ValueError, match="Could not find negative label in x_order"):
        cns.confusionplot(
            confusion_df,
            x="pred",
            y="truth",
            x_order=["pos", "pos"],
            y_order=["neg", "pos"],
            positive_x="pos",
            add_pvalue=True,
            annot=False,
        )

    class MarkerHandle:
        def __init__(self) -> None:
            self.marker_size = None

        def set_markersize(self, size: float) -> None:
            self.marker_size = size

    reg_legend = types.SimpleNamespace(legend_handles=[MarkerHandle()])
    monkeypatch.setattr(
        type(plt.gca()),
        "get_legend",
        lambda self: reg_legend,
        raising=False,
    )
    cns.figure(120, 120)
    cns.regplot(numeric_df, x="x", y="y", color="color_group", s=9)
    assert reg_legend.legend_handles[0].marker_size is not None

    class SizeHandle:
        def __init__(self) -> None:
            self.sizes = None

        def set_sizes(self, sizes: list[float]) -> None:
            self.sizes = sizes

    volcano_legend = types.SimpleNamespace(legend_handles=[SizeHandle()])
    monkeypatch.setattr(
        type(plt.gca()),
        "get_legend",
        lambda self: volcano_legend,
        raising=False,
    )
    monkeypatch.setattr(genomics_mod.cns, "take_legend_out", lambda: None)
    cns.figure(120, 120)
    cns.volcanoplot(volcano_df)
    assert volcano_legend.legend_handles[0].sizes == [20]

    cox_like_model = types.SimpleNamespace(
        name="cox",
        hue="group",
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
    cns.figure(120, 120)
    ax = cns.forestplot(cox_like_model)
    assert ax.get_xlabel() == "Hazard ratio (95% CI)"

    monkeypatch.setattr(
        specialized_mod, "validate_dataframe", lambda data, name, fn: None
    )
    with pytest.raises(TypeError, match="Internal type validation failed"):
        cns.forestplot(
            types.SimpleNamespace(name="cox", results=["not", "a", "dataframe"])
        )
