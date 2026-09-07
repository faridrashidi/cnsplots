"""Regression coverage for configurable nested logistic cross-validation."""

from __future__ import annotations

from collections import Counter
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.model_selection import (
    BaseCrossValidator,
    GridSearchCV,
    GroupKFold,
    StratifiedKFold,
    cross_val_predict,
)
from sklearn.preprocessing import StandardScaler

import cnsplots as cns
from cnsplots import _methods


class RecordingGroupKFold(GroupKFold):
    def __init__(self, n_splits: int) -> None:
        super().__init__(n_splits=n_splits)
        self.calls = []

    def split(self, X, y=None, groups=None):
        splits = list(super().split(X, y, groups))
        self.calls.append((X.copy(), np.asarray(y), np.asarray(groups), splits))
        return iter(splits)


@pytest.mark.parametrize("groups_as_column", [True, False])
def test_grouped_nested_cv_keeps_subjects_and_preprocessing_separate(
    monkeypatch: pytest.MonkeyPatch, groups_as_column: bool
) -> None:
    data = pd.DataFrame(
        {
            "event": [0, 1] * 24,
            "score": np.arange(48, dtype=float),
            "row_id": np.arange(48),
            "subject": np.repeat(np.arange(24), 2),
            "cohort": ["A"] * 24 + ["B"] * 24,
        },
        index=np.full(48, 100),
    )
    data.iloc[[0, 5, 28], data.columns.get_loc("score")] = np.nan
    groups = (
        "subject"
        if groups_as_column
        else pd.Series(data["subject"].to_numpy(), index=np.arange(48)[::-1])
    )
    outer = RecordingGroupKFold(3)
    inner = RecordingGroupKFold(2)
    design_rows = []
    scaler_rows = []
    original_design_fit = _methods._LogisticDesign.fit

    def track_design_fit(self, X, y=None):
        design_rows.append(tuple(X["row_id"]))
        return original_design_fit(self, X, y)

    class TrackingScaler(StandardScaler):
        def fit(self, X, y=None, sample_weight=None):
            scaler_rows.append(tuple(X["score"].astype(int)))
            return super().fit(X, y, sample_weight=sample_weight)

    monkeypatch.setattr(_methods._LogisticDesign, "fit", track_design_fit)
    monkeypatch.setattr(_methods, "StandardScaler", TrackingScaler)
    monkeypatch.setattr(
        cns.LogisticModel, "_compute_auc_ci", lambda self, y, p: (0.5, 0.4, 0.6)
    )
    model = cns.LogisticModel(
        data,
        event="event",
        variates=["score"],
        hue="cohort",
        groups=groups,
        outer_cv=outer,
        inner_cv=inner,
        retain_estimators=True,
    )

    model.fit()

    assert model.results is not None
    assert len(outer.calls) == 2
    assert len(inner.calls) == 6
    expected_fits = Counter()
    for cohort_index, (X, y, received_groups, outer_splits) in enumerate(outer.calls):
        cohort = "AB"[cohort_index]
        expected = data[(data["cohort"] == cohort) & data["score"].notna()]
        np.testing.assert_array_equal(X["row_id"], expected["row_id"])
        np.testing.assert_array_equal(y, expected["event"])
        np.testing.assert_array_equal(received_groups, expected["subject"])
        analysis_id = model.diagnostics.loc[
            model.diagnostics["hue_group"] == cohort, "analysis_id"
        ].iloc[0]
        retained = model.estimators[analysis_id]
        assert len(retained) == 3
        for fold, (outer_train, outer_test) in enumerate(outer_splits):
            train_subjects = set(received_groups[outer_train])
            test_subjects = set(received_groups[outer_test])
            assert train_subjects.isdisjoint(test_subjects)
            outer_rows = X["row_id"].to_numpy()[outer_train]
            expected_fits[tuple(outer_rows)] += 1
            inner_X, inner_y, inner_groups, inner_splits = inner.calls[
                cohort_index * 3 + fold
            ]
            np.testing.assert_array_equal(inner_X["row_id"], outer_rows)
            np.testing.assert_array_equal(inner_y, y[outer_train])
            np.testing.assert_array_equal(inner_groups, received_groups[outer_train])
            for inner_train, inner_test in inner_splits:
                assert set(inner_groups[inner_train]).isdisjoint(
                    inner_groups[inner_test]
                )
                assert set(inner_groups[inner_train]).isdisjoint(test_subjects)
                expected_fits[tuple(outer_rows[inner_train])] += 10
            pipeline = retained[fold]
            assert pipeline.steps[0][1].formula == "score"
            np.testing.assert_allclose(pipeline.steps[1][1].mean_, [outer_rows.mean()])
            assert pipeline.steps[2][1].classes_.tolist() == [0, 1]
    assert Counter(design_rows) == expected_fits
    assert Counter(scaler_rows) == expected_fits
    assert len(design_rows) == 2 * 3 * (2 * 10 + 1)


def test_nondefault_folds_fit_fewer_than_seven_rows_per_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = pd.DataFrame({"event": [0, 1] * 6, "score": np.arange(12)})
    monkeypatch.setattr(
        cns.LogisticModel, "_compute_auc_ci", lambda self, y, p: (0.5, 0.4, 0.6)
    )
    model = cns.LogisticModel(data, "event", ["score"], outer_cv=3, inner_cv=2)

    model.fit()

    assert model.results is not None
    assert model.estimators == {}
    assert model.diagnostics["status"].tolist() == ["success"]


def test_default_predictions_match_previous_nested_cross_val_predict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event = np.tile([0, 1], 15)
    data = pd.DataFrame(
        {"event": event, "score": event + np.random.default_rng(20).normal(size=30)}
    )
    probabilities = []

    def capture_auc(self, y, p):
        probabilities.append(p)
        return 0.5, 0.4, 0.6

    monkeypatch.setattr(cns.LogisticModel, "_compute_auc_ci", capture_auc)
    model = cns.LogisticModel(data, "event", ["score"], retain_estimators=True)
    model.fit()
    pipeline = clone(model.estimators[0][0])
    previous_estimator = GridSearchCV(
        pipeline,
        {"logisticregression__C": np.logspace(-4, 4, 10)},
        cv=5,
        scoring="roc_auc",
        error_score="raise",
    )

    previous_probabilities = cross_val_predict(
        previous_estimator, data, event, cv=5, method="predict_proba"
    )[:, 1]

    np.testing.assert_array_equal(probabilities[0], previous_probabilities)


def test_shuffled_splitters_and_model_seed_are_reproducible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = pd.DataFrame({"event": [0, 1] * 12, "score": np.arange(24)})
    seeds = []
    original_rng = np.random.default_rng
    original_auc = cns.LogisticModel._compute_auc_ci

    def record_rng(seed=None):
        seeds.append(seed)
        return original_rng(seed)

    def short_bootstrap(self, y, probabilities):
        return original_auc(self, y, probabilities, n_bootstrap=30)

    monkeypatch.setattr(_methods.np.random, "default_rng", record_rng)
    monkeypatch.setattr(cns.LogisticModel, "_compute_auc_ci", short_bootstrap)
    outer = StratifiedKFold(3, shuffle=True, random_state=11)
    model = cns.LogisticModel(
        data,
        "event",
        ["score"],
        outer_cv=outer,
        inner_cv=StratifiedKFold(2, shuffle=True, random_state=7),
        random_state=17,
        retain_estimators=True,
    )
    model.fit()
    assert model.results is not None
    first_results = model.results.copy()
    first_estimators = next(iter(model.estimators.values()))

    model.fit()

    pd.testing.assert_frame_equal(model.results, first_results)
    assert seeds == [17, 17]
    second_estimators = next(iter(model.estimators.values()))
    for (train, _), first, second in zip(
        outer.split(data, data["event"]), first_estimators, second_estimators
    ):
        assert first is not second
        np.testing.assert_allclose(
            first.steps[1][1].mean_, [data.iloc[train].score.mean()]
        )
        assert second.steps[2][1].random_state == 17
        np.testing.assert_array_equal(
            first.predict_proba(data), second.predict_proba(data)
        )


@pytest.mark.parametrize(
    "groups", [[0, 1], np.zeros((12, 1)), "missing_subject", [None] * 12]
)
def test_invalid_groups_clear_stale_state_before_fitting(
    monkeypatch: pytest.MonkeyPatch, groups
) -> None:
    data = pd.DataFrame({"event": [0, 1] * 6, "score": np.arange(12)})
    model = cns.LogisticModel(data, "event", ["score"], groups=groups)
    model.results = pd.DataFrame({"old": [True]})
    model.diagnostics = pd.DataFrame({"old": [True]})
    model.estimators = {99: []}
    fit = Mock()
    monkeypatch.setattr(_methods._LogisticDesign, "fit", fit)

    with pytest.raises(ValueError):
        model.fit()

    fit.assert_not_called()
    assert model.results is None
    assert model.diagnostics.empty
    assert model.estimators == {}


class InvalidCV(BaseCrossValidator):
    def __init__(self, problem: str) -> None:
        self.problem = problem

    def get_n_splits(self, X=None, y=None, groups=None):
        return 2

    def split(self, X, y=None, groups=None):
        train = np.arange(len(X) - 2)
        test = np.arange(len(X) - 2, len(X))
        if self.problem == "overlap":
            train = np.arange(len(X))
        elif self.problem == "one class":
            test = np.flatnonzero(np.asarray(y) == 0)
            train = np.flatnonzero(np.asarray(y) == 1)
        elif self.problem == "out of range":
            test = np.array([len(X), len(X) + 1])
        elif self.problem == "no splits":
            return
        yield train, test
        if self.problem == "repeated heldout":
            yield train, test


@pytest.mark.parametrize("layer", ["inner", "outer"])
@pytest.mark.parametrize(
    "problem", ["overlap", "one class", "out of range", "no splits"]
)
def test_invalid_nested_splits_fail_before_learning(
    monkeypatch: pytest.MonkeyPatch, layer: str, problem: str
) -> None:
    data = pd.DataFrame({"event": [0, 1] * 12, "score": np.arange(24)})
    model = cns.LogisticModel(
        data,
        "event",
        ["score"],
        inner_cv=InvalidCV(problem) if layer == "inner" else 2,
        outer_cv=InvalidCV(problem) if layer == "outer" else 3,
    )
    fit = Mock()
    monkeypatch.setattr(_methods._LogisticDesign, "fit", fit)

    with pytest.warns(RuntimeWarning):
        model.fit()

    fit.assert_not_called()
    assert model.results is None
    assert model.diagnostics["status"].tolist() == ["failed"]
    assert layer.capitalize() in model.diagnostics.iloc[0]["failure_reason"]


@pytest.mark.parametrize("problem", ["missing heldout", "repeated heldout"])
def test_outer_validation_requires_each_row_exactly_once(problem: str) -> None:
    data = pd.DataFrame({"event": [0, 1] * 12, "score": np.arange(24)})
    model = cns.LogisticModel(
        data, "event", ["score"], outer_cv=InvalidCV(problem), inner_cv=2
    )

    with pytest.warns(RuntimeWarning):
        model.fit()

    assert model.results is None
    assert "exactly once" in model.diagnostics.iloc[0]["failure_reason"]


@pytest.mark.parametrize("layer", ["inner", "outer"])
def test_groups_cannot_be_silently_ignored_by_splitter(layer: str) -> None:
    data = pd.DataFrame(
        {
            "event": [0, 1] * 24,
            "score": np.arange(48),
            "subject": np.tile(np.repeat(np.arange(6), 2), 4),
        }
    )
    model = cns.LogisticModel(
        data,
        "event",
        ["score"],
        groups="subject",
        inner_cv=2,
        outer_cv=GroupKFold(3) if layer == "inner" else 3,
    )

    with pytest.warns(RuntimeWarning):
        model.fit()

    assert model.results is None
    assert "group" in model.diagnostics.iloc[0]["failure_reason"].lower()
    assert layer.capitalize() in model.diagnostics.iloc[0]["failure_reason"]
