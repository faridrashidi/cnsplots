from __future__ import annotations

import inspect
from typing import Any, Literal, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from scipy import stats
from statannotations.stats.StatTest import StatTest
from statsmodels.stats.multitest import multipletests

import cnsplots as cns

_PLOTS = ("boxplot", "violinplot", "barplot", "lollipopplot")
_TESTS = ("t-test_paired", "Wilcoxon")
PairedTest = Literal["t-test_paired", "Wilcoxon"]


@pytest.fixture
def paired_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "group": np.repeat(["A", "B", "C"], 7),
            "subject": list(range(7)) * 3,
            "value": [1, 3, 8, 2, 12, 5, 10]
            + [1, 4, 9, 1, 14, 7, 8]
            + [5, 7, 9, 7, 11, 13, 12],
        }
    ).astype({"value": float})


@pytest.fixture
def paired_annotations(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    instances = []
    original = cns.utils.Annotator

    def capture(*args: Any, **kwargs: Any) -> Any:
        annotator = original(*args, **kwargs)
        instances.append(annotator)
        return annotator

    monkeypatch.setattr(cns.utils, "Annotator", capture)
    return instances


def _reference(test: PairedTest, first: Any, second: Any) -> Any:
    if test == "t-test_paired":
        return stats.ttest_rel(first, second, alternative="two-sided")
    return stats.wilcoxon(
        first,
        second,
        alternative="two-sided",
        zero_method="wilcox",
        correction=False,
        method="auto",
    )


@pytest.mark.parametrize("plot_name", _PLOTS)
@pytest.mark.parametrize("test", _TESTS)
def test_subject_alignment_is_invariant_to_row_order(
    plot_name: str, test: PairedTest, paired_df: pd.DataFrame
) -> None:
    parameters = inspect.signature(getattr(cns, plot_name)).parameters
    assert parameters["subject"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["subject"].default is None
    original = paired_df.copy(deep=True)
    results = []
    for data in (paired_df, paired_df.sample(frac=1, random_state=21)):
        _, ax = plt.subplots()
        getattr(cns, plot_name)(
            data,
            x="group",
            y="value",
            order=["B", "A"],
            pairs=[("A", "B")],
            test=test,
            subject="subject",
            ax=ax,
        )
        results.append(cns.get_comparison_results(ax))
    pd.testing.assert_frame_equal(results[0], results[1])
    pd.testing.assert_frame_equal(paired_df, original)
    row = results[0].iloc[0]
    assert (row.group1, row.group2) == ("B", "A")
    expected = _reference(
        test,
        paired_df.loc[paired_df.group == "B", "value"],
        paired_df.loc[paired_df.group == "A", "value"],
    )
    assert row.paired
    assert (row.n1, row.n2) == (7, 7)
    assert row.pvalue_raw == pytest.approx(expected.pvalue)


@pytest.mark.parametrize("test", _TESTS)
@pytest.mark.parametrize("p_adjust", [None, "bonferroni", "holm", "fdr_bh", "fdr_by"])
def test_paired_statistics_and_corrections_match_scipy(
    test: PairedTest,
    p_adjust: Literal["bonferroni", "holm", "fdr_bh", "fdr_by"] | None,
    paired_df: pd.DataFrame,
    paired_annotations: list[Any],
) -> None:
    ax = cns.boxplot(
        paired_df.sample(frac=1, random_state=17),
        x="group",
        y="value",
        order=["C", "B", "A"],
        pairs="all",
        test=test,
        subject="subject",
        p_adjust=p_adjust,
    )
    results = cns.get_comparison_results(ax)
    assert list(results.columns) == [
        "group1",
        "group2",
        "test",
        "alternative",
        "paired",
        "n1",
        "n2",
        "pvalue_raw",
        "pvalue_adjusted",
        "p_adjust",
        "pvalue_annotation",
        "significant",
        "annotation",
    ]
    assert len(results) == 3
    raw = []
    for (_, row), annotation in zip(
        results.iterrows(), paired_annotations[0].annotations
    ):
        expected = _reference(
            test,
            paired_df.loc[paired_df.group == row.group1, "value"],
            paired_df.loc[paired_df.group == row.group2, "value"],
        )
        raw.append(expected.pvalue)
        assert annotation.data.stat_value == pytest.approx(expected.statistic)
        assert row.pvalue_raw == pytest.approx(expected.pvalue)
        assert row.test == test
        assert row.alternative == "two-sided"
        assert row.paired
        assert (row.n1, row.n2) == (7, 7)
        assert row.p_adjust == p_adjust
        assert row.pvalue_annotation == annotation.data.pvalue
        assert row.significant == annotation.data.is_significant
        assert row.annotation == annotation.text
        assert row.annotation in [text.get_text() for text in ax.texts]
    adjusted = raw if p_adjust is None else multipletests(raw, method=p_adjust)[1]
    np.testing.assert_allclose(results.pvalue_adjusted, adjusted)
    np.testing.assert_array_equal(results.significant, np.asarray(adjusted) <= 0.05)
    np.testing.assert_allclose(
        results.pvalue_annotation, adjusted if p_adjust == "bonferroni" else raw
    )


@pytest.mark.parametrize("horizontal", [False, True])
@pytest.mark.parametrize("custom_formatter", [False, True])
def test_paired_alignment_preserves_formatted_categorical_labels(
    horizontal: bool, custom_formatter: bool, paired_df: pd.DataFrame
) -> None:
    data = paired_df.assign(
        group=pd.Categorical(
            paired_df.group.map({"A": 10, "B": 20, "C": 30}),
            categories=[30, 20, 10],
        )
    )
    formatter = (lambda label: f"group-{label}") if custom_formatter else str
    plotting = {"formatter": formatter} if custom_formatter else {}
    ax = cns.boxplot(
        data.sample(frac=1, random_state=4),
        x="value" if horizontal else "group",
        y="group" if horizontal else "value",
        order=cast(Any, [20, 10]),
        pairs=[(10, 20)],
        test="t-test_paired",
        subject="subject",
        **plotting,
    )
    row = cns.get_comparison_results(ax).iloc[0]
    assert (row.group1, row.group2) == (formatter(20), formatter(10))
    assert (row.n1, row.n2) == (7, 7)
    expected = stats.ttest_rel(
        paired_df.loc[paired_df.group == "B", "value"],
        paired_df.loc[paired_df.group == "A", "value"],
    )
    assert row.pvalue_raw == pytest.approx(expected.pvalue)


@pytest.mark.parametrize("plot_name", _PLOTS)
@pytest.mark.parametrize("horizontal", [False, True])
def test_hue_pairing_uses_displayed_numeric_groups(
    plot_name: str, horizontal: bool
) -> None:
    data = pd.DataFrame(
        [
            (group, hue, subject, subject**2 + group + hue * (subject % 3))
            for group in [10, 20, 30]
            for hue in [1, 2, 9]
            for subject in range(6)
        ],
        columns=pd.Index(["group", "hue", "subject", "value"]),
    )
    # Repeated IDs in excluded categories or hues must not affect comparisons.
    excluded = data.loc[(data.group == 30) | (data.hue == 9)]
    data = pd.concat([data, excluded], ignore_index=True).sample(
        frac=1, random_state=11
    )
    plotting = (
        {} if plot_name == "lollipopplot" else {"orient": "h" if horizontal else "v"}
    )
    if plot_name == "lollipopplot":
        data["group"] = data["group"].astype(object)
    ax = getattr(cns, plot_name)(
        data,
        x="value" if horizontal else "group",
        y="group" if horizontal else "value",
        order=[20, 10],
        hue="hue",
        hue_order=[2, 1],
        pairs="hue",
        test="t-test_paired",
        subject="subject",
        **plotting,
    )
    results = cns.get_comparison_results(ax)
    assert set(zip(results.group1, results.group2)) == {
        ((20, 2), (20, 1)),
        ((10, 2), (10, 1)),
    }
    for _, row in results.iterrows():
        first, second = [
            data.loc[(data.group == group) & (data.hue == hue)].sort_values("subject")[
                "value"
            ]
            for group, hue in [row.group1, row.group2]
        ]
        assert (row.n1, row.n2) == (6, 6)
        assert row.paired
        assert row.pvalue_raw == pytest.approx(stats.ttest_rel(first, second).pvalue)


def test_paired_comparisons_allow_hue_repeating_category(
    paired_df: pd.DataFrame,
) -> None:
    ax = cns.boxplot(
        paired_df.sample(frac=1, random_state=8),
        x="group",
        y="value",
        hue="group",
        order=["B", "A"],
        pairs="all",
        test="t-test_paired",
        subject="subject",
    )
    row = cns.get_comparison_results(ax).iloc[0]
    assert (row.group1, row.group2) == ("B", "A")
    assert (row.n1, row.n2) == (7, 7)
    expected = stats.ttest_rel(
        paired_df.loc[paired_df.group == "B", "value"],
        paired_df.loc[paired_df.group == "A", "value"],
    )
    assert row.paired
    assert row.pvalue_raw == pytest.approx(expected.pvalue)


@pytest.mark.parametrize("test", _TESTS)
def test_missing_subjects_are_excluded_separately_for_each_contrast(
    test: PairedTest,
) -> None:
    data = pd.DataFrame(
        {
            "group": ["A"] * 5 + ["B"] * 5 + ["C"] * 4,
            "subject": [1, 2, 3, 4, 5] * 2 + [3, 4, 5, 6],
            "value": [1, 4, 9, 16, 25, 3, 4, np.nan, 18, 30, 10, 19, 29, 37],
        }
    )
    incomplete = pd.DataFrame(
        {
            "group": ["A", "A", "B", "B", "A", None],
            "subject": [None, None, None, None, 1, 1],
            "value": [100, 200, 300, 400, np.nan, 500],
        }
    )
    data = pd.concat([data, incomplete]).assign(unrelated=np.nan)
    ax = cns.boxplot(
        data,
        x="group",
        y="value",
        order=["A", "B", "C"],
        pairs="all",
        test=test,
        subject="subject",
    )
    matches = {("A", "B"): [1, 2, 4, 5], ("A", "C"): [3, 4, 5], ("B", "C"): [4, 5]}
    results = cns.get_comparison_results(ax)
    assert len(results) == 3
    for _, row in results.iterrows():
        subjects = matches[(row.group1, row.group2)]
        first, second = [
            data.loc[(data.group == group) & data.value.notna()]
            .set_index("subject")
            .loc[subjects, "value"]
            for group in [row.group1, row.group2]
        ]
        assert (row.n1, row.n2) == (len(subjects), len(subjects))
        assert row.pvalue_raw == pytest.approx(_reference(test, first, second).pvalue)


@pytest.mark.parametrize("plot_name", _PLOTS)
@pytest.mark.parametrize("test", _TESTS)
@pytest.mark.parametrize("pairs", [None, [("A", "B")]])
def test_paired_tests_require_subject_column(
    plot_name: str, test: PairedTest, pairs: Any, paired_df: pd.DataFrame
) -> None:
    with pytest.raises(ValueError, match="subject"):
        getattr(cns, plot_name)(paired_df, x="group", y="value", pairs=pairs, test=test)


@pytest.mark.parametrize("plot_name", _PLOTS)
def test_independent_tests_reject_subject_and_missing_column_is_reported(
    plot_name: str, paired_df: pd.DataFrame
) -> None:
    plotter = getattr(cns, plot_name)
    with pytest.raises(ValueError, match="subject"):
        plotter(paired_df, x="group", y="value", subject="subject")
    with pytest.raises(ValueError, match="absent"):
        plotter(paired_df, x="group", y="value", test="Wilcoxon", subject="absent")


@pytest.mark.parametrize("test", _TESTS)
@pytest.mark.parametrize("group", ["A", "B"])
@pytest.mark.parametrize("matched", [False, True])
def test_duplicate_subjects_are_rejected_before_alignment(
    test: PairedTest, group: str, matched: bool, paired_df: pd.DataFrame
) -> None:
    duplicate = pd.DataFrame(
        {"group": [group, group], "subject": [99, 99], "value": [5, 7]}
    )
    if matched:
        duplicate = paired_df.loc[paired_df.group == group].iloc[:1]
    data = pd.concat([paired_df, duplicate])
    with pytest.raises(ValueError, match="[Dd]uplicate"):
        cns.boxplot(
            data,
            x="group",
            y="value",
            pairs=[("A", "B")],
            test=test,
            subject="subject",
        )


@pytest.mark.parametrize("test", _TESTS)
@pytest.mark.parametrize("matched_count", [0, 1])
def test_paired_tests_require_two_complete_matches(
    test: PairedTest, matched_count: int
) -> None:
    data = pd.DataFrame(
        {
            "group": ["A", "A", "B", "B"],
            "subject": [1, 2, 1 if matched_count else 3, 4],
            "value": [1, 3, 2, 5],
        }
    )
    with pytest.raises(ValueError, match="at least (2|two)"):
        cns.boxplot(
            data,
            x="group",
            y="value",
            pairs=[("A", "B")],
            test=test,
            subject="subject",
        )


@pytest.mark.parametrize("test", _TESTS)
@pytest.mark.parametrize("count", [2, 14])
def test_all_zero_differences_are_rejected(test: PairedTest, count: int) -> None:
    data = pd.DataFrame(
        {
            "group": np.repeat(["A", "B"], count),
            "subject": list(range(count)) * 2,
            "value": list(range(count)) * 2,
        }
    )
    with pytest.raises(ValueError, match="zero"):
        cns.boxplot(
            data,
            x="group",
            y="value",
            pairs=[("A", "B")],
            test=test,
            subject="subject",
        )


@pytest.mark.parametrize("test", _TESTS)
@pytest.mark.parametrize("value", [np.inf, -np.inf])
def test_nonfinite_aligned_measurements_are_rejected(
    test: PairedTest, value: float, paired_df: pd.DataFrame
) -> None:
    paired_df.loc[0, "value"] = value
    with pytest.raises(ValueError, match="finite"):
        cns.boxplot(
            paired_df,
            x="group",
            y="value",
            pairs=[("A", "B")],
            test=test,
            subject="subject",
        )


@pytest.mark.parametrize("test", _TESTS)
def test_get_paired_results_does_not_rerun_tests(
    test: PairedTest, paired_df: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    statistical_test = StatTest.from_library(test)
    original = statistical_test._func
    calls = []

    def capture(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(statistical_test, "_func", capture)
    ax = cns.boxplot(
        paired_df,
        x="group",
        y="value",
        pairs="all",
        test=test,
        subject="subject",
        p_adjust="bonferroni",
    )
    assert len(calls) == 3
    first = cns.get_comparison_results(ax)
    second = cns.get_comparison_results(ax)
    assert len(calls) == 3
    pd.testing.assert_frame_equal(first, second)


@pytest.mark.parametrize("test", _TESTS)
def test_nonfinite_paired_result_is_not_annotated(
    test: PairedTest, paired_df: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        StatTest.from_library(test), "_func", lambda *args, **kwargs: (0.0, np.nan)
    )
    _, ax = plt.subplots()
    with pytest.raises(ValueError, match="nonfinite p-value"):
        cns.boxplot(
            paired_df,
            x="group",
            y="value",
            pairs=[("A", "B")],
            test=test,
            subject="subject",
            ax=ax,
        )
    assert not ax.texts
    assert cns.get_comparison_results(ax).empty
