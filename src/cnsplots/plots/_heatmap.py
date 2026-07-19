from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd
    from anndata import AnnData
    from matplotlib.axes import Axes
    from PyComplexHeatmap import DotClustermapPlotter

    from cnsplots.helpers._heatmap import ClusterMapPlotterNew

import matplotlib as mpl
import matplotlib.colorbar  # noqa: F401  # ensure submodule is importable for isinstance checks
import matplotlib.legend  # noqa: F401  # ensure submodule is importable for isinstance checks
import matplotlib.pyplot as plt
import num2tex
import numpy as np
import pandas as pd
import PyComplexHeatmap as pch
import seaborn as sns
from natsort import natsort_keygen
from scipy.stats import fisher_exact

import cnsplots as cns
import cnsplots.helpers._heatmap as helper_heatmap
from cnsplots._validation import (
    validate_adata_layer,
    validate_adata_obs_columns,
    validate_adata_var_columns,
    validate_anndata,
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
)


def _legend_fontsize() -> int | float:
    legend_fontsize = cns.settings.legend_fontsize
    if legend_fontsize is None:
        return cns.settings.title_fontsize
    return legend_fontsize


def _style_plotter_colorbars(cbars: list[Any]) -> None:
    font_family = mpl.rcParams.get("font.family")
    legend_fontsize = _legend_fontsize()
    for cbar in cbars:
        if not isinstance(cbar, mpl.colorbar.Colorbar):
            continue
        cbar.outline.set_linewidth(0.3)
        cbar.ax.tick_params(
            size=0,
            labelsize=legend_fontsize,
            colors=cns.settings.ytick_color,
            pad=cns.settings.ytick_major_pad,
        )
        if font_family:
            for tick_label in cbar.ax.get_yticklabels():
                tick_label.set_fontfamily(font_family)
        cbar.ax.yaxis.set_label_position("left")
        pos = cbar.ax.get_position()
        cbar.ax.set_position([pos.x0, pos.y0, pos.width * 0.4, pos.height])


def heatmapplot(
    adata: AnnData,
    layer: str | None = None,
    row_annotation: list[str] | None = None,
    col_annotation: list[str] | None = None,
    row_cluster: bool = False,
    col_cluster: bool = False,
    row_split: str | int | None = None,
    col_split: str | int | None = None,
    cmap: str | None = None,
    label: str = "value",
    xlabel: str = "xlabel",
    ylabel: str = "ylabel",
    legend_hpad: int = 2,
    legend_vpad: int = 0,
    linewidth: float = 0,
    colors: dict[str, dict[str, str]] | None = None,
    rasterized: bool = True,
    xticklabels_rotation: int = 45,
    xticklabels_fontsize: int = 7,
    yticklabels_fontsize: int = 7,
    xlabel_labelpad: float = 5,
    ylabel_labelpad: float = 3,
    **kwargs: Any,
) -> ClusterMapPlotterNew:
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
    cmap : str, optional
        Colormap for the heatmap. Can be categorical (Set1, Set2, Ecotyper1, Dark2,
        Ecotyper2, Set3) or continuous (parula, gnuplot, bwr, hot).
    label : str, default: 'value'
        Label for the colorbar.
    xlabel : str, default: 'xlabel'
        Label for the x-axis.
    ylabel : str, default: 'ylabel'
        Label for the y-axis.
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
    xlabel_labelpad : float, default: 5
        Padding between the x-axis label and the tick labels.
    ylabel_labelpad : float, default: 3
        Padding between the y-axis label and the tick labels.
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
    # Validate inputs
    validate_anndata(adata, "adata", "heatmapplot")

    # Validate layer if provided
    if layer is not None:
        validate_adata_layer(adata, layer, "heatmapplot")

    # Validate row annotations
    if row_annotation is not None:
        validate_adata_obs_columns(adata, row_annotation, "heatmapplot")

    # Validate column annotations
    if col_annotation is not None:
        validate_adata_var_columns(adata, col_annotation, "heatmapplot")

    # Validate row split if it's a string
    if isinstance(row_split, str):
        validate_adata_obs_columns(adata, row_split, "heatmapplot")

    # Validate column split if it's a string
    if isinstance(col_split, str):
        validate_adata_var_columns(adata, col_split, "heatmapplot")

    if cmap is None:
        cmap = cns.settings.palette_seq
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
            series = df[annot]
            is_numeric_annotation = pd.api.types.is_numeric_dtype(
                series
            ) and not pd.api.types.is_bool_dtype(series)

            if not is_numeric_annotation:
                if series.isna().any():
                    rc_dict[annot] = pch.anno_label(
                        series,
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
                        unique_vals_str = {str(v) for v in series.dropna().unique()}
                        color_keys_str = {str(k) for k in annot_colors}
                        if not unique_vals_str.issubset(color_keys_str):
                            annot_colors = None
                    rc_dict[annot] = pch.anno_simple(
                        series.sort_values(key=natsort_keygen()),
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
                    series,
                    cmap=cont_palettes[cont_counter],
                    height=3,
                    rasterized=True,
                    linewidth=0,
                )
                cont_counter += 1
                cbar_titles.append(annot)
        return rc_dict

    left_annotation: Any = None
    top_annotation: Any = None
    if row_annotation is not None:
        rc_dict = _annot_helper(adata.obs, row_annotation)
        left_annotation = pch.HeatmapAnnotation(
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
        top_annotation = pch.HeatmapAnnotation(axis=1, verbose=0, **ca_dict)

    row_split_val: Any = row_split
    col_split_val: Any = col_split
    if row_split is not None and not isinstance(row_split, int):
        row_split_val = adata.obs[row_split]
    if col_split is not None and not isinstance(col_split, int):
        col_split_val = adata.var[col_split]

    df = adata.to_df() if layer is None else adata.to_df(layer=layer)
    cmp = helper_heatmap.ClusterMapPlotterNew(
        data=df,
        left_annotation=left_annotation,
        top_annotation=top_annotation,
        row_cluster=row_cluster,
        col_cluster=col_cluster,
        row_split=row_split_val,
        col_split=col_split_val,
        cmap=cmap,
        rasterized=rasterized,
        label=label,
        xlabel=xlabel,
        ylabel=ylabel,
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
        ylabel_kws={"labelpad": ylabel_labelpad},
        xlabel_kws={"labelpad": xlabel_labelpad},
        verbose=0,
        row_names_side="left" if left_annotation is None else "right",
        xticklabels=True,
        yticklabels=True,
        **kwargs,
    )

    plt.setp(
        cmp.heatmap_axes[-1, 0].get_xticklabels(), rotation_mode="anchor", ha="right"
    )

    cmp.ax_heatmap.set_axis_on()
    sns.despine(ax=cmp.ax_heatmap, bottom=False, left=False, top=False, right=False)
    for s in ["top", "bottom", "left", "right"]:
        cmp.ax_heatmap.spines[s].set_linewidth(cns.settings.axes_linewidth)

    _style_plotter_colorbars(cmp.cbars)
    helper_heatmap._capture_detached_colorbar_layout(cmp)
    return cmp


def dotplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    size: str,
    value: str | None = None,
    legend_width: int = 20,
    legend_hpad: int = 10,
    legend_vpad: int = 0,
    xticklabels_rotation: int = 45,
    xticklabels_fontsize: int = 7,
    yticklabels_fontsize: int = 7,
    **kwargs: Any,
) -> DotClustermapPlotter:
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
    # Validate inputs
    validate_dataframe(data, "data", "dotplot")
    columns_to_check = [x, y, color, size]
    if value is not None:
        columns_to_check.append(value)
    validate_columns_exist(data, columns_to_check, "dotplot")
    validate_dataframe_not_empty(data, "dotplot")

    cmap = kwargs.pop("cmap", "gnuplot")
    plotter_kwargs = {
        "data": data,
        "x": x,
        "y": y,
        "c": color,
        "s": size,
        "row_cluster": False,
        "col_cluster": False,
        "show_rownames": True,
        "show_colnames": True,
        "verbose": 0,
        "cmap": cmap,
        "grid": False,
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
    plotter_kwargs.setdefault("plot_legend", plotter_kwargs.get("legend", True))
    cmp = helper_heatmap.DotClustermapPlotterNew(**plotter_kwargs)
    cmp.cbars = getattr(cmp, "cbars", [])

    hm_ax = cmp.heatmap_axes[-1, 0]
    cmp.hm_ax = hm_ax
    cmp.colorbar = next(
        (cbar for cbar in cmp.cbars if isinstance(cbar, mpl.colorbar.Colorbar)),
        None,
    )
    cmp.dot_legend = next(
        (legend for legend in cmp.cbars if isinstance(legend, mpl.legend.Legend)),
        None,
    )
    cmp.cbar_ax = None if cmp.colorbar is None else cmp.colorbar.ax
    cmp.legend_ax = None if cmp.dot_legend is None else cmp.dot_legend.axes

    for ax in [cmp.ax_heatmap, hm_ax]:
        ax.minorticks_off()
        ax.tick_params(
            axis="both",
            which="major",
            direction="out",
            length=1.5,
            width=cns.settings.axes_linewidth,
            bottom=True,
            left=True,
            top=False,
            right=False,
        )
    plt.setp(hm_ax.get_xticklabels(), rotation_mode="anchor", ha="right")

    cmp.ax_heatmap.set_axis_on()
    for ax in cmp.heatmap_axes.flat:
        ax.grid(False)
    cmp.ax_heatmap.grid(False)
    sns.despine(ax=cmp.ax_heatmap, top=True, right=True, bottom=False, left=False)
    for s in ["bottom", "left"]:
        cmp.ax_heatmap.spines[s].set_linewidth(cns.settings.axes_linewidth)

    _style_plotter_colorbars(cmp.cbars)
    return cmp


def confusionplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    add_pvalue: bool = False,
    x_order: list[str] | None = None,
    y_order: list[str] | None = None,
    positive_x: str | None = None,
    positive_y: str | None = None,
    annot: bool = True,
    cmap: Any = "Blues",
    pvalue_x_pad: float = 0.25,
    pvalue_y_pad: float = 1.5,
) -> Axes:
    """
    Create a confusion matrix heatmap with optional classification metrics.

    This function creates a confusion matrix visualization comparing predicted
    versus true labels. For binary classification (2x2 matrix), it can compute
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
        for 2x2 confusion matrices.
    x_order : list, optional
        Explicit ordering of prediction labels (columns).
    y_order : list, optional
        Explicit ordering of true labels (rows).
    positive_x : hashable, optional
        The label to treat as 'positive' class in predictions.
    positive_y : hashable, optional
        The label to treat as 'positive' class in true labels.
    annot : bool, default: True
        Whether to display count values in each cell of the matrix.
    cmap : matplotlib colormap, default: plt.cm.Blues
        Colormap for the heatmap.
    pvalue_x_pad : float, default: 0.25
        Horizontal padding for positioning the statistics text to the left of
        the plot. Larger values move the statistics block farther left.
    pvalue_y_pad : float, default: 1.5
        Vertical padding for positioning the statistics text below the plot.
        Larger values move the statistics block farther down.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    heatmapplot : Create a general heatmap with clustering.
    rocplot : Create an ROC curve for binary classification.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.confusionplot(data=df, x="predicted", y="true_label")
    >>> ax.set_title("Confusion Matrix")

    >>> # Binary classification with metrics
    >>> ax = cns.confusionplot(
    ...     data=df,
    ...     x="prediction",
    ...     y="actual",
    ...     add_pvalue=True,
    ...     pvalue_x_pad=0.4,
    ...     pvalue_y_pad=1.8,
    ...     x_order=["Negative", "Positive"],
    ...     y_order=["Negative", "Positive"],
    ...     positive_x="Positive",
    ...     positive_y="Positive",
    ... )
    """
    # Validate inputs
    validate_dataframe(data, "data", "confusionplot")
    validate_columns_exist(data, [x, y], "confusionplot")
    validate_dataframe_not_empty(data, "confusionplot")

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
                cell_value = cm_df.iat[i, j]
                if pd.isna(cell_value):
                    raise ValueError(
                        f"[confusionplot] Confusion matrix contains NaN at position [{i},{j}]. "
                        "All values must be valid numbers."
                    )
                r, g, b, _ = im.cmap(im.norm(cell_value))
                ax.text(
                    j,
                    i,
                    str(int(cell_value)),
                    ha="center",
                    va="center",
                    color=cns.utils._annotation_text_color((r, g, b, 1.0)),
                )

    # Remove colorbar to match your original style
    cb = fig.colorbar(im, ax=ax)
    cb.remove()

    # Optional stats (binary only)
    if add_pvalue:
        if cm_df.shape != (2, 2):
            raise ValueError(
                "add_pvalue=True requires a 2x2 confusion matrix. "
                "Provide y_order and x_order with exactly two labels each."
            )

        # Decide which labels are positive/negative on each axis
        pos_y = y_order[-1] if positive_y is None else positive_y
        neg_y_list = [lbl for lbl in y_order if lbl != pos_y]
        if not neg_y_list:
            raise ValueError(
                f"[confusionplot] Could not find negative label in y_order. "
                f"positive_y='{pos_y}', y_order={list(y_order)}"
            )
        neg_y = neg_y_list[0]

        pos_x = x_order[-1] if positive_x is None else positive_x
        neg_x_list = [lbl for lbl in x_order if lbl != pos_x]
        if not neg_x_list:
            raise ValueError(
                f"[confusionplot] Could not find negative label in x_order. "
                f"positive_x='{pos_x}', x_order={list(x_order)}"
            )
        neg_x = neg_x_list[0]

        # Extract counts in tn/fp/fn/tp layout
        try:
            tn_val = cm_df.loc[neg_y, neg_x]
            fp_val = cm_df.loc[neg_y, pos_x]
            fn_val = cm_df.loc[pos_y, neg_x]
            tp_val = cm_df.loc[pos_y, pos_x]
        except KeyError as e:
            raise ValueError(
                "[confusionplot] Could not find a required cell for stats. "
                f"Check x_order/y_order and positive_x/positive_y. Missing: {e}"
            ) from e

        # Validate no NaN values
        for name, val in [
            ("TN", tn_val),
            ("FP", fp_val),
            ("FN", fn_val),
            ("TP", tp_val),
        ]:
            if pd.isna(val):
                raise ValueError(
                    f"[confusionplot] {name} cell contains NaN. All confusion matrix cells "
                    "must have valid numeric values for statistics computation."
                )

        tn = int(tn_val)
        fp = int(fp_val)
        fn = int(fn_val)
        tp = int(tp_val)

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
        try:
            _, p_value = fisher_exact([[tp, fp], [fn, tn]])
        except (ValueError, RuntimeError) as e:
            raise ValueError(
                "[confusionplot] Fisher's exact test failed. Ensure confusion matrix "
                f"has valid counts. Details: {e}"
            ) from e

        odds_ratio = _safe_div(tp * tn, fp * fn)

        # Overlay the stats block
        pos = ax.get_position()
        ax2 = fig.add_axes((pos.x0, pos.y0, pos.width, pos.height), frameon=False)
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
        ax2.text(-pvalue_x_pad, -pvalue_y_pad, msg, ha="left", va="bottom")

    return ax
