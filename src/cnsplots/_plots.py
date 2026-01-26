from collections.abc import Set as AbstractSet
from typing import List, Optional, Tuple

import matplotlib as mpl
import matplotlib.gridspec as grid_spec
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import num2tex
import numpy as np
import palettable
import pandas as pd
import PyComplexHeatmap as pch
import scipy as sp
import seaborn as sns
from matplotlib.patches import Patch
from natsort import natsort_keygen
from PyComplexHeatmap import DotClustermapPlotter
from scipy.stats import fisher_exact
from sklearn.metrics import auc, roc_curve

import cnsplots as cns
import cnsplots._helper_heatmap as helper_heatmap
import cnsplots._helper_phylo as helper_phylo
import cnsplots._helper_sankey as helper_sankey
from cnsplots._utils import PALETTE_SEQ


def heatmapplot(
    adata,
    layer=None,
    row_annotation=None,
    col_annotation=None,
    row_cluster=False,
    col_cluster=False,
    row_split=None,
    col_split=None,
    cmap=PALETTE_SEQ,
    label="value",
    xlabel="xlabel",
    ylabel="ylabel",
    legend_width=20,
    legend_hpad=2,
    legend_vpad=0,
    linewidth=0,
    colors=None,
    rasterized=True,
    xticklabels_rotation=45,
    xticklabels_fontsize=7,
    yticklabels_fontsize=7,
    **kwargs,
):
    """
    Create a clustered heatmap with optional annotations and dendrograms.

    This function generates a complex heatmap visualization using PyComplexHeatmap,
    supporting hierarchical clustering, row/column annotations, and customizable
    color schemes.

    Parameters
    ----------
    adata : AnnData
        Annotated data matrix containing observations and variables.
    layer : str, optional
        Key in `adata.layers` to use for the heatmap data. If None, uses `adata.X`.
    row_annotation : list of str, optional
        Column names from `adata.obs` to display as row annotations.
    col_annotation : list of str, optional
        Column names from `adata.var` to display as column annotations.
    row_cluster : bool, default: False
        Whether to perform hierarchical clustering on rows.
    col_cluster : bool, default: False
        Whether to perform hierarchical clustering on columns.
    row_split : str or int, optional
        Column name from `adata.obs` or number of splits for row grouping.
    col_split : str or int, optional
        Column name from `adata.var` or number of splits for column grouping.
    cmap : str, default: PALETTE_SEQ
        Colormap for the heatmap. Can be categorical (Set1, Set2, Ecotyper1, Dark2,
        Ecotyper2, Set3) or continuous (parula, gnuplot, bwr, hot).
    label : str, default: 'value'
        Label for the colorbar.
    xlabel : str, default: 'xlabel'
        Label for the x-axis.
    ylabel : str, default: 'ylabel'
        Label for the y-axis.
    legend_width : int, default: 20
        Width of the legend area.
    legend_hpad : int, default: 10
        Horizontal padding for the legend.
    legend_vpad : int, default: 0
        Vertical padding for the legend.
    linewidth : float, default: 0
        Width of lines between heatmap cells.
    colors : dict, optional
        Custom color mapping for categorical annotations.
    rasterized : bool, default: True
        Whether to rasterize the heatmap for reduced file size.
    xticklabels_rotation : int, default: 45
        Rotation angle for x-axis tick labels.
    xticklabels_fontsize : int, default: 7
        Font size for x-axis tick labels.
    yticklabels_fontsize : int, default: 7
        Font size for y-axis tick labels.
    **kwargs
        Additional keyword arguments passed to `ClusterMapPlotterNew`.

    Returns
    -------
    ClusterMapPlotterNew
        The heatmap plotter object containing axes and layout information.

    See Also
    --------
    dotplot : Create a dot plot matrix with size and color encoding.
    confusionplot : Plot confusion matrix as a heatmap.

    Notes
    -----
    Categorical annotations automatically use predefined color palettes (Set1, Set2, etc.),
    while continuous annotations use sequential colormaps (parula, gnuplot, bwr, hot).
    The function cycles through available palettes when multiple annotations are present.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.heatmapplot(
    ...     adata, row_annotation=["cell_type", "batch"], col_cluster=True, cmap="bwr"
    ... )
    """
    cat_palettes = ["Set1", "Set2", "Ecotyper1", "Dark2", "Ecotyper2", "Set3"]
    cont_palettes = ["parula", "gnuplot", "bwr", "hot"]
    cbar_titles = [label]
    if cmap in cat_palettes:
        cat_palettes.remove(cmap)
    if cmap in cont_palettes:
        cont_palettes.remove(cmap)
    cat_counter, cont_counter = 0, 0

    def _annot_helper(df, rc_annotation):
        rc_dict = {}
        nonlocal cat_counter, cont_counter
        for annot in rc_annotation:
            if isinstance(df.dtypes[annot], object):
                if df[annot].isna().any():
                    rc_dict[annot] = pch.anno_label(
                        df[annot],
                        colors="black",
                        va="top",
                        ha="right",
                        relpos=(0, 0.4),
                    )
                else:
                    annot_colors = colors.get(annot) if colors else None
                    # Only use custom colors if they cover all unique values
                    # Compare using string representation to handle int/str mismatches
                    if annot_colors is not None:
                        unique_vals_str = {str(v) for v in df[annot].dropna().unique()}
                        color_keys_str = {str(k) for k in annot_colors}
                        if not unique_vals_str.issubset(color_keys_str):
                            annot_colors = None
                    rc_dict[annot] = pch.anno_simple(
                        df[annot].sort_values(key=natsort_keygen()),
                        cmap=cat_palettes[cat_counter % len(cat_palettes)],
                        legend_kws={
                            "frameon": False,
                            "labelspacing": 0.2,
                            "handletextpad": 0.4,
                            "color_text": False,
                        },
                        height=3,
                        rasterized=True,
                        linewidth=0,
                        colors=annot_colors,
                    )
                    cat_counter += 1
            else:
                rc_dict[annot] = pch.anno_simple(
                    df[annot],
                    cmap=cont_palettes[cont_counter],
                    height=3,
                    rasterized=True,
                    linewidth=0,
                )
                cont_counter += 1
                cbar_titles.append(annot)
        return rc_dict

    if row_annotation is not None:
        rc_dict = _annot_helper(adata.obs, row_annotation)
        row_annotation = pch.HeatmapAnnotation(
            axis=0,
            verbose=0,
            label_side="bottom",
            label_kws={
                "horizontalalignment": "right",
                "rotation": xticklabels_rotation,
                "rotation_mode": "anchor",
            },
            **rc_dict,
        )
    if col_annotation is not None:
        ca_dict = _annot_helper(adata.var, col_annotation)
        col_annotation = pch.HeatmapAnnotation(axis=1, verbose=0, **ca_dict)

    if row_split is not None and not isinstance(row_split, int):
        row_split = adata.obs[row_split]
    if col_split is not None and not isinstance(row_split, int):
        col_split = adata.var[col_split]

    df = adata.to_df() if layer is None else adata.to_df(layer=layer)
    cmp = helper_heatmap.ClusterMapPlotterNew(
        data=df,
        left_annotation=row_annotation,
        top_annotation=col_annotation,
        row_cluster=row_cluster,
        col_cluster=col_cluster,
        row_split=row_split,
        col_split=col_split,
        cmap=cmap,
        rasterized=rasterized,
        label=label,
        xlabel=xlabel,
        ylabel=ylabel,
        legend_width=legend_width,
        legend_hpad=legend_hpad,
        legend_vpad=legend_vpad,
        row_dendrogram_size=10,
        col_dendrogram_size=10,
        linewidth=linewidth,
        xticklabels_kws={
            "labelrotation": xticklabels_rotation,
            "labelsize": xticklabels_fontsize,
        },
        yticklabels_kws={"labelsize": yticklabels_fontsize},
        ylabel_kws={"labelpad": 3},
        xlabel_kws={"labelpad": 5},
        verbose=0,
        row_names_side="left" if row_annotation is None else "right",
        xticklabels=True,
        yticklabels=True,
        **kwargs,
    )
    for cbar in cmp.cbars:
        if isinstance(cbar, mpl.colorbar.Colorbar):
            cbar.outline.set_linewidth(0.3)
            cbar.ax.tick_params(size=0)
    for ax in cmp.legend_axes[0].figure.axes:
        if ax.get_ylabel() in cbar_titles:
            ax.yaxis.set_label_position("left")
            if ax.get_ylabel() == label:
                ax.set_aspect(0.3)
            else:
                ax.set_aspect(6)
    plt.setp(
        cmp.heatmap_axes[-1, 0].get_xticklabels(), rotation_mode="anchor", ha="right"
    )
    cmp.ax_heatmap.set_axis_on()
    sns.despine(ax=cmp.ax_heatmap, bottom=False, left=False, top=False, right=False)
    for s in ["top", "bottom", "left", "right"]:
        cmp.ax_heatmap.spines[s].set_linewidth(1.2)
    return cmp


def dotplot(
    data,
    x,
    y,
    color,
    size,
    value=None,
    legend_width=20,
    legend_hpad=10,
    legend_vpad=0,
    xticklabels_rotation=45,
    xticklabels_fontsize=7,
    yticklabels_fontsize=7,
    **kwargs,
):
    """
    Create a dot plot matrix with color and size encodings.

    This function generates a dot matrix plot where each dot's size and color
    represent different data dimensions, commonly used for visualizing expression
    patterns across groups.

    Parameters
    ----------
    data : pd.DataFrame
        Input DataFrame containing the data to plot.
    x : str
        Column name to use for x-axis categories.
    y : str
        Column name to use for y-axis categories.
    color : str
        Column name to use for dot color encoding.
    size : str
        Column name to use for dot size encoding.
    value : str
        Column name containing the values to display.
    legend_width : int, default: 20
        Width of the legend area.
    legend_hpad : int, default: 10
        Horizontal padding for the legend.
    legend_vpad : int, default: 0
        Vertical padding for the legend.
    xticklabels_rotation : int, default: 45
        Rotation angle for x-axis tick labels.
    xticklabels_fontsize : int, default: 7
        Font size for x-axis tick labels.
    yticklabels_fontsize : int, default: 7
        Font size for y-axis tick labels.
    **kwargs
        Additional keyword arguments passed to `DotClustermapPlotter`.

    Returns
    -------
    DotClustermapPlotter
        The dot plot plotter object containing axes and layout information.

    See Also
    --------
    heatmapplot : Create a clustered heatmap.
    scatterplot : Create a scatter plot with optional hue encoding.

    Notes
    -----
    The dot size and color scales are automatically determined from the data range.
    Uses the 'gnuplot' colormap by default for color encoding.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.dotplot(
    ...     data=df,
    ...     x="condition",
    ...     y="gene",
    ...     color="expression",
    ...     size="pct_expressed",
    ...     value="mean_expr",
    ... )
    """
    row_annotation = pch.HeatmapAnnotation(
        axis=0,
        verbose=0,
        label=pch.anno_label(
            data.pivot(index=y, columns=x, values=color)[data[x].unique()[0]],
            colors="black",
            va="center",
            ha="right",
            relpos=(1, 0.5),
        ),
    )
    cmap = kwargs.pop("cmap", "gnuplot")
    plotter_kwargs = {
        "data": data,
        "x": x,
        "y": y,
        "c": color,
        "s": size,
        "row_cluster": False,
        "col_cluster": False,
        "show_rownames": False,
        "show_colnames": True,
        "left_annotation": row_annotation,
        "verbose": 0,
        "cmap": cmap,
        "rasterized": True,
        "row_names_side": "left",
        "xlabel": x,
        "ylabel": y,
        "ylabel_kws": {"labelpad": 10},
        "xlabel_kws": {"labelpad": 15},
        "legend_width": legend_width,
        "legend_hpad": legend_hpad,
        "legend_vpad": legend_vpad,
        "xticklabels_kws": {
            "labelrotation": xticklabels_rotation,
            "labelsize": xticklabels_fontsize,
        },
        "yticklabels_kws": {"labelsize": yticklabels_fontsize},
        "dot_legend_kws": {"frameon": False},
    }
    if value is not None:
        plotter_kwargs["value"] = value
    plotter_kwargs.update(kwargs)
    cmp = DotClustermapPlotter(**plotter_kwargs)
    for cbar in cmp.cbars:
        if isinstance(cbar, mpl.colorbar.Colorbar):
            cbar.outline.set_linewidth(0.3)
            cbar.ax.tick_params(size=0)
    for ax in cmp.legend_axes[0].figure.axes:
        if ax.get_ylabel() in color:
            ax.yaxis.set_label_position("left")
            # if ax.get_ylabel() == label:
            #     ax.set_aspect(0.3)
            # else:
            #     ax.set_aspect(6)
    cmp.ax_heatmap.set_axis_on()
    plt.setp(
        cmp.heatmap_axes[-1, 0].get_xticklabels(), rotation_mode="anchor", ha="right"
    )
    sns.despine(ax=cmp.ax_heatmap, bottom=False, left=False, top=False, right=False)
    for s in ["top", "bottom", "left", "right"]:
        cmp.ax_heatmap.spines[s].set_linewidth(1.2)
    return cmp


def boxplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    pairs: Optional[List[Tuple[str, str]]] = None,
    showoutliers: bool = False,
    addcount: bool = False,
    whis=1.5,
    **kwargs,
) -> None:
    """
    Create a box plot showing the distribution of a continuous variable across categories.

    This function creates a box plot displaying the median, quartiles, and outliers
    of a continuous variable grouped by a categorical variable. Statistical
    comparisons can be added between specified groups.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the categorical variable on the x-axis.
    y : str
        Column name for the continuous variable on the y-axis.
    pairs : list of tuple of str, optional
        List of pairs of category names from x for pairwise statistical comparisons
        using Mann-Whitney U test. Each pair should be a tuple of two category names.
        Default is None (no statistical tests).
    showoutliers : bool, default: False
        Whether to display outlier points beyond the whiskers.
    addcount : bool, default: False
        Whether to add sample size (n) labels above each box.
    whis : float or tuple of float, default: 1.5
        The proportion of the IQR past the low and high quartiles to extend the
        plot whiskers. Use (0, 100) to extend whiskers to minimum and maximum values.
    **kwargs
        Additional keyword arguments passed to `seaborn.boxplot`.
        Common options include:
        - hue: Column name for nested grouping
        - palette: Color palette or column name for coloring
        - order: Order of categories on the x-axis
        - hue_order: Order of hue categories

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    violinplot : Create a violin plot showing full distribution shape.
    stripplot : Create a strip plot showing all individual points.
    barplot : Create a bar plot showing means with error bars.

    Notes
    -----
    The box shows the first quartile (Q1), median, and third quartile (Q3).
    Whiskers extend to the most extreme data point within whis * IQR from the box.
    The function prints a message describing what the whiskers represent.

    Statistical comparisons use the two-sided Mann-Whitney U test (Wilcoxon rank-sum test).

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.boxplot(
    ...     data=df,
    ...     x="treatment",
    ...     y="response",
    ...     pairs=[("control", "treated")],
    ...     showoutliers=True,
    ... )
    """
    args = {
        "showfliers": showoutliers,
        "showcaps": False,
        "showbox": True,
        "linewidth": 0.8,
        "whis": whis,
        "boxprops": {"edgecolor": "none"},
        "medianprops": {"color": "white"},
        "whiskerprops": {"color": "black"},
        "capprops": {"color": "none"},
        "flierprops": {
            "markerfacecolor": "black",
            "markersize": 1.5,
            "markeredgecolor": "black",
            "marker": "o",
            "linewidth": 0,
        },
        "width": 0.5,
    }
    plotting = {"data": data, "x": x, "y": y}
    plotting.update(args)
    plotting.update(kwargs)
    ax = sns.boxplot(**plotting)

    box_patches = [
        patch for patch in ax.patches if isinstance(patch, mpl.patches.PathPatch)
    ]
    if len(box_patches) == 0:
        box_patches = ax.artists
    num_patches = len(box_patches)
    lines_per_boxplot = len(ax.lines) // num_patches
    for i, patch in enumerate(box_patches):
        col = patch.get_facecolor()
        patch.set_edgecolor("None")
        patch.set_facecolor(col)
        for j, line in enumerate(
            ax.lines[i * lines_per_boxplot : (i + 1) * lines_per_boxplot]
        ):
            if j != 2:
                line.set_color(col)
                line.set_mfc(col)
                line.set_mec(col)
            else:
                line.set_color("white")
                line.set_mfc("white")
                line.set_mec("white")

    cns._utils._remove_edge_from_legend_items(ax)
    whis_str = (
        "minimum and maximum values"
        if whis == (0, 100)
        else (
            f"{whis} times the interquartile range"
            if isinstance(whis, (int, float))
            else str(whis)
        )
    )
    print(
        "Boxplots represent the median and bottom and upper quartiles; whiskers"
        f" correspond to the {whis_str}."
    )
    if pairs is not None:
        cns._utils._p_value_helper("Mann-Whitney", data, ax, plotting, pairs)

    if addcount:
        cns._utils._addcount_helper(data, x, ax)


def violinplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    pairs: Optional[List[Tuple[str, str]]] = None,
    width=0.6,
    add_box=True,
    **kwargs,
) -> None:
    """
    Create a violin plot showing the distribution of a continuous variable.

    This function creates a violin plot that combines a kernel density estimate
    with an optional embedded box plot to show both the shape and summary statistics
    of the distribution.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the categorical variable on the x-axis.
    y : str
        Column name for the continuous variable on the y-axis.
    pairs : list of tuple of str, optional
        List of pairs of category names from x for pairwise statistical comparisons
        using Mann-Whitney U test. Each pair should be a tuple of two category names.
        Default is None (no statistical tests).
    width : float, default: 0.6
        Width of each violin body.
    add_box : bool, default: True
        Whether to overlay a narrow box plot inside each violin showing quartiles
        and median.
    **kwargs
        Additional keyword arguments passed to `seaborn.violinplot`.
        Common options include:
        - hue: Column name for nested grouping
        - palette: Color palette for coloring categories
        - split: Whether to split violins when using hue
        - inner: Representation of data inside violin (box, quartile, point, stick, None)

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    boxplot : Create a box plot showing quartiles without density.
    kdeplot : Create a kernel density plot.
    distplot : Create a distribution plot with histogram and KDE.

    Notes
    -----
    The violin width at each value represents the kernel density estimate of the
    underlying distribution. The embedded box plot (when add_box=True) shows the
    median, quartiles, and whiskers following standard box plot conventions.

    Statistical comparisons use the two-sided Mann-Whitney U test.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.violinplot(
    ...     data=df,
    ...     x="condition",
    ...     y="expression",
    ...     pairs=[("control", "treated")],
    ...     add_box=True,
    ... )
    """
    args = {
        "showfliers": False,
        "showcaps": False,
        "showbox": True,
        "linewidth": 0.4,
        "boxprops": {"edgecolor": "black", "zorder": 2},
        "medianprops": {"color": "black", "linewidth": 0.8},
        "whiskerprops": {"color": "black"},
        "capprops": {"color": "none"},
        "flierprops": {
            "markerfacecolor": "black",
            "markersize": 1.5,
            "markeredgecolor": "black",
            "marker": "o",
            "linewidth": 0,
        },
        "width": 0.2,
        "color": "white",
    }
    plotting = {"data": data, "x": x, "y": y}
    plotting.update(kwargs)
    ax = sns.violinplot(linewidth=0.001, width=width, **plotting)
    plotting.update(args)
    plotting.update(kwargs)
    # Remove violin-only arguments that boxplot doesn't support
    boxplot_kwargs = {k: v for k, v in plotting.items() if k not in ("split", "inner")}
    if add_box:
        sns.boxplot(**boxplot_kwargs)
    if pairs is not None:
        cns._utils._p_value_helper("Mann-Whitney", data, ax, plotting, pairs)


def barplot(data, x, y, pairs=None, addtip=False, **kwargs):
    """
    Create a bar plot showing mean values across categories with optional statistics.

    This function creates a bar plot displaying the mean of a continuous variable
    grouped by a categorical variable. Error bars are not displayed by default.
    Statistical comparisons and value labels can be added.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the categorical variable on the x-axis.
    y : str
        Column name for the continuous variable whose means are plotted on the y-axis.
    pairs : list of tuple of str, optional
        List of pairs of category names from x for pairwise statistical comparisons
        using Welch's t-test. Each pair should be a tuple of two category names.
        Default is None (no statistical tests).
    addtip : bool, default: False
        Whether to add text labels showing the mean value above each bar.
    **kwargs
        Additional keyword arguments passed to `seaborn.barplot`.
        Common options include:

        - palette : str or list or dict
            Color palette for bars. If a column name is provided, bars are colored
            by that column's values with automatic legend generation.
        - hue : str
            Column name for nested grouping within each category.
        - order : list
            Order of categories on the x-axis.
        - estimator : callable
            Statistical function to estimate within each categorical bin.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    boxplot : Create a box plot showing full distribution.
    violinplot : Create a violin plot with distribution shape.
    stackplot : Create a stacked bar plot for categorical data.

    Notes
    -----
    Error bars are disabled by default (errorbar=None). Statistical comparisons
    use Welch's t-test, which does not assume equal variances.

    When palette is a column name, the function creates a color mapping and
    automatically generates a legend.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.barplot(
    ...     data=df,
    ...     x="treatment",
    ...     y="response",
    ...     pairs=[("control", "drug_a"), ("control", "drug_b")],
    ...     addtip=True,
    ... )

    >>> # Color by group with automatic legend
    >>> cns.barplot(data=df, x="treatment", y="response", palette="cell_type")
    """
    args = {
        "edgecolor": None,
        "errorbar": None,
        "err_kws": {"color": "black", "linewidth": 0.7},
        "capsize": 0.2,
    }
    palette = kwargs.pop("palette", None)
    show_legend = False
    legend_handles = []
    if isinstance(palette, str) and palette in data.columns:
        group_col = palette
        unique_labels = data[palette].unique()
        palette_colors = sns.color_palette(n_colors=len(unique_labels))
        label_to_color = dict(zip(unique_labels, palette_colors))
        target_column = palette
        which_numeric = x if not pd.api.types.is_numeric_dtype(data[x]) else y
        mapping_index = (
            data[[which_numeric, target_column]]
            .drop_duplicates()
            .set_index(which_numeric)[target_column]
            .to_dict()
        )
        palette = {k: label_to_color[v] for k, v in mapping_index.items()}
        show_legend = True
        unique_groups = data[group_col].unique()
        color_list = sns.color_palette(n_colors=len(unique_groups))
        group_to_color = dict(zip(unique_groups, color_list))
        legend_handles = [
            Patch(facecolor=color, label=label)
            for label, color in group_to_color.items()
        ]
    plotting = {"data": data, "x": x, "y": y, "palette": palette}
    plotting.update(args)
    plotting.update(kwargs)
    ax = sns.barplot(**plotting)
    if addtip:
        groupedvalues = data.groupby(x)[[y]].mean().reset_index()
        for _, row in groupedvalues.iterrows():
            ax.text(
                row.name,
                row[y] + 0.05,
                round(row[y], 2),
                color="black",
                ha="center",
                rotation=0,
                size=6,
            )
    if pairs is not None:
        cns._utils._p_value_helper("t-test_welch", data, ax, plotting, pairs)
    if show_legend:
        ax.legend(
            handles=legend_handles,
            title=group_col,
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
        )


def stackplot(
    data,
    x,
    y,
    bar_order=None,
    stack_order=None,
    horizontal=False,
    width=0.5,
    normalize=True,
    pairs=None,
    addtip=False,
    n_factor=1,
):
    """
    Create a stacked bar plot showing categorical distributions.

    This function creates a stacked bar plot (or horizontal stacked bar plot)
    displaying the distribution or count of one categorical variable across
    levels of another categorical variable.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the categorical variable determining bar positions.
    y : str
        Column name for the categorical variable determining stack segments.
    bar_order : list, optional
        Order of categories from x to display. Default is None (natural order).
    stack_order : list, optional
        Order of categories from y for stacking. Default is None (natural order).
    horizontal : bool, default: False
        Whether to create horizontal bars instead of vertical bars.
    width : float, default: 0.5
        Width of the bars.
    normalize : bool, default: True
        Whether to normalize counts to frequencies (proportions summing to 1).
    pairs : list of tuple of str, optional
        List of pairs of category names from x for pairwise statistical comparisons.
        Uses Fisher's exact test for 2×2 tables or chi-squared test otherwise.
    addtip : bool, default: False
        Whether to add total count labels above/beside each bar when normalize=True.
    n_factor : int or float, default: 1
        Scaling factor to divide all values (useful for displaying per-n-samples).

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    barplot : Create a bar plot of means.
    pieplot : Create a pie chart for categorical proportions.
    donutplot : Create a donut chart for categorical proportions.

    Notes
    -----
    When normalize=True, displays proportions (frequencies) with ylabel "Frequency".
    When normalize=False, displays raw counts with ylabel "Count".

    Statistical tests are applied to the contingency table:
    - Fisher's exact test for 2×2 tables
    - Chi-squared test for larger tables

    The legend is automatically moved outside the plot area.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.stackplot(
    ...     data=df,
    ...     x="tissue",
    ...     y="cell_type",
    ...     normalize=True,
    ...     pairs=[("lung", "liver")],
    ... )

    >>> # Horizontal stacked bar plot
    >>> cns.stackplot(
    ...     data=df, x="patient", y="mutation", horizontal=True, normalize=False
    ... )
    """
    data2 = data.value_counts([x, y]).reset_index()
    if horizontal:
        df = data2.pivot(index=y, columns=x, values="count")
    else:
        df = data2.pivot(index=x, columns=y, values="count")
    contingency = df.copy()
    if stack_order is not None:
        df.columns = pd.CategoricalIndex(
            df.columns.values, ordered=True, categories=stack_order, name=y
        )
        df = df.sort_index(axis=1)
    if normalize:
        df = df.div(df.sum(axis=1), axis=0)
        value_label = "Frequency"
    else:
        value_label = "Count"
    df = df.reindex(index=bar_order)
    df = df / n_factor
    ax = plt.gca()
    if horizontal:
        ax = df.plot.barh(stacked=True, width=width, ax=ax, rot=0)
        ax.set_ylabel("")
        ax.set_xlabel(value_label)
    else:
        ax = df.plot.bar(stacked=True, width=width, ax=ax, rot=0)
        ax.set_ylabel(value_label)
        ax.set_xlabel("")
    cns.take_legend_out()
    if addtip and normalize:
        tips = (
            contingency.sum(axis=1).astype(int).reindex(index=bar_order).reset_index()
        )
        tips = tips.rename(columns={0: "value"})
        for _, row in tips.iterrows():
            if horizontal:
                ax.text(
                    1 + 0.02,
                    row.name,
                    row["value"],
                    color="black",
                    ha="left",
                    va="center",
                    rotation=0,
                    size=6,
                )
            else:
                ax.text(
                    row.name,
                    1 + 0.02,
                    row["value"],
                    color="black",
                    ha="center",
                    rotation=0,
                    size=6,
                )
    if pairs is not None:
        if horizontal:
            plotting = {"data": data2, "x": "count", "y": y, "order": bar_order}
        else:
            plotting = {"data": data2, "x": x, "y": "count", "order": bar_order}
        if contingency.shape[1] == 2:
            cns._utils._p_value_helper(
                "fisher-exact", data2, ax, plotting, pairs, contingency
            )
        else:
            cns._utils._p_value_helper(
                "chi-squared", data2, ax, plotting, pairs, contingency
            )


def distplot(data, x, **kwargs):
    """
    Create a distribution plot combining histogram and kernel density estimate.

    This function creates a histogram with an overlaid kernel density estimate (KDE)
    to visualize the distribution of a continuous variable.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the continuous variable to plot.
    **kwargs
        Additional keyword arguments passed to `seaborn.histplot`.
        Common options include:

        - bins : int or sequence
            Number of bins or bin edges for the histogram.
        - hue : str
            Column name for grouping and color-coding.
        - stat : str
            Statistic to compute ('count', 'frequency', 'probability', 'density').
        - element : str
            Visual representation ('bars', 'step', 'poly').
        - fill : bool
            Whether to fill the histogram bars.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    kdeplot : Create a kernel density estimate plot only.
    histplot : Create a histogram without KDE.
    violinplot : Create a violin plot showing distribution shape.

    Notes
    -----
    The KDE is enabled by default. Edge color of histogram bars is removed
    for a cleaner appearance.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.distplot(data=df, x="age")

    >>> # With grouping by category
    >>> cns.distplot(data=df, x="expression", hue="treatment")
    """
    args = {"kde": True, "edgecolor": None}
    args.update(kwargs)
    sns.histplot(data=data, x=x, **args)


def kdeplot(data, x, add_mode=True, **kwargs):
    """
    Create a kernel density estimate plot with optional mode annotation.

    This function creates a smooth kernel density estimate plot to visualize
    the distribution of a continuous variable. Can automatically annotate the
    mode (peak) of the distribution and perform statistical tests for comparisons.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the continuous variable to plot.
    add_mode : bool, default: True
        Whether to add a vertical dashed line at the mode (peak) of the distribution
        with a text label showing the mode value. Only applies when hue is not used.
    **kwargs
        Additional keyword arguments passed to `seaborn.kdeplot`.
        Common options include:

        - hue : str
            Column name for grouping. When two groups are present, automatically
            performs Kolmogorov-Smirnov test and displays p-value.
        - fill : bool
            Whether to fill the area under the curve.
        - multiple : str
            How to handle multiple distributions ('layer', 'stack', 'fill').
        - bw_adjust : float
            Bandwidth adjustment factor for smoothing.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    distplot : Create a distribution plot with histogram and KDE.
    violinplot : Create a violin plot showing distribution shape.
    ridgeplot : Create ridge plots for multiple distributions.

    Notes
    -----
    When hue is specified with exactly two groups, the function performs a
    two-sample Kolmogorov-Smirnov test and displays the p-value in the upper-right
    corner of the plot.

    The mode is identified as the x-value with maximum kernel density and marked
    with a dashed vertical line and label.

    Legend line width is automatically increased to 1.7 for better visibility.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.kdeplot(data=df, x="expression", add_mode=True)

    >>> # Compare two groups with automatic statistics
    >>> cns.kdeplot(data=df, x="score", hue="treatment", fill=True)
    """
    linewidth = kwargs.pop("linewidth", 1)
    ax = sns.kdeplot(data=data, x=x, linewidth=linewidth, **kwargs)
    ax = plt.gca()
    modes = []
    if "hue" in kwargs:
        if data[kwargs["hue"]].nunique() == 2:
            grouped = data.groupby(kwargs["hue"])
            args = [group_df[x].values for _, group_df in grouped]
            p_value = sp.stats.ks_2samp(*args)
            ax = plt.gca()
            x_lim = ax.get_xlim()
            y_lim = ax.get_ylim()
            ax.text(
                x_lim[1],
                y_lim[1],
                rf"$P={num2tex.num2tex(p_value[-1], precision=2):.2g}$",
                ha="right",
                va="top",
            )
            print("   ---> P-value was determined by Anderson-Darling test.")
    else:
        if add_mode and ax.get_lines():
            kde_data = ax.get_lines()[-1].get_data()
            x_vals, y_vals = kde_data[0], kde_data[1]
            mode_idx = np.argmax(y_vals)
            mode = x_vals[mode_idx]
            modes.append(mode)
            kde_color = ax.get_lines()[-1].get_color()
            y_mode = y_vals[mode_idx]
            y_lim = ax.get_ylim()
            ymax = (y_mode - y_lim[0]) / (y_lim[1] - y_lim[0])
            ax.axvline(
                mode,
                ymin=0,
                ymax=ymax,
                color=kde_color,
                linestyle="--",
                linewidth=0.8,
                dashes=(8, 5),
            )
            ax.text(
                mode,
                y_lim[0] + (y_lim[1] - y_lim[0]) * 0.05,
                f"{mode:.2f}",
                ha="center",
                va="bottom",
                fontsize=7,
                color=kde_color,
                bbox=dict(facecolor="white", edgecolor="none", pad=2),
            )

    if ax.get_legend() is not None:
        for handle in ax.get_legend().legend_handles:
            if hasattr(handle, "set_linewidth"):
                handle.set_linewidth(1.7)


def regplot(data, x, y, hue=None, s=3, **kwargs):
    """
    Create a regression plot with linear fit and correlation statistics.

    This function creates a scatter plot with a fitted regression line and displays
    Pearson correlation coefficient and p-value. Supports grouping by a categorical
    variable to show multiple regression lines.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the independent variable (x-axis).
    y : str
        Column name for the dependent variable (y-axis).
    hue : str, optional
        Column name for grouping. When specified, creates separate regression lines
        and correlation statistics for each group using different colors.
    s : float, default: 3
        Size of scatter plot markers.
    **kwargs
        Additional keyword arguments passed to `seaborn.regplot`.
        Common options include:

        - order : int
            Order of polynomial regression (1 for linear, 2 for quadratic, etc.).
        - logx : bool
            Fit regression in log(x) space.
        - robust : bool
            Fit a robust regression resistant to outliers.
        - ci : int
            Confidence interval size (0-100) for regression line shading.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    scatterplot : Create a scatter plot without regression line.
    kdeplot : Create a kernel density plot for distributions.

    Notes
    -----
    Pearson correlation coefficient (ρ) and p-value are displayed in the upper-left
    corner of the plot. When hue is specified, statistics are shown for each group
    in matching colors.

    The p-value tests the null hypothesis that the correlation is zero (no linear
    relationship). P-values are formatted using scientific notation when needed.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.regplot(data=df, x="age", y="expression")

    >>> # Grouped regression with separate fits
    >>> cns.regplot(data=df, x="dose", y="response", hue="cell_line")
    """
    args = {
        "line_kws": {"lw": 1.2},
        "scatter_kws": {"s": s, "alpha": 1, "edgecolor": None},
    }
    args.update(kwargs)
    palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    if hue:
        for idx, hue_val in enumerate(data[hue].unique()):
            subset = data[data[hue] == hue_val]
            ax = sns.regplot(
                data=subset,
                x=x,
                y=y,
                color=palette[idx],
                label=hue_val,
                **args,
            )
            rho, p_value = sp.stats.pearsonr(subset[x], subset[y])
            ax.text(
                0.05,
                0.95 - 0.08 * idx,
                rf"{hue_val}: $\rho$={rho:.2f},"
                rf" P=${num2tex.num2tex(p_value, precision=2):.2g}$",
                color=palette[idx],
                transform=ax.transAxes,
                ha="left",
                va="top",
            )
    else:
        ax = sns.regplot(
            data=data,
            x=x,
            y=y,
            color="black",
            **args,
        )
        rho, p_value = sp.stats.pearsonr(data[x], data[y])
        ax.text(
            0.05,
            0.95,
            rf"$\rho$={rho:.2f}, $P={num2tex.num2tex(p_value, precision=2):.2g}$",
            color="black",
            transform=ax.transAxes,
            ha="left",
            va="top",
        )
    if hue:
        plt.legend(title=hue)


def pieplot(data, x, hue_order=None):
    """
    Create a pie chart showing categorical proportions.

    This function creates a pie chart visualizing the distribution of categories
    in a single categorical variable, with percentage labels and a legend.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the categorical variable to visualize.
    hue_order : list, optional
        Order of categories to display in the pie chart. Default is None
        (order by frequency from value_counts).

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    donutplot : Create a donut chart (pie chart with center hole).
    stackplot : Create a stacked bar plot for categorical distributions.
    barplot : Create a bar plot showing category frequencies.

    Notes
    -----
    Percentages are displayed as white text within each pie slice. The legend
    is automatically positioned outside the plot area and shows category names
    with the column name as the title.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.pieplot(data=df, x="cell_type")

    >>> # Specify category order
    >>> cns.pieplot(data=df, x="response", hue_order=["CR", "PR", "SD", "PD"])
    """
    df = data[x].value_counts()
    if hue_order is None:
        hue_order = df.index
    ax = plt.gca()
    ax = df.reindex(index=hue_order).plot.pie(
        shadow=False,
        autopct="%1.0f%%",
        explode=[0] * df.shape[0],
        textprops={"fontsize": 6, "color": "white"},
        labeldistance=None,
        wedgeprops={"linewidth": 0.3, "edgecolor": "white"},
        ax=ax,
        ylabel="",
        legend=True,
    )
    cns.take_legend_out(title=x)


def donutplot(data, x, hue_order=None):
    """
    Create a donut chart showing categorical proportions.

    This function creates a donut chart (pie chart with a center hole) visualizing
    the distribution of categories in a single categorical variable, with the
    variable name displayed in the center.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the categorical variable to visualize.
    hue_order : list, optional
        Order of categories to display in the donut chart. Default is None
        (order by frequency from value_counts).

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    pieplot : Create a pie chart without center hole.
    stackplot : Create a stacked bar plot for categorical distributions.
    vennplot : Create a Venn diagram for set overlaps.

    Notes
    -----
    The column name (x) is displayed as a label in the center of the donut.
    The legend is automatically positioned outside the plot area and shows
    category names without edge colors.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.donutplot(data=df, x="tissue_type")

    >>> # Specify category order
    >>> cns.donutplot(data=df, x="grade", hue_order=["I", "II", "III", "IV"])
    """
    df = data[x].value_counts()
    if hue_order is None:
        hue_order = df.index
    ax = plt.gca()
    ax = df.reindex(index=hue_order).plot.pie(
        labeldistance=None,
        ax=ax,
        ylabel="",
        legend=True,
        wedgeprops={"edgecolor": "black", "linewidth": 0.3},
    )
    ax.add_patch(
        plt.Circle(
            (0, 0), radius=0.6, facecolor="white", edgecolor="black", linewidth=0.3
        )
    )
    plt.annotate(x, (0, 0), size=7, ha="center", va="center")
    cns._utils._remove_edge_from_legend_items(ax)
    cns.take_legend_out()


def survivalplot(data, duration, event, hue, hue_order=None):
    """
    Create a Kaplan-Meier survival plot with statistical comparisons.

    This function generates Kaplan-Meier survival curves comparing survival
    probabilities across groups, with automatic statistical testing and
    hazard ratio calculation.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing survival data.
    duration : str
        Column name for the time-to-event or time-to-censoring variable.
    event : str
        Column name for the event indicator (1 = event occurred, 0 = censored).
    hue : str
        Column name for the grouping variable to compare survival curves.
    hue_order : list, optional
        Order of groups from hue to display and compare. Default is None
        (uses unique values from data). If provided, should match existing groups.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    cumulativeincidenceplot : Create a cumulative incidence plot for competing risks.
    forestplot : Create a forest plot from a Cox model.

    Notes
    -----
    The function automatically performs statistical testing:

    - For two groups: Two-sided multivariate log-rank test
    - For >2 groups: Log-rank test for trend using Cox proportional hazards model

    Hazard ratio (HR) with 95% confidence interval is calculated comparing the
    last group to the first group in hue_order. HR > 1 indicates higher hazard
    (worse survival) in the last group.

    The x-axis automatically adjusts tick spacing based on the time range:

    - Range > 120: Major ticks every 24 units (months)
    - Range > 12: Major ticks every 12 units (months)
    - Range ≤ 12: Major ticks every 1 unit (years)

    Each group label shows the group name and sample size as "group (n=N)".

    Statistical results are printed to console and displayed on the plot.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.survivalplot(
    ...     data=df,
    ...     duration="time_months",
    ...     event="death",
    ...     hue="treatment",
    ...     hue_order=["control", "drug_a", "drug_b"],
    ... )
    """
    import lifelines as ll

    ax = None
    if hue_order is None or set(data[hue].unique()) != set(hue_order):
        hue_order = list(data[hue].unique())
    data[hue] = pd.Categorical(data[hue], categories=hue_order, ordered=True)
    data = data.sort_values(hue)
    kmf = ll.KaplanMeierFitter()
    for i, group in enumerate(hue_order):
        df = data[data[hue] == group]
        label = f"{group} (n={df.shape[0]})"
        kmf.fit(df[duration], df[event], label=label)
        if i != 0:
            ax = kmf.plot_survival_function(
                linewidth=1, ci_show=False, show_censors=True, censor_styles={"ms": 3}
            )
        else:
            ax = kmf.plot_survival_function(
                ax=ax,
                linewidth=1,
                ci_show=False,
                show_censors=True,
                censor_styles={"ms": 3},
            )
    plt.ylim(-0.05, 1.01)
    if ax.get_xlim()[1] > 120:
        ax.xaxis.set_major_locator(plt.MultipleLocator(24))
        plt.xlabel("Time (Months)")
    elif ax.get_xlim()[1] > 12:
        ax.xaxis.set_major_locator(plt.MultipleLocator(12))
        plt.xlabel("Time (Months)")
    else:
        ax.xaxis.set_major_locator(plt.MultipleLocator(1))
        plt.xlabel("Time (Years)")
    plt.ylabel("Overall survival probability")

    df = data[[duration, hue, event]].copy()
    df[hue] = df[hue].cat.codes

    if len(hue_order) == 2:
        logrank_test = ll.statistics.multivariate_logrank_test(
            df[duration], df[hue], df[event]
        )
        p = num2tex.num2tex(logrank_test.p_value, precision=2)
        print("   ---> P-value was determined by two-sided multivariate log-rank test.")
    else:
        cph = ll.CoxPHFitter()
        cph.fit(df, duration_col=duration, event_col=event)
        trend_test = cph.log_likelihood_ratio_test()
        p = num2tex.num2tex(trend_test.p_value, precision=2)
        print(
            "   ---> P-value was determined by two-sided multivariate log-rank test for trend."
        )

    df = data[[duration, hue, event]].copy()
    df = df[df[hue].isin([hue_order[0], hue_order[-1]])]
    df[hue] = pd.Categorical(
        df[hue], categories=[hue_order[0], hue_order[-1]], ordered=True
    )
    df[hue] = df[hue].cat.codes
    cph = ll.CoxPHFitter()
    cph.fit(df, duration_col=duration, event_col=event)
    hazard_ratio = cph.hazard_ratios_.iloc[0]
    ci1 = cph.summary["exp(coef) lower 95%"].iloc[0]
    ci2 = cph.summary["exp(coef) upper 95%"].iloc[0]
    ax.text(
        0, 0, f"HR = {hazard_ratio:.2f} ({ci1:.2f}-{ci2:.2f})\nP = " + rf"${p:.2g}$"
    )

    if ax.get_legend() is not None:
        for handle in ax.get_legend().legend_handles:
            if hasattr(handle, "set_linewidth"):
                handle.set_linewidth(1.7)


def cumulativeincidenceplot(
    data,
    duration,
    event,
    hue,
    hue_order=None,
    pvalue_position=(0, 0.5),
    show_risk_table=False,
    risk_table_rows=("At risk",),
    risk_table_ypos=-0.2,
    xticks=None,
):
    """
    Create a cumulative incidence plot for competing risks analysis.

    This function generates cumulative incidence curves using the Aalen-Johansen
    estimator for competing risks data, with automatic statistical testing and
    optional at-risk table.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing time-to-event data with competing risks.
    duration : str
        Column name for the time-to-event or time-to-censoring variable.
    event : str
        Column name for the event indicator (0 = censored, 1 = event of interest,
        2+ = competing events).
    hue : str
        Column name for the grouping variable to compare cumulative incidence curves.
    hue_order : list, optional
        Order of groups from hue to display and compare. Default is None
        (uses unique values from data). If provided, should match existing groups.
    pvalue_position : tuple of float, default: (0, 0.5)
        (x, y) coordinates in data space for placing the p-value text annotation.
    show_risk_table : bool, default: False
        Whether to display a risk table below the plot showing the number of
        subjects at risk at each time point.
    risk_table_rows : tuple of str, default: ('At risk',)
        Which rows to show in the risk table. Options include 'At risk'.
    risk_table_ypos : float, default: -0.2
        Vertical position of the risk table relative to the plot.
    xticks : array-like, optional
        Specific x-axis tick positions. If provided, adjusts x-axis limits to
        include all specified ticks.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    survivalplot : Create a Kaplan-Meier survival plot.
    forestplot : Create a forest plot from a Cox model.

    Notes
    -----
    The function uses the Aalen-Johansen estimator to calculate cumulative
    incidence functions in the presence of competing risks. Event of interest
    is assumed to be event=1.

    Censored observations (event=0) are marked with '+' symbols on the curves.

    Statistical testing requires the `cmprsk` package:

    - Uses Gray's test for comparing cumulative incidence curves across groups
    - The p-value is displayed on the plot at pvalue_position

    Each group label shows the group name and sample size (when show_risk_table=False)
    or just the group name (when show_risk_table=True).

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.cumulativeincidenceplot(
    ...     data=df,
    ...     duration="time_years",
    ...     event="event_type",
    ...     hue="treatment",
    ...     hue_order=["placebo", "drug"],
    ...     show_risk_table=True,
    ... )

    >>> # With custom tick positions
    >>> ax = cns.cumulativeincidenceplot(
    ...     data=df,
    ...     duration="months",
    ...     event="outcome",
    ...     hue="risk_group",
    ...     xticks=[0, 12, 24, 36, 48, 60],
    ... )
    """
    import lifelines as ll

    ax = None
    if hue_order is None or set(data[hue].unique()) != set(hue_order):
        hue_order = list(data[hue].unique())
    data[hue] = pd.Categorical(data[hue], categories=hue_order, ordered=True)
    data = data.sort_values(hue)
    fitters = []
    for i, group in enumerate(hue_order):
        df = data[data[hue] == group]
        label = f"{group} (n={df.shape[0]})"
        if show_risk_table:
            label = group
        fitter = ll.AalenJohansenFitter()
        fitter.fit(df[duration], df[event], label=label, event_of_interest=1)
        fitters.append(fitter)
        df = pd.merge(
            fitter.cumulative_density_.reset_index(drop=False),
            df,
            how="outer",
            left_on="event_at",
            right_on=duration,
        )
        df = df.loc[df[event] == 0].copy()
        if i == 0:
            ax = fitter.plot(linewidth=1, ci_show=False)
        else:
            ax = fitter.plot(ax=ax, linewidth=1, ci_show=False)
        line_color = ax.get_lines()[-1].get_color()
        ax.plot(df[duration], df["CIF_1"], "+", markersize=3, color=line_color)
    ax.set_ylim(-0.05, 1.01)
    ax.set_ylabel("Cumulative incidence probability")
    ax.set_xlabel("Time (Years)")
    specified_xticks = None
    if xticks is not None:
        specified_xticks = np.asarray(list(xticks), dtype=float)
        if specified_xticks.size > 0:
            ax.set_xticks(specified_xticks)
            current_xlim = ax.get_xlim()
            new_xlim = (
                min(current_xlim[0], specified_xticks.min()),
                max(current_xlim[1], specified_xticks.max()),
            )
            ax.set_xlim(new_xlim)
    try:
        from cmprsk import cmprsk

        if data[hue].nunique() > 1:
            pvalue = cmprsk.cuminc(
                data[duration], data[event], group=data[hue].cat.codes
            )
            p = num2tex.num2tex(pvalue.stats["pv"].values[0], precision=2)
            print("   ---> P-value was determined by two-sided Gray's test.")
            ax.text(pvalue_position[0], pvalue_position[1], "P = " + rf"${p:.2g}$")
    except ImportError:
        print("pip install cmprsk")

    if show_risk_table:
        rows = None if risk_table_rows is None else list(risk_table_rows)
        xticks = np.asarray(ax.get_xticks())
        xticks = xticks[
            (xticks >= ax.get_xlim()[0] - 1e-8) & (xticks <= ax.get_xlim()[1] + 1e-8)
        ]
        ll.plotting.add_at_risk_counts(
            *fitters,
            ax=ax,
            rows_to_show=rows,
            ypos=risk_table_ypos,
            xticks=xticks.tolist(),
        )
    return ax


def volcanoplot(
    data,
    x="log2FoldChange",
    y="-log10(adjp)",
    symbol="symbol",
    show_list=None,
):
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
        List of specific gene symbols to highlight and label. If None,
        automatically selects top 10 upregulated and top 10 downregulated
        genes based on combined significance and fold change.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    gseaplot : Create a GSEA dot plot.
    scatterplot : Create a general scatter plot.

    Notes
    -----
    Genes are categorized into four groups:

    - 'Up': Upregulated (log2FC > 0.5, adj.p < 0.05) and selected for labeling
    - 'Down': Downregulated (log2FC < -0.5, adj.p < 0.05) and selected for labeling
    - 'p_adj < 0.05': Significant but not selected for labeling
    - 'NS': Not significant

    When show_list=None, genes are ranked by the product of significance and
    absolute fold change, and the top 10 up/down genes are labeled.

    Gene labels are automatically positioned to avoid overlap using the
    adjustText library, with arrows pointing to the corresponding points.

    A vertical dashed line at x=0 indicates no change.

    Colors: Blue for downregulated, red for upregulated, black/grey for others.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.volcanoplot(
    ...     data=de_results, x="log2FoldChange", y="-log10(padj)", symbol="gene_name"
    ... )

    >>> # Highlight specific genes
    >>> cns.volcanoplot(
    ...     data=de_results,
    ...     x="log2FoldChange",
    ...     y="-log10(padj)",
    ...     symbol="gene_name",
    ...     show_list=["TP53", "EGFR", "KRAS"],
    ... )
    """
    import adjustText as at

    hue = "DEG"
    n_show = 10
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
                    size=6,
                    path_effects=[pe.withStroke(linewidth=1, foreground="white")],
                )
            )
    at.adjust_text(
        annotations, arrowprops={"arrowstyle": "-", "color": "black", "lw": 0.5}
    )

    ax.spines["right"].set_visible(True)
    ax.spines["top"].set_visible(True)
    ax.set_xlabel("log2(fold change)")
    ax.set_ylabel("–log10(adjusted p-value)")
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


def stripplot(
    data, x, y, size=2, showmedian=True, showmeans=False, addcount=False, **kwargs
):
    """
    Create a strip plot showing individual data points with optional summary statistics.

    This function creates a categorical scatter plot (strip plot) where all individual
    data points are displayed, optionally overlaid with median or mean markers.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the categorical variable on the x-axis.
    y : str
        Column name for the continuous variable on the y-axis.
    size : float, default: 2
        Size of individual data point markers.
    showmedian : bool, default: True
        Whether to overlay a horizontal line at the median for each category.
    showmeans : bool, default: False
        Whether to overlay a marker at the mean for each category.
    addcount : bool, default: False
        Whether to add sample size (n) labels above each category.
    **kwargs
        Additional keyword arguments passed to `seaborn.stripplot`.
        Common options include:

        - hue : str
            Column name for nested grouping and color-coding.
        - dodge : bool
            Whether to separate hue levels along the categorical axis.
        - jitter : bool or float
            Amount of jitter (horizontal displacement) to apply.
        - order : list
            Order of categories on the x-axis.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    boxplot : Create a box plot showing quartiles.
    violinplot : Create a violin plot showing distribution shape.
    scatterplot : Create a general scatter plot.

    Notes
    -----
    The median is shown as a thin black horizontal line within each category.
    The mean (when showmeans=True) is shown as a white circle with black edge.

    All individual data points are visible, making this plot suitable for
    smaller datasets or when transparency of raw data is important.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.stripplot(
    ...     data=df, x="treatment", y="response", showmedian=True, addcount=True
    ... )

    >>> # With grouping and means
    >>> cns.stripplot(
    ...     data=df, x="tissue", y="expression", hue="genotype", showmeans=True, size=3
    ... )
    """
    ax = sns.stripplot(data=data, x=x, y=y, size=size, **kwargs)
    sns.boxplot(
        data=data,
        x=x,
        y=y,
        medianprops={"visible": showmedian, "color": "black", "lw": 1},
        meanprops={
            "markerfacecolor": "white",
            "markeredgecolor": "black",
            "marker": "o",
            "markersize": size + 1,
        },
        whiskerprops={"visible": False},
        zorder=10,
        showfliers=False,
        showbox=False,
        showcaps=False,
        width=0.3,
        ax=ax,
        showmeans=showmeans,
    )
    if addcount:
        cns._utils._addcount_helper(data, x, ax)

    if ax.get_legend() is not None:
        for handle in ax.get_legend().legend_handles:
            if hasattr(handle, "set_sizes"):
                handle.set_sizes([size**2])
            elif hasattr(handle, "set_markersize"):
                handle.set_markersize(size * 2)


def histplot(**kwargs):
    """
    Create a histogram plot (wrapper around seaborn.histplot).

    This is a convenience wrapper that creates a histogram with edge colors
    removed by default for a cleaner appearance.

    Parameters
    ----------
    **kwargs
        Keyword arguments passed directly to `seaborn.histplot`.
        Common options include:

        - data : pd.DataFrame
            Input DataFrame.
        - x : str
            Column name for the variable to plot.
        - bins : int or sequence
            Number of bins or bin edges.
        - kde : bool
            Whether to overlay a kernel density estimate.
        - hue : str
            Column name for grouping and color-coding.
        - stat : str
            Statistic to compute ('count', 'frequency', 'probability', 'density').
        - multiple : str
            How to handle multiple distributions ('layer', 'dodge', 'stack', 'fill').

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    distplot : Create a distribution plot with histogram and KDE.
    kdeplot : Create a kernel density plot only.
    barplot : Create a bar plot of means.

    Notes
    -----
    Edge color is set to None by default but can be overridden by passing
    edgecolor in kwargs.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.histplot(data=df, x="age", bins=20)

    >>> # With KDE overlay
    >>> cns.histplot(data=df, x="expression", kde=True, hue="treatment")
    """
    kwargs.setdefault("edgecolor", None)
    sns.histplot(**kwargs)


def lineplot(**kwargs):
    """
    Create a line plot (wrapper around seaborn.lineplot).

    This is a convenience wrapper that creates a line plot with automatic
    aggregation and confidence intervals.

    Parameters
    ----------
    **kwargs
        Keyword arguments passed directly to `seaborn.lineplot`.
        Common options include:

        - data : pd.DataFrame
            Input DataFrame.
        - x : str
            Column name for the x-axis variable.
        - y : str
            Column name for the y-axis variable.
        - hue : str
            Column name for grouping and color-coding lines.
        - style : str
            Column name for grouping with different line styles.
        - markers : bool or list
            Whether to show markers at data points.
        - dashes : bool or list
            Whether to use different line styles for hue levels.
        - errorbar : str or tuple
            Method for computing confidence intervals ('ci', 'sd', 'se', etc.).
        - estimator : str or callable
            Aggregation function ('mean', 'median', etc.).

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    regplot : Create a regression plot with linear fit.
    scatterplot : Create a scatter plot without connecting lines.
    survivalplot : Create a Kaplan-Meier survival plot.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.lineplot(data=df, x="time", y="value")

    >>> # Multiple groups with error bands
    >>> cns.lineplot(
    ...     data=df, x="timepoint", y="expression", hue="treatment", errorbar="se"
    ... )
    """
    sns.lineplot(**kwargs)


def scatterplot(data, x, y, s=7, **kwargs):
    """
    Create a scatter plot with automatic legend size correction.

    This function creates a scatter plot with marker edge colors removed by default
    and automatically adjusts legend marker sizes to match the plot markers.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the x-axis variable.
    y : str
        Column name for the y-axis variable.
    s : float, default: 7
        Size of scatter plot markers.
    **kwargs
        Additional keyword arguments passed to `seaborn.scatterplot`.
        Common options include:

        - hue : str
            Column name for grouping and color-coding points.
        - style : str
            Column name for grouping with different marker styles.
        - size : str
            Column name for grouping with different marker sizes.
        - palette : str or list
            Color palette for hue levels.
        - alpha : float
            Transparency level (0-1) for markers.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    regplot : Create a scatter plot with regression line.
    stripplot : Create a categorical scatter plot.
    volcanoplot : Create a volcano plot for differential expression.

    Notes
    -----
    Edge color is removed (edgecolor=None) for cleaner marker appearance.
    Legend marker sizes are automatically corrected to match the plot marker size,
    which prevents the default seaborn behavior of using different sizes in the legend.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.scatterplot(data=df, x="PC1", y="PC2", s=10)

    >>> # With grouping by category
    >>> cns.scatterplot(data=df, x="UMAP1", y="UMAP2", hue="cell_type", s=5, alpha=0.7)
    """
    ax = sns.scatterplot(data=data, x=x, y=y, s=s, edgecolor=None, **kwargs)

    if ax.get_legend() is not None:
        for handle in ax.get_legend().legend_handles:
            if hasattr(handle, "set_sizes"):
                handle.set_sizes([s])
            elif hasattr(handle, "set_markersize"):
                handle.set_markersize(2 * np.sqrt(s / np.pi))


def upsetplot(sets, **kwargs):
    """
    Create an UpSet plot for visualizing set intersections.

    This function creates an UpSet plot, an advanced alternative to Venn diagrams
    for visualizing intersections among multiple sets. It displays both set sizes
    and intersection sizes in a matrix layout.

    Parameters
    ----------
    sets : dict
        Dictionary mapping set names (str) to sets or array-like collections.
        Each value is converted to a set if not already.
    **kwargs
        Additional keyword arguments passed to `upsetplot.UpSet`.
        Common options include:

        - min_subset_size : int
            Minimum intersection size to display.
        - max_subset_rank : int
            Maximum number of intersections to show.
        - sort_by : str
            How to sort intersections ('cardinality' or 'degree').
        - sort_categories_by : str
            How to sort set categories.

    Returns
    -------
    None
        This function modifies the current figure and returns nothing.

    See Also
    --------
    vennplot : Create a Venn diagram for 2-3 sets.

    Notes
    -----
    UpSet plots are more scalable than Venn diagrams and can clearly show
    intersections among many sets without the visual complexity of overlapping
    circles.

    The plot consists of:
    - A bar chart showing total set sizes (top or left)
    - A matrix showing which sets participate in each intersection
    - A bar chart showing intersection sizes

    Intersection counts are displayed with comma separators for readability.

    Examples
    --------
    >>> import cnsplots as cns
    >>> sets = {
    ...     "Set A": [1, 2, 3, 4, 5],
    ...     "Set B": [3, 4, 5, 6, 7],
    ...     "Set C": [5, 6, 7, 8, 9],
    ... }
    >>> cns.upsetplot(sets)

    >>> # Limit to larger intersections
    >>> cns.upsetplot(sets, min_subset_size=10)
    """
    import upsetplot as usp

    sets = {k: (v if isinstance(v, set) else set(v)) for k, v in sets.items()}
    memberships = []
    for item in set.union(*sets.values()):
        membership = [name for name, s in sets.items() if item in s]
        memberships.append(membership)
    data = usp.from_memberships(memberships)
    # Set default subset_size to "count" to handle non-unique groups
    kwargs.setdefault("subset_size", "count")
    upset = usp.UpSet(data, element_size=17, show_counts="{:,}", **kwargs)
    axes = upset.plot()
    plt.grid(False)
    ax_tot = axes.get("totals")
    cns.setup_ax(axes["matrix"])
    cns.setup_ax(axes["shading"])
    cns.setup_ax(axes["intersections"])
    axes["matrix"].tick_params(axis="both", which="both", length=0)
    for txt in axes["intersections"].texts:
        txt.set_size(cns.FONTSIZE_LEGEND)
    if ax_tot is not None:
        cns.setup_ax(ax_tot)
        for txt in ax_tot.texts:
            txt.set_size(cns.FONTSIZE_LEGEND)
        pos_mat = ax_tot.get_position()
        dx = 0.03
        new_pos = [pos_mat.x0 + dx, pos_mat.y0, pos_mat.width, pos_mat.height]
        ax_tot.set_position(new_pos)


def vennplot(lists, labels):
    """
    Create a Venn diagram for 2 or 3 sets.

    This function generates a Venn diagram showing overlaps between 2 or 3 sets
    using colored, semi-transparent circles with intersection counts.

    Parameters
    ----------
    lists : list of set or array-like
        List of 2 or 3 sets or array-like collections to compare. Each element
        is converted to a set if not already.
    labels : tuple or list of str
        Labels for each set, in the same order as lists.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    upsetplot : Create an UpSet plot for multiple set intersections.

    Notes
    -----
    The function automatically determines whether to create a 2-set or 3-set
    Venn diagram based on the length of the lists parameter.

    Set labels are displayed outside the circles, and intersection counts are
    shown inside overlapping regions. All circles have black edges and are
    semi-transparent (alpha=0.8) for clear visualization of overlaps.

    Font sizes:
    - Intersection counts: 6 pt
    - Set labels: 7 pt

    Examples
    --------
    >>> import cnsplots as cns
    >>> set1 = {1, 2, 3, 4, 5}
    >>> set2 = {3, 4, 5, 6, 7}
    >>> set3 = {5, 6, 7, 8, 9}
    >>> cns.vennplot([set1, set2], labels=["Group A", "Group B"])

    >>> # Three-way Venn diagram
    >>> cns.vennplot(
    ...     [set1, set2, set3], labels=["Treatment A", "Treatment B", "Treatment C"]
    ... )
    """
    import matplotlib_venn as venn

    lists = [s if isinstance(s, AbstractSet) else set(s) for s in lists]
    if len(lists) == 2:
        areas = ["10", "01", "11"]
        func = venn.venn2
        names = ["A", "B"]
        colors = sns.color_palette(n_colors=2)
    else:
        areas = ["100", "010", "001", "110", "101", "011", "111"]
        func = venn.venn3
        names = ["A", "B", "C"]
        colors = sns.color_palette(n_colors=3)
    ax = func(lists, labels, set_colors=colors, alpha=0.8)
    for area in areas:
        try:
            ax.get_label_by_id(area).set_fontsize(6)
            ax.get_patch_by_id(area).set_edgecolor("black")
            ax.get_patch_by_id(area).set_linewidth(0.5)
        except AttributeError:
            pass
    for area in names:
        ax.get_label_by_id(area).set_fontsize(7)


def confusionplot(
    data,
    x,
    y,
    add_pvalue=False,
    x_order=None,
    y_order=None,
    positive_x=None,
    positive_y=None,
    annot=True,
    cmap=plt.cm.Blues,
    pvalue_pad=1.5,
):
    """
    Create a confusion matrix heatmap with optional classification metrics.

    This function creates a confusion matrix visualization comparing predicted
    versus true labels. For binary classification (2×2 matrix), it can compute
    and display comprehensive classification metrics.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing predicted and true labels.
    x : str
        Column name containing predicted labels.
    y : str
        Column name containing true (ground truth) labels.
    add_pvalue : bool, default: False
        Whether to compute and display classification metrics. Only applicable
        for 2×2 confusion matrices. Metrics include: specificity, sensitivity,
        PPV, NPV, Cohen's kappa, Fisher's exact test p-value, and odds ratio.
    x_order : list, optional
        Explicit ordering of prediction labels (columns). Default is None
        (order of first appearance in data).
    y_order : list, optional
        Explicit ordering of true labels (rows). Default is None
        (order of first appearance in data).
    positive_x : hashable, optional
        The label to treat as 'positive' class in predictions when computing
        binary metrics. Default is None (uses last label in x_order).
    positive_y : hashable, optional
        The label to treat as 'positive' class in true labels when computing
        binary metrics. Default is None (uses last label in y_order).
    annot : bool, default: True
        Whether to display count values in each cell of the matrix.
    cmap : matplotlib colormap, default: plt.cm.Blues
        Colormap for the heatmap.
    pvalue_pad : float, default: 1.5
        Vertical padding for positioning the statistics text below the plot.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    heatmapplot : Create a general heatmap with clustering.
    rocplot : Create an ROC curve for binary classification.

    Notes
    -----
    The confusion matrix is displayed with true labels on rows and predicted
    labels on columns.

    For binary classification (when add_pvalue=True), the following metrics
    are computed and displayed:

    - **Specificity**: TN / (TN + FP)
    - **Sensitivity (Recall)**: TP / (TP + FN)
    - **PPV (Precision)**: TP / (TP + FP)
    - **NPV**: TN / (TN + FN)
    - **Cohen's kappa**: Agreement measure correcting for chance
    - **Fisher's exact test**: Two-sided p-value for association
    - **Odds ratio**: (TP × TN) / (FP × FN)

    The colorbar is removed by default for a cleaner appearance.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.confusionplot(data=df, x="predicted", y="true_label")

    >>> # Binary classification with metrics
    >>> cns.confusionplot(
    ...     data=df,
    ...     x="prediction",
    ...     y="actual",
    ...     add_pvalue=True,
    ...     x_order=["Negative", "Positive"],
    ...     y_order=["Negative", "Positive"],
    ...     positive_x="Positive",
    ...     positive_y="Positive",
    ... )
    """

    if y_order is None:
        y_order = pd.unique(data[y])
    if x_order is None:
        x_order = pd.unique(data[x])

    y_cat = pd.Categorical(data[y], categories=y_order, ordered=True)
    x_cat = pd.Categorical(data[x], categories=x_order, ordered=True)

    cm_df = pd.crosstab(y_cat, x_cat, dropna=False)

    # Plot
    ax = plt.gca()
    fig = plt.gcf()
    im = ax.imshow(cm_df.values, interpolation="nearest", cmap=cmap)
    ax.set_xlabel(x)
    ax.set_ylabel(y)

    # Ticks & tick labels
    ax.set_xticks(np.arange(len(x_order)))
    ax.set_yticks(np.arange(len(y_order)))
    ax.set_xticklabels([str(v) for v in x_order], rotation=0, ha="center")
    ax.set_yticklabels([str(v) for v in y_order], rotation=0, va="center")

    # Draw cell borders for readability
    for _, spine in ax.spines.items():
        spine.set_visible(True)

    # Optional annotations
    if annot:
        for i in range(cm_df.shape[0]):
            for j in range(cm_df.shape[1]):
                ax.text(j, i, int(cm_df.iat[i, j]), ha="center", va="center")

    # Remove colorbar to match your original style
    # (comment these two lines if you'd like to keep it)
    cb = fig.colorbar(im, ax=ax)
    cb.remove()

    # Optional stats (binary only)
    if add_pvalue:
        if cm_df.shape != (2, 2):
            raise ValueError(
                "add_pvalue=True requires a 2×2 confusion matrix. "
                "Provide y_order and x_order with exactly two labels each."
            )

        # Decide which labels are positive/negative on each axis
        pos_y = y_order[-1] if positive_y is None else positive_y
        neg_y = [lbl for lbl in y_order if lbl != pos_y][0]

        pos_x = x_order[-1] if positive_x is None else positive_x
        neg_x = [lbl for lbl in x_order if lbl != pos_x][0]

        # Extract counts in tn/fp/fn/tp layout:
        # rows = true (neg_y, pos_y), cols = pred (neg_x, pos_x)
        try:
            tn = int(cm_df.loc[neg_y, neg_x])
            fp = int(cm_df.loc[neg_y, pos_x])
            fn = int(cm_df.loc[pos_y, neg_x])
            tp = int(cm_df.loc[pos_y, pos_x])
        except KeyError as e:
            raise ValueError(
                "Could not find a required cell for stats. "
                f"Check x_order/y_order and positive_x/positive_y. Missing: {e}"
            ) from e

        # Compute stats safely (avoid zero-division)
        def _safe_div(a, b):
            return np.nan if b == 0 else a / b

        specificity = _safe_div(tn, tn + fp)
        sensitivity = _safe_div(tp, tp + fn)
        ppv = _safe_div(tp, tp + fp)
        npv = _safe_div(tn, tn + fn)
        total = tp + tn + fp + fn
        po = _safe_div(tp + tn, total)

        # Expected agreement for kappa (binary)
        pe = _safe_div((tp + fp) * (tp + fn) + (tn + fp) * (tn + fn), total**2)
        kappa = np.nan if (pe is np.nan or pe == 1) else _safe_div(po - pe, 1 - pe)

        # Fisher exact & odds ratio
        _, p_value = fisher_exact([[tp, fp], [fn, tn]])
        odds_ratio = _safe_div(tp * tn, fp * fn)

        # Overlay the stats block
        ax2 = fig.add_axes(ax.get_position(), frameon=False)
        ax2.tick_params(
            labelcolor="none", top=False, bottom=False, left=False, right=False
        )

        msg = rf"""
        Specificity: {specificity:.2f}
        Sensitivity: {sensitivity:.2f}
        PPV: {ppv:.2f}
        NPV: {npv:.2f}
        Cohen's kappa: {kappa:.2f}
        Fisher's exact test: ${num2tex.num2tex(p_value, precision=2):.2g}$
        Odds ratio: {odds_ratio:.2f}
        """
        # place just below the plot area; tweak as needed
        ax2.text(-0.25, -pvalue_pad, msg, ha="left", va="bottom")


def sankeyplot(data, x, y):
    """
    Create a Sankey diagram showing flows between two categorical variables.

    This function generates a Sankey (alluvial) diagram visualizing the flow
    and connections between categories in two variables, with ribbon widths
    proportional to frequencies.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to visualize.
    x : str
        Column name for the source (left-side) categorical variable.
    y : str
        Column name for the target (right-side) categorical variable.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    stackplot : Create a stacked bar plot for categorical distributions.
    vennplot : Create a Venn diagram for set overlaps.

    Notes
    -----
    Categories are automatically colored using the current matplotlib color cycle.
    The same color is used for a category whether it appears in x or y.

    The width of each ribbon (flow) is proportional to the number of observations
    that share that combination of x and y values.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.sankeyplot(data=df, x="initial_diagnosis", y="final_diagnosis")

    >>> # Patient flow across treatment stages
    >>> cns.sankeyplot(data=df, x="stage_1_response", y="stage_2_response")
    """
    ax = plt.gca()
    current_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    keys = np.union1d(data[x].unique(), data[y].unique())
    color_dict = dict(zip(keys, current_colors))
    helper_sankey.sankeyplot(data[x], data[y], fontsize=6, colorDict=color_dict, ax=ax)


def phyloplot(adata):
    """
    Create a phylogenetic tree plot with associated heatmaps.

    This function generates a phylogenetic tree visualization with optional
    heatmap annotations showing additional data for tree tips.

    Parameters
    ----------
    adata : AnnData
        Annotated data matrix containing tree structure and annotations.
        Should contain phylogenetic information in the appropriate format.

    Returns
    -------
    None
        This function modifies the current figure and returns nothing.

    See Also
    --------
    heatmapplot : Create a clustered heatmap.

    Notes
    -----
    This function is a wrapper around the phylogenetic plotting functionality
    in the helper_phylo module. The exact structure and requirements for the
    AnnData object depend on the phylogenetic data format.

    Examples
    --------
    >>> import cnsplots as cns
    >>> # adata should contain phylogenetic tree information
    >>> cns.phyloplot(adata)
    """
    # TODO: write examples
    helper_phylo.phyloplot(adata)


def forestplot(model):
    """
    Create a forest plot displaying effect sizes from a regression model.

    This function generates a forest plot showing hazard ratios (from Cox models)
    or AUC values (from logistic models) with confidence intervals. Optionally
    displays -log10(p-values) for Cox models.

    Parameters
    ----------
    model : CoxModel or LogisticModel
        Fitted regression model object containing results to plot. Must have:
        - `results`: DataFrame with effect sizes, confidence intervals, p-values
        - `name`: Model type ('cox' or other)
        - `hue`: Optional grouping variable name

    Returns
    -------
    None
        This function modifies the current figure and returns nothing.

    See Also
    --------
    survivalplot : Create a Kaplan-Meier survival plot.
    rocplot : Create an ROC curve plot.
    boxplot : Create a box plot with statistical comparisons.

    Notes
    -----
    **For Cox proportional hazards models (model.name='cox'):**

    - Left panel: Hazard ratios with 95% confidence intervals
    - Right panel: -log10(p-values) as horizontal bars
    - Reference line at HR = 1 (no effect)
    - Variables with HR > 1 have increased hazard (worse outcome)
    - P-value threshold line at p = 0.05 shown in right panel

    **For Logistic regression models:**

    - Single panel: AUC values with 95% confidence intervals
    - Reference line at AUC = 0.5 (no discrimination)

    When multiple hue groups are present, effect sizes are displayed with slight
    vertical offsets and different colors for each group.

    The function automatically adjusts x-axis limits if confidence intervals
    extend beyond 7 units.

    Examples
    --------
    >>> import cnsplots as cns
    >>> from cnsplots import CoxModel
    >>>
    >>> # Fit Cox model
    >>> model = CoxModel(data=df, duration="time", event="death")
    >>> model.fit(predictors=["age", "stage", "treatment"])
    >>>
    >>> # Create forest plot
    >>> cns.forestplot(model)

    >>> # With grouping variable
    >>> model = CoxModel(data=df, duration="time", event="death", hue="cohort")
    >>> model.fit(predictors=["biomarker_a", "biomarker_b"])
    >>> cns.forestplot(model)
    """
    data = model.results.copy()

    if model.name == "cox":
        y = "display_label"
        x1 = "exp(coef)"
        x2 = "log10_pvalue"
        x1err = ["exp(coef) lower_err", "exp(coef) upper_err"]
        x1label = "Hazard ratio (95% CI)"
        x2label = "–log10(p-value)"
    else:
        y = "predictor"
        x1 = "auc"
        x2 = ""
        x1err = ["lower_ci", "upper_ci"]
        x1label = "AUC (95% CI)"
        x2label = ""
    fig = plt.gcf()

    if model.name == "cox":
        gs = grid_spec.GridSpec(1, 2, width_ratios=[5, 3])
    else:
        gs = grid_spec.GridSpec(1, 1)
    ax1 = fig.add_subplot(gs[0])

    unique_hue_groups = data["hue_group"].unique()
    colors = sns.color_palette(n_colors=len(unique_hue_groups))
    color_map = dict(zip(unique_hue_groups, colors))
    unique_labels = data[y].drop_duplicates().tolist()
    y_positions = {label: i for i, label in enumerate(reversed(unique_labels))}

    max_offset = 0.15
    n_hue_groups = len(unique_hue_groups)
    offsets = (
        np.linspace(-max_offset, max_offset, n_hue_groups) if n_hue_groups > 1 else [0]
    )
    hue_offset_map = dict(zip(unique_hue_groups, offsets))

    factor = 0.5
    for hue_group in unique_hue_groups:
        hue_data = data[data["hue_group"] == hue_group]
        color = color_map[hue_group]
        y_coords = []
        x_coords = []
        x_errs_lower = []
        x_errs_upper = []
        for _, row in hue_data.iterrows():
            y_pos = y_positions[row[y]] + hue_offset_map[hue_group]
            y_coords.append(y_pos)
            x_coords.append(row[x1])
            x_errs_lower.append(row[x1err[0]])
            x_errs_upper.append(row[x1err[1]])

        ax1.errorbar(
            x_coords,
            y_coords,
            xerr=[x_errs_lower, x_errs_upper],
            fmt="s",
            color=color,
            markeredgewidth=0.8,
            elinewidth=0.8,
            capsize=2,
            markersize=3,
            label=hue_group,
        )
        if max(x_errs_upper) + max(x_coords) > 7:
            factor = 1
            ax1.set_xlim(0, 7)
    ax1.set_yticks(list(y_positions.values()))
    ax1.set_yticklabels(list(y_positions.keys()))
    ax1.set_ylim(-0.5, len(unique_labels) - 0.5)
    ax1.set_xlabel(x1label)
    if len(unique_hue_groups) > 1:
        ax1.legend(title=model.hue, loc="lower right")
    if model.name == "cox":
        ax1.axvline(x=1, color="red", linestyle="--", linewidth=0.8)
        ax1.xaxis.set_major_locator(plt.MultipleLocator(factor))
    else:
        ax1.axvline(x=0.5, color="red", linestyle="--", linewidth=0.8)

    if model.name == "cox":
        ax2 = fig.add_subplot(gs[1])
        bar_width = 0.8 / len(unique_hue_groups) if len(unique_hue_groups) > 1 else 0.6
        for i, label in enumerate(reversed(unique_labels)):
            label_data = data[data[y] == label]
            for j, hue_group in enumerate(unique_hue_groups):
                hue_data = label_data[label_data["hue_group"] == hue_group]
                if len(hue_data) > 0:
                    color = color_map[hue_group]
                    if len(unique_hue_groups) > 1:
                        bar_pos = i + (j - (len(unique_hue_groups) - 1) / 2) * bar_width
                    else:
                        bar_pos = i
                    ax2.barh(
                        bar_pos,
                        hue_data[x2].iloc[0],
                        height=bar_width,
                        color=color,
                        edgecolor=None,
                    )

        ax2.set_yticks(list(range(len(unique_labels))))
        ax2.set_yticklabels([])
        ax2.set_xlabel(x2label)
        ax2.axvline(
            x=-np.log10(0.05), color="red", linestyle="--", linewidth=0.8, alpha=0.7
        )
        ax2.set_ylim(-0.5, len(unique_labels) - 0.5)
        ax2.xaxis.set_major_locator(plt.MultipleLocator(1))


def ridgeplot(data, x, y):
    """
    Create a ridge plot (joyplot) showing distributions across categories.

    This function generates a ridge plot with overlapping kernel density curves
    for a continuous variable across multiple categories, creating a "mountain range"
    visualization effect.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to visualize.
    x : str
        Column name for the continuous variable to plot as distributions.
    y : str
        Column name for the categorical variable determining separate curves.
        Each unique value creates one ridge.

    Returns
    -------
    None
        This function modifies the current figure and returns nothing.

    See Also
    --------
    kdeplot : Create a kernel density plot.
    violinplot : Create a violin plot showing distribution shapes.
    distplot : Create a distribution plot with histogram and KDE.

    Notes
    -----
    The ridge plots are stacked vertically with overlapping to create a compact
    visualization of many distributions. Each category is represented by a filled
    density curve with a color from the 'viridis' colormap.

    The curves are partially transparent and overlap (negative hspace) to create
    the characteristic ridge plot appearance.

    Category labels are displayed to the left of each ridge.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.ridgeplot(data=df, x="expression", y="tissue_type")

    >>> # Time series data
    >>> cns.ridgeplot(data=df, x="temperature", y="month")
    """
    countries = data[y].unique()
    colors = cns._utils._get_hex_colors_from_colorbar("viridis", len(countries))
    gs = grid_spec.GridSpec(len(countries), 1)
    fig = plt.gcf()
    ax_objs = []
    for i, country in enumerate(countries):
        x_v = np.array(data[data[y] == country][x])

        # creating new axes object
        ax_objs.append(fig.add_subplot(gs[i : i + 1, 0:]))

        # plotting the distribution
        ax = sns.kdeplot(x=x_v, ax=ax_objs[-1], color="#f0f0f0", fill=False)
        l1 = ax.lines[0]
        x1 = l1.get_xydata()[:, 0]
        y1 = l1.get_xydata()[:, 1]
        ax.fill_between(x1, y1, alpha=1, color=colors[i])
        ax.set_ylabel("")

        # setting uniform x and y lims
        ax_objs[-1].set_xlim(data[x].min(), data[x].max())

        # make background transparent
        rect = ax_objs[-1].patch
        rect.set_alpha(0)

        # remove borders, axis ticks, and labels
        ax_objs[-1].set_yticks([])
        if i == len(countries) - 1:
            ax_objs[-1].set_xlabel(x)
        else:
            ax_objs[-1].set_xticks([])
        spines = ["top", "right", "left", "bottom"]
        for s in spines:
            ax_objs[-1].spines[s].set_visible(False)
        ax_objs[-1].text(-0.02, 0, country, ha="right")
    gs.update(hspace=-0.5)


def slopeplot(data, x, y, hue):
    """
    Create a slope plot showing paired changes between two conditions.

    This function generates a slope plot (also called slope graph) that visualizes
    changes in a continuous variable between two time points or conditions for
    multiple subjects or groups.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing paired observations.
    x : str
        Column name for the categorical variable defining the two conditions
        or time points being compared.
    y : str
        Column name for the continuous variable to plot.
    hue : str
        Column name for the grouping variable. Must have exactly two unique values
        representing the two conditions to compare.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    lineplot : Create a line plot for time series.
    scatterplot : Create a scatter plot.
    regplot : Create a regression plot.

    Notes
    -----
    Each line connects paired observations (same x value) between the two hue
    conditions. Lines are colored based on direction of change:

    - Blue: Increase (left to right)
    - Red: Decrease (left to right)

    Points are colored to match their respective hue group (blue for first,
    red for second).

    The slope and color of each line make it easy to see the magnitude and
    direction of change for each subject/group.

    Examples
    --------
    >>> import cnsplots as cns
    >>> # Compare before/after measurements for multiple patients
    >>> cns.slopeplot(
    ...     data=df,
    ...     x="patient_id",
    ...     y="tumor_size",
    ...     hue="timepoint",  # e.g., 'baseline' and 'week_12'
    ... )

    >>> # Compare two treatments across sites
    >>> cns.slopeplot(data=df, x="site", y="response_rate", hue="treatment")
    """
    # https://cduvallet.github.io/posts/2018/03/slopegraphs-in-python
    red = palettable.colorbrewer.qualitative.Set1_9.hex_colors[0]
    blue = palettable.colorbrewer.qualitative.Set1_9.hex_colors[1]
    hues = data[hue].unique()

    ax = plt.gca()

    sites = []
    i = 1.0
    for site, subdf in data.groupby(x):
        sites.append(site)
        h = subdf[subdf[hue] == hues[0]][y].values
        d = subdf[subdf[hue] == hues[1]][y].values

        x1 = i - 0.2
        x2 = i + 0.2

        line_colors = (h - d) > 0
        line_colors = [blue if j else red for j in line_colors]

        alphas = [0.4] * len(line_colors)

        for hi, di, ci, ai in zip(h, d, line_colors, alphas):
            ax.plot([x1, x2], [hi, di], c=ci, alpha=ai)

        ax.scatter(len(h) * [x1], h, c=blue, s=10, lw=0.5, label=hues[0])
        ax.scatter(len(d) * [x2], d, c=red, s=10, lw=0.5, label=hues[1])

        i += 1

    ax.set_xticks(list(1 + np.arange(len(sites))))
    _ = ax.set_xticklabels(sites)

    handles, labels = ax.get_legend_handles_labels()
    lgd = ax.legend(
        handles[0:2],
        labels[0:2],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.1),
        ncol=2,
    )
    for handle in lgd.legend_handles:
        handle.set_sizes([12])


def qqplot(data, x, **kwargs):
    """
    Create a quantile-quantile (Q-Q) plot to assess normality.

    This function generates a Q-Q plot comparing the quantiles of a variable
    against the theoretical quantiles of a normal distribution to assess whether
    the data follows a normal distribution.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to plot.
    x : str
        Column name for the variable to test for normality.
    **kwargs
        Additional keyword arguments passed to `statsmodels.api.qqplot`.
        Common options include:

        - line : str
            Type of reference line ('45', 's', 'r', 'q', or None).
        - fit : bool
            Whether to fit a regression line.
        - dist : scipy.stats distribution
            Theoretical distribution to compare against (default is normal).

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    distplot : Create a distribution plot with histogram and KDE.
    kdeplot : Create a kernel density plot.

    Notes
    -----
    If data points fall approximately along the 45-degree reference line, the
    data is approximately normally distributed.

    Deviations from the line indicate departures from normality:
    - S-shaped pattern: Skewed distribution
    - Curved pattern: Heavy or light tails compared to normal distribution

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.qqplot(data=df, x="residuals")

    >>> # With custom distribution
    >>> from scipy import stats
    >>> cns.qqplot(data=df, x="values", dist=stats.t, distargs=(10,))
    """
    import statsmodels.api as sm

    ax = plt.gca()
    sm.qqplot(
        data[x],
        ax=ax,
        markerfacecolor="black",
        markeredgewidth=0,
        markersize=3,
        **kwargs,
    )


def rocplot(data, true_label_col, pred_prob_cols):
    """
    Create a receiver operating characteristic (ROC) curve plot.

    This function generates ROC curves for one or more binary classifiers,
    showing the trade-off between true positive rate and false positive rate
    at various classification thresholds.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing true labels and predicted probabilities.
    true_label_col : str
        Column name for the true binary labels (0 or 1).
    pred_prob_cols : str or list of str
        Column name(s) for predicted probabilities. Can be a single column name
        or a list of column names to compare multiple models.

    Returns
    -------
    None
        This function modifies the current axes and returns nothing.

    See Also
    --------
    confusionplot : Create a confusion matrix heatmap.
    forestplot : Create a forest plot from a logistic model.

    Notes
    -----
    The ROC curve plots the True Positive Rate (Sensitivity) on the y-axis
    versus the False Positive Rate (1 - Specificity) on the x-axis.

    The area under the ROC curve (AUC) is calculated and displayed in the legend
    for each classifier:

    - AUC = 1.0: Perfect classifier
    - AUC = 0.5: Random classifier (diagonal reference line)
    - AUC < 0.5: Worse than random

    A diagonal dashed line represents the performance of a random classifier.

    Legend line width is automatically increased to 1.7 for better visibility.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.rocplot(
    ...     data=df, true_label_col="disease", pred_prob_cols="model_probability"
    ... )

    >>> # Compare multiple models
    >>> cns.rocplot(
    ...     data=df,
    ...     true_label_col="outcome",
    ...     pred_prob_cols=["model_a_prob", "model_b_prob", "model_c_prob"],
    ... )
    """
    if isinstance(pred_prob_cols, str):
        pred_prob_cols = [pred_prob_cols]

    for col in pred_prob_cols:
        fpr, tpr, _ = roc_curve(data[true_label_col], data[col])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, label=f"{col} (AUC={roc_auc:.2f})", linewidth=1)

    plt.plot(
        [0, 1], [0, 1], color="black", linestyle="--", linewidth=0.8, dashes=(8, 5)
    )
    plt.xlim([-0.02, 1.02])
    plt.ylim([-0.02, 1.02])
    plt.xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    ax = plt.gca()
    ax.legend(loc="lower right")

    if ax.get_legend() is not None:
        for handle in ax.get_legend().legend_handles:
            if hasattr(handle, "set_linewidth"):
                handle.set_linewidth(1.7)


def gseaplot(
    data, y, color="NES", cutoff=0.05, cmap="BuRd_custom", top_term=20, size=1.8
):
    """
    Create a Gene Set Enrichment Analysis (GSEA) dot plot.

    This function generates a dot plot visualizing GSEA results, with gene sets
    on the y-axis, normalized enrichment scores on the x-axis, and dot size/color
    representing statistical significance and enrichment strength.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing GSEA results. Typically output from
        gseapy or similar GSEA analysis tools.
    y : str
        Column name for gene set names or pathway names (y-axis labels).
    color : str, default: 'NES'
        Column name for the variable to use for dot color encoding.
        Typically 'NES' (Normalized Enrichment Score) or adjusted p-value.
    cutoff : float, default: 0.05
        Significance cutoff for filtering gene sets. Gene sets with adjusted
        p-value < cutoff are displayed.
    cmap : str, default: 'BuRd_custom'
        Colormap for encoding the color variable.
    top_term : int, default: 20
        Maximum number of top gene sets to display.
    size : float, default: 1.8
        Scaling factor for dot sizes.

    Returns
    -------
    None
        This function modifies the current figure and returns nothing.

    See Also
    --------
    volcanoplot : Create a volcano plot for differential expression.
    dotplot : Create a dot plot matrix.

    Notes
    -----
    This function is a wrapper around `gseapy.dotplot` with customized styling
    and layout adjustments for publication-quality figures.

    The plot typically shows:
    - Dot position along x-axis: Normalized Enrichment Score (NES)
    - Dot size: Statistical significance (-log10 p-value or similar)
    - Dot color: Enrichment strength or significance

    Positive NES indicates enrichment in the first phenotype, negative NES
    indicates enrichment in the second phenotype (for two-class comparisons).

    The colorbar and legend are automatically adjusted for optimal positioning.

    Examples
    --------
    >>> import cnsplots as cns
    >>> # GSEA results from gseapy
    >>> cns.gseaplot(data=gsea_results, y="Term", color="NES", top_term=15, cutoff=0.05)

    >>> # Color by adjusted p-value instead
    >>> cns.gseaplot(
    ...     data=gsea_results,
    ...     y="Term",
    ...     color="Adjusted P-value",
    ...     cmap="viridis",
    ...     top_term=30,
    ... )
    """
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
    pos = cbar_ax.get_position()
    cbar_ax.set_position([pos.x0 + 0.1, pos.y0 - 0.1, pos.width, pos.height])
    cbar_ax.yaxis.set_label_position("left")
    cbar_ax.yaxis.labelpad = 1
    cbar_ax.set_ylabel("")
    legend = ax.get_legend()
    handles = legend.legend_handles
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
