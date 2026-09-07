from __future__ import annotations

from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle

import cnsplots as cns
from cnsplots.plots._genomics import enrichmentbarplot


@pytest.fixture
def enrichment_results() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Term": ["Repair", "Signaling", "Repair", "Boundary", "Outside", "Tie"],
            "FDR q-val": [0.01, 0.001, 0.0001, 0.05, 0.06, 0.01],
            "Count": [7, 12, 3, 0, 99, 8],
        },
        index=pd.Index([4, 2, 2, 9, 1, 4]),
    )


def _labels(ax: Axes) -> list[str]:
    return [text.get_text() for text in ax.get_yticklabels()]


def _bars(ax: Axes) -> list[Rectangle]:
    return [cast(Rectangle, patch) for patch in ax.patches]


def test_bar_lengths_selection_labels_and_counts(
    enrichment_results: pd.DataFrame,
) -> None:
    original = enrichment_results.copy(deep=True)

    ax = enrichmentbarplot(enrichment_results, "Term", count="Count", top_term=4)

    assert _labels(ax) == ["Repair", "Signaling", "Repair", "Tie"]
    assert [bar.get_width() for bar in _bars(ax)] == pytest.approx([4, 3, 2, 2])
    assert [bar.get_y() + bar.get_height() / 2 for bar in _bars(ax)] == pytest.approx(
        [0, 1, 2, 3]
    )
    assert ax.yaxis_inverted()
    assert ax.get_xlabel() == "\u2013log10(FDR q-val)"
    assert ax.get_ylabel() == "Term"
    assert ax.get_xlim()[0] == 0
    assert [text.get_text() for text in ax.texts] == ["n=3", "n=12", "n=7", "n=8"]
    assert [cast(Any, text).xy for text in ax.texts] == [(4, 0), (3, 1), (2, 2), (2, 3)]
    assert len(ax.containers) == 1
    pd.testing.assert_frame_equal(enrichment_results, original)


def test_input_display_order_keeps_significance_selection(
    enrichment_results: pd.DataFrame,
) -> None:
    ax = enrichmentbarplot(enrichment_results, "Term", top_term=3, order="input")

    assert _labels(ax) == ["Repair", "Signaling", "Repair"]
    assert [bar.get_width() for bar in _bars(ax)] == pytest.approx([2, 3, 4])
    assert not ax.texts


def test_default_top_twenty_keeps_input_order_for_ties() -> None:
    results = pd.DataFrame(
        {"Term": [f"Term {i}" for i in range(25)], "FDR q-val": [0.01] * 25}
    )

    ax = enrichmentbarplot(results, "Term")

    assert _labels(ax) == [f"Term {i}" for i in range(20)]


def test_object_numeric_columns_from_enrichment_results_are_supported() -> None:
    results = pd.DataFrame(
        {
            "Term": ["A", "B", "C"],
            "FDR q-val": pd.Series([0.001, 0.02, 0.01], dtype=object),
            "Count": pd.Series([12, np.nan, 3], dtype=object),
        }
    )
    original = results.copy(deep=True)

    ax = enrichmentbarplot(results, "Term", count="Count")

    assert _labels(ax) == ["A", "C", "B"]
    assert [bar.get_width() for bar in _bars(ax)] == pytest.approx(
        [3, 2, -np.log10(0.02)]
    )
    assert [text.get_text() for text in ax.texts] == ["n=12", "n=3"]
    pd.testing.assert_frame_equal(results, original)


def test_count_annotations_have_space_inside_axes() -> None:
    cns.figure(160, 100)
    results = pd.DataFrame(
        {"Term": ["A", "B"], "FDR q-val": [0.001, 0.02], "Count": [18, 7]}
    )

    ax = enrichmentbarplot(results, "Term", count="Count")
    ax.figure.canvas.draw()

    assert ax.get_xlim()[1] == pytest.approx(3.6)
    for annotation in ax.texts:
        assert annotation.get_window_extent().x1 <= ax.get_window_extent().x1


def test_cutoff_is_inclusive_and_can_be_disabled(
    enrichment_results: pd.DataFrame,
) -> None:
    _, (ax, unfiltered_ax) = plt.subplots(1, 2)
    enrichmentbarplot(enrichment_results, "Term", top_term=None, ax=ax)
    enrichmentbarplot(
        enrichment_results,
        "Term",
        cutoff=None,
        top_term=None,
        order="input",
        ax=unfiltered_ax,
    )

    assert _labels(ax) == ["Repair", "Signaling", "Repair", "Tie", "Boundary"]
    assert _bars(ax)[-1].get_width() == pytest.approx(-np.log10(0.05))
    assert _labels(unfiltered_ax) == enrichment_results["Term"].tolist()
    assert len(unfiltered_ax.patches) == len(enrichment_results)


def test_zero_significance_has_finite_width_without_clipping_positive_values() -> None:
    smallest_positive = np.nextafter(0, 1)
    results = pd.DataFrame(
        {"Term": ["Zero", "Subnormal", "One"], "padj": [0, smallest_positive, 1]}
    )
    original = results.copy(deep=True)

    ax = enrichmentbarplot(results, "Term", "padj", cutoff=None)

    assert [bar.get_width() for bar in _bars(ax)] == pytest.approx(
        [-np.log10(np.finfo(float).tiny), -np.log10(smallest_positive), 0]
    )
    assert _labels(ax) == ["Zero", "Subnormal", "One"]
    assert ax.get_xlabel() == "\u2013log10(padj)"
    pd.testing.assert_frame_equal(results, original)


def test_cutoff_zero_selects_only_exact_zeros() -> None:
    results = pd.DataFrame({"Term": ["Zero", "Positive"], "FDR q-val": [0, 0.001]})

    ax = enrichmentbarplot(results, "Term", cutoff=0)

    assert _labels(ax) == ["Zero"]


@pytest.mark.parametrize("empty_mode", ["input", "filter", "selection"])
def test_empty_results_return_labeled_axes(
    enrichment_results: pd.DataFrame, empty_mode: str
) -> None:
    results = (
        enrichment_results.iloc[:0] if empty_mode == "input" else enrichment_results
    )
    _, ax = plt.subplots()

    returned = enrichmentbarplot(
        results,
        "Term",
        count="Count",
        cutoff=0 if empty_mode == "filter" else 0.05,
        top_term=0 if empty_mode == "selection" else None,
        ax=ax,
    )

    assert returned is ax
    assert not ax.patches
    assert not ax.texts
    assert not _labels(ax)
    assert ax.get_xlabel() == "\u2013log10(FDR q-val)"
    ax.figure.canvas.draw()


def test_untyped_empty_results_are_supported() -> None:
    results = pd.DataFrame(columns=pd.Index(["Term", "FDR q-val", "Count"]))

    ax = enrichmentbarplot(results, "Term", count="Count")

    assert not ax.patches


@pytest.mark.parametrize("all_missing", [False, True])
def test_missing_counts_omit_annotations(all_missing: bool) -> None:
    results = pd.DataFrame(
        {
            "Term": ["A", "B", "C"],
            "FDR q-val": pd.array([0.001, 0.01, 0.02], dtype="Float64"),
            "Count": pd.array(
                [pd.NA, pd.NA, pd.NA] if all_missing else [3, pd.NA, 0], dtype="Int64"
            ),
        }
    )
    original = results.copy(deep=True)

    ax = enrichmentbarplot(results, "Term", count="Count")

    assert [text.get_text() for text in ax.texts] == (
        [] if all_missing else ["n=3", "n=0"]
    )
    pd.testing.assert_frame_equal(results, original)


def test_explicit_axes_and_multipanel(enrichment_results: pd.DataFrame) -> None:
    mp = cns.multipanel(max_width=300)
    target_ax = mp.panel("A", width=110, height=100)
    other_ax = mp.panel("B", width=100, height=100)
    original_texts = list(other_ax.texts)
    plt.sca(other_ax)

    returned = enrichmentbarplot(
        enrichment_results, "Term", count="Count", ax=target_ax
    )

    assert returned is target_ax
    assert not other_ax.patches
    assert list(other_ax.texts) == original_texts
    assert plt.gca() is other_ax
    assert len(target_ax.patches) == 5
    implicit_ax = enrichmentbarplot(enrichment_results, "Term", top_term=2)
    assert implicit_ax is other_ax
    mp.newline()
    mp.panel("C", width=90, height=80)
    assert mp.fig is not None
    mp.fig.canvas.draw()
    assert len(target_ax.patches) == 5
    assert len(other_ax.patches) == 2


@pytest.mark.parametrize("value", [np.nan, pd.NA, np.inf, -np.inf, -0.01, 1.01])
def test_invalid_significance_is_rejected_before_filtering(value: Any) -> None:
    results = pd.DataFrame(
        {
            "Term": ["Good", "Invalid"],
            "FDR q-val": pd.array([0.01, value], dtype="Float64"),
        }
    )

    with pytest.raises(ValueError, match="finite, nonmissing significance"):
        enrichmentbarplot(results, "Term", top_term=1)


@pytest.mark.parametrize("column", ["FDR q-val", "Count"])
@pytest.mark.parametrize("value", ["0.01", True, 0.01 + 0j])
def test_nonnumeric_columns_are_rejected(column: str, value: Any) -> None:
    results = pd.DataFrame({"Term": ["A"], "FDR q-val": [0.01], "Count": [2]})
    results[column] = [value]

    with pytest.raises(ValueError, match="real numeric"):
        enrichmentbarplot(results, "Term", count="Count")


@pytest.mark.parametrize("value", [-1, 1.5, np.inf, -np.inf])
def test_invalid_counts_are_rejected(value: float) -> None:
    results = pd.DataFrame({"Term": ["A"], "FDR q-val": [0.01], "Count": [value]})

    with pytest.raises(ValueError, match="nonnegative integer counts"):
        enrichmentbarplot(results, "Term", count="Count", cutoff=0)


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"top_term": True}, TypeError, "'top_term'"),
        ({"top_term": 1.5}, TypeError, "'top_term'"),
        ({"top_term": -1}, ValueError, "'top_term'"),
        ({"cutoff": True}, TypeError, "'cutoff'"),
        ({"cutoff": "0.05"}, TypeError, "'cutoff'"),
        ({"cutoff": -0.1}, ValueError, "'cutoff'"),
        ({"cutoff": 1.1}, ValueError, "'cutoff'"),
        ({"cutoff": np.nan}, ValueError, "'cutoff'"),
        ({"order": "descending"}, ValueError, "'order'"),
    ],
)
def test_invalid_options(
    enrichment_results: pd.DataFrame,
    kwargs: dict[str, Any],
    error: type[Exception],
    match: str,
) -> None:
    with pytest.raises(error, match=match):
        enrichmentbarplot(enrichment_results, "Term", **kwargs)


def test_dataframe_columns_and_term_names_are_validated(
    enrichment_results: pd.DataFrame,
) -> None:
    with pytest.raises(TypeError, match="pandas DataFrame"):
        enrichmentbarplot(cast(Any, []), "Term")
    for column in ["Term", "FDR q-val", "Count"]:
        with pytest.raises(ValueError, match="not found"):
            enrichmentbarplot(
                enrichment_results.drop(columns=column), "Term", count="Count"
            )
    missing_term = enrichment_results.copy()
    missing_term.loc[9, "Term"] = None
    with pytest.raises(ValueError, match="missing terms"):
        enrichmentbarplot(missing_term, "Term")
