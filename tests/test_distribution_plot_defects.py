"""Regression tests for distribution plot validation."""

from typing import Any

import numpy as np
import pandas as pd
import pytest

import cnsplots as cns


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
