from __future__ import annotations

import inspect
from collections.abc import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
import seaborn as sns
from matplotlib.axes import Axes

import cnsplots as cns


PLOT_NAMES = [
    "barplot",
    "lollipopplot",
    "stackplot",
    "stripplot",
    "pieplot",
    "donutplot",
    "boxplot",
    "violinplot",
    "distplot",
    "kdeplot",
    "histplot",
    "ridgeplot",
    "qqplot",
    "regplot",
    "scatterplot",
    "lineplot",
    "slopeplot",
    "dumbbellplot",
]


def _artist_count(ax: Axes) -> int:
    return len(ax.lines) + len(ax.collections) + len(ax.patches) + len(ax.texts)


def test_core_plot_axes_are_explicit_keyword_only_parameters() -> None:
    for name in PLOT_NAMES:
        parameter = inspect.signature(getattr(cns, name)).parameters["ax"]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is None


@pytest.mark.parametrize(
    ("wrapper", "seaborn_function"),
    [(cns.histplot, sns.histplot), (cns.lineplot, sns.lineplot)],
)
def test_seaborn_passthrough_signatures_match_named_parameters(
    wrapper: Callable[..., Axes],
    seaborn_function: Callable[..., Axes],
) -> None:
    wrapper_parameters = inspect.signature(wrapper).parameters
    seaborn_parameters = inspect.signature(seaborn_function).parameters

    assert list(wrapper_parameters) == list(seaborn_parameters)
    for name, parameter in seaborn_parameters.items():
        assert wrapper_parameters[name].kind is parameter.kind
        assert wrapper_parameters[name].default == parameter.default


def test_core_plots_draw_on_and_return_supplied_axes(
    categorical_df: pd.DataFrame,
    stack_df: pd.DataFrame,
    numeric_df: pd.DataFrame,
    line_df: pd.DataFrame,
) -> None:
    slope_data = pd.DataFrame(
        {
            "site": ["S1", "S1", "S2", "S2"],
            "value": [1.0, 2.0, 2.0, 1.5],
            "condition": ["before", "after"] * 2,
            "subject": ["P1", "P1", "P2", "P2"],
        }
    )
    dumbbell_data = pd.DataFrame(
        {
            "site": ["S1", "S1", "S2", "S2"],
            "value": [1.0, 2.0, 2.5, 1.5],
            "condition": ["before", "after"] * 2,
        }
    )
    plotters: list[tuple[str, Callable[[Axes], Axes]]] = [
        (
            "barplot",
            lambda ax: cns.barplot(categorical_df, x="group", y="value", ax=ax),
        ),
        (
            "lollipopplot",
            lambda ax: cns.lollipopplot(categorical_df, x="group", y="value", ax=ax),
        ),
        (
            "stackplot",
            lambda ax: cns.stackplot(stack_df, x="treatment", stack="response", ax=ax),
        ),
        (
            "stripplot",
            lambda ax: cns.stripplot(categorical_df, x="group", y="value", ax=ax),
        ),
        ("pieplot", lambda ax: cns.pieplot(categorical_df, x="group", ax=ax)),
        ("donutplot", lambda ax: cns.donutplot(categorical_df, x="group", ax=ax)),
        (
            "boxplot",
            lambda ax: cns.boxplot(categorical_df, x="group", y="value", ax=ax),
        ),
        (
            "violinplot",
            lambda ax: cns.violinplot(categorical_df, x="group", y="value", ax=ax),
        ),
        ("distplot", lambda ax: cns.distplot(numeric_df, x="x", ax=ax)),
        (
            "ridgeplot",
            lambda ax: cns.ridgeplot(categorical_df, "value", "group", ax=ax),
        ),
        ("qqplot", lambda ax: cns.qqplot(numeric_df, x="x", ax=ax)),
        ("regplot", lambda ax: cns.regplot(numeric_df, x="x", y="y", ax=ax)),
        (
            "scatterplot",
            lambda ax: cns.scatterplot(numeric_df, x="x", y="y", ax=ax),
        ),
        (
            "lineplot",
            lambda ax: cns.lineplot(line_df, x="time", y="value", ax=ax),
        ),
        (
            "slopeplot",
            lambda ax: cns.slopeplot(
                slope_data,
                x="site",
                y="value",
                hue="condition",
                pair="subject",
                ax=ax,
            ),
        ),
        (
            "dumbbellplot",
            lambda ax: cns.dumbbellplot(
                dumbbell_data,
                x="site",
                y="value",
                hue="condition",
                ax=ax,
            ),
        ),
    ]

    for name, plotter in plotters:
        _, (target_ax, current_ax) = plt.subplots(1, 2)
        plt.sca(current_ax)

        result = plotter(target_ax)

        assert result is target_ax, name
        assert _artist_count(target_ax) > 0, name
        assert _artist_count(current_ax) == 0, name
        plt.close(target_ax.figure)


@pytest.mark.parametrize("plot_name", ["barplot", "boxplot", "violinplot"])
def test_statistical_pairs_support_explicit_axes(
    plot_name: str,
    categorical_df: pd.DataFrame,
) -> None:
    _, (target_ax, current_ax) = plt.subplots(1, 2)
    plt.sca(current_ax)

    result = getattr(cns, plot_name)(
        categorical_df,
        x="group",
        y="value",
        pairs=[("A", "B")],
        ax=target_ax,
    )

    assert result is target_ax
    assert target_ax.texts
    assert _artist_count(current_ax) == 0


def test_kdeplot_annotations_stay_on_supplied_axes(numeric_df: pd.DataFrame) -> None:
    _, (target_ax, current_ax) = plt.subplots(1, 2)
    plt.sca(current_ax)

    result = cns.kdeplot(numeric_df, x="x", add_mode=True, ax=target_ax)

    assert result is target_ax
    assert target_ax.lines
    assert target_ax.texts
    assert _artist_count(current_ax) == 0


def test_histplot_colorbar_uses_supplied_host_axes() -> None:
    rng = np.random.default_rng(0)
    data = pd.DataFrame({"x": rng.normal(size=100), "y": rng.normal(size=100)})
    _, (target_ax, current_ax) = plt.subplots(1, 2)
    plt.sca(current_ax)

    result = cns.histplot(data, x="x", y="y", cbar=True, ax=target_ax)

    assert result is target_ax
    assert target_ax.collections[0].colorbar is not None
    assert target_ax.collections[0].colorbar.ax.figure is target_ax.figure
    assert _artist_count(current_ax) == 0


def test_passthrough_wrappers_keep_vector_and_wide_form_support() -> None:
    _, (hist_ax, line_ax) = plt.subplots(1, 2)

    hist_result = cns.histplot(x=np.arange(5), ax=hist_ax)
    line_result = cns.lineplot(
        pd.DataFrame({"first": [1, 2, 3], "second": [3, 2, 1]}),
        ax=line_ax,
    )

    assert hist_result is hist_ax
    assert line_result is line_ax


def test_passthrough_wrappers_validate_string_semantic_mappings() -> None:
    data = pd.DataFrame({"x": [1, 2], "y": [2, 3]})

    with pytest.raises(ValueError, match="missing_weight"):
        cns.histplot(data, x="x", weights="missing_weight")
    with pytest.raises(ValueError, match="missing_style"):
        cns.lineplot(data, x="x", y="y", style="missing_style")
