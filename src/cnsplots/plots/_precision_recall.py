from __future__ import annotations

from typing import TypedDict, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from pandas.api.types import is_bool_dtype, is_complex_dtype, is_numeric_dtype
from sklearn.metrics import average_precision_score, precision_recall_curve

from cnsplots._validation import (
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
    validate_no_nulls,
)


class PrecisionRecallResults(TypedDict):
    """Detached curve coordinates and average-precision summaries."""

    curves: pd.DataFrame
    metrics: pd.DataFrame


_CURVE_COLUMNS = ("model", "recall", "precision", "threshold")
_METRIC_COLUMNS = (
    "model",
    "average_precision",
    "prevalence",
    "method",
    "pos_label",
    "n",
    "n_positive",
    "n_negative",
)


def get_precision_recall_results(ax: Axes | None = None) -> PrecisionRecallResults:
    """Return tables from the latest precisionrecallplot call on an axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes, optional
        Axes returned by :func:`precisionrecallplot`. Defaults to the current axes.

    Returns
    -------
    PrecisionRecallResults
        A mapping of two detached DataFrames. ``curves`` contains ``model``,
        ``recall``, ``precision``, and ``threshold`` in prediction-column order.
        Thresholds increase and recall decreases within each model, following
        scikit-learn. The final endpoint has recall 0, precision 1, and a NaN
        threshold because it does not represent a score cutoff. Thresholds use
        object dtype to preserve exact integer scores alongside that endpoint.

        ``metrics`` contains one row per model in prediction-column order:
        ``model``, ``average_precision``, ``prevalence``, ``method``
        (``"average_precision"``), ``pos_label``, ``n``, ``n_positive``, and
        ``n_negative``. Precision, recall, AP, and prevalence are unitless
        fractions; thresholds have the same units as the input scores. Counts
        include every input row because missing values are rejected.

        Empty tables with these same columns are returned before plotting or
        after the axes are cleared or a model's curve is removed.

    Notes
    -----
    No statistics are recomputed. Each call returns copies, and each successful
    :func:`precisionrecallplot` call replaces the results stored on its axes.

    Examples
    --------
    >>> ax = cns.precisionrecallplot(df, "outcome", ["model_a", "model_b"])
    >>> results = cns.get_precision_recall_results(ax)
    >>> results["metrics"].to_csv("average_precision.csv", index=False)
    """
    if ax is None:
        ax = plt.gca()
    stored = getattr(ax, "_cnsplots_precision_recall_results", None)
    if stored is None or any(artist not in ax.lines for artist in stored[1]):
        return {
            "curves": pd.DataFrame(columns=pd.Index(_CURVE_COLUMNS)),
            "metrics": pd.DataFrame(columns=pd.Index(_METRIC_COLUMNS)),
        }
    results = cast(PrecisionRecallResults, stored[0])
    return {
        "curves": results["curves"].copy(deep=True),
        "metrics": results["metrics"].copy(deep=True),
    }


def precisionrecallplot(
    data: pd.DataFrame,
    true_label_col: str,
    pred_prob_cols: str | list[str],
    *,
    pos_label: str | int | float | bool = 1,
    ax: Axes | None = None,
) -> Axes:
    """Plot binary precision-recall curves and report average precision (AP).

    Parameters
    ----------
    data : pandas.DataFrame
        Input data, containing one observation per row. It is not modified.
        Missing labels or scores and nonfinite numeric values are rejected;
        no rows are silently dropped.
    true_label_col : str
        Column containing exactly two distinct class labels, both observed.
        Numeric, boolean, and string labels are supported.
    pred_prob_cols : str or list of str
        One or more unique columns of finite, real numeric prediction scores.
        Larger scores must indicate stronger evidence for ``pos_label``.
        Scores may be probabilities or decision scores outside [0, 1]. Boolean,
        complex, and nonnumeric score columns are rejected. Models, legend
        entries, and result tables preserve the supplied column order.
    pos_label : str, int, float, or bool, default: 1
        The observed label treated as positive. Set this explicitly for string
        labels or when the positive class is not 1.
    ax : matplotlib.axes.Axes, optional
        Axes on which to draw. Defaults to the current axes, including a current
        :class:`cnsplots.multipanel` panel.

    Returns
    -------
    matplotlib.axes.Axes
        The target axes, containing one step line per model and a dashed
        horizontal prevalence reference. Recall is on the x-axis and precision
        on the y-axis, both as fractions from 0 to 1. The legend identifies each
        model's AP and the positive-class prevalence. Exact coordinates, AP,
        and sample counts are available through :func:`get_precision_recall_results`.

    Raises
    ------
    TypeError
        If data is not a DataFrame, prediction column names have the wrong type,
        or scores are not real numeric values.
    ValueError
        If data is empty, requested columns are absent or duplicated, no models
        are selected, labels do not contain two classes including ``pos_label``,
        or labels or scores contain missing or nonfinite values.

    Notes
    -----
    Coordinates use :func:`sklearn.metrics.precision_recall_curve`, including
    its final (recall=0, precision=1) endpoint. AP is computed using
    :func:`sklearn.metrics.average_precision_score`: the sum of precision
    weighted by each increase in recall. AP is not trapezoidal PR area.
    The prevalence reference is the positive count divided by the total count.
    Confidence bands and statistical model-comparison tests are not performed.

    See Also
    --------
    rocplot : Plot receiver operating characteristic curves.
    calibrationplot : Compare predicted probabilities with observed outcomes.
    get_precision_recall_results : Retrieve exact curve and AP tables.

    Examples
    --------
    >>> import pandas as pd
    >>> import cnsplots as cns
    >>> data = pd.DataFrame({"truth": [0, 0, 1, 1], "score": [0.1, 0.4, 0.35, 0.8]})
    >>> ax = cns.precisionrecallplot(data, "truth", "score")
    >>> results = cns.get_precision_recall_results(ax)

    >>> # Set the positive class for text labels
    >>> data["outcome"] = ["control", "control", "case", "case"]
    >>> ax = cns.precisionrecallplot(data, "outcome", "score", pos_label="case")
    """
    validate_dataframe(data, "data", "precisionrecallplot")
    validate_dataframe_not_empty(data, "precisionrecallplot")
    if isinstance(pred_prob_cols, str):
        pred_prob_cols = [pred_prob_cols]
    if not isinstance(pred_prob_cols, list) or not all(
        isinstance(column, str) for column in pred_prob_cols
    ):
        raise TypeError(
            "[precisionrecallplot] 'pred_prob_cols' must be a string or list of strings."
        )
    if not pred_prob_cols:
        raise ValueError("[precisionrecallplot] Select at least one prediction column.")
    if len(set(pred_prob_cols)) != len(pred_prob_cols):
        raise ValueError("[precisionrecallplot] Prediction columns must be unique.")
    validate_columns_exist(
        data, [true_label_col] + pred_prob_cols, "precisionrecallplot"
    )
    validate_no_nulls(data, true_label_col, "precisionrecallplot")
    labels = data[true_label_col]
    classes = labels.unique()
    if any(
        isinstance(value, (int, float, complex, np.number)) and not np.isfinite(value)
        for value in classes
    ):
        raise ValueError("[precisionrecallplot] Class labels must be finite.")
    if len(classes) != 2:
        raise ValueError(
            "[precisionrecallplot] Labels must contain exactly two classes."
        )
    if pos_label not in classes:
        raise ValueError("[precisionrecallplot] 'pos_label' must be an observed class.")

    scores = {}
    for column in pred_prob_cols:
        dtype = data[column].dtype
        if (
            not is_numeric_dtype(dtype)
            or is_complex_dtype(dtype)
            or is_bool_dtype(dtype)
        ):
            raise TypeError(
                f"[precisionrecallplot] Scores in {column!r} must be real numeric values."
            )
        if data[column].isna().any() or not np.isfinite(data[column]).all():
            raise ValueError(
                f"[precisionrecallplot] Scores in {column!r} must be finite "
                "with no missing values."
            )
        scores[column] = data[column].to_numpy()

    if ax is None:
        ax = plt.gca()
    positive = (labels == pos_label).to_numpy(dtype=bool)
    n_positive = int(positive.sum())
    prevalence = n_positive / len(data)
    curves = []
    metrics = []
    artists = []
    for column in pred_prob_cols:
        precision, recall, thresholds = precision_recall_curve(positive, scores[column])
        ap = float(average_precision_score(positive, scores[column]))
        curves.append(
            pd.DataFrame(
                {
                    "model": column,
                    "recall": recall,
                    "precision": precision,
                    "threshold": np.append(thresholds.astype(object), np.nan),
                }
            )
        )
        metrics.append(
            {
                "model": column,
                "average_precision": ap,
                "prevalence": prevalence,
                "method": "average_precision",
                "pos_label": pos_label,
                "n": len(data),
                "n_positive": n_positive,
                "n_negative": len(data) - n_positive,
            }
        )
        (curve,) = ax.step(
            recall, precision, where="post", label=f"{column} (AP={ap:.2f})", lw=1
        )
        artists.append(curve)

    ax.axhline(
        prevalence,
        color="black",
        linestyle="--",
        linewidth=0.8,
        label=f"Prevalence={prevalence:.2f}",
    )
    ax.set_xlim((-0.02, 1.02))
    ax.set_ylim((-0.02, 1.02))
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.legend(loc="lower left")
    results: PrecisionRecallResults = {
        "curves": pd.concat(curves, ignore_index=True),
        "metrics": pd.DataFrame(metrics),
    }
    setattr(ax, "_cnsplots_precision_recall_results", (results, artists))
    return ax
