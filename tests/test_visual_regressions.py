from __future__ import annotations

from collections.abc import Iterator
import os
import platform
import sys

import anndata as ad
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import pytest
from matplotlib import ft2font
from matplotlib.figure import Figure

import cnsplots as cns


@pytest.fixture(autouse=True)
def _assert_visual_hash_environment(
    request: pytest.FixtureRequest,
    pytestconfig: pytest.Config,
) -> None:
    visual_mode = (
        pytestconfig.getoption("--mpl")
        or pytestconfig.getoption("--mpl-generate-hash-library") is not None
    )
    if request.node.get_closest_marker("mpl_image_compare") is None or not visual_mode:
        return

    actual = (
        sys.platform,
        platform.machine(),
        sys.version_info[:2],
        mpl.__version__,
        ft2font.__freetype_version__,
    )
    expected = ("linux", "x86_64", (3, 12), "3.10.8", "2.6.1")
    if actual == expected:
        return

    message = (
        "visual hashes require Linux x86_64, Python 3.12, Matplotlib 3.10.8, "
        f"and FreeType 2.6.1; got {actual!r}"
    )
    if os.environ.get("CNSPLOTS_REQUIRE_VISUAL_ENV") == "1":
        raise AssertionError(message)
    pytest.skip(message)


@pytest.fixture(autouse=True)
def _stable_visual_font() -> Iterator[None]:
    with mpl.rc_context(), cns.settings.context(font_sans_serif=("DejaVu Sans",)):
        yield


def _figure(width: int = 180, height: int = 160) -> Figure:
    cns.figure(width, height)
    return plt.gcf()


@pytest.mark.mpl_image_compare
def test_visual_boxplot(categorical_df: pd.DataFrame) -> Figure:
    figure = _figure()
    cns.boxplot(
        categorical_df,
        x="group",
        y="value",
        order=["A", "B", "C"],
        add_count=True,
        showoutliers=True,
        whis=(0, 100),
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_split_violinplot(categorical_df: pd.DataFrame) -> Figure:
    figure = _figure()
    cns.violinplot(
        categorical_df,
        x="group",
        y="value",
        hue="hue",
        order=["A", "B", "C"],
        hue_order=["H1", "H2"],
        split=True,
        inner="quart",
        add_box=True,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_bar_strip_overlay(categorical_df: pd.DataFrame) -> Figure:
    figure = _figure()
    ax = cns.barplot(
        categorical_df,
        x="group",
        y="value",
        order=["A", "B", "C"],
        errorbar="sd",
    )
    cns.stripplot(
        categorical_df,
        x="group",
        y="value",
        hue="hue",
        order=["A", "B", "C"],
        hue_order=["H1", "H2"],
        jitter=False,
        dodge=True,
        legend=False,
        ax=ax,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_grouped_lollipopplot(categorical_df: pd.DataFrame) -> Figure:
    figure = _figure()
    cns.lollipopplot(
        categorical_df,
        x="group",
        y="value",
        hue="hue",
        order=["A", "B", "C"],
        hue_order=["H1", "H2"],
        errorbar="se",
        add_tip=True,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_normalized_stackplot(stack_df: pd.DataFrame) -> Figure:
    figure = _figure()
    cns.stackplot(
        stack_df,
        x="treatment",
        stack="response",
        order=["A", "B", "C"],
        stack_order=["Yes", "No"],
        normalize=True,
        add_count=True,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_dumbbellplot() -> Figure:
    data = pd.DataFrame(
        {
            "pathway": ["A", "A", "B", "B", "C", "C"],
            "score": [1.0, 3.0, 2.0, 5.0, 4.0, 6.0],
            "condition": ["before", "after"] * 3,
        }
    )
    figure = _figure()
    cns.dumbbellplot(
        data,
        x="score",
        y="pathway",
        hue="condition",
        order=["A", "B", "C"],
        hue_order=["before", "after"],
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_ridgeplot(categorical_df: pd.DataFrame) -> Figure:
    figure = _figure()
    cns.ridgeplot(
        categorical_df,
        x="value",
        y="group",
        cmap="viridis",
        overlap=0.55,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_bivariate_histplot() -> Figure:
    data = pd.DataFrame(
        {
            "x": [4.5, 4.7, 4.9, 5.1, 5.3, 5.7, 5.9, 6.1, 6.3, 6.8, 7.1, 7.4],
            "y": [2.2, 2.4, 3.1, 3.3, 3.6, 4.0, 4.2, 2.9, 2.7, 3.0, 3.5, 2.8],
        }
    )
    figure = _figure()
    cns.histplot(
        data=data,
        x="x",
        y="y",
        bins=(4, 4),
        cbar=True,
        cmap="hot",
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_grouped_regplot() -> Figure:
    data = pd.DataFrame(
        {
            "x": [0.0, 1.0, 0.0, 1.0],
            "y": [1.0, 3.0, -2.0, 1.0],
            "group": ["A", "A", "B", "B"],
        }
    )
    figure = _figure()
    cns.regplot(
        data,
        x="x",
        y="y",
        hue="group",
        hue_order=["A", "B"],
        fit_reg=False,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_slopeplot() -> Figure:
    data = pd.DataFrame(
        {
            "site": ["site1", "site1", "site2", "site2", "site3", "site3"],
            "value": [1.0, 2.0, 2.0, 1.0, 1.5, 1.7],
            "condition": ["healthy", "disease"] * 3,
        }
    )
    figure = _figure()
    cns.slopeplot(
        data,
        x="site",
        y="value",
        hue="condition",
        pair="site",
        hue_order=["healthy", "disease"],
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_annotated_heatmap(heatmap_adata: ad.AnnData) -> Figure:
    _figure(220, 180)
    plotter = cns.heatmapplot(
        heatmap_adata,
        layer="scaled",
        row_annotation=["cluster"],
        col_annotation=["pathway"],
        row_split="cluster",
        col_split="pathway",
        row_cluster=False,
        col_cluster=False,
        colors={"cluster": {"A": "#111111", "B": "#777777"}},
        cmap="viridis",
    )
    assert plotter.ax_heatmap is not None
    figure = plotter.ax_heatmap.figure
    assert isinstance(figure, Figure)
    return figure


@pytest.mark.mpl_image_compare
def test_visual_dotplot(dotplot_df: pd.DataFrame) -> Figure:
    figure = _figure(200, 180)
    cns.dotplot(
        dotplot_df,
        x="sample",
        y="gene",
        color="mean_expr",
        size="pct_expr",
        value="score",
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_confusionplot(confusion_df: pd.DataFrame) -> Figure:
    figure = _figure(200, 170)
    cns.confusionplot(
        confusion_df,
        x="pred",
        y="truth",
        add_pvalue=True,
        x_order=["neg", "pos"],
        y_order=["neg", "pos"],
        positive_x="pos",
        positive_y="pos",
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_survivalplot(survival_df: pd.DataFrame) -> Figure:
    figure = _figure(200, 180)
    cns.survivalplot(
        survival_df,
        "time",
        "event",
        "group",
        hue_order=["Control", "Treatment"],
        ci_show=False,
        show_risk_table=True,
        xticks=[0, 4, 8, 12],
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_cumulative_incidenceplot(
    competing_risk_df: pd.DataFrame,
) -> Figure:
    figure = _figure(200, 180)
    cns.cumulativeincidenceplot(
        competing_risk_df,
        "time",
        "event",
        "group",
        hue_order=["A", "B"],
        show_risk_table=True,
        xticks=[0, 2, 4, 6, 8],
        censor_mark_position=["above", "below"],
        seed=0,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_grouped_forestplot() -> Figure:
    data = pd.DataFrame(
        {
            "section": [
                "Primary",
                "Primary",
                "Subgroup",
                "Subgroup",
                "Subgroup",
                "Subgroup",
            ],
            "term": ["Outcome", "Outcome", "Outcome", "Outcome", "Age", "Age"],
            "cohort": ["A", "B", "A", "B", "A", "B"],
            "effect": [0.8, 0.9, 0.7, 0.85, 1.2, 1.1],
            "ci_low": [0.6, 0.7, 0.5, 0.65, 1.0, 0.9],
            "ci_high": [1.0, 1.1, 0.9, 1.05, 1.4, 1.3],
            "probability": [0.05, 0.1, 0.01, 0.02, 0.2, 0.4],
        }
    )
    figure = _figure(240, 190)
    cns.forestplot(
        data=data,
        label="term",
        estimate="effect",
        lower="ci_low",
        upper="ci_high",
        pvalue="probability",
        group="section",
        hue="cohort",
        group_order=["Subgroup", "Primary"],
        order=["Age", "Outcome"],
        hue_order=["B", "A"],
        reference=1,
        xlabel="Risk ratio (95% CI)",
        bar_width=0.3,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_rocplot() -> Figure:
    data = pd.DataFrame(
        {
            "truth": [0, 0, 0, 0, 1, 1, 1, 1],
            "model_a": [0.1, 0.4, 0.4, 0.7, 0.3, 0.4, 0.8, 0.9],
            "model_b": [0.2, 0.3, 0.5, 0.6, 0.4, 0.5, 0.7, 0.8],
        }
    )
    figure = _figure(320, 220)
    cns.rocplot(
        data,
        "truth",
        ["model_a", "model_b"],
        pairs=[("model_a", "model_b")],
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_volcanoplot(volcano_df: pd.DataFrame) -> Figure:
    figure = _figure()
    cns.volcanoplot(volcano_df, n_show=1)
    return figure


@pytest.mark.mpl_image_compare
def test_visual_multistage_sankeyplot() -> Figure:
    data = pd.DataFrame(
        {
            "baseline": ["A", "A", "B", "B"],
            "week_4": ["C", "D", "C", "D"],
            "week_12": ["E", "E", "F", "F"],
        }
    )
    figure = _figure(220, 170)
    cns.sankeyplot(
        data,
        x=["baseline", "week_4", "week_12"],
        label_rotation=30,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_upsetplot(sets_fixture: dict[str, set[int]]) -> Figure:
    figure = _figure(220, 180)
    cns.upsetplot(
        sets_fixture,
        fig=figure,
        min_subset_size=1,
        sort_by="cardinality",
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_distplot(numeric_df: pd.DataFrame) -> Figure:
    figure = _figure()
    cns.distplot(
        numeric_df,
        x="x",
        hue="group",
        hue_order=["G1", "G2"],
        bins=[0, 3, 6, 9, 12, 15],
        stat="density",
        common_norm=False,
        kde_kws={"cut": 0, "gridsize": 64, "bw_adjust": 0.75},
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_kdeplot(numeric_df: pd.DataFrame) -> Figure:
    figure = _figure()
    cns.kdeplot(
        numeric_df,
        x="x",
        hue="group",
        hue_order=["G1", "G2"],
        add_mode=False,
        bw_adjust=0.75,
        common_norm=False,
        cut=0,
        gridsize=64,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_pieplot(categorical_df: pd.DataFrame) -> Figure:
    figure = _figure(190, 160)
    figure.subplots_adjust(right=0.7)
    cns.pieplot(
        categorical_df,
        x="group",
        order=["A", "B", "C"],
        legend="right",
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_donutplot(categorical_df: pd.DataFrame) -> Figure:
    figure = _figure(190, 160)
    figure.subplots_adjust(right=0.7)
    cns.donutplot(
        categorical_df,
        x="group",
        order=["A", "B", "C"],
        legend="right",
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_gseaplot(gsea_plot_df: pd.DataFrame) -> Figure:
    figure = _figure(220, 180)
    cns.gseaplot(
        gsea_plot_df,
        y="Clean_Term",
        color="NES",
        cutoff=0.05,
        cmap="coolwarm",
        top_term=3,
        size=1.8,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_multipanel_layout() -> Figure:
    mp = cns.multipanel(max_width=300, title="Canonical layout", loc="left")
    ax_a = mp.panel(
        "A",
        width=80,
        height=60,
        pad_left=8,
        pad_top=6,
        margin_left=0,
        margin_top=0,
        margin_right=12,
        margin_bottom=10,
    )
    ax_a.plot([0, 1, 2], [1, 3, 2], marker="o")
    ax_a.set(
        title="Primary",
        ylabel="Signal",
        xticks=[0, 1, 2],
    )
    ax_b = mp.panel(
        "B",
        width=80,
        height=60,
        pad_left=8,
        pad_top=6,
        margin_left=0,
        margin_top=0,
        margin_right=12,
        margin_bottom=10,
    )
    ax_b.bar(["X", "Y"], [2, 4])
    ax_b.set_title("Summary")
    ax_c = mp.panel(
        "C",
        width=80,
        height=45,
        below="A",
        pad_left=8,
        pad_top=6,
        margin_left=0,
        margin_top=0,
        margin_right=12,
        margin_bottom=10,
    )
    ax_c.plot([0, 1], [0, 1], color="black")
    ax_c.set_xlabel("Time")

    figure = mp.fig
    assert figure is not None
    figure.canvas.draw()
    return figure


@pytest.mark.mpl_image_compare
def test_visual_lineplot(line_df: pd.DataFrame) -> Figure:
    figure = _figure()
    cns.lineplot(
        line_df,
        x="time",
        y="value",
        hue="condition",
        style="condition",
        hue_order=["A", "B"],
        style_order=["A", "B"],
        errorbar=None,
        markers=True,
        dashes=False,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_scatterplot(numeric_df: pd.DataFrame) -> Figure:
    figure = _figure()
    cns.scatterplot(
        numeric_df,
        x="x",
        y="y",
        hue="group",
        hue_order=["G1", "G2"],
        s=18,
    )
    return figure


@pytest.mark.mpl_image_compare
def test_visual_placeholderplot() -> Figure:
    figure = _figure()
    cns.placeholderplot("Reserved analysis panel")
    return figure


@pytest.mark.mpl_image_compare
def test_visual_phyloplot(phylo_adata: ad.AnnData) -> Figure:
    _figure(220, 180)
    ax = cns.phyloplot(phylo_adata)
    figure = ax.figure
    assert isinstance(figure, Figure)
    return figure


@pytest.mark.mpl_image_compare
def test_visual_qqplot(numeric_df: pd.DataFrame) -> Figure:
    figure = _figure()
    cns.qqplot(numeric_df, x="x", line="45")
    return figure


@pytest.mark.mpl_image_compare
def test_visual_vennplot(sets_fixture: dict[str, set[int]]) -> Figure:
    figure = _figure(180, 170)
    cns.vennplot(
        [sets_fixture["A"], sets_fixture["B"]],
        labels=["A", "B"],
    )
    return figure
