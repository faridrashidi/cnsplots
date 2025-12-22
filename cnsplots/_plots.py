from typing import List, Optional, Tuple

import adjustText as at
import gseapy as gp
import lifelines as ll
import matplotlib as mpl
import matplotlib.gridspec as grid_spec
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib_venn as venn
import num2tex
import numpy as np
import palettable
import pandas as pd
import PyComplexHeatmap as pch
import scipy as sp
import seaborn as sns
import statsmodels.api as sm
import upsetplot as usp
from matplotlib.patches import Patch
from natsort import natsort_keygen
from PyComplexHeatmap import DotClustermapPlotter
from scipy.stats import fisher_exact
from sklearn.metrics import ConfusionMatrixDisplay, auc, confusion_matrix, roc_curve

import cnsplots as cns
import cnsplots._helper_heatmap as helper_heatmap
import cnsplots._helper_phylo as helper_phylo
import cnsplots._helper_sankey as helper_sankey
from cnsplots._utils import PALETTE_QUAL, PALETTE_SEQ


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
    legend_hpad=10,
    legend_vpad=0,
    linewidth=0,
    colors=None,
    rasterized=True,
    xticklabels_rotation=45,
    **kwargs,
):
    cat_palettes = ["Set1", "Set2", "Ecotyper1", "Dark2", "Ecotyper2", "Set3"]
    cont_palettes = ["parula", "gnuplot", "bwr", "hot"]
    cbar_titles = [label]
    if cmap in cat_palettes:
        cat_palettes.remove(cmap)
    if cmap in cont_palettes:
        cont_palettes.remove(cmap)
    global cat_counter, cont_counter
    cat_counter, cont_counter = 0, 0

    def _annot_helper(df, rc_annotation):
        rc_dict = {}
        global cat_counter, cont_counter
        for annot in rc_annotation:
            if df.dtypes[annot] == object:
                if df[annot].isna().any():
                    rc_dict[annot] = pch.anno_label(
                        df[annot],
                        colors="black",
                        va="top",
                        ha="right",
                        relpos=(0, 0.4),
                    )
                else:
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
                        colors=colors,
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

    if layer is None:
        df = adata.to_df()
    else:
        df = adata.to_df(layer=layer)
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
        xticklabels_kws={"labelrotation": xticklabels_rotation},
        ylabel_kws={"labelpad": 3},
        xlabel_kws={"labelpad": 5},
        verbose=0,
        row_names_side="left" if row_annotation is None else "right",
        **kwargs,
    )
    for cbar in cmp.cbars:
        if isinstance(cbar, mpl.colorbar.Colorbar):
            cbar.outline.set_linewidth(0.3)
            cbar.ax.tick_params(size=0)
    for ax in cmp.legend_axes[0].figure.axes:
        if ax.get_ylabel() in cbar_titles:
            ax.yaxis.set_label_position("left")
            # if ax.get_ylabel() == label:
            #     ax.set_aspect(0.3)
            # else:
            #     ax.set_aspect(6)
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
    value,
    legend_width=20,
    legend_hpad=10,
    legend_vpad=0,
    xticklabels_rotation=45,
    **kwargs,
):
    row_annotation = pch.HeatmapAnnotation(
        axis=0,
        verbose=0,
        label=pch.anno_label(
            data.pivot(index="day", columns="sex", values=y)[data[x].unique()[0]],
            colors="black",
            va="center",
            ha="right",
            relpos=(1, 0.5),
        ),
    )
    cmp = DotClustermapPlotter(
        data=data,
        x=x,
        y=y,
        c=color,
        s=size,
        value=value,
        row_cluster=False,
        col_cluster=False,
        show_rownames=False,
        show_colnames=True,
        left_annotation=row_annotation,
        verbose=0,
        cmap="gnuplot",
        rasterized=True,
        row_names_side="left",
        xlabel=x,
        ylabel=y,
        ylabel_kws={"labelpad": 10},
        xlabel_kws={"labelpad": 15},
        legend_width=legend_width,
        legend_hpad=legend_hpad,
        legend_vpad=legend_vpad,
        xticklabels_kws={"labelrotation": xticklabels_rotation},
        dot_legend_kws={"frameon": False},
        **kwargs,
    )
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
    """Create a box plot.
    Plot the median of y categorized by x.

    Parameters
    ----------
    data
        The input DataFrame that holds the data to be plotted.
    x
        The label for the x-axis.
    y
        The label for the y-axis.
    pairs
        A list of pairs of x attributes for calculating the p-values.
    showoutliers
        A Boolean to show outliers on the boxes.
    whis
        The proportion of the IQR past the low and high quartiles to extend the plot whiskers.
        Use (0, 100) to extend the whiskers to the minimum and maximum values.
    **kwargs
        Keyword arguments passed to the `seaborn.boxplot` function.

    Returns
    -------
    None
        This function creates a plot and does not return anything.
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
        patch for patch in ax.patches if type(patch) == mpl.patches.PathPatch
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
    """Create a violin plot.

    Parameters
    ----------
    data
        The input DataFrame that holds the data to be plotted.
    x
        The label for the x-axis.
    y
        The label for the y-axis.
    pairs
        A list of pairs of x attributes for calculating the p-values.
    **kwargs
        Keyword arguments passed to the `seaborn.violinplot` function.

    Returns
    -------
    None
        This function creates a plot and does not return anything.
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
    ax = sns.violinplot(linewidth=0, width=width, **plotting)
    plotting.update(args)
    plotting.update(kwargs)
    if add_box:
        sns.boxplot(**plotting)
    if pairs is not None:
        cns._utils._p_value_helper("Mann-Whitney", data, ax, plotting, pairs)


def barplot(data, x, y, pairs=None, addtip=False, **kwargs):
    """
    Creates a bar plot showing the mean value of a variable across different categories.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame that holds the data to be plotted.
    x : str
        The column name in data to use for categorical values on the x-axis.
    y : str
        The column name in data whose mean values will be plotted on the y-axis.
    pairs : List[Tuple[str, str]], optional
        A list of pairs of x attributes for calculating pairwise statistical significance.
        Each pair should be a tuple of two category names present in the x column.
        Default is None (no statistical tests).
    addtip : bool, optional
        If True, adds text labels showing the mean value above each bar.
        Default is False.
    **kwargs
        Additional keyword arguments passed to the seaborn.barplot function.
        Common options include:
        - color: Set the bar color
        - palette: Color palette for different categories or a column name
        - alpha: Transparency of the bars
        - order: Specify the order of categories on the x-axis

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.
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
        which_numeric = None
        if not pd.api.types.is_numeric_dtype(data[x]):
            which_numeric = x
        else:
            which_numeric = y
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
    """Plot the value of y categorized by x and grouped by hue."""
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
    args = {"kde": True, "edgecolor": None}
    args.update(kwargs)
    sns.histplot(data=data, x=x, **args)


def kdeplot(data, x, add_mode=True, **kwargs):
    ax = sns.kdeplot(data=data, x=x, linewidth=1, **kwargs)
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
        if add_mode:
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


def regplot(data, x, y, hue=None, s=3, **kwargs):
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
            "   ---> P-value was determined by two-sided multivariate log-rank test for"
            " trend."
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

        pvalue = cmprsk.cuminc(data[duration], data[event], group=data[hue].cat.codes)
        p = num2tex.num2tex(pvalue.stats["pv"].values[0], precision=2)
        print("   ---> P-value was determined by two-sided Gray's test.")
        ax.text(pvalue_position[0], pvalue_position[1], f"P = " + rf"${p:.2g}$")
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
    hue = "DEG"
    n_show = 10
    de = data.copy()

    de[hue] = "NS"
    de.loc[de[y] > -np.log10(0.05), hue] = "p_adj < 0.05"
    up = (de[y] > -np.log10(0.05)) & (de[x] > 0.5)
    down = (de[y] > -np.log10(0.05)) & (de[x] < -0.5)
    if show_list is None:
        de.loc[de.loc[up].nlargest(n_show, y).index, hue] = "Up"
        de.loc[de.loc[down].nlargest(n_show, y).index, hue] = "Down"
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


def histplot(**kwargs):
    sns.histplot(**kwargs)


def lineplot(**kwargs):
    sns.lineplot(**kwargs)


def scatterplot(data, x, y, s=7, **kwargs):
    sns.scatterplot(data=data, x=x, y=y, s=s, edgecolor=None, **kwargs)


def upsetplot(data, **kwargs):
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
        except:
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
    Plot a confusion matrix even when predicted (x) and true (y) labels
    use different vocabularies or types (e.g., str vs int).

    Parameters
    ----------
    data : pd.DataFrame
    x : str
        Column with predictions.
    y : str
        Column with ground truth.
    x_order, y_order : list, optional
        Explicit label orders for columns (pred) and rows (truth).
        Defaults to the order of first appearance.
    positive_x, positive_y : hashable, optional
        The label to treat as 'positive' in predictions and truth when computing
        binary metrics. If not given, the second label in the corresponding order
        is used (i.e., last of the two).
    add_pvalue : bool
        If True and the matrix is 2×2, compute specificity, sensitivity, PPV, NPV,
        Cohen’s kappa, Fisher’s exact p-value, and odds ratio.
    annot : bool
        Write the integer counts in each cell.
    cmap : matplotlib colormap
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
    for edge, spine in ax.spines.items():
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
        if positive_y is None:
            pos_y = y_order[-1]  # default: last of the two
        else:
            pos_y = positive_y
        neg_y = [lbl for lbl in y_order if lbl != pos_y][0]

        if positive_x is None:
            pos_x = x_order[-1]
        else:
            pos_x = positive_x
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
            )

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
    ax = plt.gca()
    current_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    keys = np.union1d(data[x].unique(), data[y].unique())
    color_dict = dict(zip(keys, current_colors))
    helper_sankey.sankeyplot(data[x], data[y], fontsize=6, colorDict=color_dict, ax=ax)


def phyloplot(adata):
    # TODO: write examples
    helper_phylo.phyloplot(adata)


def forestplot(model):
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
    if n_hue_groups > 1:
        offsets = np.linspace(-max_offset, max_offset, n_hue_groups)
    else:
        offsets = [0]
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
    countries = data[y].unique()
    colors = cns._utils._get_hex_colors_from_colorbar("viridis", len(countries))
    gs = grid_spec.GridSpec(len(countries), 1)
    fig = plt.gcf()
    i = 0
    ax_objs = []
    for country in countries:
        country = countries[i]
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
        i += 1
    gs.update(hspace=-0.5)


def slopeplot(data, x, y, hue):
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
    plt.legend(loc="lower right")
    plt.legend(loc="lower right")


def gseaplot(
    data, y, color="NES", cutoff=0.05, cmap="RdBu_custom", top_term=20, size=1.8
):
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
