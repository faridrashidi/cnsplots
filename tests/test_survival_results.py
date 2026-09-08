from __future__ import annotations

from typing import Any, cast

import lifelines as ll
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from lifelines.statistics import (
    multivariate_logrank_test,
    survival_difference_at_fixed_point_in_time_test,
)
from lifelines.utils import restricted_mean_survival_time
from statsmodels.stats.multitest import multipletests

import cnsplots as cns

_COLUMNS = {
    "kind",
    "groups",
    "group1",
    "group2",
    "test",
    "n",
    "events",
    "n1",
    "events1",
    "n2",
    "events2",
    "time",
    "estimate",
    "ci_lower",
    "ci_upper",
    "ci_level",
    "statistic",
    "pvalue_raw",
    "pvalue_adjusted",
    "p_adjust",
    "family_size",
    "status",
    "reason",
    "annotation",
}


@pytest.mark.parametrize("p_adjust", [None, "bonferroni", "holm", "fdr_bh", "fdr_by"])
def test_survival_results_match_cox_and_adjustment(
    survival_three_group_df: pd.DataFrame, p_adjust: str | None
) -> None:
    data = survival_three_group_df
    order = ["High", "Mid", "Low"]
    pairs = [("Low", "High"), ("High", "Mid"), ("Low", "Mid")]
    _, target = plt.subplots()
    ax = cns.survivalplot(
        data,
        "time",
        "event",
        "group",
        hue_order=order,
        pairs=pairs,
        p_adjust=cast(Any, p_adjust),
        time_label="Months",
        ax=target,
    )
    assert ax is target
    results = cns.get_survival_results(ax)
    assert set(results.columns) == _COLUMNS
    assert results.attrs == {
        "duration": "time",
        "event": "event",
        "hue": "group",
        "time_label": "Months",
        "event_observed": 1,
        "event_censored": 0,
        "common_follow_up": 8,
    }
    assert results.kind.tolist() == ["overall"] + ["pairwise_cox"] * 3
    overall = results.iloc[0]
    expected_overall = multivariate_logrank_test(data.time, data.group, data.event)
    assert overall.groups == tuple(order)
    assert overall.test == "logrank"
    assert overall.n == 18
    assert overall.events == 12
    assert overall[["n1", "events1", "n2", "events2"]].isna().all()
    assert overall.statistic == pytest.approx(expected_overall.test_statistic)
    assert overall.pvalue_raw == pytest.approx(expected_overall.p_value)
    assert overall.pvalue_adjusted == overall.pvalue_raw
    assert overall.p_adjust is None

    contrasts = results.loc[results.kind == "pairwise_cox"]
    assert list(zip(contrasts.group1, contrasts.group2)) == pairs
    raw = []
    for (_, row), (reference, comparison) in zip(
        contrasts.iterrows(), pairs, strict=True
    ):
        subset = data.loc[data.group.isin([reference, comparison])]
        model_data = subset[["time", "event"]].assign(
            comparison=(subset.group == comparison).astype(int)
        )
        expected = ll.CoxPHFitter().fit(model_data, "time", "event").summary.iloc[0]
        raw.append(expected["p"])
        assert row.groups == (reference, comparison)
        assert row.test == "cox_wald"
        assert (row.n, row.events) == (12, 8)
        assert (row.n1, row.events1, row.n2, row.events2) == (6, 4, 6, 4)
        assert row.estimate == pytest.approx(expected["exp(coef)"])
        assert row.ci_lower == pytest.approx(expected["exp(coef) lower 95%"])
        assert row.ci_upper == pytest.approx(expected["exp(coef) upper 95%"])
        assert row.ci_level == 0.95
        assert row.statistic == pytest.approx(expected["z"])
        assert row.pvalue_raw == pytest.approx(expected["p"])
        assert row.p_adjust == p_adjust
        assert row.family_size == 3
        assert row.status == "available"
        assert pd.isna(row.time)
    adjusted = raw if p_adjust is None else multipletests(raw, method=p_adjust)[1]
    np.testing.assert_allclose(contrasts.pvalue_adjusted, adjusted)
    annotation = ax.texts[-1].get_text()
    assert all(text and text in annotation for text in results.annotation)
    if p_adjust is not None:
        assert p_adjust in annotation
        assert "raw" in annotation.lower()
        assert "adjusted" in annotation.lower()
        assert "unadjusted" in annotation.lower()
        assert "3" in annotation


def test_survival_results_match_ordered_trend(
    survival_three_group_df: pd.DataFrame,
) -> None:
    order = ["High", "Low", "Mid"]
    data = survival_three_group_df
    ax = cns.survivalplot(
        data, "time", "event", "group", hue_order=order, overall_test="trend"
    )
    model_data = data[["time", "event"]].assign(
        order=data.group.map({group: index for index, group in enumerate(order)})
    )
    expected = (
        ll.CoxPHFitter().fit(model_data, "time", "event").log_likelihood_ratio_test()
    )
    result = cns.get_survival_results(ax).iloc[0]
    assert result.kind == "overall"
    assert result.test == "trend"
    assert result.groups == tuple(order)
    assert result.statistic == pytest.approx(expected.test_statistic)
    assert result.pvalue_raw == pytest.approx(expected.p_value)


def test_survival_results_match_descriptive_and_landmark_estimates(
    survival_df: pd.DataFrame,
) -> None:
    ax = cns.survivalplot(
        survival_df,
        "time",
        "event",
        "group",
        show_median_survival=True,
        landmark_time=6,
        rmst_time=11,
    )
    results = cns.get_survival_results(ax)
    assert results.kind.value_counts().to_dict() == {
        "overall": 1,
        "pairwise_cox": 1,
        "median_survival": 2,
        "landmark_survival": 2,
        "landmark_test": 1,
        "rmst": 2,
    }
    fitters = []
    for group in ("Control", "Treatment"):
        subset = survival_df.loc[survival_df.group == group]
        fitter = ll.KaplanMeierFitter().fit(subset.time, subset.event)
        fitters.append(fitter)
        expected = {
            "median_survival": (fitter.median_survival_time_, np.nan),
            "landmark_survival": (fitter.predict(6), 6),
            "rmst": (restricted_mean_survival_time(fitter, t=11), 11),
        }
        for kind, (estimate, time) in expected.items():
            row = results.loc[(results.kind == kind) & (results.group1 == group)].iloc[
                0
            ]
            assert row.estimate == pytest.approx(estimate)
            assert row.time == time or (pd.isna(row.time) and pd.isna(time))
            assert row.groups == (group,)
            assert row.group2 is None
            assert (row.n, row.events) == (6, 4)
            assert (row.n1, row.events1) == (6, 4)
            assert row[["n2", "events2"]].isna().all()
            assert row.status == "available"
            assert row.test is None
            assert row[["pvalue_raw", "pvalue_adjusted", "ci_level"]].isna().all()
    landmark = results.loc[results.kind == "landmark_test"].iloc[0]
    expected_test = survival_difference_at_fixed_point_in_time_test(6, *fitters)
    assert landmark.test == "fixed_time_log_minus_log"
    assert landmark.time == 6
    assert landmark.statistic == pytest.approx(expected_test.test_statistic)
    assert landmark.pvalue_raw == pytest.approx(expected_test.p_value)
    assert landmark.pvalue_adjusted == landmark.pvalue_raw
    assert landmark.p_adjust is None
    assert (landmark.n1, landmark.events1, landmark.n2, landmark.events2) == (
        6,
        4,
        6,
        4,
    )
    assert all(text and text in ax.texts[-1].get_text() for text in results.annotation)


@pytest.mark.parametrize("p_adjust", ["bonferroni", "holm", "fdr_bh", "fdr_by"])
def test_unavailable_pairs_remain_in_correction_family(
    survival_three_group_df: pd.DataFrame, p_adjust: str
) -> None:
    data = survival_three_group_df.copy()
    data.loc[data.group == "Mid", "event"] = 0
    with pytest.warns(UserWarning, match="Cox HR.*unavailable"):
        ax = cns.survivalplot(
            data,
            "time",
            "event",
            "group",
            pairs=[("Low", "Mid"), ("Low", "High")],
            p_adjust=cast(Any, p_adjust),
        )
    pairs = cns.get_survival_results(ax).query("kind == 'pairwise_cox'")
    assert pairs.group2.tolist() == ["Mid", "High"]
    assert pairs.status.tolist() == ["unavailable", "available"]
    assert pairs.family_size.tolist() == [2, 2]
    unavailable, available = pairs.iloc[0], pairs.iloc[1]
    assert unavailable.reason
    assert unavailable.events2 == 0
    assert (
        unavailable[
            [
                "estimate",
                "ci_lower",
                "ci_upper",
                "statistic",
                "pvalue_raw",
                "pvalue_adjusted",
            ]
        ]
        .isna()
        .all()
    )
    expected = multipletests([1, available.pvalue_raw], method=p_adjust)[1][1]
    assert available.pvalue_adjusted == pytest.approx(expected)
    assert unavailable.annotation in ax.texts[-1].get_text()


def test_survival_results_preserve_unavailable_landmark_and_unreached_median(
    survival_df: pd.DataFrame,
) -> None:
    data = survival_df.copy()
    data.loc[data.group == "Treatment", "event"] = 0
    with pytest.warns(UserWarning, match="Landmark test unavailable"):
        ax = cns.survivalplot(
            data,
            "time",
            "event",
            "group",
            show_hazard_ratio=False,
            show_median_survival=True,
            landmark_time=1,
        )
    results = cns.get_survival_results(ax)
    median = results.loc[
        (results.kind == "median_survival") & (results.group1 == "Treatment")
    ].iloc[0]
    assert median.estimate == np.inf
    assert median.status == "not_reached"
    assert median.reason
    assert "not reached" in median.annotation
    landmark = results.loc[results.kind == "landmark_test"].iloc[0]
    assert landmark.status == "unavailable"
    assert "strictly between 0 and 1" in landmark.reason
    assert landmark[["statistic", "pvalue_raw", "pvalue_adjusted"]].isna().all()
    assert results.loc[results.kind == "landmark_survival", "estimate"].tolist() == [
        1,
        1,
    ]


@pytest.mark.parametrize("overall_test", ["logrank", "trend"])
def test_survival_results_preserve_unavailable_overall(
    survival_df: pd.DataFrame, overall_test: str
) -> None:
    with pytest.warns(UserWarning, match="unavailable.*no events"):
        ax = cns.survivalplot(
            survival_df.assign(event=0),
            "time",
            "event",
            "group",
            hue_order=["Control", "Treatment"],
            overall_test=cast(Any, overall_test),
            show_hazard_ratio=False,
        )
    result = cns.get_survival_results(ax).iloc[0]
    assert result.status == "unavailable"
    assert result.events == 0
    assert result.reason
    assert result[["statistic", "pvalue_raw", "pvalue_adjusted"]].isna().all()


def test_survival_results_retain_fully_unavailable_corrected_family(
    survival_df: pd.DataFrame,
) -> None:
    with pytest.warns(UserWarning, match="unavailable.*no events"):
        ax = cns.survivalplot(
            survival_df.assign(event=0),
            "time",
            "event",
            "group",
            p_adjust="holm",
        )
    results = cns.get_survival_results(ax)
    assert results.status.tolist() == ["unavailable", "unavailable"]
    assert results[["statistic", "pvalue_raw", "pvalue_adjusted"]].isna().all().all()
    pair = results.iloc[1]
    assert pair.family_size == 1
    assert pair.p_adjust == "holm"
    assert "holm-adjusted; 1 contrasts" in ax.texts[-1].get_text()


@pytest.mark.parametrize("mode", ["descriptive_only", "show_hazard_ratio"])
def test_survival_results_skip_disabled_pairwise_options(
    survival_df: pd.DataFrame, mode: str
) -> None:
    kwargs: dict[str, Any] = {mode: mode == "descriptive_only"}
    ax = cns.survivalplot(
        survival_df,
        "time",
        "event",
        "group",
        pairs=cast(Any, ["invalid pair"]),
        p_adjust=cast(Any, "invalid method"),
        **kwargs,
    )
    results = cns.get_survival_results(ax)
    expected = [] if mode == "descriptive_only" else ["overall"]
    assert results.kind.tolist() == expected


@pytest.mark.parametrize(
    "pairs",
    [
        [("Low", "High"), ("Low", "High")],
        [("Low", "High"), ("High", "Low")],
    ],
)
def test_survivalplot_rejects_duplicate_contrasts(
    survival_three_group_df: pd.DataFrame, pairs: list[tuple[str, str]]
) -> None:
    with pytest.raises(ValueError, match="[Dd]uplicate"):
        cns.survivalplot(survival_three_group_df, "time", "event", "group", pairs=pairs)


@pytest.mark.parametrize("p_adjust", ["sidak", "Holm", True, ["holm"]])
def test_survivalplot_rejects_unsupported_adjustment(
    survival_df: pd.DataFrame, p_adjust: Any
) -> None:
    with pytest.raises(ValueError, match="p_adjust"):
        cns.survivalplot(survival_df, "time", "event", "group", p_adjust=p_adjust)


def test_survival_results_are_defensive_snapshots_without_refitting(
    survival_df: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    ax = cns.survivalplot(survival_df, "time", "event", "group")
    expected = cns.get_survival_results(ax)
    assert expected.kind.tolist() == ["overall", "pairwise_cox"]

    def unexpected_fit(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Reading results must not recompute inference")

    monkeypatch.setattr(ll.CoxPHFitter, "fit", unexpected_fit)
    monkeypatch.setattr(ll.KaplanMeierFitter, "fit", unexpected_fit)
    survival_df.loc[:, "time"] = 100
    result = cns.get_survival_results(ax)
    result.loc[:, "pvalue_raw"] = -1
    result.attrs["duration"] = "changed"
    pd.testing.assert_frame_equal(cns.get_survival_results(ax), expected)
    assert cns.get_survival_results(ax).attrs == expected.attrs


def test_survival_results_follow_axes_and_replace_on_reuse(
    survival_df: pd.DataFrame,
) -> None:
    _, (ax, other) = plt.subplots(1, 2)
    empty = cns.get_survival_results(ax)
    assert empty.empty
    assert set(empty.columns) == _COLUMNS
    cns.survivalplot(survival_df, "time", "event", "group", ax=ax)
    plt.sca(other)
    assert cns.get_survival_results().empty
    plt.sca(ax)
    pd.testing.assert_frame_equal(
        cns.get_survival_results(), cns.get_survival_results(ax)
    )
    cns.survivalplot(
        survival_df,
        "time",
        "event",
        "group",
        descriptive_only=True,
        show_median_survival=True,
        landmark_time=6,
        rmst_time=8,
        ax=ax,
    )
    results = cns.get_survival_results(ax)
    assert results.kind.tolist() == [
        "median_survival",
        "median_survival",
        "landmark_survival",
        "landmark_survival",
        "rmst",
        "rmst",
    ]
    assert results.pvalue_raw.isna().all()
    ax.clear()
    pd.testing.assert_frame_equal(cns.get_survival_results(ax), empty)
    cns.survivalplot(
        survival_df, "time", "event", "group", descriptive_only=True, ax=ax
    )
    assert cns.get_survival_results(ax).empty
    assert set(cns.get_survival_results(ax).columns) == _COLUMNS


def test_survival_results_expire_when_annotation_is_removed(
    survival_df: pd.DataFrame,
) -> None:
    ax = cns.survivalplot(survival_df, "time", "event", "group")
    assert not cns.get_survival_results(ax).empty
    ax.texts[-1].remove()
    assert cns.get_survival_results(ax).empty
    assert set(cns.get_survival_results(ax).columns) == _COLUMNS
