"""Regression tests for distribution plot validation."""

from typing import Any
from types import SimpleNamespace
from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from scipy.stats import ks_2samp

import cnsplots as cns


@pytest.mark.parametrize("fill", [False, True])
@pytest.mark.parametrize("categorical", [False, True])
def test_kdeplot_tests_exactly_the_plotted_observations(
    fill: bool, categorical: bool
) -> None:
    data = pd.DataFrame(
        {
            "group": ["A"] * 6 + ["B"] * 5 + [None],
            "value": [1.0, 1.2, 1.4, np.nan, np.inf, -np.inf]
            + [2.0, 2.2, 2.4, 2.6, np.nan]
            + [100.0],
            "unrelated": [np.nan] * 12,
        }
    )
    if categorical:
        data["group"] = pd.Categorical(data["group"], categories=["unused", "B", "A"])
    original = data.copy(deep=True)
    expected = data.loc[data["group"].notna() & np.isfinite(data["value"])]
    _, (ax, reference_ax) = plt.subplots(1, 2)

    with patch(
        "cnsplots.plots._distribution.sp.stats.ks_2samp", wraps=ks_2samp
    ) as test:
        cns.kdeplot(data, x="value", hue="group", fill=fill, ax=ax)

    test.assert_called_once()
    samples = sorted(test.call_args.args, key=lambda sample: sample[0])
    np.testing.assert_array_equal(samples[0], [1.0, 1.2, 1.4])
    np.testing.assert_array_equal(samples[1], [2.0, 2.2, 2.4, 2.6])
    assert ks_2samp(*samples).pvalue == pytest.approx(0.05714285714285715)
    assert [text.get_text() for text in ax.texts] == [r"$P=0.057$"]
    cns.kdeplot(expected, x="value", hue="group", fill=fill, ax=reference_ax)
    if fill:
        for actual, reference in zip(ax.collections, reference_ax.collections):
            np.testing.assert_allclose(
                actual.get_paths()[0].vertices, reference.get_paths()[0].vertices
            )
    else:
        for actual, reference in zip(ax.lines, reference_ax.lines):
            np.testing.assert_allclose(actual.get_xydata(), reference.get_xydata())
    pd.testing.assert_frame_equal(data, original)


@pytest.mark.parametrize("hue_order", [["B", "A"], ["A"], ["missing"], []])
def test_kdeplot_comparison_respects_hue_subset(hue_order: list[str]) -> None:
    data = pd.DataFrame(
        {"group": ["A"] * 3 + ["B"] * 3 + ["C"] * 3, "value": np.arange(9.0)}
    )
    with patch(
        "cnsplots.plots._distribution.sp.stats.ks_2samp", wraps=ks_2samp
    ) as test:
        ax = cns.kdeplot(data, x="value", hue="group", hue_order=hue_order)

    if len(hue_order) == 2:
        test.assert_called_once()
        samples = sorted(test.call_args.args, key=lambda sample: sample[0])
        np.testing.assert_array_equal(samples[0], [0.0, 1.0, 2.0])
        np.testing.assert_array_equal(samples[1], [3.0, 4.0, 5.0])
        assert len(ax.texts) == 1
    else:
        test.assert_not_called()
        assert not ax.texts
    assert len(ax.lines) == len(set(hue_order) & {"A", "B", "C"})


@pytest.mark.parametrize("values", [[np.nan, np.inf], [2.0, np.nan], [2.0, 2.0]])
@pytest.mark.parametrize("fill", [False, True])
def test_kdeplot_does_not_compare_undrawn_groups(
    values: list[float], fill: bool
) -> None:
    data = pd.DataFrame(
        {"group": ["A"] * 3 + ["B"] * len(values), "value": [0.0, 0.5, 1.0] + values}
    )
    ax = plt.gca()
    ax.plot([0, 1], [0, 1])
    with patch("cnsplots.plots._distribution.sp.stats.ks_2samp") as test:
        cns.kdeplot(data, x="value", hue="group", fill=fill, warn_singular=False, ax=ax)

    test.assert_not_called()
    assert not ax.texts
    assert len(ax.lines) + len(ax.collections) == 2


@pytest.mark.parametrize("values", [[np.nan, np.inf], [1.0, np.nan], [1.0, 1.0]])
def test_kdeplot_does_not_annotate_old_lines_without_a_density(
    values: list[float],
) -> None:
    ax = plt.gca()
    ax.plot([0, 1], [0, 1])

    cns.kdeplot(pd.DataFrame({"value": values}), x="value", warn_singular=False, ax=ax)

    assert len(ax.lines) == 1
    assert not ax.texts


@pytest.mark.parametrize("log_scale", [True, (True, False), None])
def test_kdeplot_logarithmic_comparison_uses_positive_values(log_scale: Any) -> None:
    data = pd.DataFrame(
        {
            "group": ["A"] * 5 + ["B"] * 5,
            "value": [-1.0, 0.0, 1.0, 2.0, 3.0, -2.0, 0.0, 4.0, 5.0, 6.0],
        }
    )
    ax = plt.gca()
    if log_scale is None:
        ax.set_xscale("log")
    with patch(
        "cnsplots.plots._distribution.sp.stats.ks_2samp", wraps=ks_2samp
    ) as test:
        cns.kdeplot(data, x="value", hue="group", log_scale=log_scale, ax=ax)

    test.assert_called_once()
    np.testing.assert_array_equal(test.call_args.args[0], [1.0, 2.0, 3.0])
    np.testing.assert_array_equal(test.call_args.args[1], [4.0, 5.0, 6.0])
    assert len(ax.texts) == 1


def test_kdeplot_nullable_numeric_values() -> None:
    data = pd.DataFrame(
        {
            "group": pd.Series(["A", "A", "A", "B", "B", None], dtype="string"),
            "value": pd.Series([1.0, 2.0, pd.NA, 3.0, 4.0, 5.0], dtype="Float64"),
        }
    )

    ax = cns.kdeplot(data, x="value", hue="group")

    assert len(ax.lines) == 2
    assert [text.get_text() for text in ax.texts] == [r"$P=0.33$"]


@pytest.mark.parametrize("variable", ["weights", "y"])
@pytest.mark.filterwarnings(
    "ignore:The following kwargs were not used by contour.*linewidth:UserWarning"
)
def test_kdeplot_omits_unweighted_univariate_test_for_other_densities(
    variable: str, numeric_df: pd.DataFrame
) -> None:
    # Keep vector kwargs aligned with the original rows, including missing x.
    data = numeric_df.copy()
    data.loc[0, "x"] = np.nan
    with patch("cnsplots.plots._distribution.sp.stats.ks_2samp") as test:
        ax = cns.kdeplot(data, x="x", hue="group", **{variable: data["y"].to_numpy()})

    test.assert_not_called()
    assert ax.has_data()
    assert not ax.texts


def test_kdeplot_omits_nonfinite_test_result(
    numeric_df: pd.DataFrame, caplog: pytest.LogCaptureFixture
) -> None:
    with patch(
        "cnsplots.plots._distribution.sp.stats.ks_2samp",
        return_value=SimpleNamespace(pvalue=np.nan),
    ):
        ax = cns.kdeplot(numeric_df, x="x", hue="group")

    assert not ax.texts
    assert "nonfinite p-value; omitted" in caplog.text


@pytest.mark.parametrize(
    ("plotter", "function_name"),
    [
        (cns.boxplot, "boxplot"),
        (cns.violinplot, "violinplot"),
        (cns.stripplot, "stripplot"),
        (cns.ridgeplot, "ridgeplot"),
    ],
)
def test_distribution_plot_rejects_all_null_values(
    plotter: Any, function_name: str
) -> None:
    data = pd.DataFrame({"group": ["A", "A", "B"], "value": [np.nan] * 3})

    with pytest.raises(
        ValueError, match=rf"\[{function_name}\].*contain only null values"
    ):
        plotter(data, x="group", y="value")


@pytest.mark.parametrize(
    ("plotter", "function_name"),
    [
        (cns.boxplot, "boxplot"),
        (cns.violinplot, "violinplot"),
        (cns.stripplot, "stripplot"),
        (cns.ridgeplot, "ridgeplot"),
    ],
)
def test_distribution_plot_rejects_data_without_complete_rows(
    plotter: Any, function_name: str
) -> None:
    data = pd.DataFrame({"group": ["A", None], "value": [None, 1.0]})

    with pytest.raises(ValueError, match=rf"\[{function_name}\].*no complete rows"):
        plotter(data, x="group", y="value")


@pytest.mark.parametrize(
    ("plotter", "x", "y"),
    [
        (cns.boxplot, "group", "value"),
        (cns.violinplot, "group", "value"),
        (cns.stripplot, "group", "value"),
        (cns.barplot, "group", "value"),
        (cns.ridgeplot, "value", "group"),
    ],
)
def test_distribution_plot_allows_partial_null_values(
    plotter: Any, x: str, y: str
) -> None:
    data = pd.DataFrame(
        {
            "group": ["A", "A", "A", "B", "B", "B"],
            "value": [1.0, np.nan, 1.2, 2.0, 2.2, np.nan],
        }
    )

    ax = plotter(data, x=x, y=y)

    assert ax.has_data()


@pytest.mark.parametrize(
    ("plotter", "function_name"),
    [
        (cns.boxplot, "boxplot"),
        (cns.violinplot, "violinplot"),
        (cns.stripplot, "stripplot"),
        (cns.ridgeplot, "ridgeplot"),
    ],
)
def test_distribution_plot_rejects_duplicate_column_names(
    plotter: Any, function_name: str
) -> None:
    data = pd.DataFrame(
        [["A", 1.0, 2.0], ["A", 2.0, 3.0], ["B", 3.0, 4.0]],
        columns=pd.Index(["group", "value", "value"]),
    )

    with pytest.raises(ValueError, match=rf"\[{function_name}\] Duplicate column name"):
        plotter(data, x="group", y="value")
