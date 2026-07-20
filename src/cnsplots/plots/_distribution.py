from __future__ import annotations

import logging
from typing import Any

import matplotlib as mpl
import matplotlib.patches  # noqa: F401  # ensure submodule is importable for isinstance checks
import matplotlib.pyplot as plt
import num2tex
import numpy as np
import pandas as pd
import scipy as sp
import seaborn as sns
from matplotlib.axes import Axes

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
    addcount: bool = False,
    whis: float | tuple[float, float] = 1.5,
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
    addcount : bool, default: False
        Whether to add sample size (n) labels above each box.
    whis : float or tuple of float, default: 1.5
        The proportion of the IQR past the low and high quartiles to extend the
        plot whiskers.
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
    ...     showoutliers=True,
    ... )
    >>> ax.set_title("Treatment Response")
    """
    # Validate inputs
    validate_dataframe(data, "data", "boxplot")
    validate_columns_exist(data, [x, y], "boxplot")
    validate_dataframe_not_empty(data, "boxplot")

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
    plotting: dict[str, Any] = {"data": data, "x": x, "y": y}
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
        utils._p_value_helper("Mann-Whitney", data, ax, plotting, pairs)

    if addcount:
        utils._addcount_helper(data, x, ax)

    return ax


def violinplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    pairs: list[tuple[str, str]] | None = None,
    width: float = 0.6,
    add_box: bool = True,
    addcount: bool = False,
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
    addcount : bool, default: False
        Whether to add sample size (n) labels above each violin.
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
    ...     add_box=True,
    ... )
    >>> ax.set_title("Expression by Condition")
    """
    # Validate inputs
    validate_dataframe(data, "data", "violinplot")
    validate_columns_exist(data, [x, y], "violinplot")
    validate_dataframe_not_empty(data, "violinplot")

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
    plotting: dict[str, Any] = {"data": data, "x": x, "y": y}
    plotting.update(kwargs)
    ax = sns.violinplot(linewidth=0.001, width=width, **plotting)
    plotting.update(args)
    plotting.update(kwargs)
    # Remove violin-only arguments that boxplot doesn't support
    boxplot_kwargs = {k: v for k, v in plotting.items() if k not in ("split", "inner")}
    if add_box:
        sns.boxplot(**boxplot_kwargs)
    if pairs is not None:
        utils._p_value_helper("Mann-Whitney", data, ax, plotting, pairs)

    if addcount:
        utils._addcount_helper(data, x, ax)

    return ax


def distplot(data: pd.DataFrame, x: str, **kwargs: Any) -> Axes:
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
    validate_column_exists(data, x, "x", "distplot")
    validate_dataframe_not_empty(data, "distplot")

    args = {"kde": True, "edgecolor": None}
    args.update(kwargs)
    ax = sns.histplot(data=data, x=x, **args)
    return ax


def kdeplot(data: pd.DataFrame, x: str, add_mode: bool = True, **kwargs: Any) -> Axes:
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
    """
    # Validate inputs
    validate_dataframe(data, "data", "kdeplot")
    columns_to_check = [x]
    if "hue" in kwargs:
        columns_to_check.append(kwargs["hue"])
    validate_columns_exist(data, columns_to_check, "kdeplot")
    validate_dataframe_not_empty(data, "kdeplot")

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
            logger.info("P-value was determined by two-sided Kolmogorov-Smirnov test.")
    else:
        if add_mode and ax.get_lines():
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


def histplot(**kwargs: Any) -> Axes:
    """
    Create a histogram plot (wrapper around seaborn.histplot).

    This is a convenience wrapper that creates a histogram with edge colors
    removed by default for a cleaner appearance.

    Parameters
    ----------
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
    # Validate inputs if provided in kwargs
    if "data" in kwargs:
        validate_dataframe(kwargs["data"], "data", "histplot")
        data = kwargs["data"]
        columns_to_check = []
        if "x" in kwargs:
            columns_to_check.append(kwargs["x"])
        if "y" in kwargs:
            columns_to_check.append(kwargs["y"])
        if columns_to_check:
            validate_columns_exist(data, columns_to_check, "histplot")

    track_detached_axes = bool(kwargs.get("cbar")) and kwargs.get("cbar_ax") is None
    host_ax = kwargs.get("ax", plt.gca())
    existing_axes = list(host_ax.figure.axes) if track_detached_axes else []

    kwargs.setdefault("edgecolor", None)
    ax = sns.histplot(**kwargs)
    if track_detached_axes:
        utils._capture_detached_axes_layout(ax, existing_axes)
    return ax


def ridgeplot(data: pd.DataFrame, x: str, y: str, cmap: str = "viridis") -> Axes:
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
    >>> axes = cns.ridgeplot(data=df, x="expression", y="tissue_type")
    >>> axes[-1].set_xlabel("Gene Expression")

    >>> # Time series data with a custom colormap
    >>> axes = cns.ridgeplot(data=df, x="temperature", y="month", cmap="plasma")
    """
    # Validate inputs
    validate_dataframe(data, "data", "ridgeplot")
    validate_columns_exist(data, [x, y], "ridgeplot")
    validate_dataframe_not_empty(data, "ridgeplot")
    validate_no_nulls(data, [x, y], "ridgeplot")

    categories = data[y].unique()
    grouped_values: list[tuple[Any, np.ndarray]] = []
    for category in categories:
        values = data.loc[data[y] == category, x].to_numpy()
        if values.size < 2:
            raise ValueError(
                f"[ridgeplot] Group {category!r} must contain at least two "
                "observations."
            )
        if pd.Series(values).nunique() < 2:
            raise ValueError(
                f"[ridgeplot] Group {category!r} is constant; kernel density "
                "estimation requires varying values."
            )
        grouped_values.append((category, values))

    n = len(categories)
    colors = utils._get_hex_colors_from_colorbar(cmap, n)
    ax = plt.gca()

    from scipy.stats import gaussian_kde

    overlap = 0.5
    x_min, x_max = data[x].min(), data[x].max()
    x_grid = np.linspace(x_min, x_max, 200)

    for i, (cat, x_v) in enumerate(grouped_values):
        kde = gaussian_kde(x_v)
        y_vals = kde(x_grid)
        y_vals = y_vals / y_vals.max()
        offset = (n - 1 - i) * (1 - overlap)
        ax.fill_between(
            x_grid,
            offset,
            y_vals + offset,
            alpha=1,
            color=colors[i],
            zorder=i,
            linewidth=0.5,
            edgecolor=colors[i],
        )
        ax.text(
            x_min,
            offset + 0.05,
            cat,
            ha="right",
            va="bottom",
            fontsize=_legend_fontsize(),
        )

    ax.set_xlim(x_min, x_max)
    ax.set_yticks([])
    ax.set_ylabel("")
    ax.set_xlabel(x)
    ax.spines["left"].set_visible(False)
    return ax


def qqplot(data: pd.DataFrame, x: str, **kwargs: Any) -> Axes:
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
