from __future__ import annotations

import logging
from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from cycler import cycler
from matplotlib.colors import to_hex, to_rgba
from matplotlib.patches import (
    Circle,
    FancyBboxPatch,
    PathPatch,
    Polygon,
    Rectangle,
    Wedge,
)

import cnsplots as cns


def _line_xy(line: Any) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.asarray(line.get_xdata(), dtype=float),
        np.asarray(line.get_ydata(), dtype=float),
    )


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
            add_count=True,
            showoutliers=True,
            whis=(0, 100),
        )
    assert ax.get_xticklabels()[0].get_text().startswith("A")
    assert "minimum and maximum values" in caplog.text
    assert calls
    box_patches = [patch for patch in ax.patches if isinstance(patch, PathPatch)]
    box_quartiles = []
    for patch in box_patches:
        vertices = np.asarray(patch.get_path().vertices, dtype=float)
        box_quartiles.append([vertices[:, 1].min(), vertices[:, 1].max()])
    np.testing.assert_allclose(
        box_quartiles,
        [[1.075, 1.325], [2.075, 2.225], [3.075, 3.225]],
    )
    median_values = []
    for line in ax.lines:
        x_data, y_data = _line_xy(line)
        if len(x_data) == 2 and np.ptp(x_data) > 0 and np.ptp(y_data) == 0:
            median_values.append(float(y_data[0]))
    np.testing.assert_allclose(median_values, [1.2, 2.15, 3.15])

    cns.figure(120, 120)
    ax2 = cns.violinplot(
        categorical_df,
        x="group",
        y="value",
        pairs=[("A", "B")],
        add_box=True,
        add_count=True,
        hue="hue",
        split=True,
        inner="quart",
    )
    assert len(ax2.collections) > 0

    cns.figure(120, 120)
    ax3 = cns.violinplot(categorical_df, x="group", y="value", add_box=False)
    assert ax3 is plt.gca()


@pytest.mark.parametrize(
    ("box_kwargs", "expected_color"),
    [({}, "white"), ({"box_color": "#d95f02"}, "#d95f02")],
)
def test_violinplot_box_color(
    categorical_df: pd.DataFrame,
    box_kwargs: dict[str, Any],
    expected_color: str,
) -> None:
    cns.figure(120, 120)
    ax = cns.violinplot(
        categorical_df,
        x="group",
        y="value",
        hue="hue",
        inner=None,
        **box_kwargs,
    )

    box_patches = [patch for patch in ax.patches if isinstance(patch, PathPatch)]
    assert box_patches
    assert {patch.get_facecolor() for patch in box_patches} == {to_rgba(expected_color)}


def test_violinplot_box_color_none_follows_hue(
    categorical_df: pd.DataFrame,
) -> None:
    cns.figure(120, 120)
    ax = cns.violinplot(
        categorical_df,
        x="group",
        y="value",
        hue="hue",
        inner=None,
        box_color=None,
    )

    box_patches = [patch for patch in ax.patches if isinstance(patch, PathPatch)]
    assert len({patch.get_facecolor() for patch in box_patches}) > 1


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
        add_tip=True,
        palette="palette_group",
    )
    legend = ax.get_legend()
    assert legend is not None
    assert legend.get_title().get_text() == "palette_group"
    np.testing.assert_allclose(
        [cast(Rectangle, patch).get_height() for patch in ax.patches],
        [1.2, 2.15, 3.15],
    )
    assert [text.get_text() for text in ax.texts] == ["1.2", "2.15", "3.15"]

    cns.figure(120, 120)
    ax2 = cns.lollipopplot(
        categorical_df,
        x="group",
        y="value",
        hue="hue",
        pairs=[(("A", "H1"), ("A", "H2"))],
        add_tip=True,
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
        add_tip=True,
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
        bar_ax = cns.barplot(categorical_df, x="group", y="value", add_tip=True)
        assert {text.get_fontsize() for text in bar_ax.texts} == {13}

        cns.figure(120, 120)
        lollipop_ax = cns.lollipopplot(
            categorical_df, x="group", y="value", add_tip=True
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
        stack="response",
        normalize=True,
        add_count=True,
        pairs=[("A", "B")],
        order=["A", "B", "C"],
        stack_order=["Yes", "No"],
    )
    assert ax.get_ylabel() == "Frequency"
    assert [tick.get_text() for tick in ax.get_xticklabels()] == [
        "A\n(n=4)",
        "B\n(n=4)",
        "C\n(n=4)",
    ]
    np.testing.assert_allclose(
        [cast(Rectangle, patch).get_height() for patch in ax.patches], [0.5] * 6
    )
    assert not ax.texts

    cns.figure(120, 120)
    ax2 = cns.stackplot(
        categorical_df.rename(columns={"group": "treatment", "binary": "response"}),
        y="treatment",
        stack="response",
        normalize=False,
        pairs=[("A", "B")],
        order=["A", "B", "C"],
        stack_order=["No", "Yes"],
    )
    assert ax2.get_xlabel() == "Count"
    np.testing.assert_allclose(
        [cast(Rectangle, patch).get_width() for patch in ax2.patches], [2.0] * 6
    )

    cns.figure(120, 120)
    ax2b = cns.stackplot(
        stack_df,
        y="treatment",
        stack="response",
        normalize=False,
        add_count=True,
    )
    assert {tick.get_text() for tick in ax2b.get_yticklabels()} == {
        "A\n(n=4)",
        "B\n(n=4)",
        "C\n(n=4)",
    }
    assert not ax2b.texts

    cns.figure(120, 120)
    ax3 = cns.stripplot(
        categorical_df,
        x="group",
        y="value",
        hue="hue",
        showmeans=True,
        add_count=True,
    )
    assert ax3.get_legend() is not None

    cns.figure(120, 120)
    ax4 = cns.pieplot(categorical_df, x="group", legend="left", order=["C", "B", "A"])
    assert ax4.get_legend() is not None
    pie_wedges = [patch for patch in ax4.patches if isinstance(patch, Wedge)]
    np.testing.assert_allclose(
        [patch.theta2 - patch.theta1 for patch in pie_wedges], [120.0] * 3
    )

    cns.figure(120, 120)
    ax5 = cns.donutplot(categorical_df, x="group", legend="top", order=["A", "B", "C"])
    assert ax5.get_legend() is not None
    assert any(text.get_text() == "group" for text in ax5.texts)
    donut_wedges = [patch for patch in ax5.patches if isinstance(patch, Wedge)]
    np.testing.assert_allclose(
        [patch.theta2 - patch.theta1 for patch in donut_wedges], [120.0] * 3
    )
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
    assert "Kolmogorov-Smirnov test" in caplog.text

    cns.figure(120, 120)
    ax4 = cns.histplot(data=numeric_df, x="x", kde=True)
    assert sum(
        cast(Rectangle, patch).get_height() for patch in ax4.patches
    ) == pytest.approx(len(numeric_df))

    cns.figure(120, 120)
    ax5 = cns.ridgeplot(categorical_df, x="value", y="group", cmap="viridis")
    assert ax5.get_xlabel() == "value"

    cns.figure(120, 120)
    ax6 = cns.qqplot(numeric_df, x="x")
    assert ax6 is plt.gca()


@pytest.mark.parametrize(
    "plot_name",
    [
        "barplot",
        "boxplot",
        "violinplot",
        "stripplot",
        "distplot",
        "kdeplot",
        "histplot",
        "scatterplot",
        "lineplot",
    ],
)
def test_seaborn_wrappers_respect_explicit_hue_order(plot_name: str) -> None:
    data = pd.DataFrame(
        {
            "category": ["A", "A", "B", "B", "C", "C"] * 2,
            "hue": ["H1"] * 6 + ["H2"] * 6,
            "time": [0, 1, 2, 0, 1, 2] * 2,
            "value": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0] + [0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
        }
    )
    data["other"] = data["value"] * 2
    hue_order = ["H2", "H1"]

    if plot_name in {"barplot", "boxplot", "violinplot", "stripplot"}:
        kwargs: dict[str, Any] = {
            "data": data,
            "x": "category",
            "y": "value",
            "order": ["C", "B", "A"],
        }
    elif plot_name in {"distplot", "kdeplot", "histplot"}:
        kwargs = {"data": data, "x": "value"}
    elif plot_name == "scatterplot":
        kwargs = {"data": data, "x": "value", "y": "other"}
    else:
        kwargs = {"data": data, "x": "time", "y": "value"}

    cns.figure(120, 120)
    ax = getattr(cns, plot_name)(
        **kwargs,
        hue="hue",
        hue_order=hue_order,
    )

    legend = ax.get_legend()
    assert legend is not None
    assert [text.get_text() for text in legend.get_texts()][:2] == hue_order
    if "order" in kwargs:
        assert [tick.get_text() for tick in ax.get_xticklabels()] == kwargs["order"]


@pytest.mark.parametrize("plot_name", ["pieplot", "donutplot"])
def test_circular_plots_respect_category_order(plot_name: str) -> None:
    data = pd.DataFrame({"group": ["A"] + ["B"] * 2 + ["C"] * 3})
    order = ["A", "C", "B"]

    cns.figure(120, 120)
    ax = getattr(cns, plot_name)(data, x="group", order=order)

    legend = ax.get_legend()
    assert legend is not None
    assert [text.get_text() for text in legend.get_texts()] == order
    wedges = [patch for patch in ax.patches if isinstance(patch, Wedge)]
    np.testing.assert_allclose(
        [patch.theta2 - patch.theta1 for patch in wedges],
        [60.0, 180.0, 120.0],
    )


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
        ax = cns.pieplot(data, x="group", order=["dark", "light"])

    percent_texts = [text for text in ax.texts if text.get_text().endswith("%")]
    assert [text.get_color() for text in percent_texts] == ["white", "black"]

    with cns.settings.context(annotation_auto_contrast=False):
        cns.figure(120, 120)
        with plt.rc_context({"axes.prop_cycle": cycler(color=["#111111", "#eeeeee"])}):
            ax = cns.pieplot(data, x="group", order=["dark", "light"])

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
        assert "Kolmogorov-Smirnov test" not in caplog.text

    with cns.settings.context(verbosity=1):
        caplog.clear()
        cns.figure(120, 120)
        cns.kdeplot(data, x="score", hue="hue")
        assert "Kolmogorov-Smirnov test" in caplog.text


def test_line_scatter_reg_and_slope_plots(
    numeric_df: pd.DataFrame,
    line_df: pd.DataFrame,
) -> None:
    cns.figure(120, 120)
    ax = cns.regplot(numeric_df, x="x", y="y")
    assert "$r$" in ax.texts[0].get_text()

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
    ax6 = cns.slopeplot(slope_df, x="site", y="value", hue="label", pair="site")
    assert ax6.get_legend() is not None


def test_placeholderplot_renders_centered_placeholder() -> None:
    with cns.settings.context(title_fontsize=11, title_fontweight="normal"):
        cns.figure(180, 120)
        plt.plot([0, 1], [0, 1])
        ax = cns.placeholderplot("A description to be centered in the panel")

        assert ax is plt.gca()
        assert len(ax.lines) == 0
        assert len(ax.texts) == 1
        assert len(ax.patches) >= 6

        text = ax.texts[0]
        assert text.get_text() == "A description to be centered in the panel"
        assert text.get_horizontalalignment() == "center"
        assert text.get_verticalalignment() == "center"
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
) -> None:
    cns.figure(120, 120)
    axes = cns.upsetplot(sets_fixture, min_subset_size=1)
    assert set(axes) >= {"matrix", "intersections"}
    assert all(ax is None or ax.get_facecolor()[-1] == 0 for ax in axes.values())
    matrix_ax = axes["matrix"]
    shading_ax = axes["shading"]
    assert matrix_ax is not None
    assert shading_ax is not None
    assert matrix_ax.figure.patch.get_facecolor()[-1] == 0
    assert all(
        not tick.tick1line.get_visible() for tick in shading_ax.yaxis.get_major_ticks()
    )

    fig = plt.figure()
    embedded_axes = cns.upsetplot(sets_fixture, fig=fig, min_subset_size=1)
    assert all(ax is None or ax.figure is fig for ax in embedded_axes.values())
    assert fig.patch.get_facecolor()[-1] == 0

    with cns.settings.context(legend_fontsize=None, title_fontsize=12):
        cns.figure(120, 120)
        inherited_axes = cns.upsetplot(sets_fixture, min_subset_size=1)
        intersections_ax = inherited_axes["intersections"]
        assert intersections_ax is not None
        assert intersections_ax.texts
        assert {text.get_fontsize() for text in intersections_ax.texts} == {12}

    custom_fig = plt.figure()
    custom_fig.patch.set_facecolor("red")
    custom_fig.patch.set_alpha(1)
    cns.upsetplot(sets_fixture, fig=custom_fig, min_subset_size=1)
    assert custom_fig.patch.get_facecolor() == to_rgba("red")

    cns.figure(120, 120)
    venn = cns.vennplot(list(sets_fixture.values())[:2], labels=["A", "B"])
    assert {
        area: venn.get_label_by_id(area).get_text() for area in ["10", "01", "11"]
    } == {"10": "1", "01": "1", "11": "2"}
    assert [venn.get_label_by_id(area).get_text() for area in ["A", "B"]] == [
        "A",
        "B",
    ]

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

    roc_df = pd.DataFrame(
        {
            "truth": [0, 0, 1, 1],
            "model_a": [0.1, 0.4, 0.35, 0.8],
            "model_b": [0.1, 0.8, 0.4, 0.7],
        }
    )
    cns.figure(120, 120)
    ax2 = cns.rocplot(roc_df, "truth", "model_a")
    model_a_x, model_a_y = _line_xy(ax2.lines[0])
    diagonal_x, diagonal_y = _line_xy(ax2.lines[1])
    np.testing.assert_allclose(model_a_x, [0, 0, 0.5, 0.5, 1])
    np.testing.assert_allclose(model_a_y, [0, 0.5, 0.5, 1, 1])
    assert ax2.lines[0].get_label() == "model_a (AUC=0.75)"
    np.testing.assert_allclose(diagonal_x, [0, 1])
    np.testing.assert_allclose(diagonal_y, [0, 1])

    cns.figure(120, 120)
    ax3 = cns.rocplot(roc_df, "truth", ["model_a", "model_b"])
    assert [line.get_label() for line in ax3.lines[:2]] == [
        "model_a (AUC=0.75)",
        "model_b (AUC=0.50)",
    ]
    model_a_x, model_a_y = _line_xy(ax3.lines[0])
    model_b_x, model_b_y = _line_xy(ax3.lines[1])
    diagonal_x, diagonal_y = _line_xy(ax3.lines[2])
    np.testing.assert_allclose(model_a_x, [0, 0, 0.5, 0.5, 1])
    np.testing.assert_allclose(model_a_y, [0, 0.5, 0.5, 1, 1])
    np.testing.assert_allclose(model_b_x, [0, 0.5, 0.5, 1])
    np.testing.assert_allclose(model_b_y, [0, 0, 1, 1])
    np.testing.assert_allclose(diagonal_x, [0, 1])
    np.testing.assert_allclose(diagonal_y, [0, 1])


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
