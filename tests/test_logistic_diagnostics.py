"""Regression coverage for logistic analysis diagnostics and retained models."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline

import cnsplots as cns


@pytest.fixture
def logistic_data(monkeypatch: pytest.MonkeyPatch) -> pd.DataFrame:
    monkeypatch.setattr(
        cns.LogisticModel,
        "_compute_auc_ci",
        lambda self, y, predictions: (0.5, 0.4, 0.6),
    )
    return pd.DataFrame({"event": [0, 1] * 12, "score": np.arange(24, dtype=float)})


@pytest.mark.parametrize("retain_estimators", [False, True])
def test_diagnostics_record_every_hue_and_formula(
    logistic_data: pd.DataFrame, retain_estimators: bool
) -> None:
    successful = logistic_data.assign(cohort="A")
    successful.loc[:1, "score"] = np.nan
    data = pd.concat(
        [successful, logistic_data.assign(event=0, cohort="B")], ignore_index=True
    )
    data["only_zero"] = np.where(data["event"] == 0, 1.0, np.nan)
    model = cns.LogisticModel(
        data,
        "event",
        ["score", "only_zero", "unknown_predictor"],
        hue="cohort",
        inner_cv=2,
        outer_cv=2,
        retain_estimators=retain_estimators,
    )

    with pytest.warns(RuntimeWarning) as caught:
        model.fit()

    assert len(caught) == 5
    diagnostics = model.diagnostics
    assert diagnostics.columns.tolist() == [
        "analysis_id",
        "analysis",
        "hue_group",
        "status",
        "n_input",
        "n_analyzed",
        "n_dropped",
        "class_counts",
        "failure_reason",
    ]
    assert diagnostics["analysis_id"].is_unique
    assert diagnostics[["hue_group", "analysis"]].to_records(index=False).tolist() == [
        (hue, formula)
        for hue in ["A", "B"]
        for formula in ["score", "only_zero", "unknown_predictor"]
    ]
    assert diagnostics["status"].tolist() == ["success"] + ["failed"] * 5
    assert diagnostics["n_input"].tolist() == [24] * 6
    rows = diagnostics.set_index(["hue_group", "analysis"])
    success = rows.loc[("A", "score")]
    assert success["n_analyzed"] == 22
    assert success["n_dropped"] == 2
    assert success["class_counts"] == {0: 11, 1: 11}
    assert success["failure_reason"] is None
    for hue, formula, n_analyzed in [
        ("A", "only_zero", 12),
        ("B", "score", 24),
        ("B", "only_zero", 24),
    ]:
        row = rows.loc[(hue, formula)]
        assert row["n_analyzed"] == n_analyzed
        assert row["n_dropped"] == 24 - n_analyzed
        assert row["class_counts"] == {0: n_analyzed}
        assert row["failure_reason"] == "No variance in outcome"
    for hue in ["A", "B"]:
        row = rows.loc[(hue, "unknown_predictor")]
        assert pd.isna(row["n_analyzed"])
        assert pd.isna(row["n_dropped"])
        assert row["class_counts"] is None
        assert "unknown_predictor" in row["failure_reason"]

    assert model.results is not None
    assert model.results.columns.tolist() == [
        "predictor",
        "auc",
        "lower_ci",
        "upper_ci",
        "hue_group",
    ]
    assert model.results[["predictor", "hue_group"]].to_dict("records") == [
        {"predictor": "score", "hue_group": "A"}
    ]
    if retain_estimators:
        assert list(model.estimators) == [success["analysis_id"]]
        estimators = model.estimators[success["analysis_id"]]
        assert len(estimators) == 2
        complete = successful.dropna(subset=["score"])
        for estimator in estimators:
            assert isinstance(estimator, Pipeline)
            assert estimator.named_steps["standardscaler"].n_samples_seen_ == 11
            probabilities = estimator.predict_proba(complete)
            assert probabilities.shape == (22, 2)
            assert np.isfinite(probabilities).all()
            np.testing.assert_allclose(probabilities.sum(axis=1), 1)
    else:
        assert model.estimators == {}


def test_duplicate_formulas_retain_distinct_analyses(
    logistic_data: pd.DataFrame,
) -> None:
    model = cns.LogisticModel(
        logistic_data,
        "event",
        ["score", "score"],
        inner_cv=2,
        outer_cv=2,
        retain_estimators=True,
    )
    model.fit()

    assert model.diagnostics["analysis"].tolist() == ["score", "score"]
    assert model.diagnostics["status"].tolist() == ["success", "success"]
    analysis_ids = model.diagnostics["analysis_id"].tolist()
    assert len(set(analysis_ids)) == 2
    assert set(model.estimators) == set(analysis_ids)
    assert (
        model.estimators[analysis_ids[0]][0] is not model.estimators[analysis_ids[1]][0]
    )
    assert model.results is not None
    assert len(model.results) == 2


def test_refitting_clears_results_diagnostics_and_estimators(
    logistic_data: pd.DataFrame,
) -> None:
    model = cns.LogisticModel(
        logistic_data,
        "event",
        ["score"],
        inner_cv=2,
        outer_cv=2,
        retain_estimators=True,
    )
    model.fit()
    assert model.estimators
    assert model.results is not None
    assert model.diagnostics["status"].tolist() == ["success"]

    model.variates = ["unknown_predictor"]
    with pytest.warns(RuntimeWarning):
        model.fit()

    assert model.results is None
    assert model.estimators == {}
    assert model.diagnostics["analysis"].tolist() == ["unknown_predictor"]
    assert model.diagnostics["status"].tolist() == ["failed"]

    model.data = logistic_data.iloc[:0]
    with pytest.raises(ValueError, match="empty"):
        model.fit()

    assert model.results is None
    assert model.diagnostics.empty
    assert model.estimators == {}


def test_invalid_refit_clears_successful_retained_models(
    logistic_data: pd.DataFrame,
) -> None:
    model = cns.LogisticModel(
        logistic_data,
        "event",
        ["score"],
        inner_cv=2,
        outer_cv=2,
        retain_estimators=True,
    )
    model.fit()
    assert model.estimators

    model.groups = [0]
    with pytest.raises(ValueError, match="one identifier per input row"):
        model.fit()

    assert model.results is None
    assert model.diagnostics.empty
    assert model.estimators == {}


def test_failed_outer_fold_does_not_retain_partial_estimators(
    logistic_data: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_predict = GridSearchCV.predict_proba
    predicted_folds = 0

    def fail_second_prediction(self, X):
        nonlocal predicted_folds
        predicted_folds += 1
        if predicted_folds == 2:
            raise ValueError("Held-out prediction failed")
        return original_predict(self, X)

    monkeypatch.setattr(GridSearchCV, "predict_proba", fail_second_prediction)
    model = cns.LogisticModel(
        logistic_data,
        "event",
        ["score"],
        inner_cv=2,
        outer_cv=2,
        retain_estimators=True,
    )

    with pytest.warns(RuntimeWarning) as caught:
        model.fit()

    assert predicted_folds == 2
    assert any("Held-out prediction failed" in str(w.message) for w in caught)
    assert model.results is None
    assert model.estimators == {}
    assert model.diagnostics["status"].tolist() == ["failed"]
    assert model.diagnostics["failure_reason"].tolist() == [
        "Held-out prediction failed"
    ]
    assert model.diagnostics["n_analyzed"].tolist() == [24]
