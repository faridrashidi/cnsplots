"""Regression tests for statistical model correctness."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegressionCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import cnsplots as cns
from cnsplots import _methods


def test_auc_ci_uses_bootstrap_median_without_changing_global_rng(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeGenerator:
        def __init__(self) -> None:
            self.samples = iter(
                [
                    np.array([0, 0, 0, 0]),
                    np.array([1, 1, 2, 3]),
                    np.array([1, 1, 2, 3]),
                ]
            )

        def choice(self, n: int, size: int, replace: bool) -> np.ndarray:
            assert (n, size, replace) == (4, 4, True)
            return next(self.samples)

    def fake_default_rng(seed: int) -> FakeGenerator:
        assert seed == 42
        return FakeGenerator()

    monkeypatch.setattr(_methods.np.random, "default_rng", fake_default_rng)
    model = cns.LogisticModel(
        pd.DataFrame({"event": [0, 0, 1, 1]}), event="event", variates=["1"]
    )
    rng_state_before = repr(np.random.get_state())

    auc, lower, upper = model._compute_auc_ci(
        np.array([0, 0, 1, 1]),
        np.array([0.1, 0.9, 0.8, 0.7]),
        n_bootstrap=3,
    )

    rng_state_after = repr(np.random.get_state())
    assert (auc, lower, upper) == (0.0, 0.0, 0.0)
    assert rng_state_before == rng_state_after


@pytest.mark.parametrize("hue", [None, "group"])
def test_logistic_model_uses_scaled_out_of_fold_predictions(
    monkeypatch: pytest.MonkeyPatch, hue: str | None
) -> None:
    data = pd.DataFrame(
        {
            "event": [0, 1] * 10,
            "score": np.arange(20, dtype=float),
            "group": ["A"] * 10 + ["B"] * 10,
        }
    )
    seen_estimators: list[Pipeline] = []

    def fake_cross_val_predict(
        estimator: Pipeline,
        X: pd.DataFrame,
        y: np.ndarray,
        *,
        cv: int,
        method: str,
        **kwargs: Any,
    ) -> np.ndarray:
        assert cv == 5
        assert method == "predict_proba"
        assert kwargs == {}
        seen_estimators.append(estimator)
        probabilities = np.linspace(0.1, 0.9, len(y))
        return np.column_stack((1 - probabilities, probabilities))

    monkeypatch.setattr(_methods, "cross_val_predict", fake_cross_val_predict)
    monkeypatch.setattr(
        cns.LogisticModel,
        "_compute_auc_ci",
        lambda self, y, predictions: (0.5, 0.4, 0.6),
    )

    model = cns.LogisticModel(data, event="event", variates=["score"], hue=hue)
    model.fit()

    assert len(seen_estimators) == (1 if hue is None else 2)
    for estimator in seen_estimators:
        scaler, classifier = (step for _, step in estimator.steps)
        assert isinstance(scaler, StandardScaler)
        assert isinstance(classifier, LogisticRegressionCV)
        assert classifier.penalty == "l1"
        assert classifier.solver == "liblinear"
        assert classifier.cv == 5


def test_cox_model_warns_for_failed_unstratified_fit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingCoxPHFitter:
        def fit(self, *args: Any, **kwargs: Any) -> None:
            raise ValueError("invalid formula")

    monkeypatch.setattr(_methods.ll, "CoxPHFitter", FailingCoxPHFitter)
    model = cns.CoxModel(
        pd.DataFrame({"time": [1.0, 2.0], "event": [0, 1]}),
        duration="time",
        event="event",
        variates=["missing"],
    )

    with pytest.warns(RuntimeWarning) as caught:
        model.fit()

    messages = [str(warning.message) for warning in caught]
    assert any(
        "Error fitting missing for hue group All: invalid formula" in message
        for message in messages
    )
    assert "No successful model fits" in messages
    assert model.results is None


def test_logistic_model_warns_for_failed_unstratified_fit() -> None:
    model = cns.LogisticModel(
        pd.DataFrame({"event": [0, 1] * 5}),
        event="event",
        variates=["missing"],
    )

    with pytest.warns(RuntimeWarning) as caught:
        model.fit()

    messages = [str(warning.message) for warning in caught]
    assert any(
        "Error fitting missing for hue group All" in message for message in messages
    )
    assert "No successful model fits" in messages
    assert model.results is None


@pytest.mark.parametrize(
    "model",
    [
        cns.CoxModel(
            pd.DataFrame({"time": [1.0, 2.0]}),
            duration="time",
            event="event",
            variates=["1"],
        ),
        cns.LogisticModel(
            pd.DataFrame({"score": [1.0, 2.0]}),
            event="event",
            variates=["score"],
        ),
    ],
)
def test_models_validate_required_columns(model: Any) -> None:
    model.results = pd.DataFrame({"stale": [True]})
    with pytest.raises(ValueError, match=r"Column\(s\).*event"):
        model.fit()
    assert model.results is None


def test_prerank_requires_gene_and_rank_column_names() -> None:
    data = pd.DataFrame({"gene": ["A"], "rank": [1.0]})

    with pytest.raises(ValueError, match="name_gene.*name_rank"):
        cns.prerank(data, {"set": ["A"]})
