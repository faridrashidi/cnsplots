from __future__ import annotations

import logging
from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
import pytest
from cycler import cycler
from matplotlib.colors import to_hex, to_rgba
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Wedge

import cnsplots as cns


def test_boxplot_and_violinplot(
    categorical_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(
        cns.utils,
        "_p_value_helper",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    cns.figure(120, 120)
    with caplog.at_level(logging.INFO, logger="cnsplots"):
        ax = cns.boxplot(
            categorical_df,
            x="group",
            y="value",
            pairs=[("A", "B")],
            addcount=True,
            showoutliers=True,
            whis=(0, 100),
        )
    assert ax.get_xticklabels()[0].get_text().startswith("A")
    assert "minimum and maximum values" in caplog.text
    assert calls

    cns.figure(120, 120)
    ax2 = cns.violinplot(
        categorical_df,
        x="group",
        y="value",
        pairs=[("A", "B")],
        add_box=True,
        addcount=True,
        hue="hue",
        split=True,
        inner="quart",
    )
    assert len(ax2.collections) > 0

    cns.figure(120, 120)
    ax3 = cns.violinplot(categorical_df, x="group", y="value", add_box=False)
    assert ax3 is plt.gca()


def test_barplot_and_lollipopplot(
    categorical_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(
        cns.utils,
        "_p_value_helper",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    cns.figure(120, 120)
    ax = cns.barplot(
        categorical_df,
        x="group",
        y="value",
        pairs=[("A", "B")],
        addtip=True,
        palette="palette_group",
    )
    assert ax.get_legend() is not None
    assert ax.get_legend().get_title().get_text() == "palette_group"

    cns.figure(120, 120)
    ax2 = cns.lollipopplot(
        categorical_df,
        x="group",
        y="value",
        hue="hue",
        pairs=[(("A", "H1"), ("A", "H2"))],
        addtip=True,
        errorbar="ci",
        palette="Set1",
    )
    assert ax2.get_legend() is not None

    cns.figure(120, 120)
    ax3 = cns.lollipopplot(
        categorical_df.rename(columns={"group": "cat", "value": "num"}),
        x="num",
        y="cat",
        color="black",
        errorbar="sd",
        addtip=True,
        estimator="median",
    )
    assert ax3.get_yticklabels()[0].get_text()

    cns.figure(120, 120)
    ax4 = cns.lollipopplot(
        categorical_df,
        x="group",
        y="value",
        palette="palette_group",
        errorbar="se",
    )
    assert ax4.get_legend() is not None
    assert calls


def test_categorical_annotations_use_legend_fontsize(
    categorical_df: pd.DataFrame,
) -> None:
    with cns.settings.context(legend_fontsize=13):
        cns.figure(120, 120)
        bar_ax = cns.barplot(categorical_df, x="group", y="value", addtip=True)
        assert {text.get_fontsize() for text in bar_ax.texts} == {13}

        cns.figure(120, 120)
        lollipop_ax = cns.lollipopplot(
            categorical_df, x="group", y="value", addtip=True
        )
        assert {text.get_fontsize() for text in lollipop_ax.texts} == {13}

        cns.figure(120, 120)
        donut_ax = cns.donutplot(categorical_df, x="group")
        center_label = next(
            text for text in donut_ax.texts if text.get_text() == "group"
        )
        assert center_label.get_fontsize() == pytest.approx(13)

    with cns.settings.context(legend_fontsize=None, title_fontsize=12):
        cns.figure(120, 120)
        donut_ax = cns.donutplot(categorical_df, x="group")
        center_label = next(
            text for text in donut_ax.texts if text.get_text() == "group"
        )
        assert center_label.get_fontsize() == pytest.approx(12)


def test_stack_strip_pie_and_donut_plots(
    categorical_df: pd.DataFrame,
    stack_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(
        cns.utils,
        "_p_value_helper",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    cns.figure(120, 120)
    ax = cns.stackplot(
        stack_df,
        x="treatment",
        y="response",
        normalize=True,
        addcount=True,
        pairs=[("A", "B")],
        bar_order=["A", "B", "C"],
        stack_order=["Yes", "No"],
    )
    assert ax.get_ylabel() == "Frequency"
    assert [tick.get_text() for tick in ax.get_xticklabels()] == [
        "A\n(n=4)",
        "B\n(n=4)",
        "C\n(n=4)",
    ]
    assert not ax.texts

    cns.figure(120, 120)
    ax2 = cns.stackplot(
        categorical_df.rename(columns={"group": "treatment", "binary": "response"}),
        x="treatment",
        y="response",
        horizontal=True,
        normalize=False,
        pairs=[("A", "B")],
        bar_order=["A", "B", "C"],
        stack_order=["No", "Yes"],
    )
    assert ax2.get_xlabel() == "Count"

    cns.figure(120, 120)
    ax2b = cns.stackplot(
        stack_df,
        x="treatment",
        y="response",
        horizontal=True,
        normalize=False,
        addcount=True,
    )
    assert {tick.get_text() for tick in ax2b.get_yticklabels()} == {
        "No\n(n=6)",
        "Yes\n(n=6)",
    }
    assert not ax2b.texts

    cns.figure(120, 120)
    ax3 = cns.stripplot(
        categorical_df,
        x="group",
        y="value",
        hue="hue",
        showmeans=True,
        addcount=True,
    )
    assert ax3.get_legend() is not None

    cns.figure(120, 120)
    ax4 = cns.pieplot(
        categorical_df, x="group", legend="left", hue_order=["C", "B", "A"]
    )
    assert ax4.get_legend() is not None

    cns.figure(120, 120)
    ax5 = cns.donutplot(
        categorical_df, x="group", legend="top", hue_order=["A", "B", "C"]
    )
    assert ax5.get_legend() is not None
    assert any(text.get_text() == "group" for text in ax5.texts)
    donut_wedges = [patch for patch in ax5.patches if isinstance(patch, Wedge)]
    assert donut_wedges
    assert all(patch.width == pytest.approx(0.4) for patch in donut_wedges)
    assert calls


def test_distribution_wrappers(
    numeric_df: pd.DataFrame,
    categorical_df: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    cns.figure(120, 120)
    ax = cns.distplot(numeric_df, x="x", hue="group")
    assert ax is plt.gca()

    cns.figure(120, 120)
    ax2 = cns.kdeplot(numeric_df, x="x", add_mode=True)
    assert any(line.get_linestyle() == "--" for line in ax2.lines)

    cns.figure(120, 120)
    with caplog.at_level(logging.INFO, logger="cnsplots"):
        ax3 = cns.kdeplot(
            categorical_df.rename(columns={"value": "score"}), x="score", hue="hue"
        )
    assert ax3.get_legend() is not None
    assert "Anderson-Darling test" in caplog.text

    cns.figure(120, 120)
    ax4 = cns.histplot(data=numeric_df, x="x", kde=True)
    assert ax4 is plt.gca()

    cns.figure(120, 120)
    ax5 = cns.ridgeplot(categorical_df, x="value", y="group", cmap="viridis")
    assert ax5.get_xlabel() == "value"

    cns.figure(120, 120)
    ax6 = cns.qqplot(numeric_df, x="x")
    assert ax6 is plt.gca()


def test_distribution_annotations_use_legend_fontsize(
    numeric_df: pd.DataFrame,
    categorical_df: pd.DataFrame,
) -> None:
    with cns.settings.context(legend_fontsize=13):
        cns.figure(120, 120)
        kde_ax = cns.kdeplot(numeric_df, x="x", add_mode=True)
        assert kde_ax.texts
        assert {text.get_fontsize() for text in kde_ax.texts} == {13}

        cns.figure(120, 120)
        ridge_ax = cns.ridgeplot(categorical_df, x="value", y="group")
        assert {text.get_fontsize() for text in ridge_ax.texts} == {13}

    with cns.settings.context(legend_fontsize=None, title_fontsize=12):
        cns.figure(120, 120)
        kde_ax = cns.kdeplot(numeric_df, x="x", add_mode=True)
        assert kde_ax.texts
        assert {text.get_fontsize() for text in kde_ax.texts} == {12}


def test_pieplot_uses_legend_fontsize(categorical_df: pd.DataFrame) -> None:
    with cns.settings.context(legend_fontsize=13):
        cns.figure(120, 120)
        ax = cns.pieplot(categorical_df, x="group")
        assert {
            text.get_fontsize() for text in ax.texts if text.get_text().endswith("%")
        } == {13}

    with cns.settings.context(legend_fontsize=None, title_fontsize=12):
        cns.figure(120, 120)
        ax = cns.pieplot(categorical_df, x="group")
        assert {
            text.get_fontsize() for text in ax.texts if text.get_text().endswith("%")
        } == {12}


def test_pieplot_uses_contrast_text_color() -> None:
    data = pd.DataFrame({"group": ["dark"] * 3 + ["light"] * 2})

    cns.figure(120, 120)
    with plt.rc_context({"axes.prop_cycle": cycler(color=["#111111", "#eeeeee"])}):
        ax = cns.pieplot(data, x="group", hue_order=["dark", "light"])

    percent_texts = [text for text in ax.texts if text.get_text().endswith("%")]
    assert [text.get_color() for text in percent_texts] == ["white", "black"]

    with cns.settings.context(annotation_auto_contrast=False):
        cns.figure(120, 120)
        with plt.rc_context({"axes.prop_cycle": cycler(color=["#111111", "#eeeeee"])}):
            ax = cns.pieplot(data, x="group", hue_order=["dark", "light"])

    percent_texts = [text for text in ax.texts if text.get_text().endswith("%")]
    assert [text.get_color() for text in percent_texts] == ["white", "white"]


def test_distribution_logging_respects_settings_verbosity(
    categorical_df: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    data = categorical_df.rename(columns={"value": "score"})

    caplog.set_level(logging.INFO)
    with cns.settings.context(verbosity=0):
        caplog.clear()
        cns.figure(120, 120)
        cns.kdeplot(data, x="score", hue="hue")
        assert "Anderson-Darling test" not in caplog.text

    with cns.settings.context(verbosity=1):
        caplog.clear()
        cns.figure(120, 120)
        cns.kdeplot(data, x="score", hue="hue")
        assert "Anderson-Darling test" in caplog.text


def test_line_scatter_reg_and_slope_plots(
    numeric_df: pd.DataFrame,
    line_df: pd.DataFrame,
) -> None:
    cns.figure(120, 120)
    ax = cns.regplot(numeric_df, x="x", y="y")
    assert "\\rho" in ax.texts[0].get_text()

    cns.figure(120, 120)
    ax2 = cns.regplot(numeric_df, x="x", y="y", hue="group", s=5)
    assert ax2.get_legend() is not None

    cns.figure(120, 120)
    ax3 = cns.regplot(numeric_df, x="x", y="y", color="color_group")
    assert ax3.get_legend() is not None

    cns.figure(120, 120)
    ax4 = cns.scatterplot(numeric_df, x="x", y="y", hue="group", s=10)
    assert ax4.get_legend() is not None

    cns.figure(120, 120)
    ax5 = cns.lineplot(data=line_df, x="time", y="value", hue="condition")
    assert ax5.get_legend() is not None

    slope_df = pd.DataFrame(
        {
            "site": ["site1", "site1", "site2", "site2", "site3", "site3"],
            "value": [1.0, 2.0, 2.0, 1.0, 1.5, 1.7],
            "label": ["healthy", "disease"] * 3,
        }
    )
    cns.figure(120, 120)
    ax6 = cns.slopeplot(slope_df, x="site", y="value", hue="label")
    assert ax6.get_legend() is not None


def test_placeholderplot_renders_centered_placeholder() -> None:
    with cns.settings.context(title_fontsize=11, title_fontweight="normal"):
        cns.figure(120, 180)
        plt.plot([0, 1], [0, 1])
        ax = cns.placeholderplot("A description to be centered in the panel")

        assert ax is plt.gca()
        assert len(ax.lines) == 0
        assert len(ax.texts) == 1
        assert len(ax.patches) >= 6

        text = ax.texts[0]
        assert text.get_text() == "A description to be centered in the panel"
        assert text.get_ha() == "center"
        assert text.get_va() == "center"
        assert text.get_wrap() is True
        assert text.get_fontsize() == pytest.approx(11)
        assert text.get_fontweight() == "normal"
        assert text.get_fontfamily() == list(plt.rcParams["font.family"])

        outer_card = next(
            patch
            for patch in ax.patches
            if isinstance(patch, FancyBboxPatch)
            and to_hex(patch.get_facecolor(), keep_alpha=False) == "#eef1f4"
        )
        assert to_hex(outer_card.get_edgecolor(), keep_alpha=False) == "#b8c0cc"
        assert outer_card.get_linewidth() == pytest.approx(0.9)

        assert any(
            isinstance(patch, FancyBboxPatch)
            and to_hex(patch.get_facecolor(), keep_alpha=False) == "#e0e5eb"
            for patch in ax.patches
        )
        assert any(
            isinstance(patch, Circle)
            and to_hex(patch.get_facecolor(), keep_alpha=False) == "#c7d0db"
            for patch in ax.patches
        )
        assert sum(isinstance(patch, Polygon) for patch in ax.patches) >= 2

        assert not ax.axison


def test_placeholderplot_requires_string_description() -> None:
    cns.figure(120, 120)
    with pytest.raises(TypeError, match="must be a string"):
        cast(Any, cns.placeholderplot)(123)


def test_sets_and_specialized_plots(
    sets_fixture: dict[str, set[int]],
    sankey_df: pd.DataFrame,
    roc_df: pd.DataFrame,
) -> None:
    cns.figure(120, 120)
    axes = cns.upsetplot(sets_fixture, min_subset_size=1)
    assert set(axes) >= {"matrix", "intersections"}
    assert all(ax is None or ax.get_facecolor()[-1] == 0 for ax in axes.values())
    assert axes["matrix"].figure.patch.get_facecolor()[-1] == 0
    assert all(
        not tick.tick1line.get_visible()
        for tick in axes["shading"].yaxis.get_major_ticks()
    )

    fig = plt.figure()
    embedded_axes = cns.upsetplot(sets_fixture, fig=fig, min_subset_size=1)
    assert all(ax is None or ax.figure is fig for ax in embedded_axes.values())
    assert fig.patch.get_facecolor()[-1] == 0

    with cns.settings.context(legend_fontsize=None, title_fontsize=12):
        cns.figure(120, 120)
        inherited_axes = cns.upsetplot(sets_fixture, min_subset_size=1)
        assert inherited_axes["intersections"].texts
        assert {
            text.get_fontsize() for text in inherited_axes["intersections"].texts
        } == {12}

    custom_fig = plt.figure()
    custom_fig.patch.set_facecolor("red")
    custom_fig.patch.set_alpha(1)
    cns.upsetplot(sets_fixture, fig=custom_fig, min_subset_size=1)
    assert custom_fig.patch.get_facecolor() == to_rgba("red")

    cns.figure(120, 120)
    venn = cns.vennplot(list(sets_fixture.values())[:2], labels=["A", "B"])
    assert venn is not None

    cns.figure(120, 120)
    ax = cns.sankeyplot(sankey_df, x="source", y="target")
    assert ax is plt.gca()
    assert (
        len(ax.texts) == sankey_df["source"].nunique() + sankey_df["target"].nunique()
    )
    assert all(text.get_rotation() == 0 for text in ax.texts)

    cns.figure(120, 120)
    ax_rotated = cns.sankeyplot(sankey_df, x="source", y="target", label_rotation=90)
    assert ax_rotated is plt.gca()
    assert len(ax_rotated.texts) == len(ax.texts)
    assert all(text.get_rotation() == 90 for text in ax_rotated.texts)

    cns.figure(120, 120)
    ax2 = cns.rocplot(roc_df, "truth", "model_a")
    assert len(ax2.lines) == 2

    cns.figure(120, 120)
    ax3 = cns.rocplot(roc_df, "truth", ["model_a", "model_b"])
    assert len(ax3.lines) == 3


def test_sankey_annotations_use_legend_fontsize(sankey_df: pd.DataFrame) -> None:
    with cns.settings.context(legend_fontsize=13):
        cns.figure(120, 120)
        ax = cns.sankeyplot(sankey_df, x="source", y="target")
        assert ax.texts
        assert {text.get_fontsize() for text in ax.texts} == {13}

    with cns.settings.context(legend_fontsize=None, title_fontsize=12):
        cns.figure(120, 120)
        ax = cns.sankeyplot(sankey_df, x="source", y="target")
        assert ax.texts
        assert {text.get_fontsize() for text in ax.texts} == {12}
