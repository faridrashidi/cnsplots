from __future__ import annotations

from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from scipy import stats
from statannotations.stats.StatTest import StatTest
from statsmodels.stats.multitest import multipletests

import cnsplots as cns

_CONTINUOUS_PLOTS = ("boxplot", "violinplot", "barplot", "lollipopplot")
_COLUMNS = [
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


@pytest.fixture
def result_annotations(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    instances = []
    original = cns.utils.Annotator

    def capture(*args: Any, **kwargs: Any) -> Any:
        annotator = original(*args, **kwargs)
        instances.append(annotator)
        return annotator

    monkeypatch.setattr(cns.utils, "Annotator", capture)
    return instances


@pytest.mark.parametrize("plot_name", _CONTINUOUS_PLOTS)
@pytest.mark.parametrize("p_adjust", [None, "bonferroni", "holm", "fdr_bh", "fdr_by"])
def test_results_match_tests_and_rendered_annotations(
    plot_name: str,
    p_adjust: str | None,
    categorical_df: pd.DataFrame,
    result_annotations: list[Any],
) -> None:
    ax = getattr(cns, plot_name)(
        categorical_df,
        x="group",
        y="value",
        order=["C", "B", "A"],
        pairs=[("A", "C"), ("A", "B"), ("B", "C")],
        p_adjust=p_adjust,
    )
    results = cns.get_comparison_results(ax)
    annotations = result_annotations[0].annotations

    assert list(results.columns) == _COLUMNS
    assert len(results) == 3
    assert list(zip(results.group1, results.group2)) == [
        (item.structs[0]["group"][0], item.structs[1]["group"][0])
        for item in annotations
    ]
    test = "Mann-Whitney" if plot_name in {"boxplot", "violinplot"} else "t-test_welch"
    expected_pvalues = []
    for (_, row), annotation in zip(results.iterrows(), annotations):
        first = categorical_df.loc[categorical_df.group == row.group1, "value"]
        second = categorical_df.loc[categorical_df.group == row.group2, "value"]
        expected = (
            stats.mannwhitneyu(first, second, alternative="two-sided")
            if test == "Mann-Whitney"
            else stats.ttest_ind(first, second, equal_var=False)
        )
        expected_pvalues.append(expected.pvalue)
        assert row.test == test
        assert row.alternative == "two-sided"
        assert not row.paired
        assert (row.n1, row.n2) == (len(first), len(second))
        assert row.pvalue_raw == pytest.approx(expected.pvalue)
        assert row.p_adjust == p_adjust
        assert row.pvalue_annotation == annotation.data.pvalue
        assert row.significant == annotation.data.is_significant
        assert row.annotation == annotation.text
        assert row.annotation in [text.get_text() for text in ax.texts]

    adjusted = (
        expected_pvalues
        if p_adjust is None
        else multipletests(expected_pvalues, method=p_adjust)[1]
    )
    np.testing.assert_allclose(results.pvalue_adjusted, adjusted)
    np.testing.assert_array_equal(results.significant, np.asarray(adjusted) <= 0.05)
    np.testing.assert_allclose(
        results.pvalue_annotation,
        adjusted if p_adjust == "bonferroni" else expected_pvalues,
    )


@pytest.mark.parametrize("plot_name", _CONTINUOUS_PLOTS)
@pytest.mark.parametrize("horizontal", [False, True])
def test_hue_results_use_displayed_complete_observations(
    plot_name: str, horizontal: bool, result_annotations: list[Any]
) -> None:
    data = pd.DataFrame(
        {
            "group": ["A"] * 8 + ["B"] * 8 + ["C", None],
            "value": [1, 2, 3, np.nan, 5, 6, 7, 8] + list(range(9, 19)),
            "hue": ["H1", "H1", "H2", "H2", "H2", "H3", None, "H1"] * 2 + ["H1", "H1"],
            "unrelated": np.nan,
        }
    )
    ax = getattr(cns, plot_name)(
        data,
        x="value" if horizontal else "group",
        y="group" if horizontal else "value",
        order=["B", "A"],
        hue="hue",
        hue_order=["H2", "H1"],
        pairs="hue",
        test="Mann-Whitney",
        p_adjust="holm",
    )
    results = cns.get_comparison_results(ax)
    assert set(zip(results.group1, results.group2)) == {
        (("B", "H2"), ("B", "H1")),
        (("A", "H2"), ("A", "H1")),
    }
    assert list(zip(results.group1, results.group2)) == [
        (item.structs[0]["group"], item.structs[1]["group"])
        for item in result_annotations[0].annotations
    ]
    expected_pvalues = []
    for _, row in results.iterrows():
        groups = [
            data.loc[(data.group == group) & (data.hue == hue), "value"].dropna()
            for group, hue in (row.group1, row.group2)
        ]
        expected = stats.mannwhitneyu(*groups, alternative="two-sided")
        expected_pvalues.append(expected.pvalue)
        assert (row.n1, row.n2) == tuple(map(len, groups))
        assert row.pvalue_raw == pytest.approx(expected.pvalue)
    np.testing.assert_allclose(
        results.pvalue_adjusted, multipletests(expected_pvalues, method="holm")[1]
    )


@pytest.mark.parametrize("plot_name", _CONTINUOUS_PLOTS)
def test_results_preserve_numeric_category_labels(
    plot_name: str, categorical_df: pd.DataFrame
) -> None:
    data = categorical_df.assign(
        group=categorical_df.group.map({"A": 0, "B": 1, "C": 2})
    )
    ax = getattr(cns, plot_name)(
        data, x="group", y="value", order=[2, 1, 0], pairs=[(0, 2)]
    )
    results = cns.get_comparison_results(ax)
    assert list(zip(results.group1, results.group2)) == [(2, 0)]
    assert list(zip(results.n1, results.n2)) == [(4, 4)]


def test_results_preserve_saturated_raw_values_and_corrected_ns() -> None:
    data = pd.DataFrame(
        {
            "group": np.repeat(["A", "B", "C"], 4),
            "value": [0, 1, 2, 3, 1, 2, 3, 4, 2, 3, 4, 5],
        }
    )
    ax = cns.boxplot(data, x="group", y="value", pairs="all", p_adjust="bonferroni")
    results = cns.get_comparison_results(ax)
    assert (results.pvalue_adjusted == 1).any()
    for _, row in results.iterrows():
        expected = stats.mannwhitneyu(
            data.loc[data.group == row.group1, "value"],
            data.loc[data.group == row.group2, "value"],
            alternative="two-sided",
        )
        assert row.pvalue_raw == pytest.approx(expected.pvalue)
        assert row.pvalue_adjusted == pytest.approx(min(expected.pvalue * 3, 1))

    data["value"] = np.arange(12)
    _, ax = plt.subplots()
    cns.boxplot(data, x="group", y="value", pairs="all", p_adjust="holm", ax=ax)
    results = cns.get_comparison_results(ax)
    assert (results.pvalue_raw < 0.05).all()
    assert (results.pvalue_adjusted > 0.05).all()
    assert not results.significant.any()
    assert results.annotation.str.contains("ns").all()


@pytest.mark.parametrize("horizontal", [False, True])
@pytest.mark.parametrize("normalize", [False, True])
@pytest.mark.parametrize("test", ["auto", "chi-squared"])
def test_stack_results_count_raw_contingency_observations(
    horizontal: bool, normalize: bool, test: Literal["auto", "chi-squared"]
) -> None:
    counts = pd.DataFrame(
        [[8, 2], [3, 7], [5, 4]],
        index=pd.Index(list("ABC")),
        columns=pd.Index(["no", "yes"]),
    )
    data = pd.DataFrame(
        [
            (group, outcome)
            for group in counts.index
            for outcome in counts.columns
            for _ in range(counts.loc[group, outcome])
        ]
        + [("A", None), (None, "yes")],
        columns=pd.Index(["group", "outcome"]),
    )
    ax = cns.stackplot(
        data,
        x=None if horizontal else "group",
        y="group" if horizontal else None,
        stack="outcome",
        order=["C", "A", "B"],
        normalize=normalize,
        n_factor=2,
        pairs="all",
        test=test,
        p_adjust="bonferroni",
    )
    results = cns.get_comparison_results(ax)
    assert len(results) == 3
    for _, row in results.iterrows():
        table = counts.loc[[row.group1, row.group2]].to_numpy()
        expected = (
            stats.fisher_exact(table)
            if test == "auto"
            else stats.chi2_contingency(table)
        )
        assert row.test == ("fisher-exact" if test == "auto" else "chi-squared")
        assert row.alternative == ("two-sided" if test == "auto" else None)
        assert not row.paired
        assert (row.n1, row.n2) == tuple(table.sum(axis=1))
        assert row.pvalue_raw == pytest.approx(expected[1])
        assert row.pvalue_adjusted == pytest.approx(min(expected[1] * 3, 1))


def test_statistics_are_computed_once(
    categorical_df: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    test = StatTest.from_library("Mann-Whitney")
    original = test._func
    calls = []

    def capture(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(test, "_func", capture)
    ax = cns.boxplot(
        categorical_df, x="group", y="value", pairs="all", p_adjust="bonferroni"
    )
    first = cns.get_comparison_results(ax)
    second = cns.get_comparison_results(ax)
    assert len(calls) == 3
    pd.testing.assert_frame_equal(first, second)


def test_multiclass_fisher_results_reuse_the_computed_pvalue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = pd.DataFrame(
        {
            "group": ["A"] * 6 + ["B"] * 5,
            "outcome": ["one", "two", "three", "one", "two", "three"]
            + ["one", "two", "three", "one", "one"],
        }
    )
    original = stats.fisher_exact
    computed = []

    def capture(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        computed.append(result.pvalue)
        return result

    monkeypatch.setattr(cns.utils.stats, "fisher_exact", capture)
    ax = cns.stackplot(
        data,
        x="group",
        stack="outcome",
        order=["B", "A"],
        pairs=[("A", "B")],
        test="fisher-exact",
        p_adjust="holm",
    )
    row = cns.get_comparison_results(ax).iloc[0]
    assert len(computed) == 1
    assert (row.group1, row.group2) == ("B", "A")
    assert (row.n1, row.n2) == (5, 6)
    assert row.alternative is None
    assert row.pvalue_raw == computed[0]
    assert row.pvalue_adjusted == computed[0]
    assert row.pvalue_annotation == computed[0]


def test_results_are_detached_and_follow_axes_lifecycle(
    categorical_df: pd.DataFrame,
) -> None:
    _, (ax, other) = plt.subplots(1, 2)
    empty = cns.get_comparison_results(ax)
    assert list(empty.columns) == _COLUMNS
    assert empty.empty
    cns.boxplot(categorical_df, x="group", y="value", pairs="all", ax=ax)
    original = cns.get_comparison_results(ax)
    modified = cns.get_comparison_results(ax)
    modified.loc[0, "pvalue_raw"] = -1
    modified.drop(columns="group1", inplace=True)
    pd.testing.assert_frame_equal(cns.get_comparison_results(ax), original)
    assert cns.get_comparison_results(other).empty
    plt.sca(ax)
    pd.testing.assert_frame_equal(cns.get_comparison_results(), original)
    cns.boxplot(categorical_df, x="group", y="value", pairs=[("A", "B")], ax=ax)
    assert len(cns.get_comparison_results(ax)) == 1
    ax.clear()
    assert cns.get_comparison_results(ax).empty
    assert list(cns.get_comparison_results(ax).columns) == _COLUMNS
