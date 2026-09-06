from __future__ import annotations

import logging
from numbers import Real
from typing import Any, Literal

import matplotlib as mpl
import matplotlib.patches  # noqa: F401  # ensure submodule is importable for isinstance checks
import matplotlib.pyplot as plt
import num2tex
import numpy as np
import pandas as pd
import scipy as sp
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.typing import ColorType

import cnsplots._utils as utils
from cnsplots._utils import _legend_fontsize
from cnsplots._validation import (
    validate_column_exists,
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
    validate_no_nulls,
)

logger = logging.getLogger(__name__)


def boxplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    pairs: list[tuple[str, str]] | None = None,
    showoutliers: bool = False,
    add_count: bool = False,
    whis: float | tuple[float, float] = 1.5,
    *,
    hue: str | None = None,
    order: list[str] | None = None,
    hue_order: list[str] | None = None,
    test: Literal["Mann-Whitney", "t-test_welch"] = "Mann-Whitney",
    p_adjust: Literal["bonferroni", "holm", "fdr_bh", "fdr_by"] | None = None,
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes:
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
        using Mann-Whitney U test.
    showoutliers : bool, default: False
        Whether to display outlier points beyond the whiskers.
    add_count : bool, default: False
        Append sample sizes to the categorical axis tick labels. Counts include
        rows with non-missing x, y, and hue (when used), restricted to ``order``
        and ``hue_order``. Hue levels are pooled within each category. The same
        complete rows are used for rendering; hidden outliers still count.
    whis : float or tuple of float, default: 1.5
        The proportion of the IQR past the low and high quartiles to extend the
        plot whiskers.
    hue : str, optional
        Column name for grouping boxes within each category.
    order : list of str, optional
        Order of categories along the categorical axis.
    hue_order : list of str, optional
        Order of hue levels.
    test : {'Mann-Whitney', 't-test_welch'}, default: 'Mann-Whitney'
        Statistical test used for pairwise comparisons.
    p_adjust : {'bonferroni', 'holm', 'fdr_bh', 'fdr_by'}, optional
        Multiple-comparison correction applied across the resolved pairs.
    ax : matplotlib.axes.Axes, optional
        Axes on which to draw the plot. Defaults to the current Axes.
    **kwargs
        Additional keyword arguments passed to `seaborn.boxplot`.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    violinplot : Create a violin plot showing full distribution shape.
    stripplot : Create a strip plot showing all individual points.
    barplot : Create a bar plot showing means with error bars.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.boxplot(
    ...     data=df,
    ...     x="treatment",
    ...     y="response",
    ...     pairs=[("control", "treated")],
    ...     test="t-test_welch",
    ...     p_adjust="holm",
    ...     showoutliers=True,
    ... )
    >>> ax.set_title("Treatment Response")
    """
    # Validate inputs
    validate_dataframe(data, "data", "boxplot")
    columns = [x, y] if hue is None else [x, y, hue]
    validate_columns_exist(data, columns, "boxplot")
    validate_dataframe_not_empty(data, "boxplot")
    validate_no_nulls(data, columns, "boxplot", allow_partial=True)
    utils._validate_statistical_options(
        test,
        p_adjust,
        valid_tests=("Mann-Whitney", "t-test_welch"),
    )

    if "addcount" in kwargs:
        raise TypeError(
            "boxplot() got an unexpected keyword argument 'addcount'; "
            "use 'add_count' instead"
        )

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
    plotting: dict[str, Any] = {
        "data": data,
        "x": x,
        "y": y,
        "hue": hue,
        "order": order,
        "hue_order": hue_order,
    }
    plotting.update(args)
    plotting.update(kwargs)
    data = utils._prepare_categorical_plot_data(plotting)
    if ax is None:
        ax = plt.gca()
    ax = sns.boxplot(ax=ax, **plotting)

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

    utils._remove_edge_from_legend_items(ax)
    whis_str = (
        "minimum and maximum values"
        if whis == (0, 100)
        else (
            f"{whis} times the interquartile range"
            if isinstance(whis, (int, float))
            else str(whis)
        )
    )
    logger.info(
        "Boxplots represent the median and bottom and upper quartiles; whiskers"
        f" correspond to the {whis_str}."
    )
    if pairs is not None:
        utils._p_value_helper(
            test,
            data,
            ax,
            plotting,
            pairs,
            p_adjust=p_adjust,
        )

    if add_count:
        axis = "y" if plotting["orient"] == "h" else "x"
        utils._add_count_helper(data, plotting[axis], ax, axis=axis)

    return ax


def violinplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    pairs: list[tuple[str, str]] | None = None,
    width: float = 0.6,
    add_box: bool = True,
    add_count: bool = False,
    *,
    box_color: ColorType | None = "white",
    hue: str | None = None,
    order: list[str] | None = None,
    hue_order: list[str] | None = None,
    test: Literal["Mann-Whitney", "t-test_welch"] = "Mann-Whitney",
    p_adjust: Literal["bonferroni", "holm", "fdr_bh", "fdr_by"] | None = None,
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes:
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
        List of pairs of category names from x for pairwise statistical comparisons.
    width : float, default: 0.6
        Width of each violin body.
    add_box : bool, default: True
        Whether to overlay a narrow box plot inside each violin.
    add_count : bool, default: False
        Append sample sizes to the categorical axis tick labels. Counts include
        rows with non-missing x, y, and hue (when used), restricted to ``order``
        and ``hue_order``. Hue levels are pooled within each category. The same
        complete rows are used for rendering.
    box_color : matplotlib color or None, default: "white"
        Color of the embedded box plots. Set to ``None`` to color boxes according
        to *hue*.
    hue : str, optional
        Column name for grouping violins within each category.
    order : list of str, optional
        Order of categories along the categorical axis.
    hue_order : list of str, optional
        Order of hue levels.
    test : {'Mann-Whitney', 't-test_welch'}, default: 'Mann-Whitney'
        Statistical test used for pairwise comparisons.
    p_adjust : {'bonferroni', 'holm', 'fdr_bh', 'fdr_by'}, optional
        Multiple-comparison correction applied across the resolved pairs.
    ax : matplotlib.axes.Axes, optional
        Axes on which to draw the plot. Defaults to the current Axes.
    **kwargs
        Additional keyword arguments passed to `seaborn.violinplot`.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    boxplot : Create a box plot showing quartiles without density.
    kdeplot : Create a kernel density plot.
    distplot : Create a distribution plot with histogram and KDE.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.violinplot(
    ...     data=df,
    ...     x="condition",
    ...     y="expression",
    ...     pairs=[("control", "treated")],
    ...     p_adjust="fdr_bh",
    ...     add_box=True,
    ... )
    >>> ax.set_title("Expression by Condition")
    """
    # Validate inputs
    validate_dataframe(data, "data", "violinplot")
    columns = [x, y] if hue is None else [x, y, hue]
    validate_columns_exist(data, columns, "violinplot")
    validate_dataframe_not_empty(data, "violinplot")
    validate_no_nulls(data, columns, "violinplot", allow_partial=True)
    utils._validate_statistical_options(
        test,
        p_adjust,
        valid_tests=("Mann-Whitney", "t-test_welch"),
    )

    if "addcount" in kwargs:
        raise TypeError(
            "violinplot() got an unexpected keyword argument 'addcount'; "
            "use 'add_count' instead"
        )

    boxprops: dict[str, Any] = {"edgecolor": "black", "zorder": 2}
    if box_color is not None:
        boxprops["facecolor"] = box_color

    args = {
        "showfliers": False,
        "showcaps": False,
        "showbox": True,
        "linewidth": 0.4,
        "boxprops": boxprops,
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
    }
    plotting: dict[str, Any] = {
        "data": data,
        "x": x,
        "y": y,
        "hue": hue,
        "order": order,
        "hue_order": hue_order,
    }
    plotting.update(kwargs)
    data = utils._prepare_categorical_plot_data(plotting)
    if ax is None:
        ax = plt.gca()
    ax = sns.violinplot(ax=ax, linewidth=0.001, width=width, **plotting)
    plotting.update(args)
    plotting.update({k: v for k, v in kwargs.items() if k != "orient"})
    # Remove violin-only arguments that boxplot doesn't support
    boxplot_kwargs = {k: v for k, v in plotting.items() if k not in ("split", "inner")}
    if add_box:
        sns.boxplot(ax=ax, **boxplot_kwargs)
    if pairs is not None:
        utils._p_value_helper(
            test,
            data,
            ax,
            plotting,
            pairs,
            p_adjust=p_adjust,
        )

    if add_count:
        axis = "y" if plotting["orient"] == "h" else "x"
        utils._add_count_helper(data, plotting[axis], ax, axis=axis)

    return ax


def distplot(
    data: pd.DataFrame,
    x: str,
    *,
    hue: str | None = None,
    hue_order: list[str] | None = None,
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes:
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
    hue : str, optional
        Column name for grouping distributions.
    hue_order : list of str, optional
        Order of hue levels.
    ax : matplotlib.axes.Axes, optional
        Axes on which to draw the plot. Defaults to the current Axes.
    **kwargs
        Additional keyword arguments passed to `seaborn.histplot`.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    kdeplot : Create a kernel density estimate plot only.
    histplot : Create a histogram without KDE.
    violinplot : Create a violin plot showing distribution shape.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.distplot(data=df, x="age")
    >>> ax.set_title("Age Distribution")

    >>> # With grouping by category
    >>> ax = cns.distplot(data=df, x="expression", hue="treatment")
    >>> ax.set_xlabel("Gene Expression")
    """
    # Validate inputs
    validate_dataframe(data, "data", "distplot")
    columns = [x] if hue is None else [x, hue]
    validate_columns_exist(data, columns, "distplot")
    validate_dataframe_not_empty(data, "distplot")

    args = {"kde": True, "edgecolor": None}
    args.update(kwargs)
    if ax is None:
        ax = plt.gca()
    ax = sns.histplot(
        data=data,
        x=x,
        hue=hue,
        hue_order=hue_order,
        ax=ax,
        **args,
    )
    return ax


def kdeplot(
    data: pd.DataFrame,
    x: str,
    add_mode: bool = True,
    *,
    hue: str | None = None,
    hue_order: list[str] | None = None,
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes:
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
        Whether to add a vertical dashed line at the mode (peak) of the distribution.
    hue : str, optional
        Column name for grouping density estimates.
    hue_order : list of str, optional
        Order of hue levels.
    ax : matplotlib.axes.Axes, optional
        Axes on which to draw the plot. Defaults to the current Axes.
    **kwargs
        Additional keyword arguments passed to `seaborn.kdeplot`.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    distplot : Create a distribution plot with histogram and KDE.
    violinplot : Create a violin plot showing distribution shape.
    ridgeplot : Create ridge plots for multiple distributions.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.kdeplot(data=df, x="expression", add_mode=True)
    >>> ax.set_title("Expression Distribution")

    >>> # Compare two groups with automatic statistics
    >>> ax = cns.kdeplot(data=df, x="score", hue="treatment", fill=True)
    >>> ax.set_xlabel("Score")

    Notes
    -----
    For unweighted, univariate plots, plotting and testing use finite ``x`` values
    with nonmissing hue labels, restricted to ``hue_order`` when supplied.
    Logarithmic x axes additionally require positive values. Unused categorical
    levels do not enter the test.
    A two-sided Kolmogorov-Smirnov test is annotated only for unweighted,
    univariate plots with exactly two observed hue groups and two drawn densities.
    Groups with fewer than two observations or zero variance cannot produce a
    density; seaborn's ``warn_singular`` controls their warning. If either density
    is skipped, no comparison is annotated. Empty cleaned data produces no density.
    """
    # Validate inputs
    validate_dataframe(data, "data", "kdeplot")
    columns_to_check = [x] if hue is None else [x, hue]
    validate_columns_exist(data, columns_to_check, "kdeplot")
    validate_dataframe_not_empty(data, "kdeplot")

    linewidth = kwargs.pop("linewidth", 1)
    if ax is None:
        ax = plt.gca()
    unweighted_univariate = kwargs.get("weights") is None and kwargs.get("y") is None
    if unweighted_univariate:
        values = data[x].to_numpy(dtype=float, na_value=np.nan)
        data = data.loc[np.isfinite(values)]
        if hue is not None:
            data = data.loc[data[hue].notna()]
            if hue_order is not None:
                data = data.loc[data[hue].isin(hue_order)]
        log_scale = kwargs.get("log_scale")
        log_x = log_scale[0] if isinstance(log_scale, (tuple, list)) else log_scale
        if log_x or ax.get_xscale() == "log":
            data = data.loc[data[x] > 0]
        if data.empty:
            return ax

    line_count = len(ax.lines)
    artist_count = line_count + len(ax.collections)
    ax = sns.kdeplot(
        data=data,
        x=x,
        hue=hue,
        hue_order=hue_order,
        linewidth=linewidth,
        ax=ax,
        **kwargs,
    )
    modes = []
    if hue is not None:
        drawn_densities = len(ax.lines) + len(ax.collections) - artist_count
        if data[hue].nunique() == 2 and drawn_densities == 2 and unweighted_univariate:
            grouped = data.groupby(hue, observed=True, sort=False)
            args = [group_df[x].to_numpy(dtype=float) for _, group_df in grouped]
            p_value = sp.stats.ks_2samp(*args).pvalue
            if not np.isfinite(p_value):
                logger.warning(
                    "[kdeplot] KS test returned a nonfinite p-value; omitted."
                )
                return ax
            x_lim = ax.get_xlim()
            y_lim = ax.get_ylim()
            ax.text(
                x_lim[1],
                y_lim[1],
                rf"$P={num2tex.num2tex(p_value, precision=2):.2g}$",
                ha="right",
                va="top",
            )
            logger.info("P-value was determined by two-sided Kolmogorov-Smirnov test.")
    else:
        if add_mode and len(ax.lines) > line_count:
            kde_data = ax.get_lines()[-1].get_data()
            x_vals = np.asarray(kde_data[0], dtype=float)
            y_vals = np.asarray(kde_data[1], dtype=float)
            mode_idx = int(np.argmax(y_vals))
            mode = float(x_vals[mode_idx])
            modes.append(mode)
            kde_color = ax.get_lines()[-1].get_color()
            y_mode = float(y_vals[mode_idx])
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
                fontsize=_legend_fontsize(),
                color=kde_color,
                bbox=dict(facecolor="white", edgecolor="none", pad=2),
            )

    legend = ax.get_legend()
    if legend is not None:
        for handle in legend.legend_handles:
            set_linewidth = getattr(handle, "set_linewidth", None)
            if callable(set_linewidth):
                set_linewidth(1.7)

    return ax


def histplot(
    data: pd.DataFrame | None = None,
    *,
    x: Any = None,
    y: Any = None,
    hue: Any = None,
    weights: Any = None,
    stat: str = "count",
    bins: Any = "auto",
    binwidth: float | None = None,
    binrange: tuple[float, float] | None = None,
    discrete: bool | None = None,
    cumulative: bool = False,
    common_bins: bool = True,
    common_norm: bool = True,
    multiple: str = "layer",
    element: str = "bars",
    fill: bool = True,
    shrink: float = 1,
    kde: bool = False,
    kde_kws: dict[str, Any] | None = None,
    line_kws: dict[str, Any] | None = None,
    thresh: float | None = 0,
    pthresh: float | None = None,
    pmax: float | None = None,
    cbar: bool = False,
    cbar_ax: Axes | None = None,
    cbar_kws: dict[str, Any] | None = None,
    palette: Any = None,
    hue_order: list[Any] | None = None,
    hue_norm: Any = None,
    color: Any = None,
    log_scale: Any = None,
    legend: bool = True,
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes:
    """
    Create a histogram plot (wrapper around seaborn.histplot).

    This is a convenience wrapper that creates a histogram with edge colors
    removed by default for a cleaner appearance.

    Parameters
    ----------
    data : pd.DataFrame, optional
        Input data in long or wide form.
    x, y, hue, weights : str or vector, optional
        Variables that define positions, grouping, and observation weights.
    stat : str, default: "count"
        Aggregate statistic shown by each bin.
    bins, binwidth, binrange, discrete
        Parameters controlling how histogram bins are defined.
    cumulative, common_bins, common_norm : bool
        Parameters controlling cumulative and shared histogram calculations.
    multiple, element, fill, shrink
        Parameters controlling how histogram marks are drawn.
    kde : bool, default: False
        Whether to add a kernel density estimate.
    kde_kws, line_kws : dict, optional
        Additional keyword arguments for the KDE and its line artists.
    thresh, pthresh, pmax : float, optional
        Thresholds used when drawing a bivariate histogram.
    cbar : bool, default: False
        Whether to add a colorbar for a bivariate histogram.
    cbar_ax : matplotlib.axes.Axes, optional
        Axes on which to draw the colorbar.
    cbar_kws : dict, optional
        Additional keyword arguments for the colorbar.
    palette, hue_order, hue_norm, color
        Parameters controlling color mapping.
    log_scale : bool, number, or pair, optional
        Log scaling configuration for the plot axes.
    legend : bool, default: True
        Whether to draw a legend.
    ax : matplotlib.axes.Axes, optional
        Axes on which to draw the plot. Defaults to the current Axes.
    **kwargs
        Keyword arguments passed directly to `seaborn.histplot`.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    distplot : Create a distribution plot with histogram and KDE.
    kdeplot : Create a kernel density plot only.
    barplot : Create a bar plot of means.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.histplot(data=df, x="age", bins=20)
    >>> ax.set_title("Age Distribution")

    >>> # With KDE overlay
    >>> ax = cns.histplot(data=df, x="expression", kde=True, hue="treatment")
    >>> ax.set_xlabel("Gene Expression")
    """
    if data is not None:
        validate_dataframe(data, "data", "histplot")
        columns_to_check = [
            value for value in (x, y, hue, weights) if isinstance(value, str)
        ]
        if columns_to_check:
            validate_columns_exist(data, columns_to_check, "histplot")

    if ax is None:
        ax = plt.gca()
    track_detached_axes = cbar and cbar_ax is None
    existing_axes = list(ax.figure.axes) if track_detached_axes else []

    kwargs.setdefault("edgecolor", None)
    ax = sns.histplot(
        data=data,
        x=x,
        y=y,
        hue=hue,
        weights=weights,
        stat=stat,
        bins=bins,
        binwidth=binwidth,
        binrange=binrange,
        discrete=discrete,
        cumulative=cumulative,
        common_bins=common_bins,
        common_norm=common_norm,
        multiple=multiple,
        element=element,
        fill=fill,
        shrink=shrink,
        kde=kde,
        kde_kws=kde_kws,
        line_kws=line_kws,
        thresh=thresh,
        pthresh=pthresh,
        pmax=pmax,
        cbar=cbar,
        cbar_ax=cbar_ax,
        cbar_kws=cbar_kws,
        palette=palette,
        hue_order=hue_order,
        hue_norm=hue_norm,
        color=color,
        log_scale=log_scale,
        legend=legend,
        ax=ax,
        **kwargs,
    )
    if track_detached_axes:
        utils._capture_detached_axes_layout(ax, existing_axes)
    return ax


def ridgeplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    cmap: str = "viridis",
    *,
    hue: str | None = None,
    overlap: float = 0.5,
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes:
    """
    Create a ridge plot (joyplot) showing distributions across categories.

    This function generates a ridge plot with overlapping kernel density curves
    for a continuous variable across multiple categories.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to visualize.
    x : str
        Column name for the continuous variable to plot as distributions.
    y : str
        Column name for the categorical variable determining separate curves.
    cmap : str, optional
        Name of a matplotlib colormap to use for coloring the ridges.
        Default is ``"viridis"``.
    hue : str, optional
        Column name for grouping density estimates within each ridge. Each observed
        hue level is drawn at the same vertical offset and included in a legend.
    overlap : float, default: 0.5
        Fractional overlap between adjacent ridges. Must be between 0 and 1,
        inclusive. Zero makes adjacent ridges touch and one fully aligns them.
    ax : matplotlib.axes.Axes, optional
        Axes on which to draw the plot. Defaults to the current Axes.
    **kwargs
        Additional keyword arguments passed to `matplotlib.axes.Axes.fill_between`.

    Returns
    -------
    matplotlib.axes.Axes
        The Axes object containing the ridge plot.

    See Also
    --------
    kdeplot : Create a kernel density plot.
    violinplot : Create a violin plot showing distribution shapes.
    distplot : Create a distribution plot with histogram and KDE.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.ridgeplot(data=df, x="expression", y="tissue_type")
    >>> ax.set_xlabel("Gene Expression")

    >>> # Time series data with a custom colormap
    >>> ax = cns.ridgeplot(data=df, x="temperature", y="month", cmap="plasma")

    >>> # Compare groups within each ridge and adjust their overlap
    >>> ax = cns.ridgeplot(
    ...     data=df,
    ...     x="expression",
    ...     y="tissue_type",
    ...     hue="treatment",
    ...     overlap=0.7,
    ...     alpha=0.6,
    ... )
    """
    # Validate inputs
    validate_dataframe(data, "data", "ridgeplot")
    columns = [x, y] if hue is None else [x, y, hue]
    validate_columns_exist(data, columns, "ridgeplot")
    validate_dataframe_not_empty(data, "ridgeplot")
    validate_no_nulls(data, columns, "ridgeplot", allow_partial=True)
    data = data.dropna(subset=columns)

    if isinstance(overlap, (bool, np.bool_)) or not isinstance(overlap, Real):
        raise TypeError(
            "[ridgeplot] Parameter 'overlap' must be a number between 0 and 1"
        )
    if not np.isfinite(overlap) or not 0 <= overlap <= 1:
        raise ValueError(
            "[ridgeplot] Parameter 'overlap' must be finite and between 0 and 1"
        )

    categories = list(data[y].unique())
    hue_levels = [] if hue is None else list(data[hue].unique())
    grouped_values: list[tuple[int, Any, Any | None, np.ndarray]] = []
    for category_index, category in enumerate(categories):
        category_data = data.loc[data[y] == category]
        group_hues: list[Any | None] = [None] if hue is None else hue_levels
        for hue_value in group_hues:
            values = (
                category_data[x].to_numpy()
                if hue is None
                else category_data.loc[category_data[hue] == hue_value, x].to_numpy()
            )
            if values.size == 0:
                continue
            group_description = (
                f"{category!r}"
                if hue is None
                else f"{category!r} with {hue}={hue_value!r}"
            )
            if values.size < 2:
                raise ValueError(
                    f"[ridgeplot] Group {group_description} must contain at least two "
                    "observations."
                )
            if pd.Series(values).nunique() < 2:
                raise ValueError(
                    f"[ridgeplot] Group {group_description} is constant; kernel "
                    "density estimation requires varying values."
                )
            grouped_values.append((category_index, category, hue_value, values))

    n = len(categories)
    color_levels = categories if hue is None else hue_levels
    colors = utils._get_hex_colors_from_colorbar(cmap, len(color_levels))
    color_map = dict(zip(color_levels, colors))
    if ax is None:
        ax = plt.gca()

    from scipy.stats import gaussian_kde

    x_min, x_max = data[x].min(), data[x].max()
    x_grid = np.linspace(x_min, x_max, 200)
    hue_handles: dict[Any, Any] = {}

    for category_index, _, hue_value, x_v in grouped_values:
        kde = gaussian_kde(x_v)
        y_vals = kde(x_grid)
        y_vals = y_vals / y_vals.max()
        offset = (n - 1 - category_index) * (1 - overlap)
        color_level = categories[category_index] if hue is None else hue_value
        color = color_map[color_level]
        fill_kwargs: dict[str, Any] = {
            "alpha": 1,
            "color": color,
            "zorder": category_index,
            "linewidth": 0.5,
            "edgecolor": color,
        }
        fill_kwargs.update(kwargs)
        collection = ax.fill_between(
            x_grid,
            offset,
            y_vals + offset,
            **fill_kwargs,
        )
        if hue is not None and hue_value not in hue_handles:
            hue_handles[hue_value] = collection

    for category_index, category in enumerate(categories):
        offset = (n - 1 - category_index) * (1 - overlap)
        ax.text(
            x_min,
            offset + 0.05,
            category,
            ha="right",
            va="bottom",
            fontsize=_legend_fontsize(),
        )

    if hue is not None:
        ax.legend(
            [hue_handles[hue_value] for hue_value in hue_levels],
            [str(hue_value) for hue_value in hue_levels],
            title=hue,
        )

    ax.set_xlim(x_min, x_max)
    ax.set_yticks([])
    ax.set_ylabel("")
    ax.set_xlabel(x)
    ax.spines["left"].set_visible(False)
    return ax


def qqplot(
    data: pd.DataFrame,
    x: str,
    *,
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes:
    """
    Create a quantile-quantile (Q-Q) plot to assess normality.

    This function generates a Q-Q plot comparing the quantiles of a variable
    against the theoretical quantiles of a normal distribution.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to plot.
    x : str
        Column name for the variable to test for normality.
    ax : matplotlib.axes.Axes, optional
        Axes on which to draw the plot. Defaults to the current Axes.
    **kwargs
        Additional keyword arguments passed to `statsmodels.api.qqplot`.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    distplot : Create a distribution plot with histogram and KDE.
    kdeplot : Create a kernel density plot.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.qqplot(data=df, x="residuals")
    >>> ax.set_title("Q-Q Plot of Residuals")

    >>> # With custom distribution
    >>> from scipy import stats
    >>> ax = cns.qqplot(data=df, x="values", dist=stats.t, distargs=(10,))
    """
    # Validate inputs
    validate_dataframe(data, "data", "qqplot")
    validate_column_exists(data, x, "x", "qqplot")
    validate_dataframe_not_empty(data, "qqplot")

    import statsmodels.api as sm

    if ax is None:
        ax = plt.gca()
    sm.qqplot(
        data[x],
        ax=ax,
        markerfacecolor="black",
        markeredgewidth=0,
        markersize=3,
        **kwargs,
    )
    return ax
