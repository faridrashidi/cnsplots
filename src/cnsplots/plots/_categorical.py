from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    import pandas as pd
    from matplotlib.axes import Axes

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch

import cnsplots._utils as utils
from cnsplots._utils import _legend_fontsize, _resize_legend_markers
from cnsplots._validation import (
    validate_column_exists,
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
)

LollipopPair = Union[tuple[str, str], tuple[tuple[str, str], tuple[str, str]]]


def _resolve_palette_column(
    data: pd.DataFrame,
    category_column: str,
    palette_column: str,
) -> tuple[dict[Any, Any], list[Patch]]:
    """Map categories to colors through a palette-label column."""
    unique_labels = data[palette_column].unique()
    palette_colors = sns.color_palette(n_colors=len(unique_labels))
    label_to_color = dict(zip(unique_labels, palette_colors))
    category_labels = data[[category_column, palette_column]].drop_duplicates()
    ambiguous = category_labels[category_column].duplicated(keep=False)
    if ambiguous.any():
        ambiguous_categories = category_labels.loc[ambiguous, category_column].unique()
        raise ValueError(
            f"Palette column '{palette_column}' must map each category to one label; "
            f"multiple labels found for {list(ambiguous_categories)}."
        )
    category_to_label = category_labels.set_index(category_column)[
        palette_column
    ].to_dict()
    category_to_color = {
        category: label_to_color[label] for category, label in category_to_label.items()
    }
    legend_handles = [
        Patch(facecolor=resolved_color, label=label)
        for label, resolved_color in label_to_color.items()
    ]
    return category_to_color, legend_handles


def _compute_lollipop_error(group_values: pd.Series, errorbar: str) -> float:
    """Compute the requested lollipop error magnitude for one group."""
    sem = group_values.std() / np.sqrt(len(group_values))
    if errorbar == "se":
        return sem
    if errorbar == "sd":
        return group_values.std()
    if errorbar == "ci":
        return 1.96 * sem
    return 0


def _lollipop_errors(
    grouped: Any,
    categories: list[str],
    errorbar: str | None,
    *,
    require_multiple: bool,
) -> pd.Series | None:
    """Aggregate lollipop errors once for each category."""
    if errorbar is None:
        return None
    errors = grouped.apply(
        lambda values: _compute_lollipop_error(values, errorbar)
    ).reindex(categories)
    if require_multiple:
        counts = grouped.count().reindex(categories)
        errors = errors.where(counts > 1)
    return errors


def _draw_lollipop_series(
    ax: Axes,
    *,
    orient: str,
    positions: np.ndarray,
    values: pd.Series,
    colors: Any,
    baseline: float,
    linewidth: float,
    markersize: float,
    marker: str,
    errors: pd.Series | None,
    addtip: bool,
    tip_offset: float,
    label: Any = None,
) -> None:
    """Draw one lollipop series using orientation-independent inputs."""
    line_function = ax.vlines if orient == "v" else ax.hlines
    line_function(
        positions,
        baseline,
        values,
        linewidth=linewidth,
        alpha=0.4,
        colors=colors,
        zorder=2,
    )
    scatter_x, scatter_y = (positions, values) if orient == "v" else (values, positions)
    ax.scatter(
        scatter_x,
        scatter_y,
        s=markersize,
        marker=marker,
        color=colors,
        zorder=3,
        label=label,
    )

    if errors is not None:
        for position, value, error in zip(positions, values, errors):
            if pd.isna(error):
                continue
            error_kwargs = {"yerr" if orient == "v" else "xerr": error}
            point = (position, value) if orient == "v" else (value, position)
            ax.errorbar(
                *point,
                **error_kwargs,
                fmt="none",
                ecolor="black",
                elinewidth=0.7,
                capsize=2,
            )

    if addtip:
        for position, value in zip(positions, values):
            if pd.isna(value):
                continue
            text_x, text_y = (
                (position, value + tip_offset)
                if orient == "v"
                else (value + tip_offset, position)
            )
            ax.text(
                text_x,
                text_y,
                f"{value:.2f}",
                color="black",
                ha="center" if orient == "v" else "left",
                va="bottom" if orient == "v" else "center",
                fontsize=_legend_fontsize(),
            )


def barplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    pairs: list[tuple[str, str]] | None = None,
    addtip: bool = False,
    **kwargs: Any,
) -> Axes:
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
        using Welch's t-test.
    addtip : bool, default: False
        Whether to add text labels showing the mean value above each bar.
    **kwargs
        Additional keyword arguments passed to `seaborn.barplot`.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    boxplot : Create a box plot showing full distribution.
    violinplot : Create a violin plot with distribution shape.
    stackplot : Create a stacked bar plot for categorical data.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.barplot(
    ...     data=df,
    ...     x="treatment",
    ...     y="response",
    ...     pairs=[("control", "drug_a"), ("control", "drug_b")],
    ...     addtip=True,
    ... )
    >>> ax.set_title("Treatment Response")

    >>> # Color by group with automatic legend
    >>> ax = cns.barplot(data=df, x="treatment", y="response", palette="cell_type")
    >>> ax.set_ylabel("Mean Response")
    """
    # Validate inputs
    validate_dataframe(data, "data", "barplot")
    validate_columns_exist(data, [x, y], "barplot")
    validate_dataframe_not_empty(data, "barplot")

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
        category_column = x if not pd.api.types.is_numeric_dtype(data[x]) else y
        palette, legend_handles = _resolve_palette_column(
            data,
            category_column,
            group_col,
        )
        show_legend = True
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
                size=_legend_fontsize(),
            )
    if pairs is not None:
        utils._p_value_helper("t-test_welch", data, ax, plotting, pairs)
    if show_legend:
        ax.legend(
            handles=legend_handles,
            title=group_col,
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
        )

    return ax


def lollipopplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    hue: str | None = None,
    order: list[str] | None = None,
    hue_order: list[str] | None = None,
    pairs: list[LollipopPair] | None = None,
    addtip: bool = False,
    estimator: str = "mean",
    errorbar: str | None = None,
    markersize: float = 20,
    linewidth: float = 1.5,
    marker: str = "o",
    dodge: float = 0.8,
    color: str | None = None,
    palette: Any = None,
    baseline: float = 0,
) -> Axes:
    """
    Create a lollipop plot showing values across categories.

    A lollipop plot is a cleaner alternative to bar plots, using a stem (line)
    topped with a dot to represent aggregated values for each category.
    Orientation is automatically detected based on which axis is categorical.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the x-axis variable.
    y : str
        Column name for the y-axis variable.
    hue : str, optional
        Column name for grouping data into separate lollipop sets.
    order : list of str, optional
        Order of categories along the categorical axis.
    hue_order : list of str, optional
        Order of hue levels.
    pairs : list of tuple of str, optional
        List of pairs of category names for pairwise statistical comparisons
        using Welch's t-test.
    addtip : bool, default: False
        Whether to add text labels showing the aggregated value at each dot.
    estimator : {'mean', 'median'}, default: 'mean'
        The aggregation function to compute for each category.
    errorbar : {'se', 'sd', 'ci'}, optional
        Type of error bar to draw. ``'se'`` for standard error, ``'sd'`` for
        standard deviation, ``'ci'`` for 95% confidence interval.
    markersize : float, default: 20
        Size of the dot markers (in points squared, passed to scatter ``s``).
    linewidth : float, default: 1.5
        Width of the stem lines.
    marker : str, default: 'o'
        Marker style for the dots.
    dodge : float, default: 0.8
        Total width for grouped lollipops within each category position.
    color : str, optional
        A single color for all stems and dots (e.g. ``"black"``).
        Overrides ``palette``.
    palette : str, list, or dict, optional
        Colors to use. Can be a seaborn palette name, a list of colors,
        or a column name in data for palette-as-column mapping.
    baseline : float, default: 0
        Value at which the stems originate.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    barplot : Create a bar plot showing mean values.
    stripplot : Create a strip plot showing individual data points.
    boxplot : Create a box plot showing full distribution.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.lollipopplot(data=df, x="treatment", y="response")
    >>> ax.set_title("Treatment Response")

    >>> # Horizontal lollipop plot
    >>> ax = cns.lollipopplot(data=df, x="response", y="treatment")

    >>> # With hue grouping
    >>> ax = cns.lollipopplot(data=df, x="day", y="total_bill", hue="sex")
    """
    # Validate inputs
    validate_dataframe(data, "data", "lollipopplot")
    validate_columns_exist(data, [x, y], "lollipopplot")
    validate_dataframe_not_empty(data, "lollipopplot")
    if hue is not None:
        validate_column_exists(data, hue, "hue", "lollipopplot")

    palette_is_column = isinstance(palette, str) and palette in data.columns
    if hue is not None and palette_is_column and palette != hue:
        raise ValueError(
            "[lollipopplot] A palette column cannot be combined with a different "
            "'hue' column. Pass a palette name, list, or dict instead."
        )

    # Detect orientation
    x_is_numeric = pd.api.types.is_numeric_dtype(data[x])
    y_is_numeric = pd.api.types.is_numeric_dtype(data[y])
    if x_is_numeric and not y_is_numeric:
        orient = "h"
        cat_col, val_col = y, x
    else:
        orient = "v"
        cat_col, val_col = x, y

    # Category order
    categories = order if order is not None else list(data[cat_col].unique())
    cat_positions = np.arange(len(categories))

    ax = plt.gca()

    # Resolve palette and legend
    show_legend = False
    legend_handles = []
    group_col = None

    if color is not None:
        resolved_colors = [color] * len(categories)
    elif palette_is_column and hue is None:
        group_col = palette
        category_colors, legend_handles = _resolve_palette_column(
            data,
            cat_col,
            palette,
        )
        resolved_colors = [category_colors[category] for category in categories]
        show_legend = True
    elif palette is not None:
        resolved_colors = sns.color_palette(palette, n_colors=len(categories))
    else:
        resolved_colors = sns.color_palette(n_colors=len(categories))

    agg_func = np.median if estimator == "median" else np.mean

    if hue is None:
        grouped = data.groupby(cat_col, sort=False)[val_col]
        means = grouped.agg(agg_func).reindex(categories)
        errors = _lollipop_errors(grouped, categories, errorbar, require_multiple=False)
        _draw_lollipop_series(
            ax,
            orient=orient,
            positions=cat_positions,
            values=means,
            colors=resolved_colors,
            baseline=baseline,
            linewidth=linewidth,
            markersize=markersize,
            marker=marker,
            errors=errors,
            addtip=addtip,
            tip_offset=(means.max() - baseline) * 0.02,
        )
    else:
        hue_levels = hue_order if hue_order is not None else list(data[hue].unique())
        n_hue = len(hue_levels)
        width = dodge / n_hue
        offsets = np.linspace(-(dodge - width) / 2, (dodge - width) / 2, n_hue)

        if color is not None:
            hue_colors = [color] * n_hue
        elif palette is not None and not palette_is_column:
            hue_colors = sns.color_palette(palette, n_colors=n_hue)
        else:
            hue_colors = sns.color_palette(n_colors=n_hue)

        for i, hue_val in enumerate(hue_levels):
            subset = data[data[hue] == hue_val]
            grouped = subset.groupby(cat_col, sort=False)[val_col]
            means = grouped.agg(agg_func).reindex(categories)
            positions = cat_positions + offsets[i]
            errors = _lollipop_errors(
                grouped, categories, errorbar, require_multiple=True
            )
            _draw_lollipop_series(
                ax,
                orient=orient,
                positions=positions,
                values=means,
                colors=hue_colors[i],
                baseline=baseline,
                linewidth=linewidth,
                markersize=markersize,
                marker=marker,
                errors=errors,
                addtip=addtip,
                tip_offset=means.max() * 0.02,
                label=hue_val,
            )

    if orient == "v":
        ax.set_xticks(cat_positions)
        ax.set_xticklabels(categories)
    else:
        ax.set_yticks(cat_positions)
        ax.set_yticklabels(categories)

    # Statistical annotations
    if pairs is not None:
        # Draw invisible barplot so statannotations can find bar heights
        bar_kw: dict[str, Any] = {
            "data": data,
            "x": x,
            "y": y,
            "ax": ax,
            "alpha": 0,
            "edgecolor": "none",
        }
        if order is not None:
            bar_kw["order"] = order
        if hue is not None:
            bar_kw["hue"] = hue
        if hue_order is not None:
            bar_kw["hue_order"] = hue_order
        sns.barplot(**bar_kw)
        plotting: dict[str, Any] = {"data": data, "x": x, "y": y}
        if order is not None:
            plotting["order"] = order
        if hue is not None:
            plotting["hue"] = hue
        if hue_order is not None:
            plotting["hue_order"] = hue_order
        utils._p_value_helper("t-test_welch", data, ax, plotting, pairs)

    # Legend
    if show_legend:
        ax.legend(
            handles=legend_handles,
            title=group_col,
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
        )
    elif hue is not None and ax.get_legend() is None:
        ax.legend(title=hue)

    return ax


def stackplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    bar_order: list[str] | None = None,
    stack_order: list[str] | None = None,
    horizontal: bool = False,
    width: float = 0.5,
    normalize: bool = True,
    pairs: list[tuple[str, str]] | None = None,
    addcount: bool = False,
    n_factor: int | float = 1,
) -> Axes:
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
        Order of categories from x to display.
    stack_order : list, optional
        Order of categories from y for stacking.
    horizontal : bool, default: False
        Whether to create horizontal bars instead of vertical bars.
    width : float, default: 0.5
        Width of the bars.
    normalize : bool, default: True
        Whether to normalize counts to frequencies (proportions summing to 1).
    pairs : list of tuple of str, optional
        List of pairs of category names from x for pairwise statistical comparisons.
    addcount : bool, default: False
        Whether to append total counts to the category tick labels in the
        format ``n=...``.
    n_factor : int or float, default: 1
        Scaling factor to divide all values.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    barplot : Create a bar plot of means.
    pieplot : Create a pie chart for categorical proportions.
    donutplot : Create a donut chart for categorical proportions.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.stackplot(
    ...     data=df,
    ...     x="tissue",
    ...     y="cell_type",
    ...     normalize=True,
    ...     pairs=[("lung", "liver")],
    ... )
    >>> ax.set_title("Cell Type Distribution by Tissue")

    >>> # Horizontal stacked bar plot
    >>> ax = cns.stackplot(
    ...     data=df, x="patient", y="mutation", horizontal=True, normalize=False
    ... )
    >>> ax.set_xlabel("Mutation Count")
    """
    # Validate inputs
    validate_dataframe(data, "data", "stackplot")
    validate_columns_exist(data, [x, y], "stackplot")
    validate_dataframe_not_empty(data, "stackplot")

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
    utils.take_legend_out()
    if addcount:
        count_attr = y if horizontal else x
        count_axis = "y" if horizontal else "x"
        utils._addcount_helper(data, count_attr, ax, axis=count_axis)
    if pairs is not None:
        if horizontal:
            plotting = {"data": data2, "x": "count", "y": y, "order": bar_order}
        else:
            plotting = {"data": data2, "x": x, "y": "count", "order": bar_order}
        if contingency.shape[1] == 2:
            utils._p_value_helper(
                "fisher-exact", data2, ax, plotting, pairs, contingency
            )
        else:
            utils._p_value_helper(
                "chi-squared", data2, ax, plotting, pairs, contingency
            )

    return ax


def stripplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    size: float = 2,
    showmedian: bool = True,
    showmeans: bool = False,
    addcount: bool = False,
    **kwargs: Any,
) -> Axes:
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

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    boxplot : Create a box plot showing quartiles.
    violinplot : Create a violin plot showing distribution shape.
    scatterplot : Create a general scatter plot.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.stripplot(
    ...     data=df, x="treatment", y="response", showmedian=True, addcount=True
    ... )
    >>> ax.set_title("Treatment Response")

    >>> # With grouping and means
    >>> ax = cns.stripplot(
    ...     data=df, x="tissue", y="expression", hue="genotype", showmeans=True, size=3
    ... )
    >>> ax.set_ylabel("Gene Expression")
    """
    # Validate inputs
    validate_dataframe(data, "data", "stripplot")
    validate_columns_exist(data, [x, y], "stripplot")
    validate_dataframe_not_empty(data, "stripplot")

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
        utils._addcount_helper(data, x, ax)

    _resize_legend_markers(ax.get_legend(), size**2, marker_size=size * 2)

    return ax


def pieplot(
    data: pd.DataFrame,
    x: str,
    legend: str = "bottom",
    hue_order: list[str] | None = None,
) -> Axes:
    """
    Create a pie chart showing categorical proportions.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the categorical variable to visualize.
    legend : {'right', 'left', 'top', 'bottom'}, default: 'bottom'
        Position of the legend relative to the pie chart.
    hue_order : list, optional
        Order of categories to display in the pie chart.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    donutplot : Create a donut chart (pie chart with center hole).
    stackplot : Create a stacked bar plot for categorical distributions.
    barplot : Create a bar plot showing category frequencies.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.pieplot(data=df, x="cell_type")
    >>> ax.set_title("Cell Type Distribution")

    >>> # Specify category order
    >>> ax = cns.pieplot(data=df, x="response", hue_order=["CR", "PR", "SD", "PD"])
    """
    # Validate inputs
    validate_dataframe(data, "data", "pieplot")
    validate_column_exists(data, x, "x", "pieplot")
    validate_dataframe_not_empty(data, "pieplot")

    df = data[x].value_counts()
    if hue_order is None:
        hue_order = df.index
    ax = plt.gca()
    ax = df.reindex(index=hue_order).plot.pie(
        shadow=False,
        autopct="%1.0f%%",
        explode=[0] * df.shape[0],
        textprops={"fontsize": _legend_fontsize(), "color": "white"},
        labeldistance=None,
        wedgeprops={"linewidth": 0.3, "edgecolor": "white"},
        ax=ax,
        ylabel="",
        legend=True,
    )
    percent_texts = [text for text in ax.texts if text.get_text().endswith("%")]
    for wedge, text in zip(ax.patches, percent_texts):
        text.set_color(utils._annotation_text_color(wedge.get_facecolor()))
    legend_positions = {
        "right": {"loc": "upper left", "bbox_to_anchor": (1, 1.02)},
        "left": {"loc": "upper right", "bbox_to_anchor": (-0.02, 1.02)},
        "top": {"loc": "lower center", "bbox_to_anchor": (0.5, 1.05)},
        "bottom": {"loc": "upper center", "bbox_to_anchor": (0.5, -0.05)},
    }
    pos = legend_positions.get(legend, legend_positions["right"])
    ax.legend(**pos, title=x)
    return ax


def donutplot(
    data: pd.DataFrame,
    x: str,
    legend: str = "bottom",
    hue_order: list[str] | None = None,
) -> Axes:
    """
    Create a donut chart showing categorical proportions.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    x : str
        Column name for the categorical variable to visualize.
    legend : {'right', 'left', 'top', 'bottom'}, default: 'bottom'
        Position of the legend relative to the pie chart.
    hue_order : list, optional
        Order of categories to display in the donut chart.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    pieplot : Create a pie chart without center hole.
    stackplot : Create a stacked bar plot for categorical distributions.
    vennplot : Create a Venn diagram for set overlaps.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.donutplot(data=df, x="tissue_type")
    >>> ax.set_title("Tissue Type Distribution")

    >>> # Specify category order
    >>> ax = cns.donutplot(data=df, x="grade", hue_order=["I", "II", "III", "IV"])
    """
    # Validate inputs
    validate_dataframe(data, "data", "donutplot")
    validate_column_exists(data, x, "x", "donutplot")
    validate_dataframe_not_empty(data, "donutplot")

    df = data[x].value_counts()
    if hue_order is None:
        hue_order = df.index
    ax = plt.gca()
    ax = df.reindex(index=hue_order).plot.pie(
        labeldistance=None,
        ax=ax,
        ylabel="",
        legend=True,
        wedgeprops={"edgecolor": "black", "linewidth": 0.3, "width": 0.4},
    )
    plt.annotate(x, (0, 0), size=_legend_fontsize(), ha="center", va="center")
    utils._remove_edge_from_legend_items(ax)
    legend_positions = {
        "right": {"loc": "upper left", "bbox_to_anchor": (1, 1.02)},
        "left": {"loc": "upper right", "bbox_to_anchor": (-0.02, 1.02)},
        "top": {"loc": "lower center", "bbox_to_anchor": (0.5, 1.05)},
        "bottom": {"loc": "upper center", "bbox_to_anchor": (0.5, -0.05)},
    }
    pos = legend_positions.get(legend, legend_positions["right"])
    ax.legend(**pos, title=x)
    return ax
