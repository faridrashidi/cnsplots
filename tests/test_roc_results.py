from __future__ import annotations

from typing import Any, Literal

import matplotlib.pyplot as plt
import num2tex
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import auc, roc_curve
from statsmodels.stats.multitest import multipletests

import cnsplots as cns
from cnsplots.helpers import _roc
from cnsplots.plots import _specialized


_TABLES: tuple[Literal["curves", "metrics", "bands", "comparisons"], ...] = (
    "curves",
    "metrics",
    "bands",
    "comparisons",
)
_COLUMNS = {
    "curves": ["model", "fpr", "tpr", "threshold"],
    "metrics": ["model", "auc", "method", "pos_label", "n", "n_positive", "n_negative"],
    "bands": ["model", "fpr", "lower", "upper", "ci_level", "method"],
    "comparisons": [
        "model1",
        "model2",
        "auc1",
        "auc2",
        "pvalue_raw",
        "pvalue_adjusted",
        "method",
        "p_adjust",
        "family_size",
        "pos_label",
        "n",
        "n_positive",
        "n_negative",
    ],
}


@pytest.fixture
def tied_roc_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "truth": [0, 0, 0, 0, 1, 1, 1, 1, 1],
            "first": [0.1, 0.3, 0.3, 0.8, 0.3, 0.4, 0.5, 0.8, 0.9],
            "second": [0.2, 0.3, 0.6, 0.7, 0.3, 0.4, 0.7, 0.8, 0.9],
            "third": [0.1, 0.4, 0.5, 0.7, 0.2, 0.3, 0.5, 0.8, 0.9],
        }
    )


def test_roc_results_match_sklearn_and_plotted_values(
    tied_roc_df: pd.DataFrame,
) -> None:
    models = ["second", "first", "third"]
    _, ax = plt.subplots()
    assert cns.rocplot(tied_roc_df, "truth", models, ax=ax) is ax
    result = cns.get_roc_results(ax)
    assert set(result) == set(_COLUMNS)
    assert result["curves"].model.unique().tolist() == models
    assert result["metrics"].model.tolist() == models
    for key in _TABLES:
        assert result[key].columns.tolist() == _COLUMNS[key]
    for model, line in zip(models, ax.lines[:3], strict=True):
        fpr, tpr, thresholds = roc_curve(tied_roc_df.truth, tied_roc_df[model])
        expected_auc = auc(fpr, tpr)
        curve = result["curves"].query("model == @model")
        np.testing.assert_array_equal(curve.fpr, fpr)
        np.testing.assert_array_equal(curve.tpr, tpr)
        np.testing.assert_array_equal(curve.threshold, thresholds)
        assert np.isposinf(curve.threshold.iloc[0])
        np.testing.assert_array_equal(curve[["fpr", "tpr"]], line.get_xydata())
        metric = result["metrics"].query("model == @model").iloc[0]
        assert metric.auc == expected_auc
        assert metric.method == "trapezoidal"
        assert metric.pos_label == 1
        assert metric.n == 9
        assert metric.n_positive == 5
        assert metric.n_negative == 4
        assert line.get_label() == f"{model} (AUC={metric.auc:.2f})"
    assert result["bands"].empty
    assert result["comparisons"].empty


@pytest.mark.parametrize("p_adjust", [None, "bonferroni", "holm", "fdr_bh", "fdr_by"])
def test_roc_comparison_results_match_delong_and_adjustments(
    tied_roc_df: pd.DataFrame, p_adjust: Any
) -> None:
    models = ["third", "first", "second"]
    expected_pairs = [("third", "first"), ("third", "second"), ("first", "second")]
    raw = [
        _roc._delong_roc_test(
            tied_roc_df.truth.to_numpy(),
            tied_roc_df[first].to_numpy(),
            tied_roc_df[second].to_numpy(),
        )
        for first, second in expected_pairs
    ]
    adjusted = raw if p_adjust is None else multipletests(raw, method=p_adjust)[1]
    ax = cns.rocplot(tied_roc_df, "truth", models, pairs="all", p_adjust=p_adjust)
    result = cns.get_roc_results(ax)
    comparisons = result["comparisons"]
    assert list(zip(comparisons.model1, comparisons.model2)) == expected_pairs
    np.testing.assert_array_equal(comparisons.pvalue_raw, raw)
    np.testing.assert_array_equal(comparisons.pvalue_adjusted, adjusted)
    assert comparisons.method.tolist() == ["delong"] * 3
    assert comparisons.p_adjust.tolist() == [p_adjust] * 3
    assert comparisons.family_size.tolist() == [3] * 3
    assert comparisons.pos_label.tolist() == [1] * 3
    assert comparisons.n.tolist() == [9] * 3
    assert comparisons.n_positive.tolist() == [5] * 3
    assert comparisons.n_negative.tolist() == [4] * 3
    metrics = result["metrics"].set_index("model")
    for _, row in comparisons.iterrows():
        assert row.auc1 == metrics.loc[row.model1, "auc"]
        assert row.auc2 == metrics.loc[row.model2, "auc"]
        displayed = rf"${num2tex.num2tex(row.pvalue_adjusted, precision=2):.2g}$"
        assert (
            f"{row.model1} vs {row.model2}: P = {displayed}" in ax.texts[-1].get_text()
        )


@pytest.mark.parametrize("pairs", [None, []])
def test_unrequested_roc_comparisons_are_empty_without_testing(
    tied_roc_df: pd.DataFrame, pairs: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_test(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("No DeLong comparisons were requested")

    monkeypatch.setattr(_roc, "_delong_roc_test", unexpected_test)
    ax = cns.rocplot(tied_roc_df, "truth", ["first", "second"], pairs=pairs)
    result = cns.get_roc_results(ax)
    assert result["comparisons"].empty
    assert result["comparisons"].columns.tolist() == _COLUMNS["comparisons"]
    assert len(ax.texts) == 0


def test_roc_results_preserve_requested_degenerate_comparisons() -> None:
    truth = np.array([0, 0, 0, 1, 1, 1])
    data = pd.DataFrame(
        {"truth": truth, "perfect": truth, "identical": truth, "reversed": 1 - truth}
    )
    ax = cns.rocplot(
        data,
        "truth",
        ["perfect", "identical", "reversed"],
        pairs=[("perfect", "reversed"), ("identical", "perfect")],
    )
    result = cns.get_roc_results(ax)
    assert result["metrics"].auc.tolist() == [1.0, 1.0, 0.0]
    comparisons = result["comparisons"]
    assert comparisons.model1.tolist() == ["perfect", "identical"]
    assert comparisons.model2.tolist() == ["reversed", "perfect"]
    assert comparisons.pvalue_raw.tolist() == [0.0, 1.0]
    assert comparisons.pvalue_adjusted.tolist() == [0.0, 1.0]


def test_roc_results_capture_exact_bands_and_are_defensive_snapshots(
    tied_roc_df: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    computed_bands = []
    bootstrap = _roc._bootstrap_roc_confidence_band

    def capture_band(*args: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        band = bootstrap(*args)
        computed_bands.append(band)
        return band

    monkeypatch.setattr(_roc, "_bootstrap_roc_confidence_band", capture_band)
    ax = cns.rocplot(
        tied_roc_df, "truth", ["first", "second"], ci_show=True, pairs="all"
    )
    expected = cns.get_roc_results(ax)
    assert len(computed_bands) == 2
    for model, (fpr, lower, upper), artist in zip(
        ["first", "second"], computed_bands, ax.collections, strict=True
    ):
        band = expected["bands"].query("model == @model")
        np.testing.assert_array_equal(band.fpr, fpr)
        np.testing.assert_array_equal(band.lower, lower)
        np.testing.assert_array_equal(band.upper, upper)
        assert band.ci_level.tolist() == [0.95] * 101
        assert band.method.tolist() == ["stratified_bootstrap"] * 101
        vertices = np.asarray(artist.get_paths()[0].vertices)
        np.testing.assert_array_equal(vertices[1:102], np.column_stack([fpr, lower]))
        np.testing.assert_array_equal(
            vertices[103:204][::-1], np.column_stack([fpr, upper])
        )

    def unexpected_compute(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Reading ROC results must not recompute statistics")

    monkeypatch.setattr(_roc, "_bootstrap_roc_confidence_band", unexpected_compute)
    monkeypatch.setattr(_roc, "_delong_roc_test", unexpected_compute)
    monkeypatch.setattr(_specialized, "roc_curve", unexpected_compute)
    monkeypatch.setattr(_specialized, "auc", unexpected_compute)
    tied_roc_df.loc[:, "first"] = 0.0
    result = cns.get_roc_results(ax)
    for key in _TABLES:
        table = result[key]
        table.iloc[0, 0] = "changed"
        table.attrs["source"] = "changed"
    result["metrics"] = pd.DataFrame()
    ax.lines[0].set_label("Updated legend")
    legend = ax.get_legend()
    assert legend is not None
    legend.remove()
    actual = cns.get_roc_results(ax)
    for key in _TABLES:
        pd.testing.assert_frame_equal(actual[key], expected[key])
        assert actual[key].attrs == expected[key].attrs


def test_roc_results_follow_current_axes_and_replace_on_reuse(
    roc_df: pd.DataFrame,
) -> None:
    _, (ax, other) = plt.subplots(1, 2)
    empty = cns.get_roc_results(ax)
    for key in _TABLES:
        assert empty[key].empty
        assert empty[key].columns.tolist() == _COLUMNS[key]
    cns.rocplot(roc_df, "truth", ["model_a", "model_b"], pairs="all", ax=ax)
    old_curve = ax.lines[0]
    plt.sca(other)
    assert all(cns.get_roc_results()[key].empty for key in _TABLES)
    plt.sca(ax)
    for key in _TABLES:
        pd.testing.assert_frame_equal(
            cns.get_roc_results()[key], cns.get_roc_results(ax)[key]
        )
    cns.rocplot(roc_df, "truth", "model_b", ax=ax)
    old_curve.remove()
    result = cns.get_roc_results(ax)
    assert result["metrics"].model.tolist() == ["model_b"]
    assert result["comparisons"].empty
    ax.clear()
    for key in _TABLES:
        pd.testing.assert_frame_equal(cns.get_roc_results(ax)[key], empty[key])


@pytest.mark.parametrize("artist_kind", ["curve", "band", "annotation"])
def test_roc_results_expire_when_plot_artist_removed(
    roc_df: pd.DataFrame, artist_kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        _roc,
        "_bootstrap_roc_confidence_band",
        lambda *args: (
            np.array([0.0, 1.0]),
            np.array([0.0, 0.5]),
            np.array([0.5, 1.0]),
        ),
    )
    ax = cns.rocplot(roc_df, "truth", ["model_a", "model_b"], ci_show=True, pairs="all")
    artist = {
        "curve": ax.lines[0],
        "band": ax.collections[0],
        "annotation": ax.texts[0],
    }[artist_kind]
    artist.remove()
    for key in _TABLES:
        table = cns.get_roc_results(ax)[key]
        assert table.empty
        assert table.columns.tolist() == _COLUMNS[key]
