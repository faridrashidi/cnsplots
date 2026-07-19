from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd
    from matplotlib.axes import Axes

import matplotlib.pyplot as plt
import num2tex
import numpy as np
import palettable.colorbrewer.qualitative  # noqa: F401  # ensure submodule is importable
import scipy as sp
import seaborn as sns

from cnsplots._validation import (
    validate_column_type,
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
)


def regplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    hue: str | None = None,
    s: float = 3,
    color="black",
    **kwargs: Any,
) -> Axes:
    """
    Create a regression plot with linear fit and correlation statistics.

    This function creates a scatter plot with a fitted regression line and displays
    Pearson correlation coefficient and p-value.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the independent variable (x-axis).
    y : str
        Column name for the dependent variable (y-axis).
    hue : str, optional
        Column name for grouping. When set, separate regression lines and
        correlation statistics are drawn for each group.
    s : float, default: 3
        Size of scatter plot markers.
    color : str, default: "black"
        Either a matplotlib color string (e.g. ``"black"``, ``"#ff0000"``) or the
        name of a column in *data*.  When a column name is given, the scatter
        points are colored by the unique values of that column and a legend is
        added, while a single overall regression line and correlation statistic
        are shown.  If *hue* is also specified, *hue* takes precedence and
        *color* is ignored.
    **kwargs
        Additional keyword arguments passed to `seaborn.regplot`.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    scatterplot : Create a scatter plot without regression line.
    kdeplot : Create a kernel density plot for distributions.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.regplot(data=df, x="age", y="expression")
    >>> ax.set_title("Age vs Expression")

    >>> # Grouped regression with separate fits
    >>> ax = cns.regplot(data=df, x="dose", y="response", hue="cell_line")
    >>> ax.set_xlabel("Drug Dose")

    >>> # Color points by a column (single regression line)
    >>> ax = cns.regplot(data=df, x="age", y="expression", color="cell_type")
    """
    # Validate inputs
    validate_dataframe(data, "data", "regplot")
    columns_to_check = [x, y]
    if hue is not None:
        columns_to_check.append(hue)
    validate_columns_exist(data, columns_to_check, "regplot")
    validate_dataframe_not_empty(data, "regplot")

    # Validate numeric columns
    validate_column_type(data, x, ["numeric"], "regplot")
    validate_column_type(data, y, ["numeric"], "regplot")

    ax = plt.gca()
    args = {
        "line_kws": {"lw": 1.2},
        "scatter_kws": {"s": s, "alpha": 1, "edgecolor": None},
    }
    args.update(kwargs)
    palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    color_is_column = isinstance(color, str) and color in data.columns
    if hue:
        for idx, hue_val in enumerate(data[hue].unique()):
            subset = data[data[hue] == hue_val]
            ax = sns.regplot(
                data=subset,
                x=x,
                y=y,
                ax=ax,
                color=palette[idx % len(palette)],
                label=hue_val,
                **args,
            )
            rho, p_value = sp.stats.pearsonr(subset[x], subset[y])
            ax.text(
                0.05,
                0.95 - 0.08 * idx,
                rf"{hue_val}: $\rho$={rho:.2f},"
                rf" P=${num2tex.num2tex(p_value, precision=2):.2g}$",
                color=palette[idx % len(palette)],
                transform=ax.transAxes,
                ha="left",
                va="top",
            )
        ax.legend(title=hue)
    elif color_is_column:
        line_args = {k: v for k, v in args.items() if k != "scatter_kws"}
        ax = sns.regplot(
            data=data,
            x=x,
            y=y,
            ax=ax,
            color="black",
            scatter=False,
            **line_args,
        )
        unique_vals = data[color].unique()
        for idx, val in enumerate(unique_vals):
            subset = data[data[color] == val]
            ax.scatter(
                subset[x],
                subset[y],
                s=s,
                color=palette[idx % len(palette)],
                label=val,
                alpha=1,
                edgecolors="none",
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
        ax.legend(title=color)
        for handle in ax.get_legend().legend_handles:
            if hasattr(handle, "set_sizes"):
                handle.set_sizes([2 * s])
            elif hasattr(handle, "set_markersize"):
                handle.set_markersize(2 * np.sqrt(s / np.pi))
    else:
        ax = sns.regplot(
            data=data,
            x=x,
            y=y,
            ax=ax,
            color=color,
            **args,
        )
        rho, p_value = sp.stats.pearsonr(data[x], data[y])
        ax.text(
            0.05,
            0.95,
            rf"$\rho$={rho:.2f}, $P={num2tex.num2tex(p_value, precision=2):.2g}$",
            color=color,
            transform=ax.transAxes,
            ha="left",
            va="top",
        )

    return ax


def scatterplot(
    data: pd.DataFrame, x: str, y: str, s: float = 7, **kwargs: Any
) -> Axes:
    """
    Create a scatter plot with automatic legend size correction.

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

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    regplot : Create a scatter plot with regression line.
    stripplot : Create a categorical scatter plot.
    volcanoplot : Create a volcano plot for differential expression.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.scatterplot(data=df, x="PC1", y="PC2", s=10)
    >>> ax.set_title("PCA Plot")

    >>> # With grouping by category
    >>> ax = cns.scatterplot(
    ...     data=df, x="UMAP1", y="UMAP2", hue="cell_type", s=5, alpha=0.7
    ... )
    >>> ax.set_xlabel("UMAP Dimension 1")
    """
    # Validate inputs
    validate_dataframe(data, "data", "scatterplot")
    validate_columns_exist(data, [x, y], "scatterplot")
    validate_dataframe_not_empty(data, "scatterplot")

    ax = sns.scatterplot(data=data, x=x, y=y, s=s, edgecolor=None, **kwargs)

    if ax.get_legend() is not None:
        for handle in ax.get_legend().legend_handles:
            if hasattr(handle, "set_sizes"):
                handle.set_sizes([s])
            elif hasattr(handle, "set_markersize"):
                handle.set_markersize(2 * np.sqrt(s / np.pi))

    return ax


def lineplot(**kwargs: Any) -> Axes:
    """
    Create a line plot (wrapper around seaborn.lineplot).

    Parameters
    ----------
    **kwargs
        Keyword arguments passed directly to `seaborn.lineplot`.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    regplot : Create a regression plot with linear fit.
    scatterplot : Create a scatter plot without connecting lines.
    survivalplot : Create a Kaplan-Meier survival plot.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.lineplot(data=df, x="time", y="value")
    >>> ax.set_title("Time Series")

    >>> # Multiple groups with error bands
    >>> ax = cns.lineplot(
    ...     data=df, x="timepoint", y="expression", hue="treatment", errorbar="se"
    ... )
    >>> ax.set_ylabel("Gene Expression")
    """
    # Validate inputs if provided in kwargs
    if "data" in kwargs:
        validate_dataframe(kwargs["data"], "data", "lineplot")
        data = kwargs["data"]
        columns_to_check = []
        if "x" in kwargs:
            columns_to_check.append(kwargs["x"])
        if "y" in kwargs:
            columns_to_check.append(kwargs["y"])
        if columns_to_check:
            validate_columns_exist(data, columns_to_check, "lineplot")

    ax = sns.lineplot(**kwargs)
    return ax


def slopeplot(data: pd.DataFrame, x: str, y: str, hue: str) -> Axes:
    """
    Create a slope plot showing paired changes between two conditions.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing paired observations.
    x : str
        Column name for the categorical variable defining the two conditions.
    y : str
        Column name for the continuous variable to plot.
    hue : str
        Column name for the grouping variable. Must have exactly two unique values.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    lineplot : Create a line plot for time series.
    scatterplot : Create a scatter plot.
    regplot : Create a regression plot.

    Examples
    --------
    >>> import cnsplots as cns
    >>> # Compare before/after measurements for multiple patients
    >>> ax = cns.slopeplot(
    ...     data=df,
    ...     x="patient_id",
    ...     y="tumor_size",
    ...     hue="timepoint",
    ... )
    >>> ax.set_ylabel("Tumor Size (mm)")

    >>> # Compare two treatments across sites
    >>> ax = cns.slopeplot(data=df, x="site", y="response_rate", hue="treatment")
    """
    # Validate inputs
    validate_dataframe(data, "data", "slopeplot")
    validate_columns_exist(data, [x, y, hue], "slopeplot")
    validate_dataframe_not_empty(data, "slopeplot")

    # https://cduvallet.github.io/posts/2018/03/slopegraphs-in-python
    red = palettable.colorbrewer.qualitative.Set1_9.hex_colors[0]
    blue = palettable.colorbrewer.qualitative.Set1_9.hex_colors[1]
    hues = data[hue].unique()

    ax = plt.gca()

    sites: list[str] = []
    i = 1.0
    for site, subdf in data.groupby(x):
        sites.append(str(site))
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
    ax.set_ylabel(y)
    _ = ax.set_xticklabels(sites)

    handles, labels = ax.get_legend_handles_labels()
    lgd = ax.legend(
        handles[0:2],
        labels[0:2],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=2,
    )
    for handle in lgd.legend_handles:
        set_sizes = getattr(handle, "set_sizes", None)
        if callable(set_sizes):
            set_sizes([12])

    return ax
