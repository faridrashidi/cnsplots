"""Regression tests for statistical model correctness."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock
import warnings

import lifelines as ll
import numpy as np
import pandas as pd
import pytest
from lifelines.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegressionCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import cnsplots as cns
from cnsplots import _methods


def test_auc_ci_uses_full_predictions_and_bootstrap_only_for_bounds(
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
    assert (auc, lower, upper) == (0.5, 0.0, 0.0)
    assert rng_state_before == rng_state_after


@pytest.mark.parametrize("hue", [None, "group"])
def test_logistic_model_uses_scaled_out_of_fold_predictions(
    monkeypatch: pytest.MonkeyPatch, hue: str | None
) -> None:
    data = pd.DataFrame(
        {
            "event": [0, 1] * 14,
            "score": np.arange(28, dtype=float),
            "group": ["A"] * 14 + ["B"] * 14,
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
        if classifier.penalty == "deprecated":
            assert classifier.l1_ratios == (1,)
            assert classifier.use_legacy_attributes is False
        else:
            assert classifier.penalty == "l1"
        assert classifier.solver == "liblinear"
        assert classifier.cv == 5


def test_logistic_model_aligns_outcome_after_patsy_drops_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = pd.DataFrame(
        {
            "event": [0, 1] * 8,
            "score": np.arange(16, dtype=float),
        },
        index=np.arange(100, 116),
    )
    data.loc[[100, 101], "score"] = np.nan

    def fake_cross_val_predict(
        estimator: Pipeline,
        X: pd.DataFrame,
        y: np.ndarray,
        *,
        cv: int,
        method: str,
    ) -> np.ndarray:
        assert X.index.tolist() == list(range(2, 16))
        np.testing.assert_array_equal(y, data["event"].to_numpy()[2:])
        probabilities = np.linspace(0.1, 0.9, len(y))
        return np.column_stack((1 - probabilities, probabilities))

    monkeypatch.setattr(_methods, "cross_val_predict", fake_cross_val_predict)
    monkeypatch.setattr(
        cns.LogisticModel,
        "_compute_auc_ci",
        lambda self, y, predictions: (0.5, 0.4, 0.6),
    )

    model = cns.LogisticModel(data, event="event", variates=["score"])
    model.fit()

    assert model.results is not None


@pytest.mark.parametrize(
    ("minority_count", "message"),
    [
        (4, "Outer 5-fold cross-validation requires at least 5 observations"),
        (6, "Inner 5-fold cross-validation requires at least 5 observations"),
    ],
)
def test_logistic_model_validates_each_nested_cv_layer(
    minority_count: int, message: str
) -> None:
    event = [0] * minority_count + [1] * 10
    data = pd.DataFrame({"event": event, "score": np.arange(len(event))})
    model = cns.LogisticModel(data, event="event", variates=["score"])

    with pytest.warns(RuntimeWarning) as caught:
        model.fit()

    messages = [str(warning.message) for warning in caught]
    assert any(message in warning_message for warning_message in messages)
    assert "No successful model fits" in messages
    assert model.results is None


def test_logistic_model_rejects_more_than_two_outcome_classes() -> None:
    data = pd.DataFrame({"event": [0, 1, 2] * 7, "score": np.arange(21, dtype=float)})
    model = cns.LogisticModel(data, event="event", variates=["score"])

    with pytest.warns(RuntimeWarning) as caught:
        model.fit()

    messages = [str(warning.message) for warning in caught]
    assert any(
        "requires exactly two outcome classes" in warning_message
        for warning_message in messages
    )
    assert "No successful model fits" in messages
    assert model.results is None


@pytest.fixture
def cox_df() -> pd.DataFrame:
    rng = np.random.default_rng(123)
    n = 80
    return pd.DataFrame(
        {
            "time": rng.exponential(10, n),
            "event": rng.integers(0, 2, n),
            "x": rng.normal(size=n),
            "group": ["A"] * (n // 2) + ["B"] * (n // 2),
        }
    )


@pytest.mark.parametrize("hue", [None, "group"])
@pytest.mark.parametrize(
    ("column", "values", "message"),
    [
        ("event", [0, 2], "only 0 and 1"),
        ("event", [0, -1], "only 0 and 1"),
        ("event", [0, 0.5], "only 0 and 1"),
        ("event", [0, np.inf], "only 0 and 1"),
        ("event", [0, -np.inf], "only 0 and 1"),
        ("event", [0, np.nan], "Null values"),
        ("event", ["0", "1"], "only 0 and 1"),
        ("event", [0j, 1 + 0j], "only 0 and 1"),
        ("time", [1, -1], "non-negative durations"),
        ("time", [1, np.inf], "finite durations"),
        ("time", [1, -np.inf], "finite durations"),
        ("time", [1, np.nan], "Null values"),
        ("time", [1 + 0j, 2 + 0j], "real-valued numeric durations"),
        ("time", [False, True], "real-valued numeric durations"),
        ("time", ["1", "2"], "must be numeric"),
    ],
)
def test_cox_model_rejects_invalid_survival_inputs_before_fitting(
    cox_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
    hue: str | None,
    column: str,
    values: list[Any],
    message: str,
) -> None:
    data = cox_df.copy()
    # Put invalid input in the last group to catch partial fitting as well.
    data[column] = pd.Series([values[0]] * (len(data) - 1) + [values[1]])
    fitter = Mock()
    monkeypatch.setattr(ll, "CoxPHFitter", fitter)
    model = cns.CoxModel(data, "time", "event", ["x"], hue=hue)
    model.results = pd.DataFrame({"stale": [True]})

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(ValueError, match=message) as exc_info:
            model.fit()

    assert "[CoxModel.fit]" in str(exc_info.value)
    assert f"'{column}'" in str(exc_info.value)
    assert not caught
    fitter.assert_not_called()
    assert model.results is None


@pytest.mark.parametrize("event_dtype", ["int64", "float64", "bool", "boolean"])
@pytest.mark.parametrize("uncensored", [False, True])
def test_cox_model_preserves_valid_event_encodings(
    cox_df: pd.DataFrame, event_dtype: str, uncensored: bool
) -> None:
    data = cox_df.copy()
    if uncensored:
        data["event"] = 1
    reference = ll.CoxPHFitter().fit(
        data, duration_col="time", event_col="event", formula="x"
    )
    data["event"] = data["event"].astype(event_dtype)
    original = data.copy(deep=True)
    model = cns.CoxModel(data, "time", "event", ["x"])

    model.fit()

    assert model.results is not None
    columns = ["exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]
    pd.testing.assert_frame_equal(
        model.results.set_index("covariate")[columns], reference.summary[columns]
    )
    if not uncensored:
        assert model.results["exp(coef)"].iloc[0] == pytest.approx(0.855151, abs=1e-6)
    pd.testing.assert_frame_equal(data, original)


@pytest.mark.parametrize("duration_dtype", ["int64", "float64", "Int64", "Float64"])
def test_cox_model_accepts_zero_and_nullable_durations(
    cox_df: pd.DataFrame, duration_dtype: str
) -> None:
    data = cox_df.copy()
    # Keep lifelines' median duration representable as a nullable integer.
    data["time"] = (2 * data["time"].astype("int64")).astype(duration_dtype)
    assert (data["time"] == 0).any()
    model = cns.CoxModel(data, "time", "event", ["x"])

    model.fit()

    assert model.results is not None
    assert np.isfinite(model.results["exp(coef)"]).all()


def test_cox_model_warns_for_failed_unstratified_fit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingCoxPHFitter:
        def fit(self, *args: Any, **kwargs: Any) -> None:
            raise ValueError("invalid formula")

    monkeypatch.setattr(ll, "CoxPHFitter", FailingCoxPHFitter)
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


def test_cox_model_retains_all_numeric_formula_coefficients(
    survival_df: pd.DataFrame,
) -> None:
    data = survival_df.assign(
        x1=survival_df["age"],
        x2=[0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0],
    )
    model = cns.CoxModel(
        data,
        duration="time",
        event="event",
        variates=["x1 + x2"],
    )

    model.fit()

    assert model.results is not None
    results = model.results.sort_values("covariate").reset_index(drop=True)
    assert results["analysis"].tolist() == ["x1 + x2", "x1 + x2"]
    assert results["covariate"].tolist() == ["x1", "x2"]
    assert results["display_label"].tolist() == [
        "x1 + x2 (x1)",
        "x1 + x2 (x2)",
    ]


def test_cox_model_retains_all_categorical_formula_coefficients(
    survival_df: pd.DataFrame,
) -> None:
    model = cns.CoxModel(
        survival_df,
        duration="time",
        event="event",
        variates=["C(stage)"],
    )

    with pytest.warns(ConvergenceWarning):
        model.fit()

    assert model.results is not None
    results = model.results.sort_values("covariate").reset_index(drop=True)
    assert results["analysis"].tolist() == ["C(stage)", "C(stage)"]
    assert set(results["covariate"]) == {
        "C(stage)[T.II]",
        "C(stage)[T.III]",
    }
    assert results["display_label"].is_unique


def test_cox_model_disambiguates_shared_single_coefficient_labels(
    survival_df: pd.DataFrame,
) -> None:
    model = cns.CoxModel(
        survival_df,
        duration="time",
        event="event",
        variates=["age", "np.log(age)"],
    )

    model.fit()

    assert model.results is not None
    labels = model.results.set_index("analysis")["display_label"].to_dict()
    assert labels == {
        "age": "age (age)",
        "np.log(age)": "np.log(age) (np.log(age))",
    }


def test_cox_model_rejects_formula_without_coefficients(
    survival_df: pd.DataFrame,
) -> None:
    model = cns.CoxModel(
        survival_df,
        duration="time",
        event="event",
        variates=["0"],
    )

    with pytest.warns(RuntimeWarning) as caught:
        model.fit()

    messages = [str(warning.message) for warning in caught]
    assert any(
        "Formula '0' produced no fitted coefficients" in message for message in messages
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
