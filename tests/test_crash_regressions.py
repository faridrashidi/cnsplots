from __future__ import annotations

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import cnsplots as cns
from cnsplots.helpers import _phylo, _sankey


def test_heatmapplot_accepts_integer_col_split() -> None:
    adata = ad.AnnData(
        np.array([[1.0, 2.0], [3.0, 4.0]]),
        var=pd.DataFrame(index=pd.Index(["gene_a", "gene_b"])),
    )

    plotter = cns.heatmapplot(adata, col_split=1, col_cluster=False)

    assert plotter.col_split == 1


def test_categorical_heatmap_accepts_series() -> None:
    fig, ax = plt.subplots()

    result_ax, cmap = _phylo._heatmap(pd.Series(["A", "B"]), ax=ax)

    assert result_ax is ax
    assert set(cmap) == {"A", "B"}


def test_sankeyplot_accepts_one_label_per_side() -> None:
    fig, ax = plt.subplots()

    result_ax = _sankey.sankeyplot(["A", "A"], np.array(["B", "B"]), ax=ax)

    assert result_ax is ax
    assert len(ax.texts) == 2
