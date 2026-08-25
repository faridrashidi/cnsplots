"""Statistical helpers for receiver operating characteristic curves."""

from __future__ import annotations

import numpy as np
from scipy.stats import norm, rankdata
from sklearn.metrics import roc_curve


def _bootstrap_roc_confidence_band(
    y_true: np.ndarray,
    y_score: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return a deterministic pointwise 95% bootstrap ROC confidence band."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    negative_indices = np.flatnonzero(y_true == 0)
    positive_indices = np.flatnonzero(y_true == 1)
    fpr_grid = np.linspace(0, 1, 101)
    bootstrap_tprs = np.empty((1000, fpr_grid.size))
    rng = np.random.default_rng(42)

    for bootstrap_index in range(bootstrap_tprs.shape[0]):
        sample_indices = np.concatenate(
            [
                rng.choice(
                    negative_indices,
                    size=negative_indices.size,
                    replace=True,
                ),
                rng.choice(
                    positive_indices,
                    size=positive_indices.size,
                    replace=True,
                ),
            ]
        )
        fpr, tpr, _ = roc_curve(y_true[sample_indices], y_score[sample_indices])
        bootstrap_tprs[bootstrap_index] = np.interp(fpr_grid, fpr, tpr)

    lower, upper = np.percentile(bootstrap_tprs, [2.5, 97.5], axis=0)
    return fpr_grid, lower, upper


def _delong_auc_covariance(
    y_true: np.ndarray,
    predictions: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Estimate correlated ROC AUCs and their DeLong covariance matrix."""
    y_true = np.asarray(y_true)
    predictions = np.atleast_2d(np.asarray(predictions, dtype=float))
    positive = predictions[:, y_true == 1]
    negative = predictions[:, y_true == 0]
    n_positive = positive.shape[1]
    n_negative = negative.shape[1]
    combined = np.concatenate([positive, negative], axis=1)

    positive_ranks = np.vstack([rankdata(row, method="average") for row in positive])
    negative_ranks = np.vstack([rankdata(row, method="average") for row in negative])
    combined_ranks = np.vstack([rankdata(row, method="average") for row in combined])

    aucs = combined_ranks[:, :n_positive].sum(axis=1) / (n_positive * n_negative) - (
        n_positive + 1
    ) / (2 * n_negative)
    positive_placements = (combined_ranks[:, :n_positive] - positive_ranks) / n_negative
    negative_placements = (
        1 - (combined_ranks[:, n_positive:] - negative_ranks) / n_positive
    )
    covariance = (
        np.cov(positive_placements) / n_positive
        + np.cov(negative_placements) / n_negative
    )
    return aucs, np.atleast_2d(covariance)


def _delong_roc_test(
    y_true: np.ndarray,
    first_scores: np.ndarray,
    second_scores: np.ndarray,
) -> float:
    """Return the paired, two-sided DeLong p-value for two ROC AUCs."""
    aucs, covariance = _delong_auc_covariance(
        y_true,
        np.vstack([first_scores, second_scores]),
    )
    contrast = np.array([1.0, -1.0])
    variance = float(contrast @ covariance @ contrast)
    if variance < 0 and np.isclose(variance, 0, atol=1e-15):
        variance = 0.0
    if variance < 0:
        raise ValueError("DeLong contrast variance must be non-negative.")

    difference = float(aucs[0] - aucs[1])
    if variance == 0:
        return 1.0 if np.isclose(difference, 0) else 0.0

    statistic = difference / np.sqrt(variance)
    return float(2 * norm.sf(abs(statistic)))
