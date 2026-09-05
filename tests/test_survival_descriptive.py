from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from lifelines import AalenJohansenFitter, KaplanMeierFitter

import cnsplots as cns


@pytest.mark.parametrize("plot_name", ["survivalplot", "cumulativeincidenceplot"])
@pytest.mark.parametrize("event_code", [0, 1])
@pytest.mark.parametrize("single_group", [False, True])
def test_descriptive_curves_match_lifelines(
    plot_name: str, event_code: int, single_group: bool
) -> None:
    data = pd.DataFrame(
        {
            "time": [1, 2, 3, 4, 1, 2, 3, 4],
            "event": event_code,
            "group": ["A"] * 4 + ["A" if single_group else "B"] * 4,
        }
    )
    original = data.copy(deep=True)
    ax = getattr(cns, plot_name)(data, "time", "event", "group", descriptive_only=True)
    curves = [line for line in ax.lines if line.get_drawstyle() == "steps-post"]
    assert len(curves) == data["group"].nunique()
    assert not ax.texts
    for curve, (_, group) in zip(curves, data.groupby("group"), strict=True):
        if plot_name == "survivalplot":
            reference = KaplanMeierFitter().fit(group["time"], group["event"])
            expected = reference.survival_function_
        else:
            reference = AalenJohansenFitter().fit(
                group["time"], group["event"], event_of_interest=1
            )
            expected = reference.cumulative_density_
        np.testing.assert_allclose(curve.get_xdata(), expected.index)
        np.testing.assert_allclose(curve.get_ydata(), expected.iloc[:, 0])
    pd.testing.assert_frame_equal(data, original)


def test_descriptive_mode_skips_all_inference(
    survival_df: pd.DataFrame,
    competing_risk_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import lifelines
    import lifelines.statistics

    from cnsplots.helpers import _cmprsk

    def unexpected(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Descriptive mode must not run inference")

    monkeypatch.setattr(lifelines, "CoxPHFitter", unexpected)
    monkeypatch.setattr(lifelines.statistics, "multivariate_logrank_test", unexpected)
    monkeypatch.setattr(
        lifelines.statistics,
        "survival_difference_at_fixed_point_in_time_test",
        unexpected,
    )
    monkeypatch.setattr(_cmprsk, "cuminc", unexpected)
    ax = cns.survivalplot(
        survival_df,
        "time",
        "event",
        "group",
        descriptive_only=True,
        overall_test="trend",
        pairs=[("missing", "ignored")],
        landmark_time=6,
        rmst_time=8,
        show_median_survival=True,
        show_risk_table=True,
        ci_show=True,
    )
    annotation = ax.texts[0].get_text()
    assert "Survival at 6" in annotation
    assert "RMST to 8" in annotation
    assert "Median survival" in annotation
    assert "P =" not in annotation
    assert "HR" not in annotation
    assert len(ax.figure.axes) == 2
    _, cif_ax = plt.subplots()
    cns.cumulativeincidenceplot(
        competing_risk_df,
        "time",
        "event",
        "group",
        descriptive_only=True,
        ax=cif_ax,
    )
    assert not cif_ax.texts


def test_all_censored_group_keeps_logrank_and_reports_unavailable_cox() -> None:
    data = pd.DataFrame(
        {
            "time": [1, 2, 3, 4, 1, 2, 3, 4],
            "event": [0, 0, 0, 0, 1, 0, 1, 0],
            "group": ["A"] * 4 + ["B"] * 4,
        }
    )
    with pytest.warns(UserWarning, match="Cox HR.*unavailable"):
        ax = cns.survivalplot(data, "time", "event", "group")
    assert "Log-rank P =" in ax.texts[0].get_text()
    assert "Cox HR (B vs A) unavailable" in ax.texts[0].get_text()
    assert "HR =" not in ax.texts[0].get_text()
    curve = next(line for line in ax.lines if line.get_label() == "A (n=4)")
    np.testing.assert_array_equal(curve.get_ydata(), np.ones(5))
    _, ax = plt.subplots()
    cns.survivalplot(data, "time", "event", "group", show_hazard_ratio=False, ax=ax)
    assert ax.texts[0].get_text().startswith("Log-rank P =")


@pytest.mark.parametrize("event_code", [0, 2, 3])
def test_cumulative_incidence_without_primary_events(event_code: int) -> None:
    data = pd.DataFrame(
        {"time": [1, 2, 3, 4], "event": event_code, "group": ["A", "A", "B", "B"]}
    )
    with pytest.warns(
        UserWarning, match="Gray's test unavailable.*no events of interest"
    ):
        ax = cns.cumulativeincidenceplot(data, "time", "event", "group")
    for line in ax.lines:
        np.testing.assert_array_equal(line.get_ydata(), np.zeros(3))
    assert "Gray's test unavailable" in ax.texts[0].get_text()
    assert len(ax.collections) == (2 if event_code == 0 else 0)


@pytest.mark.parametrize("plot_name", ["survivalplot", "cumulativeincidenceplot"])
@pytest.mark.parametrize("event_code", [0, 1])
def test_descriptive_single_observation(plot_name: str, event_code: int) -> None:
    data = pd.DataFrame({"time": [2], "event": [event_code], "group": ["A"]})
    _, target = plt.subplots()
    ax = getattr(cns, plot_name)(
        data,
        "time",
        "event",
        "group",
        descriptive_only=True,
        show_risk_table=True,
        ax=target,
    )
    assert ax is target
    assert len(ax.figure.axes) == 2


def test_entirely_uncensored_cohort_keeps_estimable_inference(
    survival_df: pd.DataFrame,
) -> None:
    from lifelines import CoxPHFitter
    from lifelines.statistics import multivariate_logrank_test

    data = survival_df.assign(event=1)
    ax = cns.survivalplot(data, "time", "event", "group")
    logrank = multivariate_logrank_test(data["time"], data["group"], data["event"])
    cox_data = data[["time", "event"]].assign(
        comparison=(data["group"] == "Treatment").astype(int)
    )
    model = CoxPHFitter().fit(cox_data, "time", "event")
    assert f"Log-rank P = ${logrank.p_value:.2g}$" in ax.texts[0].get_text()
    assert f"HR = {model.hazard_ratios_.iloc[0]:.2f}" in ax.texts[0].get_text()
    assert "unavailable" not in ax.texts[0].get_text()


def test_all_censored_cohort_reports_each_unavailable_comparison(
    survival_df: pd.DataFrame,
) -> None:
    with pytest.warns(UserWarning) as recorded:
        ax = cns.survivalplot(survival_df.assign(event=0), "time", "event", "group")
    assert len(recorded) == 2
    assert ax.texts[0].get_text().splitlines() == [
        "Log-rank unavailable",
        "Cox HR (Treatment vs Control) unavailable",
    ]
    for curve in ax.lines:
        np.testing.assert_allclose(np.asarray(curve.get_ydata()), 1)


@pytest.mark.parametrize("plot_name", ["survivalplot", "cumulativeincidenceplot"])
def test_zero_comparison_variance_is_unavailable(plot_name: str) -> None:
    data = pd.DataFrame(
        {"time": [1] * 4, "event": [1] * 4, "group": ["A", "A", "B", "B"]}
    )
    kwargs = {"show_hazard_ratio": False} if plot_name == "survivalplot" else {}
    with pytest.warns(UserWarning, match="unavailable.*variance is zero or singular"):
        ax = getattr(cns, plot_name)(data, "time", "event", "group", **kwargs)
    assert "P =" not in ax.texts[0].get_text()
    assert len(ax.lines) == 2


@pytest.mark.parametrize("overall_test", ["logrank", "trend"])
def test_cox_separation_preserves_curves(overall_test: Any) -> None:
    data = pd.DataFrame(
        {"time": list(range(1, 9)), "event": [1] * 8, "group": ["A"] * 4 + ["B"] * 4}
    )
    with pytest.warns(UserWarning, match="Cox.*unavailable"):
        ax = cns.survivalplot(
            data,
            "time",
            "event",
            "group",
            overall_test=overall_test,
            hue_order=["A", "B"],
        )
    assert len(ax.lines) == 2
    assert "HR =" not in ax.texts[0].get_text()


@pytest.mark.parametrize("event_code", [0, 2])
def test_gray_test_allows_a_group_without_primary_events(
    competing_risk_df: pd.DataFrame, event_code: int
) -> None:
    from comprisk import gray_test

    data = competing_risk_df.copy()
    data.loc[data["group"] == "A", "event"] = event_code
    original = data.copy(deep=True)
    ax = cns.cumulativeincidenceplot(data, "time", "event", "group")
    expected = gray_test(data["time"], data["event"], data["group"], cause=1)
    assert ax.texts[0].get_text() == f"P = ${expected.pvalue:.2g}$"
    np.testing.assert_allclose(np.asarray(ax.lines[0].get_ydata()), 0)
    pd.testing.assert_frame_equal(data, original)


@pytest.mark.parametrize("plot_name", ["survivalplot", "cumulativeincidenceplot"])
@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("time", -1, "non-negative durations"),
        ("time", np.inf, "finite durations"),
        ("time", np.nan, "null"),
        ("event", -1, "event codes"),
        ("event", 0.5, "event codes"),
        ("event", 1j, "event codes"),
        ("event", np.inf, "event codes"),
        ("event", np.nan, "null"),
        ("group", None, "null"),
    ],
)
def test_descriptive_mode_still_rejects_invalid_data(
    plot_name: str, column: str, value: Any, message: str
) -> None:
    data = pd.DataFrame({"time": [1.0, 2.0], "event": [0.0, 1.0], "group": ["A", "A"]})
    if isinstance(value, complex):
        data[column] = data[column].astype(complex)
    data.loc[0, column] = value
    with pytest.raises(ValueError, match=message):
        getattr(cns, plot_name)(data, "time", "event", "group", descriptive_only=True)


@pytest.mark.parametrize("test_name", ["logrank", "trend", "landmark", "gray"])
@pytest.mark.parametrize("pvalue", [np.nan, np.inf, -0.1, 1.1])
def test_invalid_backend_pvalues_preserve_estimates(
    test_name: str,
    pvalue: float,
    survival_df: pd.DataFrame,
    competing_risk_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import lifelines.statistics
    from lifelines.fitters.coxph_fitter import SemiParametricPHFitter

    from cnsplots.helpers import _cmprsk

    def invalid_result(*args: Any, **kwargs: Any) -> Any:
        return SimpleNamespace(p_value=pvalue)

    kwargs: dict[str, Any] = {}
    if test_name == "logrank":
        monkeypatch.setattr(
            lifelines.statistics, "multivariate_logrank_test", invalid_result
        )
    elif test_name == "trend":
        monkeypatch.setattr(
            SemiParametricPHFitter, "log_likelihood_ratio_test", invalid_result
        )
        kwargs.update(overall_test="trend", hue_order=["Control", "Treatment"])
    elif test_name == "landmark":
        monkeypatch.setattr(
            lifelines.statistics,
            "survival_difference_at_fixed_point_in_time_test",
            invalid_result,
        )
        kwargs.update(landmark_time=6, rmst_time=8)
    else:
        monkeypatch.setattr(_cmprsk, "cuminc", lambda *args, **kwargs: pvalue)

    with pytest.warns(UserWarning, match="unavailable.*finite p-value"):
        if test_name == "gray":
            ax = cns.cumulativeincidenceplot(
                competing_risk_df, "time", "event", "group"
            )
        else:
            ax = cns.survivalplot(survival_df, "time", "event", "group", **kwargs)
    annotation = ax.texts[0].get_text()
    assert "unavailable" in annotation
    assert "nan" not in annotation
    assert "inf" not in annotation
    if test_name != "gray":
        assert "HR =" in annotation
    if test_name == "landmark":
        assert "Control = 0.67" in annotation
        assert "RMST to 8" in annotation


@pytest.mark.parametrize(
    ("column", "value"),
    [("exp(coef)", np.inf), ("exp(coef) lower 95%", 0), ("p", np.nan)],
)
def test_invalid_cox_estimates_are_not_reported(
    column: str,
    value: float,
    survival_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from lifelines.fitters.coxph_fitter import SemiParametricPHFitter

    original_summary = SemiParametricPHFitter.summary.fget
    assert original_summary is not None

    def invalid_summary(fitter: Any) -> pd.DataFrame:
        summary = original_summary(fitter)
        summary.loc["_comparison", column] = value
        return summary

    monkeypatch.setattr(SemiParametricPHFitter, "summary", property(invalid_summary))
    with pytest.warns(UserWarning, match="Cox HR.*unavailable"):
        ax = cns.survivalplot(survival_df, "time", "event", "group")
    assert "HR =" not in ax.texts[0].get_text()
    assert "Log-rank P =" in ax.texts[0].get_text()


def test_failed_pair_does_not_discard_other_contrasts(
    survival_three_group_df: pd.DataFrame,
) -> None:
    data = survival_three_group_df.copy()
    data.loc[data["group"] == "Mid", "event"] = 0
    with pytest.warns(UserWarning, match="Cox HR \\(Mid vs Low\\) unavailable"):
        ax = cns.survivalplot(
            data, "time", "event", "group", pairs=[("Low", "Mid"), ("Low", "High")]
        )
    annotation = ax.texts[0].get_text()
    assert "Log-rank P =" in annotation
    assert "Cox HR (Mid vs Low) unavailable" in annotation
    assert "High vs Low\nHR = 0.38" in annotation


def test_uncensored_competing_events_are_not_redefined_as_censoring(
    competing_risk_df: pd.DataFrame,
) -> None:
    from comprisk import gray_test

    data = competing_risk_df.loc[competing_risk_df["event"] != 0]
    ax = cns.cumulativeincidenceplot(data, "time", "event", "group")
    expected = gray_test(data["time"], data["event"], data["group"], cause=1)
    assert ax.texts[0].get_text() == f"P = ${expected.pvalue:.2g}$"
    assert not ax.collections
    np.testing.assert_allclose(
        np.asarray(ax.lines[0].get_ydata()), [0, 0.25, 0.25, 0.5, 0.5]
    )
