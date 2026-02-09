import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch

import cnsplots as cns
from cnsplots._validation import (
    validate_column_exists,
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
)


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
        cns.utils._p_value_helper("t-test_welch", data, ax, plotting, pairs)
    if show_legend:
        ax.legend(
            handles=legend_handles,
            title=group_col,
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
        )

    return ax


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
    addtip : bool, default: False
        Whether to add total count labels above/beside each bar when normalize=True.
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
            cns.utils._p_value_helper(
                "fisher-exact", data2, ax, plotting, pairs, contingency
            )
        else:
            cns.utils._p_value_helper(
                "chi-squared", data2, ax, plotting, pairs, contingency
            )

    return ax


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
        cns.utils._addcount_helper(data, x, ax)

    if ax.get_legend() is not None:
        for handle in ax.get_legend().legend_handles:
            if hasattr(handle, "set_sizes"):
                handle.set_sizes([size**2])
            elif hasattr(handle, "set_markersize"):
                handle.set_markersize(size * 2)

    return ax


def pieplot(data, x, legend="bottom", hue_order=None):
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
        textprops={"fontsize": 6, "color": "white"},
        labeldistance=None,
        wedgeprops={"linewidth": 0.3, "edgecolor": "white"},
        ax=ax,
        ylabel="",
        legend=True,
    )
    legend_positions = {
        "right": {"loc": "upper left", "bbox_to_anchor": (1, 1.02)},
        "left": {"loc": "upper right", "bbox_to_anchor": (-0.02, 1.02)},
        "top": {"loc": "lower center", "bbox_to_anchor": (0.5, 1.05)},
        "bottom": {"loc": "upper center", "bbox_to_anchor": (0.5, -0.05)},
    }
    pos = legend_positions.get(legend, legend_positions["right"])
    ax.legend(**pos, title=x)
    return ax


def donutplot(data, x, legend="bottom", hue_order=None):
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
        wedgeprops={"edgecolor": "black", "linewidth": 0.3},
    )
    ax.add_patch(
        plt.Circle(
            (0, 0), radius=0.6, facecolor="white", edgecolor="black", linewidth=0.3
        )
    )
    plt.annotate(x, (0, 0), size=7, ha="center", va="center")
    cns.utils._remove_edge_from_legend_items(ax)
    legend_positions = {
        "right": {"loc": "upper left", "bbox_to_anchor": (1, 1.02)},
        "left": {"loc": "upper right", "bbox_to_anchor": (-0.02, 1.02)},
        "top": {"loc": "lower center", "bbox_to_anchor": (0.5, 1.05)},
        "bottom": {"loc": "upper center", "bbox_to_anchor": (0.5, -0.05)},
    }
    pos = legend_positions.get(legend, legend_positions["right"])
    ax.legend(**pos, title=x)
    return ax
