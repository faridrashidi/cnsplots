from __future__ import annotations

import inspect
from typing import Any, cast

import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

import cnsplots as cns
from cnsplots.helpers import _roc
from cnsplots.plots import _specialized


def test_rocplot_statistical_options_are_keyword_only() -> None:
    parameters = inspect.signature(cns.rocplot).parameters

    assert parameters["ci_show"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["ci_show"].default is False
    assert parameters["pairs"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["pairs"].default is None
    assert parameters["p_adjust"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["p_adjust"].default is None


def test_rocplot_defaults_remain_unchanged(roc_df: pd.DataFrame) -> None:
    ax = cns.rocplot(roc_df, "truth", ["model_a", "model_b"])

    assert [line.get_label() for line in ax.lines] == [
        "model_a (AUC=1.00)",
        "model_b (AUC=1.00)",
        "_child2",
    ]
    assert len(ax.collections) == 0
    assert len(ax.texts) == 0


def test_bootstrap_roc_band_is_deterministic_and_rng_isolated() -> None:
    y_true = np.array([0] * 8 + [1] * 8)
    y_score = np.array(
        [0.1, 0.2, 0.3, 0.35, 0.4, 0.45, 0.6, 0.7]
        + [0.25, 0.4, 0.5, 0.55, 0.65, 0.75, 0.8, 0.9]
    )
    state_before = repr(np.random.get_state())

    first = _roc._bootstrap_roc_confidence_band(y_true, y_score)
    second = _roc._bootstrap_roc_confidence_band(y_true, y_score)

    assert repr(np.random.get_state()) == state_before
    for first_values, second_values in zip(first, second, strict=True):
        np.testing.assert_array_equal(first_values, second_values)
    fpr, lower, upper = first
    np.testing.assert_array_equal(fpr, np.linspace(0, 1, 101))
    assert np.all((0 <= lower) & (lower <= upper) & (upper <= 1))


def test_rocplot_draws_one_matching_band_per_curve(
    roc_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[np.ndarray, np.ndarray]] = []

    def fake_band(
        y_true: np.ndarray, y_score: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        calls.append((y_true, y_score))
        return np.array([0.0, 1.0]), np.array([0.0, 0.5]), np.array([0.5, 1.0])

    monkeypatch.setattr(_roc, "_bootstrap_roc_confidence_band", fake_band)

    ax = cns.rocplot(
        roc_df,
        "truth",
        ["model_a", "model_b"],
        ci_show=True,
    )

    assert len(calls) == 2
    assert len(ax.collections) == 2
    for curve, band in zip(ax.lines[:2], ax.collections, strict=True):
        np.testing.assert_allclose(
            cast(Any, band.get_facecolor()[0]),
            cast(Any, mcolors.to_rgba(curve.get_color(), alpha=0.2)),
        )
        assert band.get_zorder() == curve.get_zorder() - 1


def _slow_delong_reference(
    y_true: np.ndarray, predictions: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    positive = predictions[:, y_true == 1]
    negative = predictions[:, y_true == 0]
    positive_placements = np.empty_like(positive, dtype=float)
    negative_placements = np.empty_like(negative, dtype=float)
    for model_index in range(predictions.shape[0]):
        placements = (
            positive[model_index, :, None] > negative[model_index, None, :]
        ) + 0.5 * (positive[model_index, :, None] == negative[model_index, None, :])
        positive_placements[model_index] = placements.mean(axis=1)
        negative_placements[model_index] = placements.mean(axis=0)
    aucs = positive_placements.mean(axis=1)
    covariance = (
        np.cov(positive_placements) / positive.shape[1]
        + np.cov(negative_placements) / negative.shape[1]
    )
    return aucs, covariance


def test_fast_delong_matches_tie_aware_reference() -> None:
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    predictions = np.array(
        [
            [0.1, 0.4, 0.4, 0.7, 0.3, 0.4, 0.8, 0.9],
            [0.2, 0.3, 0.5, 0.6, 0.4, 0.5, 0.7, 0.8],
        ]
    )

    aucs, covariance = _roc._delong_auc_covariance(y_true, predictions)
    expected_aucs, expected_covariance = _slow_delong_reference(y_true, predictions)

    np.testing.assert_allclose(aucs, expected_aucs)
    np.testing.assert_allclose(covariance, expected_covariance)
    np.testing.assert_allclose(
        aucs,
        [roc_auc_score(y_true, prediction) for prediction in predictions],
    )
    assert _roc._delong_roc_test(
        y_true, predictions[0], predictions[1]
    ) == pytest.approx(0.39926914317106565)


def test_delong_handles_zero_variance_comparisons() -> None:
    y_true = np.array([0, 0, 1, 1])
    scores = np.array([0.1, 0.2, 0.8, 0.9])

    assert _roc._delong_roc_test(y_true, scores, scores) == 1
    assert _roc._delong_roc_test(y_true, y_true, 1 - y_true) == 0


def test_delong_handles_floating_point_covariance_noise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        _roc,
        "_delong_auc_covariance",
        lambda y_true, predictions: (
            np.array([0.5, 0.5]),
            np.array([[-1e-16, 0.0], [0.0, 0.0]]),
        ),
    )

    assert _roc._delong_roc_test(np.array([]), np.array([]), np.array([])) == 1


def test_delong_rejects_negative_contrast_variance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        _roc,
        "_delong_auc_covariance",
        lambda y_true, predictions: (
            np.array([0.5, 0.5]),
            np.array([[-1.0, 0.0], [0.0, 0.0]]),
        ),
    )

    with pytest.raises(ValueError, match="variance must be non-negative"):
        _roc._delong_roc_test(np.array([]), np.array([]), np.array([]))


def test_rocplot_runs_requested_delong_comparison(roc_df: pd.DataFrame) -> None:
    ax = cns.rocplot(
        roc_df,
        "truth",
        ["model_a", "model_b"],
        pairs=[("model_a", "model_b")],
    )

    annotation = ax.texts[0]
    assert annotation.get_text() == ("DeLong test\nmodel_a vs model_b: P = $1$")
    assert annotation.get_position() == (0.02, 0.02)
    assert annotation.get_transform() is ax.transAxes
    assert annotation.get_horizontalalignment() == "left"
    assert annotation.get_verticalalignment() == "bottom"


@pytest.mark.parametrize(
    "p_adjust",
    ["bonferroni", "holm", "fdr_bh", "fdr_by"],
)
def test_rocplot_resolves_all_pairs_and_applies_correction(
    roc_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
    p_adjust: str,
) -> None:
    data = roc_df.assign(model_c=[0.3, 0.2, 0.1, 0.7, 0.8, 0.9])
    delong_calls: list[tuple[np.ndarray, np.ndarray]] = []
    correction_calls: list[tuple[list[float], str]] = []

    def fake_delong(
        y_true: np.ndarray,
        first_scores: np.ndarray,
        second_scores: np.ndarray,
    ) -> float:
        delong_calls.append((first_scores, second_scores))
        return 0.05

    def fake_multipletests(
        pvalues: list[float], *, method: str
    ) -> tuple[None, np.ndarray]:
        correction_calls.append((pvalues, method))
        return None, np.array([0.01, 0.02, 0.03])

    monkeypatch.setattr(_roc, "_delong_roc_test", fake_delong)
    monkeypatch.setattr(_specialized, "multipletests", fake_multipletests)

    ax = cns.rocplot(
        data,
        "truth",
        ["model_a", "model_b", "model_c"],
        pairs="all",
        p_adjust=cast(Any, p_adjust),
    )

    assert len(delong_calls) == 3
    assert correction_calls == [([0.05, 0.05, 0.05], p_adjust)]
    assert ax.texts[0].get_text().splitlines() == [
        f"DeLong test ({p_adjust}-adjusted)",
        "model_a vs model_b: P = $0.01$",
        "model_a vs model_c: P = $0.02$",
        "model_b vs model_c: P = $0.03$",
    ]


@pytest.mark.parametrize(
    ("pred_prob_cols", "pairs", "message"),
    [
        (["model_a", "model_a"], "all", "Prediction columns must be unique"),
        (["model_a"], "all", "requires at least two prediction columns"),
        (["model_a", "model_b"], "invalid", "must be a list of tuples"),
        (["model_a", "model_b"], ["model_a"], "exactly two prediction columns"),
        (
            ["model_a", "model_b"],
            [("model_a", "model_a")],
            "two distinct prediction columns",
        ),
        (
            ["model_a", "model_b"],
            [("model_a", "missing")],
            "not plotted",
        ),
        (
            ["model_a", "model_b"],
            [("model_a", "model_b"), ("model_b", "model_a")],
            "unique regardless of order",
        ),
    ],
)
def test_rocplot_validates_comparison_pairs(
    roc_df: pd.DataFrame,
    pred_prob_cols: list[str],
    pairs: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        cns.rocplot(
            roc_df,
            "truth",
            pred_prob_cols,
            pairs=cast(Any, pairs),
        )


def test_rocplot_accepts_an_empty_pair_list(roc_df: pd.DataFrame) -> None:
    ax = cns.rocplot(
        roc_df,
        "truth",
        ["model_a", "model_b"],
        pairs=[],
        p_adjust="holm",
    )

    assert len(ax.texts) == 0


@pytest.mark.parametrize(
    ("scores", "message"),
    [
        ([0.1, 0.2, None, 0.6, 0.8, 0.9], "Null values"),
        (["low", "low", "low", "high", "high", "high"], "real numeric scores"),
        ([False, False, False, True, True, True], "real numeric scores"),
        ([0.1 + 1j, 0.2, 0.3, 0.6, 0.8, 0.9], "real numeric scores"),
        ([0.1, 0.2, 0.3, 0.6, 0.8, np.inf], "finite scores"),
    ],
)
def test_rocplot_validates_prediction_scores(
    roc_df: pd.DataFrame,
    scores: list[object],
    message: str,
) -> None:
    data = roc_df.assign(invalid=scores)

    with pytest.raises(ValueError, match=message):
        cns.rocplot(data, "truth", "invalid")


def test_rocplot_rejects_null_true_labels(roc_df: pd.DataFrame) -> None:
    data = roc_df.astype({"truth": float})
    data.loc[0, "truth"] = np.nan

    with pytest.raises(ValueError, match="Null values"):
        cns.rocplot(data, "truth", "model_a")


def test_rocplot_requires_two_observations_per_class_for_delong() -> None:
    data = pd.DataFrame(
        {
            "truth": [0, 1, 1],
            "first": [0.1, 0.7, 0.8],
            "second": [0.2, 0.6, 0.9],
        }
    )

    with pytest.raises(ValueError, match="at least two positive and two negative"):
        cns.rocplot(data, "truth", ["first", "second"], pairs="all")


def test_rocplot_rejects_unknown_pvalue_correction(roc_df: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="'p_adjust' must be one of"):
        cns.rocplot(
            roc_df,
            "truth",
            ["model_a", "model_b"],
            p_adjust=cast(Any, "BH"),
        )
