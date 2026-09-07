from __future__ import annotations

from types import SimpleNamespace

import gseapy as gp
import numpy as np
import pandas as pd
import pytest

import cnsplots as cns


@pytest.fixture
def prerank_results(monkeypatch: pytest.MonkeyPatch) -> pd.DataFrame:
    results = pd.DataFrame(
        {
            "Term": [
                "GO_MODERATE",
                "KEGG_FDR_BOUNDARY",
                "GO_NEGATIVE",
                "HALLMARK_POSITIVE_BOUNDARY",
                "REACTOME_NEGATIVE_BOUNDARY",
                "GO_WEAK_POSITIVE",
                "GO_WEAK_NEGATIVE",
                "BIOCARTA_ABOVE_FDR",
                "GO_ZERO",
                "GO_TIED",
            ],
            "NES": [2.0, 3.0, -2.5, 1.5, -1.5, 1.49, -1.49, -3.5, 0.0, -2.0],
            "FDR q-val": [0.01, 0.25, 0.249, 0.01, 0.01, 0.01, 0.01, 0.251, 1, 0.01],
            "ES": np.linspace(0.1, 1.0, 10),
            "Lead_genes": [f"GENE{index};GENE{index + 1}" for index in range(10)],
        },
        index=pd.Index(range(10), name="result_row"),
    )
    results.attrs["ranking_metric"] = "log2 fold change"
    monkeypatch.setattr(gp, "prerank", lambda **kwargs: SimpleNamespace(res2d=results))
    return results


def _prerank(**kwargs: float | None) -> pd.DataFrame:
    return cns.prerank(
        pd.DataFrame({"gene": ["A", "B", "C"], "rank": [3.0, 2.0, 1.0]}),
        {"set": ["A", "B"]},
        name_gene="gene",
        name_rank="rank",
        permutation_num=10,
        **kwargs,
    )


def test_prerank_defaults_preserve_strict_thresholds_and_absolute_nes_order(
    prerank_results: pd.DataFrame,
) -> None:
    result = _prerank()

    assert result.index.tolist() == [2, 0, 9]
    assert result["Clean_Term"].tolist() == ["Negative", "Moderate", "Tied"]
    pd.testing.assert_frame_equal(
        result.drop(columns="Clean_Term"), prerank_results.loc[[2, 0, 9]]
    )


@pytest.mark.parametrize(
    ("fdr_cutoff", "min_abs_nes", "expected_rows"),
    [
        (None, None, [7, 1, 2, 0, 9, 3, 4, 5, 6, 8]),
        (None, 1.5, [7, 1, 2, 0, 9]),
        (0.25, None, [2, 0, 9, 3, 4, 5, 6]),
        (0.02, 1.0, [0, 9, 3, 4, 5, 6]),
        (0.01, None, []),
    ],
)
def test_prerank_configurable_filters_preserve_result_data(
    prerank_results: pd.DataFrame,
    fdr_cutoff: float | None,
    min_abs_nes: float | None,
    expected_rows: list[int],
) -> None:
    original = prerank_results.copy(deep=True)

    result = _prerank(fdr_cutoff=fdr_cutoff, min_abs_nes=min_abs_nes)

    assert result.index.tolist() == expected_rows
    assert result["Clean_Term"].notna().all()
    assert result.attrs == original.attrs
    pd.testing.assert_frame_equal(
        result.drop(columns="Clean_Term"), original.loc[expected_rows]
    )
    pd.testing.assert_frame_equal(prerank_results, original)


def test_prerank_all_results_allow_explicit_gseaplot_selection(
    prerank_results: pd.DataFrame,
) -> None:
    results = _prerank(fdr_cutoff=None, min_abs_nes=None)
    selected = results.loc[[1, 3, 7, 8]]

    cns.figure(140, 160)
    ax = cns.gseaplot(selected, y="Clean_Term", cutoff=1.0, top_term=len(selected))

    offsets = np.asarray(ax.collections[0].get_offsets(), dtype=float)
    rendered_nes = {
        label.get_text(): offset[0]
        for label, offset in zip(ax.get_yticklabels(), offsets, strict=True)
    }
    assert rendered_nes == pytest.approx(
        selected.set_index("Clean_Term")["NES"].to_dict()
    )
