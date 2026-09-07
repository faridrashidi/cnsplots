from __future__ import annotations

import inspect
from typing import Any

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from PyComplexHeatmap.clustermap import DendrogramPlotter
from scipy.cluster.hierarchy import linkage

import cnsplots as cns
from cnsplots.helpers import _heatmap as helper_heatmap


def _matrix(rows: int = 4, cols: int = 3) -> pd.DataFrame:
    return pd.DataFrame(
        np.random.default_rng(42).normal(size=(rows, cols)),
        index=pd.Index([f"sample_{i}" for i in range(rows)]),
        columns=pd.Index([f"feature_{i}" for i in range(cols)]),
    )


def test_cluster_memory_estimates_fifty_thousand_items() -> None:
    required_bytes = 9_999_800_000

    helper_heatmap._check_cluster_memory(
        50_000, "average", "correlation", required_bytes, "row"
    )
    with pytest.raises(ValueError, match="max_cluster_bytes"):
        helper_heatmap._check_cluster_memory(
            50_000, "average", "correlation", required_bytes - 1, "row"
        )


def test_heatmapplot_has_keyword_only_cluster_memory_limit() -> None:
    parameter = inspect.signature(cns.heatmapplot).parameters["max_cluster_bytes"]

    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default == 512 * 1024**2


@pytest.mark.parametrize(
    ("method", "metric"),
    [
        ("single", "correlation"),
        ("centroid", "euclidean"),
        ("median", "euclidean"),
        ("ward", "euclidean"),
    ],
)
def test_cluster_memory_allows_fastcluster_vector_algorithms(
    method: str, metric: str
) -> None:
    helper_heatmap._check_cluster_memory(50_000, method, metric, 0, "row")


@pytest.mark.parametrize(
    ("method", "metric"),
    [
        ("average", "euclidean"),
        ("complete", "correlation"),
        ("weighted", "euclidean"),
        ("centroid", "correlation"),
    ],
)
def test_cluster_memory_guards_condensed_distance_algorithms(
    method: str, metric: str
) -> None:
    with pytest.raises(ValueError, match="max_cluster_bytes"):
        helper_heatmap._check_cluster_memory(50_000, method, metric, 0, "row")


@pytest.mark.parametrize("method", ["single", "ward"])
def test_cluster_memory_guards_scipy_fallback(
    monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    def missing_fastcluster(name: str) -> Any:
        assert name == "fastcluster"
        raise ImportError("fastcluster is unavailable")

    monkeypatch.setattr(helper_heatmap.importlib, "import_module", missing_fastcluster)

    with pytest.raises(ValueError, match="max_cluster_bytes"):
        helper_heatmap._check_cluster_memory(50_000, method, "euclidean", 0, "row")


@pytest.mark.parametrize("axis", ["row", "col"])
def test_heatmapplot_guards_each_clustered_axis_independently(
    monkeypatch: pytest.MonkeyPatch, axis: str
) -> None:
    data = _matrix()
    if axis == "col":
        data = data.T
    other_axis = "col" if axis == "row" else "row"
    cluster_kwargs: dict[str, Any] = {f"{other_axis}_cluster": True}

    # Three clustered items require 24 bytes; four require 48 bytes.
    plotter = cns.heatmapplot(
        data,
        max_cluster_bytes=24,
        **cluster_kwargs,
    )
    assert plotter.data2d.shape == data.shape

    def unexpected_clustering(self: Any) -> None:
        pytest.fail("Memory guard should reject before distance computation")

    monkeypatch.setattr(
        DendrogramPlotter, "_calculate_linkage_fastcluster", unexpected_clustering
    )
    monkeypatch.setattr(
        DendrogramPlotter, "_calculate_linkage_scipy", unexpected_clustering
    )
    plt.figure()
    cluster_kwargs = {f"{axis}_cluster": True}
    with pytest.raises(ValueError, match=f"(?i){axis}"):
        cns.heatmapplot(
            data,
            max_cluster_bytes=24,
            **cluster_kwargs,
        )


def test_heatmapplot_does_not_guard_unclustered_axes() -> None:
    data = _matrix()

    plotter = cns.heatmapplot(data, max_cluster_bytes=0)

    pd.testing.assert_frame_equal(plotter.data2d, data)


def test_cluster_memory_override_disables_guard() -> None:
    helper_heatmap._check_cluster_memory(50_000, "average", "correlation", None, "row")
    plotter = cns.heatmapplot(
        _matrix(), row_cluster=True, col_cluster=True, max_cluster_bytes=None
    )

    assert len(plotter.dendrogram_row.linkage) == 3
    assert len(plotter.dendrogram_col.linkage) == 2


@pytest.mark.parametrize(
    ("limit", "error"),
    [(-1, ValueError), (1.5, TypeError), ("512", TypeError), (True, TypeError)],
)
def test_heatmapplot_rejects_invalid_cluster_memory_limits(
    limit: Any, error: type[Exception]
) -> None:
    with pytest.raises(error, match="max_cluster_bytes"):
        cns.heatmapplot(_matrix(), max_cluster_bytes=limit)


@pytest.mark.parametrize("axis", ["row", "col"])
def test_heatmapplot_checks_actual_metadata_split_sizes(axis: str) -> None:
    data = _matrix(rows=6)
    adata = ad.AnnData(data if axis == "row" else data.T)
    metadata = adata.obs if axis == "row" else adata.var
    metadata["group"] = ["A"] * 3 + ["B"] * 3
    split_kwargs: dict[str, Any] = {
        f"{axis}_cluster": True,
        f"{axis}_split": "group",
    }

    # Each group requires 24 bytes; clustering all six items would require 120.
    plotter = cns.heatmapplot(
        adata,
        max_cluster_bytes=24,
        **split_kwargs,
    )

    assert [len(group) for group in getattr(plotter, f"{axis}_order")] == [3, 3]

    with pytest.raises(ValueError, match=f"(?i){axis}"):
        cns.heatmapplot(
            adata,
            max_cluster_bytes=8,
            **split_kwargs,
        )


@pytest.mark.parametrize("axis", ["row", "col"])
def test_heatmapplot_guards_between_group_clustering_when_cluster_is_false(
    axis: str,
) -> None:
    data = _matrix(rows=6)
    adata = ad.AnnData(data if axis == "row" else data.T)
    metadata = adata.obs if axis == "row" else adata.var
    metadata["group"] = ["A", "A", "B", "B", "C", "C"]
    split_kwargs: dict[str, Any] = {
        f"{axis}_cluster": False,
        f"{axis}_split": "group",
    }

    # Groups each fit in 8 bytes, but clustering three group means needs 24.
    with pytest.raises(ValueError, match=f"(?i){axis}"):
        cns.heatmapplot(
            adata,
            max_cluster_bytes=8,
            **split_kwargs,
        )

    plt.figure()
    split_kwargs[f"{axis}_split_order"] = ["A", "B", "C"]
    plotter = cns.heatmapplot(
        adata,
        max_cluster_bytes=0,
        **split_kwargs,
    )
    assert [len(group) for group in getattr(plotter, f"{axis}_order")] == [2, 2, 2]


@pytest.mark.parametrize("axis", ["row", "col"])
def test_heatmapplot_integer_split_requires_full_axis_clustering(axis: str) -> None:
    data = _matrix(rows=6)
    if axis == "col":
        data = data.T
    split_kwargs: dict[str, Any] = {f"{axis}_cluster": True, f"{axis}_split": 3}

    with pytest.raises(ValueError, match=f"(?i){axis}"):
        cns.heatmapplot(
            data,
            max_cluster_bytes=24,
            **split_kwargs,
        )


def test_heatmapplot_reuses_precomputed_unsplit_linkages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _matrix()
    row_linkage = linkage(data, method="average", metric="correlation")
    col_linkage = linkage(data.T, method="average", metric="correlation")

    def unexpected_clustering(self: Any) -> None:
        pytest.fail("Precomputed linkage should avoid distance computation")

    monkeypatch.setattr(
        DendrogramPlotter, "_calculate_linkage_fastcluster", unexpected_clustering
    )
    monkeypatch.setattr(
        DendrogramPlotter, "_calculate_linkage_scipy", unexpected_clustering
    )

    plotter = cns.heatmapplot(
        data,
        row_cluster=True,
        col_cluster=True,
        max_cluster_bytes=0,
        row_dendrogram_kws={"linkage": row_linkage},
        col_dendrogram_kws={"linkage": col_linkage},
    )

    np.testing.assert_array_equal(plotter.dendrogram_row.linkage, row_linkage)
    np.testing.assert_array_equal(plotter.dendrogram_col.linkage, col_linkage)


@pytest.mark.parametrize("axis", ["row", "col"])
def test_cluster_memory_guard_applies_when_precomputed_linkage_is_disabled(
    axis: str,
) -> None:
    data = _matrix()
    plotter = cns.heatmapplot(data, max_cluster_bytes=0)
    getattr(plotter, f"{axis}_dendrogram_kws")["linkage"] = linkage(
        data if axis == "row" else data.T
    )

    with pytest.raises(ValueError, match=f"(?i){axis}"):
        getattr(plotter, f"calculate_{axis}_dendrograms")(data, use_linkage=False)
