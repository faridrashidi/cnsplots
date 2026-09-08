from __future__ import annotations

from io import StringIO
from typing import Any, Literal
import warnings

import numpy as np
import pandas as pd
import pytest
from scipy import stats
from statannotations.stats.StatResult import StatResult
from statannotations.stats.StatTest import StatTest
from statsmodels.stats.multitest import multipletests

import cnsplots as cns
from cnsplots._utils import _PValueFormatter

_PLOTS = ("boxplot", "violinplot", "barplot", "lollipopplot")
_ADJUSTMENTS = (None, "bonferroni", "holm", "fdr_bh", "fdr_by")
_P_VALUE_COLUMNS = ["pvalue_raw", "pvalue_adjusted", "pvalue_annotation"]
Adjustment = Literal["bonferroni", "holm", "fdr_bh", "fdr_by"] | None
PValueFormat = Literal["star", "full", "threshold"]


@pytest.fixture
def unavailable_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "group": np.repeat(["A", "B", "C"], 5),
            "value": [0] * 10 + [1, 2, 3, 4, 5],
        }
    )


@pytest.fixture
def unavailable_annotations(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    instances = []
    original = cns.utils.Annotator

    def capture(*args: Any, **kwargs: Any) -> Any:
        annotator = original(*args, **kwargs)
        instances.append(annotator)
        return annotator

    monkeypatch.setattr(cns.utils, "Annotator", capture)
    return instances


@pytest.mark.parametrize("plot_name", _PLOTS)
@pytest.mark.parametrize("p_adjust", _ADJUSTMENTS)
def test_nonfinite_welch_comparison_is_unavailable(
    plot_name: str,
    p_adjust: Adjustment,
    unavailable_df: pd.DataFrame,
    unavailable_annotations: list[Any],
) -> None:
    with (
        cns.settings.context(pvalue_format="threshold"),
        warnings.catch_warnings(record=True) as recorded,
    ):
        warnings.simplefilter("always", UserWarning)
        ax = getattr(cns, plot_name)(
            unavailable_df,
            x="group",
            y="value",
            pairs="all",
            test="t-test_welch",
            p_adjust=p_adjust,
        )
    results = cns.get_comparison_results(ax)
    invalid = (results.group1 == "A") & (results.group2 == "B")

    assert len(recorded) == 1
    assert recorded[0].category is UserWarning
    warning = str(recorded[0].message)
    assert "t-test_welch" in warning
    assert "A" in warning and "B" in warning
    assert "nonfinite" in warning.lower()
    assert any(hint in warning.lower() for hint in ("check", "inspect", "review"))
    assert results.loc[invalid, _P_VALUE_COLUMNS].isna().all().all()
    assert results.loc[invalid, "significant"].isna().all()
    assert results.loc[invalid, "annotation"].tolist() == ["P unavailable"]
    assert results.loc[~invalid, _P_VALUE_COLUMNS].notna().all().all()
    assert list(zip(results.n1, results.n2)) == [(5, 5)] * 3

    raw = np.asarray(
        [
            stats.ttest_ind(
                unavailable_df.loc[unavailable_df.group == row.group1, "value"],
                unavailable_df.loc[unavailable_df.group == row.group2, "value"],
                equal_var=False,
            ).pvalue
            for _, row in results.iterrows()
        ]
    )
    correction_family = np.where(np.isfinite(raw), raw, 1.0)
    expected_adjusted = (
        raw.copy()
        if p_adjust is None
        else multipletests(correction_family, method=p_adjust)[1]
    )
    expected_adjusted[invalid] = np.nan
    np.testing.assert_allclose(results.pvalue_raw, raw, equal_nan=True)
    np.testing.assert_allclose(
        results.pvalue_adjusted, expected_adjusted, equal_nan=True
    )
    np.testing.assert_allclose(
        results.pvalue_annotation,
        expected_adjusted if p_adjust == "bonferroni" else raw,
        equal_nan=True,
    )
    np.testing.assert_array_equal(
        results.loc[~invalid, "significant"], expected_adjusted[~invalid] <= 0.05
    )
    assert results.loc[~invalid, "annotation"].tolist() == ["P < 0.05"] * 2
    annotations = unavailable_annotations[0].annotations
    assert results.annotation.tolist() == [item.text for item in annotations]
    assert results.annotation.tolist() == [text.get_text() for text in ax.texts]
    np.testing.assert_allclose(
        results.pvalue_annotation,
        [item.data.pvalue for item in annotations],
        equal_nan=True,
    )


@pytest.mark.parametrize("pvalue_format", ["star", "full"])
@pytest.mark.parametrize("p_adjust", _ADJUSTMENTS)
def test_nonfinite_comparison_renders_and_exports_all_formats(
    pvalue_format: PValueFormat,
    p_adjust: Adjustment,
    unavailable_df: pd.DataFrame,
) -> None:
    with (
        cns.settings.context(pvalue_format=pvalue_format),
        pytest.warns(UserWarning, match="t-test_welch"),
    ):
        ax = cns.barplot(
            unavailable_df,
            x="group",
            y="value",
            pairs="all",
            p_adjust=p_adjust,
        )
    results = cns.get_comparison_results(ax)
    assert results.annotation.tolist() == [text.get_text() for text in ax.texts]
    exported = pd.read_csv(StringIO(results.to_csv(index=False)))
    invalid = exported.loc[exported.annotation == "P unavailable"]
    assert len(invalid) == 1
    assert invalid[_P_VALUE_COLUMNS + ["significant"]].isna().all().all()


@pytest.mark.parametrize("p_adjust", _ADJUSTMENTS)
def test_all_unavailable_comparisons_remain_missing(
    p_adjust: Adjustment, unavailable_df: pd.DataFrame
) -> None:
    with pytest.warns(UserWarning, match="t-test_welch") as recorded:
        ax = cns.barplot(
            unavailable_df.assign(value=0),
            x="group",
            y="value",
            pairs="all",
            p_adjust=p_adjust,
        )
    results = cns.get_comparison_results(ax)
    assert len(recorded) == 3
    assert results[_P_VALUE_COLUMNS + ["significant"]].isna().all().all()
    assert results.annotation.tolist() == ["P unavailable"] * 3
    assert results.annotation.tolist() == [text.get_text() for text in ax.texts]


@pytest.mark.parametrize("pvalue", [np.inf, -np.inf])
@pytest.mark.parametrize("p_adjust", _ADJUSTMENTS)
def test_infinite_pvalues_are_normalized_to_missing(
    pvalue: float,
    p_adjust: Adjustment,
    categorical_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        StatTest.from_library("Mann-Whitney"),
        "_func",
        lambda *args, **kwargs: (0.0, pvalue),
    )
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always", UserWarning)
        ax = cns.boxplot(
            categorical_df,
            x="group",
            y="value",
            pairs=[("A", "B")],
            p_adjust=p_adjust,
        )
    assert len(recorded) == 1
    assert recorded[0].category is UserWarning
    assert "Mann-Whitney" in str(recorded[0].message)
    result = cns.get_comparison_results(ax).iloc[0]
    assert result[_P_VALUE_COLUMNS].isna().all()
    assert pd.isna(result.significant)
    assert result.annotation == "P unavailable"
    assert [text.get_text() for text in ax.texts] == ["P unavailable"]


@pytest.mark.parametrize("pvalue_format", ["star", "full", "threshold"])
@pytest.mark.parametrize("pvalue", [np.nan, np.inf, -np.inf])
def test_formatter_does_not_assign_significance_to_nonfinite_pvalues(
    pvalue_format: PValueFormat, pvalue: float
) -> None:
    result = StatResult("Test", "T", None, None, pvalue)
    assert _PValueFormatter(pvalue_format, 9).format_data(result) == "P unavailable"


@pytest.mark.parametrize("pvalue_format", ["star", "full", "threshold"])
@pytest.mark.parametrize("p_adjust", _ADJUSTMENTS[1:])
def test_unavailable_comparison_keeps_correction_family_and_ns_suffix(
    pvalue_format: PValueFormat,
    p_adjust: Adjustment,
    unavailable_df: pd.DataFrame,
) -> None:
    data = unavailable_df.copy()
    data.loc[data.group == "C", "value"] = [0, 1, 2, 3, 4]
    with (
        cns.settings.context(pvalue_format=pvalue_format),
        pytest.warns(UserWarning, match="t-test_welch"),
    ):
        ax = cns.barplot(
            data,
            x="group",
            y="value",
            pairs="all",
            p_adjust=p_adjust,
        )
    results = cns.get_comparison_results(ax)
    finite = results.loc[results.pvalue_raw.notna()]
    assert (finite.pvalue_raw < 0.05).all()
    assert (finite.pvalue_adjusted > 0.05).all()
    assert not finite.significant.any()
    if p_adjust == "bonferroni":
        expected = {
            "star": "ns",
            "threshold": "P > 0.05",
            "full": r"$P = 1.4 \times 10^{-1}$",
        }
    else:
        expected = {
            "star": "* (ns)",
            "threshold": "P < 0.05 (ns)",
            "full": r"$P = 4.7 \times 10^{-2}ns$",
        }
    assert finite.annotation.tolist() == [expected[pvalue_format]] * 2
    assert results.annotation.tolist() == [text.get_text() for text in ax.texts]
