from typing import List, Optional, Tuple

import adjustText as at
import lifelines as ll
import matplotlib as mpl
import matplotlib.category
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
from natsort import natsort_keygen
from PyComplexHeatmap import DotClustermapPlotter
from sklearn.metrics import ConfusionMatrixDisplay, auc, confusion_matrix, roc_curve

import cnsplots as cns
import cnsplots._helper_heatmap as helper_heatmap
import cnsplots._helper_phylo as helper_phylo
import cnsplots._helper_sankey as helper_sankey


def heatmapplot(
    adata,
    layer=None,
    row_annotation=None,
    col_annotation=None,
    row_cluster=False,
    col_cluster=False,
    row_split=None,
    col_split=None,
    cmap="parula",
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
    print(
        "Boxplots represent the median and bottom and upper quartiles; whiskers"
        " correspond to 1.5 times the interquartile range."
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
    ax = sns.violinplot(linewidth=0, width=0.6, **plotting)
    plotting.update(args)
    plotting.update(kwargs)
    sns.boxplot(**plotting)
    if pairs is not None:
        cns._utils._p_value_helper("Mann-Whitney", data, ax, plotting, pairs)


def barplot(data, x, y, pairs=None, addtip=False, **kwargs):
    """Plot the mean of y categorized by x."""
    args = {"edgecolor": None, "linewidth": 1, "errorbar": None}
    plotting = {"data": data, "x": x, "y": y}

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


def regplot(data, x, y):
    args = {
        "line_kws": {"color": "#377EB8", "lw": 1.5},
        "scatter_kws": {"s": 3, "color": "black", "edgecolor": "black", "alpha": 1},
    }
    rho, p_value = sp.stats.pearsonr(data[x], data[y])
    ax = sns.regplot(data=data, x=x, y=y, **args)
    ax.text(
        ax.get_xlim()[0] * 2,
        ax.get_ylim()[1] * 0.9,
        rf"$\rho$={rho:.2f}, $P={num2tex.num2tex(p_value, precision=2):.2g}$",
    )


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
    data, duration, event, hue, hue_order=None, pvalue_position=(0, 0.5)
):
    ax = None
    if hue_order is None or set(data[hue].unique()) != set(hue_order):
        hue_order = list(data[hue].unique())
    data[hue] = pd.Categorical(data[hue], categories=hue_order, ordered=True)
    data = data.sort_values(hue)
    ajf = ll.AalenJohansenFitter()
    for i, group in enumerate(hue_order):
        df = data[data[hue] == group]
        label = f"{group} (n={df.shape[0]})"
        ajf.fit(df[duration], df[event], label=label, event_of_interest=1)
        df = pd.merge(
            ajf.cumulative_density_.reset_index(drop=False),
            df,
            how="outer",
            left_on="event_at",
            right_on=duration,
        )
        df = df.loc[df[event] == 0].copy()
        if i == 0:
            ax = ajf.plot(linewidth=1, ci_show=False)
        else:
            ax = ajf.plot(ax=ax, linewidth=1, ci_show=False)
        line_color = ax.get_lines()[-1].get_color()
        ax.plot(df[duration], df["CIF_1"], "+", markersize=3, color=line_color)
    plt.ylim(-0.05, 1.01)
    plt.ylabel("Cumulative incidence probability")
    plt.xlabel("Time (Years)")

    try:
        from cmprsk import cmprsk

        pvalue = cmprsk.cuminc(data[duration], data[event], group=data[hue].cat.codes)
        p = num2tex.num2tex(pvalue.stats["pv"].values[0], precision=2)
        print("   ---> P-value was determined by two-sided Gray's test.")
        ax.text(pvalue_position[0], pvalue_position[1], f"P = " + rf"${p:.2g}$")
    except ImportError:
        print("pip install cmprsk")


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

    ax = sns.scatterplot(
        data=de,
        x=x,
        y=y,
        size=hue,
        sizes={"Down": 10, "NS": 2, "Up": 10, "p_adj < 0.05": 2},
        hue=hue,
        edgecolor=None,
        palette={"Down": "blue", "NS": "grey", "Up": "red", "p_adj < 0.05": "black"},
        rasterized=True,
    )

    annotations = []
    for mode, color in [("Up", "red"), ("Down", "blue")]:
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


def stripplot(data, x, y, size=2, showmedian=True, showmeans=False, **kwargs):
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


def histplot(**kwargs):
    sns.histplot(**kwargs)


def lineplot(**kwargs):
    sns.lineplot(**kwargs)


def scatterplot(data, x, y, s=7, **kwargs):
    sns.scatterplot(data=data, x=x, y=y, s=s, edgecolor=None, **kwargs)


def upsetplot(data, **kwargs):
    upset = usp.UpSet(data, **kwargs)
    upset.plot()
    plt.grid(False)


def vennplot(lists, labels):
    if len(lists) == 2:
        areas = ["10", "01", "11"]
        func = venn.venn2
        names = ["A", "B"]
        colors = cns.palettes("Set1")[:2]
    else:
        areas = ["100", "010", "001", "110", "101", "011", "111"]
        func = venn.venn3
        names = ["A", "B", "C"]
        colors = cns.palettes("Set1")[:3]
    ax = func(
        lists,
        labels,
        set_colors=colors,
        alpha=0.8,
    )
    for area in areas:
        ax.get_label_by_id(area).set_fontsize(6)
        ax.get_patch_by_id(area).set_edgecolor("black")
        ax.get_patch_by_id(area).set_linewidth(0.5)
    for area in names:
        ax.get_label_by_id(area).set_fontsize(7)


def confusionplot(data, x, y, add_pvalue=False):
    labels = data[x].unique()
    cm = confusion_matrix(data[y], data[x], labels=labels)
    cmd = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)

    ax = plt.gca()
    cmd.plot(ax=ax, cmap=plt.cm.Blues)
    cmd.ax_.spines["right"].set_visible(True)
    cmd.ax_.spines["top"].set_visible(True)
    cmd.ax_.set_xlabel(x)
    cmd.ax_.set_ylabel(y)
    plt.yticks(rotation=90, va="center")
    colorbar = cmd.ax_.images[-1].colorbar
    colorbar.remove()

    if add_pvalue:
        tn, fp, fn, tp = cm.ravel()
        specificity = tn / (tn + fp)
        sensitivity = tp / (tp + fn)
        ppv = tp / (tp + fp)
        npv = tn / (tn + fn)
        po = (tp + tn) / (tp + tn + fp + fn)
        pe = ((tp + fp) * (tp + fn) + (tn + fp) * (tn + fn)) / (tp + tn + fp + fn) ** 2
        kappa = (po - pe) / (1 - pe)
        _, p_value = sp.stats.fisher_exact([[tp, fp], [fn, tn]])
        odds_ratio = (tp * tn) / (fp * fn)

        fig = plt.gcf()
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
        ax2.text(-0.25, -1.5, msg, ha="left", va="bottom")


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
    data = model.results
    if model.name == "cox":
        y = "display_label"
        x1 = "exp(coef)"
        x2 = "log10_pvalue"
        x1err = ["exp(coef) lower 95%", "exp(coef) upper 95%"]
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
    ax1.errorbar(
        data[x1],
        data[y],
        xerr=data[x1err].T.values,
        fmt="s",
        markeredgewidth=0.8,
        elinewidth=0.8,
        capsize=1.5,
        markersize=3,
    )
    if not isinstance(
        ax1.get_yaxis().get_major_locator(), matplotlib.category.StrCategoryLocator
    ):
        ax1.locator_params(axis="y", tight=True, nbins=2)
    ax1.set_xlabel(x1label)

    if model.name == "cox":
        ax1.plot(
            [1, 1],
            [0, len(data) - 1],
            color="red",
            linestyle="--",
            linewidth=0.8,
            dashes=(3, 2),
        )
        ax1.xaxis.set_major_locator(plt.MultipleLocator(1))
    else:
        ax1.plot(
            [0.5, 0.5],
            [0, len(data) - 1],
            color="red",
            linestyle="--",
            linewidth=0.8,
            dashes=(3, 2),
        )
        # ax1.set_xlim(0.47, 1.03)

    if model.name == "cox":
        ax2 = fig.add_subplot(gs[1])
        data[x2].plot.barh(width=0.5, ax=ax2, rot=0, edgecolor=None, linewidth=1)
        ax2.set_ylabel("")
        ax2.set_xlabel(x2label)
        ax2.plot(
            [-np.log10(0.05), -np.log10(0.05)],
            [-1, len(data)],
            color="red",
            linestyle="--",
            linewidth=0.8,
            dashes=(3, 2),
        )
        ax2.yaxis.set_ticks([])
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
