"""Check the documented fixed-prediction AUC interval example."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import cnsplots as cns


def test_documented_auc_interval_matches_paired_row_percentiles() -> None:
    labels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    probabilities = np.array([0.1, 0.4, 0.35, 0.8, 0.3, 0.2, 0.9, 0.6, 0.7, 0.5])
    model = cns.LogisticModel(
        pd.DataFrame({"outcome": labels, "score": probabilities}),
        "outcome",
        ["score"],
    )

    # Compute reference AUCs by comparing every positive/negative pair, without
    # using the implementation's sklearn ROC-AUC calculation.
    rng = np.random.default_rng(42)
    bootstrap_aucs = []
    for _ in range(1000):
        rows = rng.choice(len(labels), len(labels), replace=True)
        positive = probabilities[rows][labels[rows] == 1]
        negative = probabilities[rows][labels[rows] == 0]
        if not len(positive) or not len(negative):
            continue
        differences = positive[:, None] - negative
        bootstrap_aucs.append(np.mean((differences > 0) + 0.5 * (differences == 0)))

    auc, lower, upper = model._compute_auc_ci(labels, probabilities)

    assert len(bootstrap_aucs) == 999
    assert auc == pytest.approx(0.72)
    assert auc != pytest.approx(np.mean(bootstrap_aucs))
    np.testing.assert_allclose(
        [lower, upper], np.percentile(bootstrap_aucs, [2.5, 97.5])
    )
    assert (lower, upper) == pytest.approx((7 / 24, 1.0))
