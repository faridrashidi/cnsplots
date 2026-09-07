from __future__ import annotations

from types import SimpleNamespace

import pytest
from statannotations.stats.StatResult import StatResult

from cnsplots._utils import _PValueFormatter


@pytest.mark.parametrize(
    ("pvalue", "star", "threshold"),
    [
        (0, "****", "P < 0.0001"),
        (1e-4, "****", "P < 0.0001"),
        (1.1e-4, "***", "P < 0.001"),
        (1e-3, "***", "P < 0.001"),
        (1.1e-3, "**", "P < 0.01"),
        (1e-2, "**", "P < 0.01"),
        (1.1e-2, "*", "P < 0.05"),
        (0.05, "*", "P < 0.05"),
        (0.051, "ns", "P > 0.05"),
        (1, "ns", "P > 0.05"),
    ],
)
def test_pvalue_formatter_star_and_threshold_boundaries(
    pvalue: float, star: str, threshold: str
) -> None:
    result = StatResult("Test", "T", None, None, pvalue)

    assert _PValueFormatter("star", 9).format_data(result) == star
    assert _PValueFormatter("threshold", 9).format_data(result) == threshold


@pytest.mark.parametrize(
    ("pvalue", "expected"),
    [
        (0, r"$P = 0.0 \times 10^{0}$"),
        (0.0000123, r"$P = 1.2 \times 10^{-5}$"),
        (0.2, r"$P = 2.0 \times 10^{-1}$"),
        (1, r"$P = 1.0 \times 10^{0}$"),
    ],
)
def test_pvalue_formatter_full_preserves_scientific_notation(
    pvalue: float, expected: str
) -> None:
    result = StatResult("Test", "T", None, None, pvalue)
    formatter = _PValueFormatter("full", 9)
    formatter.config(show_test_name=False, pvalue_format_string="{:.1e}")

    assert formatter.format_data(result) == expected

    formatter.config(show_test_name=True)
    assert formatter.format_data(result) == expected.replace("$P", "$T P")


@pytest.mark.parametrize(
    ("format", "expected"),
    [
        ("star", "** (ns)"),
        ("threshold", "P < 0.01 (ns)"),
        ("full", r"$P = 1.0 \times 10^{-2}ns$"),
    ],
)
def test_pvalue_formatter_preserves_corrected_significance(
    format: str, expected: str
) -> None:
    result = StatResult("Test", "T", None, None, 0.01)
    result.correction_method = "Holm-Bonferroni"
    result.corrected_significance = False
    formatter = _PValueFormatter(format, 9)
    formatter.config(show_test_name=False, pvalue_format_string="{:.1e}")

    assert formatter.format_data(result) == expected

    result.corrected_significance = True
    assert formatter.format_data(result) == expected.replace(" (ns)", "").replace(
        "ns$", "$"
    )


@pytest.mark.parametrize(
    ("pvalue", "expected"), [(0.01, "P < 0.01"), (0.2, "P > 0.05")]
)
def test_pvalue_formatter_threshold_accepts_result_without_adjust(
    pvalue: float, expected: str
) -> None:
    result = SimpleNamespace(pvalue=pvalue)

    assert _PValueFormatter("threshold", 9).format_data(result) == expected


def test_pvalue_formatter_instances_keep_configuration_independent() -> None:
    first = _PValueFormatter("star", 7)
    second = _PValueFormatter("star", 11)
    full = _PValueFormatter("full", "small")
    result = StatResult("Test", "T", None, None, 0.00001)

    first.pvalue_thresholds[0][1] = "custom"
    first.config(fontsize=13, show_test_name=False, pvalue_format_string="{:.1e}")

    assert first.format_data(result) == "custom"
    assert second.format_data(result) == "****"
    assert full.format_data(result) == r"$T P = 1.000 \times 10^{-5}$"
    assert first.fontsize == 13
    assert second.fontsize == 11
    assert full.fontsize == "small"
    assert second.show_test_name is True
    assert second.pvalue_format_string == "{:.3e}"

    result.correction_method = "Holm-Bonferroni"
    result.corrected_significance = False
    first.config(correction_format="replace")

    assert first.format_data(result) == "ns"
    assert second.format_data(result) == "**** (ns)"
