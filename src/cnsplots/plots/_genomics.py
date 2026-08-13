from __future__ import annotations

from typing import Any, cast

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes

import cnsplots._utils as utils
from cnsplots._setup import setup_ax
from cnsplots._utils import _legend_fontsize, _resize_legend_markers
from cnsplots._validation import (
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
)

_CNS_CONTINUOUS_CMAPS = {
    "BuRd_custom",
    "OrBu_custom",
    "WhYlOrRd_custom",
    "YlGnBu_custom",
    "parula",
}


def volcanoplot(
    data: pd.DataFrame,
    x: str = "log2FoldChange",
    y: str = "-log10(adjp)",
    symbol: str = "symbol",
    show_list: list[str] | None = None,
    n_show: int = 10,
    *,
    pvalue_threshold: float = 0.05,
    fold_change_threshold: float = 0.5,
    transform_y: bool = False,
    ax: Axes | None = None,
) -> Axes:
    """
    Create a volcano plot for differential expression analysis.

    This function generates a volcano plot to visualize statistical significance
    versus fold change in genomics data, with automatic labeling of top
    differentially expressed genes.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing differential expression results.
    x : str, default: 'log2FoldChange'
        Column name for log2 fold change values (x-axis).
    y : str, default: '-log10(adjp)'
        Column name for -log10 adjusted p-values (y-axis).
    symbol : str, default: 'symbol'
        Column name for gene symbols or feature names to label.
    show_list : list, optional
        List of specific gene symbols to highlight and label.
    n_show : int, default: 10
        Number of top upregulated and downregulated genes to label automatically
        when ``show_list`` is ``None``. If ``show_list`` is provided, it takes
        precedence and ``n_show`` is ignored.
    pvalue_threshold : float, default: 0.05
        P-value threshold used to identify significant features.
    fold_change_threshold : float, default: 0.5
        Absolute fold-change threshold used to identify upregulated and
        downregulated features.
    transform_y : bool, default: False
        If True, treat ``y`` as raw p-values and plot their -log10 transform.
        If False, ``y`` must already contain -log10-transformed values.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. If None, uses the current axes.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    gseaplot : Create a GSEA dot plot.
    scatterplot : Create a general scatter plot.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.volcanoplot(
    ...     data=de_results, x="log2FoldChange", y="-log10(padj)", symbol="gene_name"
    ... )
    >>> ax.set_title("Differential Expression")

    >>> # Use raw p-values and custom thresholds
    >>> ax = cns.volcanoplot(
    ...     data=de_results,
    ...     x="LFC",
    ...     y="padj",
    ...     symbol="gene_name",
    ...     pvalue_threshold=0.01,
    ...     fold_change_threshold=1,
    ...     transform_y=True,
    ... )

    >>> # Highlight specific genes
    >>> ax = cns.volcanoplot(
    ...     data=de_results,
    ...     x="log2FoldChange",
    ...     y="-log10(padj)",
    ...     symbol="gene_name",
    ...     show_list=["TP53", "EGFR", "KRAS"],
    ... )
    """
    # Validate inputs
    validate_dataframe(data, "data", "volcanoplot")
    validate_columns_exist(data, [x, y, symbol], "volcanoplot")
    validate_dataframe_not_empty(data, "volcanoplot")
    if isinstance(n_show, bool) or not isinstance(n_show, (int, np.integer)):
        raise TypeError("[volcanoplot] Parameter 'n_show' must be an integer")
    if n_show < 0:
        raise ValueError("[volcanoplot] Parameter 'n_show' must be non-negative")
    numeric_types = (int, float, np.integer, np.floating)
    if isinstance(pvalue_threshold, bool) or not isinstance(
        pvalue_threshold, numeric_types
    ):
        raise TypeError("[volcanoplot] Parameter 'pvalue_threshold' must be a number")
    if not 0 < pvalue_threshold <= 1:
        raise ValueError(
            "[volcanoplot] Parameter 'pvalue_threshold' must be greater than 0 "
            "and at most 1"
        )
    if isinstance(fold_change_threshold, bool) or not isinstance(
        fold_change_threshold, numeric_types
    ):
        raise TypeError(
            "[volcanoplot] Parameter 'fold_change_threshold' must be a number"
        )
    if not np.isfinite(fold_change_threshold) or fold_change_threshold < 0:
        raise ValueError(
            "[volcanoplot] Parameter 'fold_change_threshold' must be a finite, "
            "non-negative number"
        )
    if not isinstance(transform_y, bool):
        raise TypeError("[volcanoplot] Parameter 'transform_y' must be a boolean")

    import adjustText as at

    hue = "DEG"
    de = data.copy()
    if transform_y:
        if not pd.api.types.is_numeric_dtype(de[y]):
            raise ValueError(f"[volcanoplot] Column '{y}' must be numeric")
        if ((de[y] < 0) | (de[y] > 1)).any():
            raise ValueError(
                f"[volcanoplot] Column '{y}' must contain p-values between 0 and 1"
            )
        de[y] = -np.log10(de[y].clip(lower=np.finfo(float).tiny))

    de[hue] = "NS"
    significance_cutoff = -np.log10(pvalue_threshold)
    significance_label = f"p_adj < {pvalue_threshold:g}"
    de.loc[de[y] > significance_cutoff, hue] = significance_label
    up = (de[y] > significance_cutoff) & (de[x] > fold_change_threshold)
    down = (de[y] > significance_cutoff) & (de[x] < -fold_change_threshold)
    if show_list is None:
        de["rank"] = de[y] * de[x].abs()
        de.loc[de.loc[up].nlargest(n_show, "rank").index, hue] = "Up"
        de.loc[de.loc[down].nlargest(n_show, "rank").index, hue] = "Down"
    else:
        de.loc[de[symbol].isin(show_list) & up, hue] = "Up"
        de.loc[de[symbol].isin(show_list) & down, hue] = "Down"
    de = de.sort_values(hue)

    blue = utils.get_hexcolors_from_apalette([0], "BlueRed")[0]
    red = utils.get_hexcolors_from_apalette([1], "BlueRed")[0]
    if ax is None:
        ax = plt.gca()
    ax = sns.scatterplot(
        data=de,
        x=x,
        y=y,
        size=hue,
        sizes={"Down": 10, "NS": 2, "Up": 10, significance_label: 2},
        hue=hue,
        edgecolor=None,
        palette={"Down": blue, "NS": "grey", "Up": red, significance_label: "black"},
        rasterized=True,
        ax=ax,
    )

    annotations = []
    for mode, color in [("Up", red), ("Down", blue)]:
        for _, (x0, y0, t) in de.loc[de[hue] == mode, [x, y, symbol]].iterrows():
            annotations.append(
                ax.annotate(
                    t,
                    (x0, y0),
                    color=color,
                    size=_legend_fontsize(),
                    path_effects=[pe.withStroke(linewidth=1, foreground="white")],
                )
            )
    at.adjust_text(
        annotations,
        arrowprops={"arrowstyle": "-", "color": "black", "lw": 0.5},
        ax=ax,
    )

    ax.spines["right"].set_visible(True)
    ax.spines["top"].set_visible(True)
    ax.set_xlabel("log2(fold change)" if x == "log2FoldChange" else x)
    if transform_y:
        ax.set_ylabel(f"\u2013log10({y})")
    else:
        ax.set_ylabel("\u2013log10(adjusted p-value)" if y == "-log10(adjp)" else y)
    ax.plot(
        [0, 0],
        [0, max(de[y])],
        color="black",
        linestyle="--",
        linewidth=0.8,
        dashes=(8, 5),
    )
    utils.take_legend_out(ax=ax)
    _resize_legend_markers(ax.get_legend(), 20)

    return ax


def gseaplot(
    data: pd.DataFrame,
    y: str,
    color: str = "NES",
    cutoff: float = 0.05,
    cmap: str = "BuRd_custom",
    top_term: int = 20,
    size: float = 1.8,
    significance_column: str = "FDR q-val",
    *,
    ax: Axes | None = None,
) -> Axes:
    """
    Create a Gene Set Enrichment Analysis (GSEA) dot plot.

    This function generates a dot plot visualizing GSEA results, with gene sets
    on the y-axis, normalized enrichment scores on the x-axis, and dot size/color
    representing statistical significance and enrichment strength.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing GSEA results.
    y : str
        Column name for gene set names or pathway names (y-axis labels).
    color : str, default: 'NES'
        Column name for the variable to use for dot color encoding.
    cutoff : float, default: 0.05
        Significance cutoff applied to ``significance_column`` when filtering
        gene sets.
    cmap : str, default: 'BuRd_custom'
        Colormap for encoding the color variable.
    top_term : int, default: 20
        Maximum number of top gene sets to display.
    size : float, default: 1.8
        Scaling factor for dot sizes.
    significance_column : str, default: 'FDR q-val'
        Column containing significance values used to filter gene sets by
        ``cutoff``. This is independent of the ``color`` encoding.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. If None, uses the current axes.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    volcanoplot : Create a volcano plot for differential expression.
    dotplot : Create a dot plot matrix.

    Examples
    --------
    >>> import cnsplots as cns
    >>> # GSEA results from gseapy
    >>> ax = cns.gseaplot(
    ...     data=gsea_results, y="Term", color="NES", top_term=15, cutoff=0.05
    ... )
    >>> ax.set_title("Gene Set Enrichment Analysis")

    >>> # Color by adjusted p-value instead
    >>> ax = cns.gseaplot(
    ...     data=gsea_results,
    ...     y="Term",
    ...     color="Adjusted P-value",
    ...     cmap="viridis",
    ...     top_term=30,
    ... )
    """
    # Validate inputs
    validate_dataframe(data, "data", "gseaplot")
    validate_columns_exist(data, [y, "NES", color, significance_column], "gseaplot")
    validate_dataframe_not_empty(data, "gseaplot")

    import gseapy as gp

    plot_data = data.loc[data[significance_column] <= cutoff].copy()
    resolved_cmap = utils.palettes(cmap) if cmap in _CNS_CONTINUOUS_CMAPS else cmap

    if ax is None:
        ax = plt.gca()
    gp.dotplot(
        plot_data,
        cmap=cast(Any, resolved_cmap),
        y=y,
        x="NES",
        cutoff=np.inf,
        column=color,
        ax=ax,
        top_term=top_term,
        size=size,
    )
    fig = ax.figure
    cbar_ax = fig.axes[-1]
    cbar_ax.yaxis.set_label_position("left")
    cbar_ax.yaxis.labelpad = 1
    cbar_ax.set_ylabel("")
    legend = ax.get_legend()
    if legend is None:
        raise RuntimeError("[gseaplot] GSEA plot did not produce a legend")
    handles = [h for h in legend.legend_handles if h is not None]
    labels = [t.get_text() for t in legend.get_texts()]
    title = legend.get_title().get_text()
    ax.legend(
        handles,
        labels,
        title=title,
        bbox_to_anchor=(1.2, 1),
        labelspacing=0.2,
        markerscale=1.5,
    )
    setup_ax(ax, colorbar_label="")
    ax.set_xlabel("Normalized Enrichment Score (NES)")
    return ax
