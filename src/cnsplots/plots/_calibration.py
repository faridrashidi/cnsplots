"""Calibration curves for supplied binary prediction probabilities."""

from __future__ import annotations

from typing import Literal, TypedDict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes

from cnsplots._validation import (
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
    validate_no_nulls,
)

_BIN_COLUMNS = [
    "model",
    "bin",
    "bin_lower",
    "bin_upper",
    "count",
    "mean_predicted_probability",
    "observed_frequency",
]
_METRIC_COLUMNS = [
    "model",
    "brier_score",
    "method",
    "pos_label",
    "n",
    "n_positive",
    "n_negative",
    "strategy",
    "n_bins",
]


class CalibrationResults(TypedDict):
    """Tables describing calibration bins and probabilistic prediction quality."""

    bins: pd.DataFrame
    metrics: pd.DataFrame


def get_calibration_results(ax: Axes | None = None) -> CalibrationResults:
    """Return detached tables from the latest calibrationplot call on an axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes, optional
        Axes returned by calibrationplot. Defaults to the current axes.

    Returns
    -------
    CalibrationResults
        A dictionary containing two DataFrames. ``bins`` contains ``model``,
        zero-based ``bin``, ``bin_lower``, ``bin_upper``, ``count``,
        ``mean_predicted_probability``, and ``observed_frequency``. Rows follow
        prediction-column order, then ascending bin order. Empty bins have zero
        count and NaN means; repeated quantile boundaries are retained. The
        first bin includes both boundaries; later bins exclude their lower
        boundary and include their upper boundary. Ties belong to the first
        matching bin, as in sklearn.calibration.calibration_curve.

        ``metrics`` has one row per model, in prediction-column order:
        ``model``, ``brier_score``, ``method`` (``"brier_score"``), ``pos_label``,
        ``n``, ``n_positive``, ``n_negative``, ``strategy``, and ``n_bins``.
        Brier score is mean squared probability error, in [0, 1]; lower values
        indicate better overall probabilistic prediction quality. It measures
        more than calibration alone and is independent of the chosen bins.

    Notes
    -----
    Results are computed once when plotting. Each call returns fresh table
    copies. Replotting replaces the stored results for that axes; clearing the
    axes or removing a model curve makes the results unavailable. Axes with no
    available results return empty tables with the same columns.

    Examples
    --------
    >>> ax = cns.calibrationplot(df, "outcome", "probability")
    >>> results = cns.get_calibration_results(ax)
    >>> results["bins"].to_csv("calibration_bins.csv", index=False)
    """
    if ax is None:
        ax = plt.gca()
    stored = getattr(ax, "_cnsplots_calibration_results", None)
    if stored is None or any(curve not in ax.lines for curve in stored[1]):
        return {
            "bins": pd.DataFrame(columns=pd.Index(_BIN_COLUMNS)),
            "metrics": pd.DataFrame(columns=pd.Index(_METRIC_COLUMNS)),
        }
    results = stored[0]
    return {
        "bins": results["bins"].copy(deep=True),
        "metrics": results["metrics"].copy(deep=True),
    }


def calibrationplot(
    data: pd.DataFrame,
    true_label_col: str,
    pred_prob_cols: str | list[str],
    *,
    pos_label: str | int | float | bool = 1,
    n_bins: int = 5,
    strategy: Literal["uniform", "quantile"] = "uniform",
    brier_show: bool = True,
    ax: Axes | None = None,
) -> Axes:
    """Plot observed event frequencies against mean predicted probabilities.

    Parameters
    ----------
    data : pandas.DataFrame
        One observation per row. Supply held-out or out-of-fold predictions;
        no estimator is fitted, refitted, or recalibrated by this function.
        The input is not modified. Missing labels or probabilities are rejected.
    true_label_col : str
        Column containing exactly two distinct, nonmissing class labels.
        One-class data is rejected explicitly. Numeric labels must be finite.
    pred_prob_cols : str or list of str
        One or more distinct numeric probability columns, each giving the
        probability of ``pos_label``. Values must be finite and in [0, 1];
        boolean, complex, and nonnumeric columns are rejected. Curves and legend
        entries preserve the supplied column order.
    pos_label : str, int, float, or bool, default: 1
        Observed class treated as the positive event. Specify this explicitly
        for string labels or labels other than 0/1. The other class is negative.
    n_bins : int, default: 5
        Positive number of bins. More bins show finer detail but may have few
        observations; inspect counts using get_calibration_results.
    strategy : {"uniform", "quantile"}, default: "uniform"
        Uniform bins divide [0, 1] into equal widths. Quantile bins use each
        model's empirical probability quantiles to target similar counts.
        Ties can produce repeated boundaries and empty bins. Empty bins remain
        in the result table with zero counts and NaN means, but are omitted
        from the curve; occupied bins are connected in ascending order.
    brier_show : bool, default: True
        Append the Brier score to each model's legend label. The score measures
        overall probabilistic prediction quality, not calibration alone.
        Disabling the annotation does not remove it from the results table.
    ax : matplotlib.axes.Axes, optional
        Target axes, including a multipanel panel. Defaults to the current axes.

    Returns
    -------
    matplotlib.axes.Axes
        The target axes, with one line and circular markers per model, followed
        by a dashed identity line. Both axes use dimensionless probabilities
        from 0 to 1: x is mean predicted probability and y observed positive
        event frequency. A legend identifies the models. Artists are available
        through ``ax.lines``; numerical tables through get_calibration_results.

    See Also
    --------
    get_calibration_results : Retrieve bin counts and per-model Brier scores.
    rocplot : Evaluate binary discrimination across decision thresholds.

    Examples
    --------
    >>> ax = cns.calibrationplot(df, "outcome", ["model_a", "model_b"], n_bins=10)
    >>> ax = cns.calibrationplot(
    ...     df, "diagnosis", "probability", pos_label="positive", strategy="quantile"
    ... )
    """
    validate_dataframe(data, "data", "calibrationplot")
    if isinstance(pred_prob_cols, str):
        pred_prob_cols = [pred_prob_cols]
    if not isinstance(pred_prob_cols, list) or not all(
        isinstance(column, str) for column in pred_prob_cols
    ):
        raise TypeError(
            "[calibrationplot] 'pred_prob_cols' must be a string or list of strings."
        )
    if not pred_prob_cols:
        raise ValueError(
            "[calibrationplot] At least one prediction column is required."
        )
    if len(set(pred_prob_cols)) != len(pred_prob_cols):
        raise ValueError("[calibrationplot] Prediction columns must be unique.")
    columns = [true_label_col, *pred_prob_cols]
    validate_columns_exist(data, columns, "calibrationplot")
    validate_dataframe_not_empty(data, "calibrationplot")
    validate_no_nulls(data, columns, "calibrationplot")
    if (
        isinstance(n_bins, (bool, np.bool_))
        or not isinstance(n_bins, (int, np.integer))
        or n_bins < 1
    ):
        raise ValueError("[calibrationplot] 'n_bins' must be a positive integer.")
    if strategy not in ("uniform", "quantile"):
        raise ValueError(
            "[calibrationplot] 'strategy' must be 'uniform' or 'quantile'."
        )

    labels = data[true_label_col]
    classes = labels.unique()
    if any(
        np.iscomplexobj(value)
        or (isinstance(value, (int, float, np.number)) and not np.isfinite(value))
        for value in classes
    ):
        raise ValueError(
            "[calibrationplot] Class labels must be finite and noncomplex."
        )
    if len(classes) != 2:
        raise ValueError(
            "[calibrationplot] Labels must contain exactly two classes; "
            "one-class data is not supported."
        )
    if pos_label not in classes:
        raise ValueError(
            "[calibrationplot] 'pos_label' must be an observed class label."
        )
    y_true = (labels == pos_label).to_numpy(dtype=int)

    bin_tables = []
    metric_rows = []
    for model in pred_prob_cols:
        dtype = data[model].dtype
        if (
            not pd.api.types.is_numeric_dtype(dtype)
            or pd.api.types.is_bool_dtype(dtype)
            or pd.api.types.is_complex_dtype(dtype)
        ):
            raise ValueError(
                f"[calibrationplot] Column '{model}' must contain real numeric scores."
            )
        scores = data[model].to_numpy(dtype=float)
        if not np.isfinite(scores).all():
            raise ValueError(
                f"[calibrationplot] Column '{model}' must contain only finite scores."
            )
        if ((scores < 0) | (scores > 1)).any():
            raise ValueError(
                f"[calibrationplot] Column '{model}' probabilities must be in [0, 1]."
            )
        edges = np.linspace(0, 1, n_bins + 1)
        if strategy == "quantile":
            edges = np.percentile(scores, edges * 100)
        bin_ids = np.searchsorted(edges[1:-1], scores)
        counts = np.bincount(bin_ids, minlength=n_bins)
        score_sums = np.bincount(bin_ids, weights=scores, minlength=n_bins)
        event_sums = np.bincount(bin_ids, weights=y_true, minlength=n_bins)
        mean_scores = np.full(n_bins, np.nan)
        frequencies = np.full(n_bins, np.nan)
        np.divide(score_sums, counts, out=mean_scores, where=counts > 0)
        np.divide(event_sums, counts, out=frequencies, where=counts > 0)
        bin_tables.append(
            pd.DataFrame(
                {
                    "model": model,
                    "bin": np.arange(n_bins),
                    "bin_lower": edges[:-1],
                    "bin_upper": edges[1:],
                    "count": counts,
                    "mean_predicted_probability": mean_scores,
                    "observed_frequency": frequencies,
                }
            )
        )
        metric_rows.append(
            {
                "model": model,
                "brier_score": float(np.mean((scores - y_true) ** 2)),
                "method": "brier_score",
                "pos_label": pos_label,
                "n": len(y_true),
                "n_positive": int(y_true.sum()),
                "n_negative": int(len(y_true) - y_true.sum()),
                "strategy": strategy,
                "n_bins": int(n_bins),
            }
        )

    if ax is None:
        ax = plt.gca()
    curves = []
    for table, row in zip(bin_tables, metric_rows, strict=True):
        occupied = table[table["count"] > 0]
        label = str(row["model"])
        if brier_show:
            label += f" (Brier={row['brier_score']:.3f})"
        (curve,) = ax.plot(
            occupied["mean_predicted_probability"],
            occupied["observed_frequency"],
            marker="o",
            markersize=3,
            linewidth=1.2,
            label=label,
        )
        curves.append(curve)
    ax.plot([0, 1], [0, 1], color="black", linestyle="--", linewidth=0.8)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xticks(np.linspace(0, 1, 6))
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.set_xlabel("Mean Predicted Probability")
    ax.set_ylabel("Observed Event Frequency")
    ax.legend(loc="lower right")
    results: CalibrationResults = {
        "bins": pd.concat(bin_tables, ignore_index=True),
        "metrics": pd.DataFrame(metric_rows),
    }
    setattr(ax, "_cnsplots_calibration_results", (results, curves))
    return ax
