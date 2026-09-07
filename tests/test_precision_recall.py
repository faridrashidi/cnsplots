from __future__ import annotations

from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score, precision_recall_curve

import cnsplots as cns
from cnsplots.plots._precision_recall import (
    get_precision_recall_results,
    precisionrecallplot,
)


CURVE_COLUMNS = ["model", "recall", "precision", "threshold"]
METRIC_COLUMNS = [
    "model",
    "average_precision",
    "prevalence",
    "method",
    "pos_label",
    "n",
    "n_positive",
    "n_negative",
]


@pytest.mark.parametrize(
    ("labels", "scores"),
    [
        ([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]),
        ([0, 0, 1, 1], [0.1, 0.4, 0.4, 0.8]),
        ([0, 0, 0, 0, 0, 1], [0.2, 0.8, 0.4, 0.1, 0.1, 0.6]),
        ([0, 0, 1, 1], [0.9, 0.7, 0.2, 0.1]),
        ([0, 0, 1, 1], [0.5, 0.5, 0.5, 0.5]),
        ([0, 0, 1, 1], [-3, 0, -1, 4]),
    ],
)
def test_precision_recall_matches_sklearn(
    labels: list[int], scores: list[float]
) -> None:
    data = pd.DataFrame({"truth": labels, "model": scores})
    original = data.copy(deep=True)
    ax = precisionrecallplot(data, "truth", "model")
    expected_precision, expected_recall, thresholds = precision_recall_curve(
        labels, scores
    )
    expected_ap = average_precision_score(labels, scores)
    results = get_precision_recall_results(ax)
    assert list(results["curves"].columns) == CURVE_COLUMNS
    assert list(results["metrics"].columns) == METRIC_COLUMNS
    curves = results["curves"]
    assert curves.model.tolist() == ["model"] * len(expected_recall)
    np.testing.assert_array_equal(curves.recall, expected_recall)
    np.testing.assert_array_equal(curves.precision, expected_precision)
    np.testing.assert_array_equal(curves.threshold.iloc[:-1], thresholds)
    endpoint = curves.iloc[-1]
    assert endpoint.recall == 0
    assert endpoint.precision == 1
    assert np.isnan(endpoint.threshold)
    np.testing.assert_array_equal(ax.lines[0].get_xdata(), expected_recall)
    np.testing.assert_array_equal(ax.lines[0].get_ydata(), expected_precision)
    assert ax.lines[0].get_drawstyle() == "steps-post"
    assert ax.lines[0].get_label() == f"model (AP={expected_ap:.2f})"
    assert results["metrics"].iloc[0].to_dict() == {
        "model": "model",
        "average_precision": pytest.approx(expected_ap),
        "prevalence": np.mean(labels),
        "method": "average_precision",
        "pos_label": 1,
        "n": len(labels),
        "n_positive": sum(labels),
        "n_negative": len(labels) - sum(labels),
    }
    np.testing.assert_array_equal(ax.lines[-1].get_ydata(), [np.mean(labels)] * 2)
    assert ax.lines[-1].get_linestyle() == "--"
    assert ax.lines[-1].get_label() == f"Prevalence={np.mean(labels):.2f}"
    assert ax.get_xlabel() == "Recall"
    assert ax.get_ylabel() == "Precision"
    assert ax.get_xlim() == (-0.02, 1.02)
    assert ax.get_ylim() == (-0.02, 1.02)
    assert not ax.collections
    assert not ax.texts
    pd.testing.assert_frame_equal(data, original)


def test_average_precision_is_not_trapezoidal_area() -> None:
    data = pd.DataFrame({"truth": [0, 0, 1, 1], "score": [0.1, 0.4, 0.35, 0.8]})
    ax = precisionrecallplot(data, "truth", "score")
    metric = get_precision_recall_results(ax)["metrics"].iloc[0]
    assert metric.average_precision == pytest.approx(5 / 6)
    assert metric.average_precision != pytest.approx(19 / 24)
    assert "AUC" not in str(ax.lines[0].get_label())


@pytest.mark.parametrize("dtype", ["int64", "Int64", "uint64"])
def test_large_integer_scores_preserve_ranking_and_thresholds(dtype: str) -> None:
    data = pd.DataFrame(
        {
            "truth": [0, 1],
            "score": pd.Series([2**53, 2**53 + 1], dtype=dtype),
        }
    )
    # Give sklearn the numeric array: its pandas nullable adapter casts to float.
    scores = data.score.to_numpy()
    expected_precision, expected_recall, thresholds = precision_recall_curve(
        data.truth, scores
    )
    ax = precisionrecallplot(data, "truth", "score")
    results = get_precision_recall_results(ax)
    np.testing.assert_array_equal(results["curves"].precision, expected_precision)
    np.testing.assert_array_equal(results["curves"].recall, expected_recall)
    assert results["curves"].threshold.iloc[:-1].tolist() == thresholds.tolist()
    assert np.isnan(results["curves"].threshold.iloc[-1])
    assert results["metrics"].average_precision.iloc[0] == (
        average_precision_score(data.truth, scores)
    )
    assert results["metrics"].average_precision.iloc[0] == 1


@pytest.mark.parametrize(
    ("labels", "pos_label"),
    [
        (["case", "control", "case", "control"], "control"),
        ([2, -1, 2, -1], -1),
        ([True, False, True, False], False),
        ([0.2, 0.9, 0.2, 0.9], 0.9),
    ],
)
def test_positive_class_semantics(labels: list[Any], pos_label: Any) -> None:
    data = pd.DataFrame({"truth": labels, "score": [0.1, 0.9, 0.2, 0.8]})
    ax = precisionrecallplot(data, "truth", "score", pos_label=pos_label)
    metrics = get_precision_recall_results(ax)["metrics"].iloc[0]
    assert metrics.average_precision == 1
    assert metrics.pos_label == pos_label
    assert metrics.n_positive == 2


def test_multiple_models_preserve_order_and_use_explicit_axes(
    roc_df: pd.DataFrame,
) -> None:
    _, (target, current) = plt.subplots(1, 2)
    plt.sca(current)
    ax = precisionrecallplot(roc_df, "truth", ["model_b", "model_a"], ax=target)
    assert ax is target
    assert plt.gca() is current
    assert len(current.lines) == 0
    results = get_precision_recall_results(ax)
    assert results["metrics"].model.tolist() == ["model_b", "model_a"]
    assert results["curves"].model.unique().tolist() == ["model_b", "model_a"]
    legend = ax.get_legend()
    assert legend is not None
    assert [text.get_text() for text in legend.texts] == [
        "model_b (AP=1.00)",
        "model_a (AP=1.00)",
        "Prevalence=0.50",
    ]


def test_precision_recall_works_in_multipanel(roc_df: pd.DataFrame) -> None:
    mp = cns.multipanel(max_width=300)
    mp.panel("A", 100, 100)
    first = precisionrecallplot(roc_df, "truth", "model_a")
    assert first is mp.get_axes("A")
    mp.panel("B", 100, 100)
    second = precisionrecallplot(roc_df, "truth", "model_b")
    assert second is mp.get_axes("B")
    assert get_precision_recall_results()["metrics"].model.tolist() == ["model_b"]
    assert get_precision_recall_results(first)["metrics"].model.tolist() == ["model_a"]


def test_nullable_labels_and_scores_are_supported() -> None:
    data = pd.DataFrame(
        {
            "truth": pd.Series([0, 0, 1, 1], dtype="Int64"),
            "score": pd.Series([0.1, 0.4, 0.35, 0.8], dtype="Float64"),
        }
    )
    ax = precisionrecallplot(data, "truth", "score")
    assert get_precision_recall_results(ax)["metrics"].average_precision.iloc[0] == (
        pytest.approx(5 / 6)
    )


def test_results_are_copies_and_replaced_by_latest_plot(roc_df: pd.DataFrame) -> None:
    ax = precisionrecallplot(roc_df, "truth", "model_a")
    first = get_precision_recall_results(ax)
    first["curves"].loc[:, "precision"] = -1
    first["metrics"].loc[:, "average_precision"] = -1
    stored = get_precision_recall_results(ax)
    assert (stored["curves"].precision >= 0).all()
    assert stored["metrics"].average_precision.iloc[0] == 1
    precisionrecallplot(roc_df, "truth", "model_b", ax=ax)
    assert get_precision_recall_results(ax)["metrics"].model.tolist() == ["model_b"]
    # Removing a previous call's curve does not invalidate the newest results.
    ax.lines[0].remove()
    assert not get_precision_recall_results(ax)["metrics"].empty


@pytest.mark.parametrize("state", ["unplotted", "cleared", "removed"])
def test_unavailable_results_have_fixed_empty_schemas(
    roc_df: pd.DataFrame, state: str
) -> None:
    _, ax = plt.subplots()
    if state != "unplotted":
        precisionrecallplot(roc_df, "truth", "model_a", ax=ax)
        if state == "cleared":
            ax.clear()
        else:
            ax.lines[0].remove()
    results = get_precision_recall_results(ax)
    assert results["curves"].empty
    assert results["metrics"].empty
    assert list(results["curves"].columns) == CURVE_COLUMNS
    assert list(results["metrics"].columns) == METRIC_COLUMNS


@pytest.mark.parametrize(
    ("columns", "error", "message"),
    [
        ([], ValueError, "at least one prediction"),
        (["model_a", "model_a"], ValueError, "must be unique"),
        (["missing"], ValueError, "not found"),
        (None, TypeError, "string or list of strings"),
        ([1], TypeError, "string or list of strings"),
        (("model_a",), TypeError, "string or list of strings"),
    ],
)
def test_invalid_prediction_columns(
    roc_df: pd.DataFrame, columns: Any, error: type[Exception], message: str
) -> None:
    with pytest.raises(error, match=message):
        precisionrecallplot(roc_df, "truth", columns)


@pytest.mark.parametrize(
    ("labels", "pos_label", "message"),
    [
        ([1, 1, 1, 1], 1, "exactly two classes"),
        ([0, 1, 2, 0], 1, "exactly two classes"),
        ([0, 1, None, 0], 1, "null values"),
        ([0, 1, np.nan, 0], 1, "null values"),
        ([0, np.inf, 0, np.inf], 0, "must be finite"),
        (["case", np.inf, "case", np.inf], "case", "must be finite"),
        ([0, 1, 0, 1], 2, "observed class"),
        (["case", "control", "case", "control"], 1, "observed class"),
    ],
)
def test_invalid_labels(labels: list[Any], pos_label: Any, message: str) -> None:
    data = pd.DataFrame({"truth": labels, "score": [0.1, 0.9, 0.2, 0.8]})
    with pytest.raises(ValueError, match=message):
        precisionrecallplot(data, "truth", "score", pos_label=pos_label)


@pytest.mark.parametrize(
    ("scores", "error", "message"),
    [
        ([0.1, np.nan, 0.7, 0.8], ValueError, "must be finite"),
        ([0.1, np.inf, 0.7, 0.8], ValueError, "must be finite"),
        ([0.1, -np.inf, 0.7, 0.8], ValueError, "must be finite"),
        (pd.Series([0.1, pd.NA, 0.7, 0.8], dtype="Float64"), ValueError, "finite"),
        (["0.1", "0.3", "0.7", "0.8"], TypeError, "real numeric"),
        ([1j, 2j, 3j, 4j], TypeError, "real numeric"),
        ([True, False, True, True], TypeError, "real numeric"),
    ],
)
def test_invalid_scores_are_rejected_before_drawing(
    scores: Any, error: type[Exception], message: str
) -> None:
    data = pd.DataFrame(
        {"truth": [0, 0, 1, 1], "valid": [0.1, 0.3, 0.7, 0.8], "invalid": scores}
    )
    _, ax = plt.subplots()
    with pytest.raises(error, match=message):
        precisionrecallplot(data, "truth", ["valid", "invalid"], ax=ax)
    assert not ax.lines
    assert get_precision_recall_results(ax)["curves"].empty


def test_invalid_dataframe_and_ambiguous_columns(roc_df: pd.DataFrame) -> None:
    with pytest.raises(TypeError, match="pandas DataFrame"):
        precisionrecallplot(cast(Any, [0, 1]), "truth", "score")
    with pytest.raises(ValueError, match="empty"):
        precisionrecallplot(roc_df.iloc[:0], "truth", "model_a")
    with pytest.raises(ValueError, match="not found"):
        precisionrecallplot(roc_df, "missing", "model_a")
    duplicated = pd.concat([roc_df, roc_df[["model_a"]]], axis=1)
    with pytest.raises(ValueError, match="Duplicate column"):
        precisionrecallplot(duplicated, "truth", "model_a")
