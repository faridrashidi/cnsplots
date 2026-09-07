"""Auditable fit outcomes and opt-in retained Cox estimators."""

from __future__ import annotations

import lifelines as ll
import numpy as np
import pandas as pd
import pytest

import cnsplots as cns


@pytest.fixture
def cox_data() -> pd.DataFrame:
    rng = np.random.default_rng(13)
    return pd.DataFrame(
        {
            "time": rng.exponential(10, 120),
            "event": rng.integers(0, 2, 120),
            "x": rng.normal(size=120),
            "z": rng.normal(size=120),
            "group": ["A"] * 60 + ["B"] * 60,
        }
    )


def test_cox_diagnostics_include_every_group_formula_and_missing_row(
    cox_data: pd.DataFrame,
) -> None:
    data = cox_data.copy()
    data.loc[[2, 5], "z"] = np.nan
    # Counts must identify rows by position even when input labels repeat.
    data.index = pd.Index([0] * len(data))
    original = data.copy(deep=True)
    model = cns.CoxModel(
        data,
        "time",
        "event",
        ["x", "z", "missing"],
        hue="group",
        retain_estimators=True,
    )
    assert model.diagnostics.empty
    assert model.estimators == {}

    with pytest.warns(RuntimeWarning, match="Error fitting") as caught:
        model.fit()

    assert len(caught) == 3
    diagnostics = model.diagnostics
    assert diagnostics["analysis_id"].tolist() == list(range(6))
    assert diagnostics["analysis"].tolist() == ["x", "z", "missing"] * 2
    assert diagnostics["hue_group"].tolist() == ["A"] * 3 + ["B"] * 3
    assert diagnostics["status"].tolist() == [
        "success",
        "failed",
        "failed",
        "success",
        "success",
        "failed",
    ]
    assert diagnostics["n_input"].tolist() == [60] * 6
    assert diagnostics.loc[[0, 1, 3, 4], "n_analyzed"].tolist() == [60, 58, 60, 60]
    assert diagnostics.loc[[0, 1, 3, 4], "n_dropped"].tolist() == [0, 2, 0, 0]
    assert (
        diagnostics.loc[1, "event_count"]
        == cox_data.loc[cox_data.index[:60].difference([2, 5]), "event"].sum()
    )
    assert diagnostics.loc[3, "event_count"] == cox_data.iloc[60:]["event"].sum()
    assert (
        diagnostics.loc[[2, 5], ["n_analyzed", "n_dropped", "event_count"]]
        .isna()
        .all()
        .all()
    )
    assert diagnostics.loc[[0, 3, 4], "failure_reason"].isna().all()
    assert diagnostics.loc[[1, 2, 5], "failure_reason"].str.len().gt(0).all()
    assert set(model.estimators) == {0, 3, 4}
    assert all(
        isinstance(fitter, ll.CoxPHFitter) for fitter in model.estimators.values()
    )
    assert model.results is not None
    assert len(model.results) == 3
    pd.testing.assert_frame_equal(data, original)


def test_cox_estimator_retention_preserves_results_and_fitted_predictions(
    cox_data: pd.DataFrame,
) -> None:
    default = cns.CoxModel(cox_data, "time", "event", ["x + z"])
    retained = cns.CoxModel(
        cox_data, "time", "event", ["x + z"], retain_estimators=True
    )

    default.fit()
    retained.fit()

    assert default.estimators == {}
    assert default.results is not None
    assert retained.results is not None
    pd.testing.assert_frame_equal(default.results, retained.results)
    pd.testing.assert_frame_equal(default.diagnostics, retained.diagnostics)
    assert len(retained.results) == 2
    assert len(retained.diagnostics) == 1
    reference = ll.CoxPHFitter().fit(
        cox_data, duration_col="time", event_col="event", formula="x + z"
    )
    pd.testing.assert_frame_equal(retained.estimators[0].summary, reference.summary)
    pd.testing.assert_series_equal(
        retained.estimators[0].predict_partial_hazard(cox_data),
        reference.predict_partial_hazard(cox_data),
    )
    assert retained.diagnostics.loc[0, "event_count"] == cox_data["event"].sum()


def test_cox_diagnostics_and_estimators_reset_for_each_fit(
    cox_data: pd.DataFrame,
) -> None:
    model = cns.CoxModel(cox_data, "time", "event", ["x"], retain_estimators=True)
    model.fit()
    first_estimator = model.estimators[0]
    model.variates = ["z", "x"]
    model.fit()

    assert model.diagnostics["analysis"].tolist() == ["z", "x"]
    assert model.diagnostics["analysis_id"].tolist() == [0, 1]
    assert set(model.estimators) == {0, 1}
    assert model.estimators[0] is not first_estimator

    model.variates = ["missing"]
    with pytest.warns(RuntimeWarning):
        model.fit()

    assert model.results is None
    assert model.estimators == {}
    assert model.diagnostics["analysis"].tolist() == ["missing"]
    assert model.diagnostics["status"].tolist() == ["failed"]

    model.data = cox_data.drop(columns="event")
    with pytest.raises(ValueError, match="event"):
        model.fit()

    assert model.results is None
    assert model.diagnostics.empty
    assert model.estimators == {}


def test_cox_all_missing_predictors_have_zero_eligible_rows(
    cox_data: pd.DataFrame,
) -> None:
    model = cns.CoxModel(cox_data.assign(x=np.nan), "time", "event", ["x"])

    with pytest.warns(RuntimeWarning):
        model.fit()

    row = model.diagnostics.iloc[0]
    assert row["status"] == "failed"
    assert row["n_input"] == len(cox_data)
    assert row["n_analyzed"] == 0
    assert row["n_dropped"] == len(cox_data)
    assert row["event_count"] == 0
    assert row["failure_reason"]
    assert model.results is None


def test_cox_failure_counts_use_lifelines_formula_row_order(
    cox_data: pd.DataFrame,
) -> None:
    data = cox_data.assign(time=np.arange(120, 0, -1), event=[0] + [1] * 119)
    model = cns.CoxModel(data, "time", "event", ["x.shift(1)"])

    with pytest.warns(RuntimeWarning):
        model.fit()

    row = model.diagnostics.iloc[0]
    assert row["status"] == "failed"
    assert row["n_analyzed"] == 119
    assert row["n_dropped"] == 1
    # lifelines sorts by duration before evaluating the shift, excluding the
    # final input row (event=1), not the first input row (event=0).
    assert row["event_count"] == 118
