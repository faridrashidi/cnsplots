from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
    from matplotlib.axes import Axes

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

import cnsplots as cns
from cnsplots._validation import (
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
)


def _legend_fontsize() -> int | float:
    legend_fontsize = cns.settings.legend_fontsize
    if legend_fontsize is None:
        return cns.settings.title_fontsize
    return legend_fontsize


def volcanoplot(
    data: pd.DataFrame,
    x: str = "log2FoldChange",
    y: str = "-log10(adjp)",
    symbol: str = "symbol",
    show_list: list[str] | None = None,
    n_show: int = 10,
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

    >>> # Label fewer top genes automatically
    >>> ax = cns.volcanoplot(
    ...     data=de_results,
    ...     x="log2FoldChange",
    ...     y="-log10(padj)",
    ...     symbol="gene_name",
    ...     n_show=5,
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

    import adjustText as at

    hue = "DEG"
    de = data.copy()

    de[hue] = "NS"
    de.loc[de[y] > -np.log10(0.05), hue] = "p_adj < 0.05"
    up = (de[y] > -np.log10(0.05)) & (de[x] > 0.5)
    down = (de[y] > -np.log10(0.05)) & (de[x] < -0.5)
    if show_list is None:
        de["rank"] = de[y] * de[x].abs()
        de.loc[de.loc[up].nlargest(n_show, "rank").index, hue] = "Up"
        de.loc[de.loc[down].nlargest(n_show, "rank").index, hue] = "Down"
    else:
        de.loc[de[symbol].isin(show_list) & up, hue] = "Up"
        de.loc[de[symbol].isin(show_list) & down, hue] = "Down"
    de = de.sort_values(hue)

    blue = cns.get_hexcolors_from_apalette([0], "BlueRed")
    red = cns.get_hexcolors_from_apalette([1], "BlueRed")
    ax = sns.scatterplot(
        data=de,
        x=x,
        y=y,
        size=hue,
        sizes={"Down": 10, "NS": 2, "Up": 10, "p_adj < 0.05": 2},
        hue=hue,
        edgecolor=None,
        palette={"Down": blue, "NS": "grey", "Up": red, "p_adj < 0.05": "black"},
        rasterized=True,
    )

    annotations = []
    for mode, color in [("Up", red), ("Down", blue)]:
        for _, (x0, y0, t) in de.loc[de[hue] == mode, [x, y, symbol]].iterrows():
            annotations.append(
                plt.annotate(
                    t,
                    (x0, y0),
                    color=color,
                    size=_legend_fontsize(),
                    path_effects=[pe.withStroke(linewidth=1, foreground="white")],
                )
            )
    at.adjust_text(
        annotations, arrowprops={"arrowstyle": "-", "color": "black", "lw": 0.5}
    )

    ax.spines["right"].set_visible(True)
    ax.spines["top"].set_visible(True)
    ax.set_xlabel("log2(fold change)")
    ax.set_ylabel("\u2013log10(adjusted p-value)")
    plt.plot(
        [0, 0],
        [0, max(de[y])],
        color="black",
        linestyle="--",
        linewidth=0.8,
        dashes=(8, 5),
    )
    cns.take_legend_out()
    if ax.get_legend() is not None:
        for handle in ax.get_legend().legend_handles:
            legend_dot_size = 20
            if hasattr(handle, "set_sizes"):
                handle.set_sizes([legend_dot_size])
            elif hasattr(handle, "set_markersize"):
                handle.set_markersize(2 * np.sqrt(legend_dot_size / np.pi))

    return ax


def gseaplot(
    data: pd.DataFrame,
    y: str,
    color: str = "NES",
    cutoff: float = 0.05,
    cmap: str = "BuRd_custom",
    top_term: int = 20,
    size: float = 1.8,
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
        Significance cutoff for filtering gene sets.
    cmap : str, default: 'BuRd_custom'
        Colormap for encoding the color variable.
    top_term : int, default: 20
        Maximum number of top gene sets to display.
    size : float, default: 1.8
        Scaling factor for dot sizes.

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
    validate_columns_exist(data, [y, "NES", color], "gseaplot")
    validate_dataframe_not_empty(data, "gseaplot")

    import gseapy as gp

    ax = plt.gca()
    gp.dotplot(
        data,
        cmap=cmap,
        y=y,
        x="NES",
        cutoff=cutoff,
        column=color,
        ax=ax,
        top_term=top_term,
        size=size,
    )
    fig = plt.gcf()
    cbar_ax = fig.axes[-1]
    cbar_ax.yaxis.set_label_position("left")
    cbar_ax.yaxis.labelpad = 1
    cbar_ax.set_ylabel("")
    legend = ax.get_legend()
    assert legend is not None
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
    cns.setup_ax(ax, colorbar_label="")
    plt.xlabel("Normalized Enrichment Score (NES)")
    return ax
