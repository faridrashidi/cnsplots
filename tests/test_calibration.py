"""Numerical and artist contracts for binary probability calibration."""

from __future__ import annotations

from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss

import cnsplots as cns
from cnsplots.plots._calibration import calibrationplot, get_calibration_results


@pytest.mark.parametrize("strategy", ["uniform", "quantile"])
@pytest.mark.parametrize(
    "scores",
    [
        [0, 0.15, 0.25, 0.4, 0.4, 0.75, 0.85, 1],
        [0, 0, 0.5, 0.5, 0.5, 0.5, 1, 1],
        [0.5] * 8,
    ],
)
def test_calibration_matches_sklearn_with_ties_and_endpoints(
    strategy: str, scores: list[float]
) -> None:
    data = pd.DataFrame(
        {"truth": [0, 0, 1, 0, 1, 1, 0, 1], "first": scores, "second": scores[::-1]}
    )
    original = data.copy(deep=True)
    ax = calibrationplot(
        data, "truth", ["second", "first"], n_bins=8, strategy=cast(Any, strategy)
    )
    results = get_calibration_results(ax)

    pd.testing.assert_frame_equal(data, original)
    assert results["bins"]["model"].tolist() == ["second"] * 8 + ["first"] * 8
    assert results["metrics"]["model"].tolist() == ["second", "first"]
    assert results["metrics"]["strategy"].tolist() == [strategy, strategy]
    assert results["metrics"]["n_bins"].tolist() == [8, 8]
    assert results["metrics"]["method"].tolist() == ["brier_score"] * 2
    assert results["metrics"]["pos_label"].tolist() == [1, 1]
    for index, model in enumerate(["second", "first"]):
        bins = results["bins"].query("model == @model")
        occupied = bins[bins["count"] > 0]
        expected_frequency, expected_probability = calibration_curve(
            data["truth"], data[model], n_bins=8, strategy=strategy
        )
        np.testing.assert_allclose(
            occupied["mean_predicted_probability"], expected_probability
        )
        np.testing.assert_allclose(occupied["observed_frequency"], expected_frequency)
        np.testing.assert_allclose(
            np.asarray(ax.lines[index].get_xdata(), dtype=float), expected_probability
        )
        np.testing.assert_allclose(
            np.asarray(ax.lines[index].get_ydata(), dtype=float), expected_frequency
        )
        assert bins["count"].sum() == len(data)
        assert bins["bin"].tolist() == list(range(8))
        assert (
            bins.loc[
                bins["count"] == 0,
                ["mean_predicted_probability", "observed_frequency"],
            ]
            .isna()
            .all()
            .all()
        )
        metrics = results["metrics"].iloc[index]
        expected_brier = brier_score_loss(data["truth"], data[model])
        assert metrics["brier_score"] == pytest.approx(expected_brier)
        assert metrics[["n", "n_positive", "n_negative"]].tolist() == [8, 4, 4]
        assert ax.lines[index].get_label() == f"{model} (Brier={expected_brier:.3f})"


def test_calibration_uniform_boundaries_include_upper_endpoint() -> None:
    data = pd.DataFrame(
        {"truth": [0, 1, 0, 1, 0, 1], "probability": np.linspace(0, 1, 6)}
    )
    ax = calibrationplot(data, "truth", "probability")
    bins = get_calibration_results(ax)["bins"]

    assert bins["count"].tolist() == [2, 1, 1, 1, 1]
    np.testing.assert_allclose(bins["bin_lower"], np.linspace(0, 1, 6)[:-1])
    np.testing.assert_allclose(bins["bin_upper"], np.linspace(0, 1, 6)[1:])
    np.testing.assert_allclose(bins["observed_frequency"], [0.5, 0, 1, 0, 1])


def test_calibration_quantile_repeated_boundaries_remain_empty() -> None:
    data = pd.DataFrame({"truth": [0, 1, 0, 1], "probability": [0.4] * 4})
    ax = calibrationplot(data, "truth", "probability", strategy="quantile")
    bins = get_calibration_results(ax)["bins"]

    assert bins["count"].tolist() == [4, 0, 0, 0, 0]
    assert bins["bin_lower"].tolist() == [0.4] * 5
    assert bins["bin_upper"].tolist() == [0.4] * 5
    np.testing.assert_allclose(np.asarray(ax.lines[0].get_xdata(), dtype=float), [0.4])
    np.testing.assert_allclose(np.asarray(ax.lines[0].get_ydata(), dtype=float), [0.5])


@pytest.mark.parametrize("pos_label", ["case", "control", 2, 3, False, True])
def test_calibration_respects_explicit_positive_label(pos_label: Any) -> None:
    labels = ["control", "case"] if isinstance(pos_label, str) else [2, 3]
    if isinstance(pos_label, bool):
        labels = [False, True]
    data = pd.DataFrame({"truth": labels * 2, "probability": [0, 0.4, 0.8, 1]})
    ax = calibrationplot(
        data, "truth", "probability", pos_label=pos_label, n_bins=1, brier_show=False
    )
    results = get_calibration_results(ax)

    assert results["metrics"].iloc[0]["pos_label"] == pos_label
    assert results["metrics"].iloc[0]["brier_score"] == pytest.approx(
        brier_score_loss(data["truth"] == pos_label, data["probability"])
    )
    np.testing.assert_allclose(np.asarray(ax.lines[0].get_xdata(), dtype=float), [0.55])
    np.testing.assert_allclose(np.asarray(ax.lines[0].get_ydata(), dtype=float), [0.5])
    assert ax.lines[0].get_label() == "probability"


def test_calibration_axes_identity_legend_and_multipanel(roc_df: pd.DataFrame) -> None:
    mp = cns.multipanel(max_width=450)
    target = mp.panel("A", width=140, height=140)
    other = mp.panel("B", width=140, height=140)
    ax = calibrationplot(roc_df, "truth", ["model_b", "model_a"], ax=target)

    assert ax is target
    assert plt.gca() is other
    assert len(other.lines) == 0
    assert len(ax.lines) == 3
    np.testing.assert_array_equal(ax.lines[-1].get_xdata(), [0, 1])
    np.testing.assert_array_equal(ax.lines[-1].get_ydata(), [0, 1])
    assert ax.lines[-1].get_linestyle() == "--"
    assert ax.lines[0].get_marker() == "o"
    legend = ax.get_legend()
    assert legend is not None
    assert [text.get_text() for text in legend.texts] == [
        ax.lines[0].get_label(),
        ax.lines[1].get_label(),
    ]
    assert ax.get_xlabel() == "Mean Predicted Probability"
    assert ax.get_ylabel() == "Observed Event Frequency"
    assert ax.get_xlim() == pytest.approx((-0.02, 1.02))
    assert ax.get_ylim() == pytest.approx((-0.02, 1.02))
    assert calibrationplot(roc_df, "truth", "model_a") is other
    assert get_calibration_results()["metrics"]["model"].tolist() == ["model_a"]
    assert get_calibration_results(target)["metrics"]["model"].tolist() == [
        "model_b",
        "model_a",
    ]


def test_calibration_results_are_detached_latest_and_clearable(
    roc_df: pd.DataFrame,
) -> None:
    _, ax = plt.subplots()
    empty = get_calibration_results(ax)
    assert empty["bins"].empty
    assert empty["metrics"].empty
    calibrationplot(roc_df, "truth", "model_a", ax=ax)
    first = get_calibration_results(ax)
    assert first["bins"].columns.tolist() == empty["bins"].columns.tolist()
    assert first["metrics"].columns.tolist() == empty["metrics"].columns.tolist()
    first["bins"].loc[0, "count"] = 999
    first["metrics"].loc[0, "brier_score"] = 999
    assert get_calibration_results(ax)["bins"].loc[0, "count"] != 999
    assert get_calibration_results(ax)["metrics"].loc[0, "brier_score"] != 999

    calibrationplot(roc_df, "truth", "model_b", ax=ax)
    assert get_calibration_results(ax)["metrics"]["model"].tolist() == ["model_b"]
    ax.lines[-2].remove()
    assert get_calibration_results(ax)["bins"].empty
    calibrationplot(roc_df, "truth", "model_b", ax=ax)
    ax.clear()
    pd.testing.assert_frame_equal(get_calibration_results(ax)["bins"], empty["bins"])
    pd.testing.assert_frame_equal(
        get_calibration_results(ax)["metrics"], empty["metrics"]
    )


@pytest.mark.parametrize(
    ("scores", "message"),
    [
        ([0.1, None], "Null values"),
        ([0.1, np.nan], "Null values"),
        ([0.1, np.inf], "finite scores"),
        ([0.1, -np.inf], "finite scores"),
        ([0.1, -0.01], r"in \[0, 1\]"),
        ([0.1, 1.01], r"in \[0, 1\]"),
        (["0.1", "0.9"], "real numeric scores"),
        ([0.1j, 0.9], "real numeric scores"),
        ([False, True], "real numeric scores"),
    ],
)
def test_calibration_rejects_invalid_scores_before_drawing(
    scores: list[Any], message: str
) -> None:
    data = pd.DataFrame({"truth": [0, 1], "valid": [0.1, 0.9], "invalid": scores})
    _, ax = plt.subplots()
    with pytest.raises(ValueError, match=message):
        calibrationplot(data, "truth", ["valid", "invalid"], ax=ax)
    assert len(ax.lines) == 0
    assert get_calibration_results(ax)["metrics"].empty


@pytest.mark.parametrize(
    ("labels", "message"),
    [
        ([0, None], "Null values"),
        ([0, 0], "exactly two classes"),
        ([1, 1], "exactly two classes"),
        (["case", "case"], "exactly two classes"),
        ([0, 1, 2], "exactly two classes"),
        ([0, np.inf], "finite and noncomplex"),
        ([0j, 1j], "finite and noncomplex"),
        (["control", "case"], "'pos_label' must be an observed"),
    ],
)
def test_calibration_rejects_invalid_labels(labels: list[Any], message: str) -> None:
    data = pd.DataFrame({"truth": labels, "probability": [0.5] * len(labels)})
    with pytest.raises(ValueError, match=message):
        calibrationplot(data, "truth", "probability")


@pytest.mark.parametrize("n_bins", [0, -1, 1.5, True, np.bool_(True), "5"])
def test_calibration_rejects_invalid_bin_count(
    roc_df: pd.DataFrame, n_bins: Any
) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        calibrationplot(roc_df, "truth", "model_a", n_bins=n_bins)


def test_calibration_validates_columns_and_structure(roc_df: pd.DataFrame) -> None:
    with pytest.raises(TypeError, match="pandas DataFrame"):
        calibrationplot(cast(Any, {}), "truth", "model_a")
    with pytest.raises(ValueError, match="At least one prediction column"):
        calibrationplot(roc_df, "truth", [])
    with pytest.raises(ValueError, match="Prediction columns must be unique"):
        calibrationplot(roc_df, "truth", ["model_a", "model_a"])
    with pytest.raises(ValueError, match="not found in data"):
        calibrationplot(roc_df, "truth", "missing")
    duplicate = pd.concat([roc_df, roc_df[["model_a"]]], axis=1)
    with pytest.raises(ValueError, match="Duplicate column"):
        calibrationplot(duplicate, "truth", "model_a")
    with pytest.raises(ValueError, match="Data is empty"):
        calibrationplot(roc_df.iloc[:0], "truth", "model_a")
    with pytest.raises(ValueError, match="'strategy' must be"):
        calibrationplot(roc_df, "truth", "model_a", strategy=cast(Any, "invalid"))
    with pytest.raises(ValueError, match="'pos_label' must be an observed"):
        calibrationplot(roc_df, "truth", "model_a", pos_label=2)


def test_calibration_accepts_nullable_numeric_columns_and_numpy_bin_count() -> None:
    data = pd.DataFrame(
        {"truth": pd.Series([0, 1], dtype="Int64"), "probability": [0.1, 0.9]}
    ).astype({"probability": "Float64"})
    ax = calibrationplot(data, "truth", "probability", n_bins=cast(Any, np.int64(2)))
    assert get_calibration_results(ax)["bins"]["count"].tolist() == [1, 1]


@pytest.mark.parametrize("dtype", ["object", "category"])
@pytest.mark.parametrize("invalid_label", [np.inf, 1j])
def test_calibration_rejects_invalid_label_scalars(
    dtype: str, invalid_label: Any
) -> None:
    data = pd.DataFrame(
        {
            "truth": pd.Series([0, invalid_label], dtype=dtype),
            "probability": [0.1, 0.9],
        }
    )
    with pytest.raises(ValueError, match="finite and noncomplex"):
        calibrationplot(data, "truth", "probability")


@pytest.mark.parametrize("columns", [None, 1, ["model_a", 1], ("model_a",)])
def test_calibration_rejects_invalid_column_selection_types(
    roc_df: pd.DataFrame, columns: Any
) -> None:
    with pytest.raises(TypeError, match="string or list of strings"):
        calibrationplot(roc_df, "truth", columns)
