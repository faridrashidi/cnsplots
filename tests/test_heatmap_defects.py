from __future__ import annotations

import types
from pathlib import Path
from typing import Any, cast

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from scipy import sparse

import cnsplots as cns
from cnsplots.plots import _heatmap as heatmap_mod


def _stub_plotter(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_plotter(**kwargs: object) -> types.SimpleNamespace:
        ax = plt.gca()
        return types.SimpleNamespace(
            data2d=kwargs["data"],
            heatmap_axes=np.array([[ax]], dtype=object),
            ax_heatmap=ax,
            cbars=[],
        )

    monkeypatch.setattr(
        heatmap_mod.helper_heatmap, "ClusterMapPlotterNew", fake_plotter
    )


def test_heatmapplot_cycles_continuous_annotation_palettes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adata = ad.AnnData(np.ones((3, 2)))
    annotations = [f"score_{index}" for index in range(4)]
    for index, annotation in enumerate(annotations):
        adata.obs[annotation] = np.arange(3) + index

    seen_cmaps: list[str] = []

    def fake_anno_simple(series: pd.Series, **kwargs: object) -> object:
        seen_cmaps.append(str(kwargs["cmap"]))
        return object()

    monkeypatch.setattr(heatmap_mod.pch, "anno_simple", fake_anno_simple)
    monkeypatch.setattr(heatmap_mod.pch, "HeatmapAnnotation", lambda **kwargs: kwargs)
    _stub_plotter(monkeypatch)

    with cns.settings.context(palette_seq="parula"):
        cns.heatmapplot(adata, row_annotation=annotations)

    assert seen_cmaps == ["gnuplot", "bwr", "hot", "gnuplot"]


@pytest.mark.parametrize("layer", [None, "counts"])
def test_heatmapplot_converts_sparse_data_without_anndata_to_df(
    monkeypatch: pytest.MonkeyPatch, layer: str | None
) -> None:
    matrix = sparse.csr_matrix([[1.0, 0.0], [0.0, 2.0]])
    adata = ad.AnnData(matrix)
    adata.obs_names = ["cell_1", "cell_2"]
    adata.var_names = ["gene_1", "gene_2"]
    adata.layers["counts"] = matrix * 2
    expected_matrix = matrix if layer is None else matrix * 2

    monkeypatch.setattr(
        ad.AnnData,
        "to_df",
        lambda *args, **kwargs: pytest.fail("heatmapplot called AnnData.to_df()"),
    )
    _stub_plotter(monkeypatch)

    plotter = cns.heatmapplot(adata, layer=layer)

    expected = pd.DataFrame(
        expected_matrix.toarray(), index=adata.obs_names, columns=adata.var_names
    )
    pd.testing.assert_frame_equal(plotter.data2d, expected)


def test_heatmapplot_rejects_unsafe_sparse_densification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adata = ad.AnnData(sparse.csr_matrix((2, 2), dtype=np.float64))
    monkeypatch.setattr(heatmap_mod, "_MAX_DENSE_HEATMAP_BYTES", 1)
    monkeypatch.setattr(
        ad.AnnData,
        "to_df",
        lambda *args, **kwargs: pytest.fail("heatmapplot called AnnData.to_df()"),
    )

    with pytest.raises(
        ValueError,
        match=r"approximately 0\.0 MiB.*subset AnnData before plotting",
    ):
        cns.heatmapplot(adata)


def test_heatmapplot_converts_backed_sparse_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    matrix = sparse.csr_matrix([[1.0, 0.0], [0.0, 2.0]])
    source = ad.AnnData(matrix)
    source.obs_names = ["cell_1", "cell_2"]
    source.var_names = ["gene_1", "gene_2"]
    path = tmp_path / "sparse.h5ad"
    ad.AnnData.write_h5ad(source, path)
    backed = ad.read_h5ad(path, backed="r")

    monkeypatch.setattr(
        ad.AnnData,
        "to_df",
        lambda *args, **kwargs: pytest.fail("heatmapplot called AnnData.to_df()"),
    )
    _stub_plotter(monkeypatch)

    try:
        plotter = cns.heatmapplot(backed)
    finally:
        backed.file.close()

    expected = pd.DataFrame(
        matrix.toarray(), index=source.obs_names, columns=source.var_names
    )
    pd.testing.assert_frame_equal(plotter.data2d, expected)


def test_heatmapplot_preserves_missing_x_error() -> None:
    adata = ad.AnnData(X=None, shape=(2, 2))

    with pytest.raises(ValueError, match="X is None, cannot convert to dataframe"):
        cns.heatmapplot(adata)


def test_heatmapplot_accepts_dataframe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = pd.DataFrame(
        [[1.0, 2.0], [3.0, 4.0]],
        index=pd.Index(["sample_1", "sample_2"]),
        columns=pd.Index(["feature_1", "feature_2"]),
    )
    _stub_plotter(monkeypatch)

    plotter = cns.heatmapplot(data)

    pd.testing.assert_frame_equal(plotter.data2d, data)


def test_heatmapplot_accepts_ndarray(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = np.array([[1.0, 2.0], [3.0, 4.0]])
    _stub_plotter(monkeypatch)

    plotter = cns.heatmapplot(data)

    pd.testing.assert_frame_equal(plotter.data2d, pd.DataFrame(data))


@pytest.mark.parametrize("data", [pd.DataFrame(), np.empty((0, 2))])
def test_heatmapplot_rejects_empty_tabular_data(data: Any) -> None:
    with pytest.raises(ValueError, match="Data is empty"):
        cns.heatmapplot(data)


def test_heatmapplot_rejects_non_matrix_input() -> None:
    with pytest.raises(TypeError, match="AnnData, pandas DataFrame, or numpy ndarray"):
        cns.heatmapplot(cast(Any, [[1.0, 2.0], [3.0, 4.0]]))

    with pytest.raises(ValueError, match="two-dimensional"):
        cns.heatmapplot(np.ones((2, 2, 2)))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"layer": "scaled"},
        {"row_annotation": ["group"]},
        {"col_annotation": ["group"]},
        {"row_split": "group"},
        {"col_split": "group"},
    ],
)
def test_heatmapplot_rejects_anndata_options_for_dataframe(
    kwargs: dict[str, Any],
) -> None:
    with pytest.raises(ValueError, match="only supported for AnnData"):
        cns.heatmapplot(pd.DataFrame([[1.0]]), **kwargs)
