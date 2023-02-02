from typing import List, Optional, Tuple

import adjustText as at
import lifelines as ll
import matplotlib as mpl
import matplotlib.pyplot as plt
import num2tex
import pandas as pd
import PyComplexHeatmap as pch
import scipy as sp
import scipy.stats as stats
import seaborn as sns
from natsort import natsort_keygen

import cnsplots as cns


def heatmap(
    adata,
    row_annotation=None,
    col_annotation=None,
    row_split=None,
    col_split=None,
    rasterized=True,
    cmap="parula",
    label="value",
    linewidth=0,
    **kwargs,
):
    cat_palettes = ["Set1", "Dark2", "Set3"]
    cont_palettes = ["parula", "gnuplot", "bwr"]
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
                        # arrowprops={
                        #     "color": "red",
                        #     "connectionstyle": None,
                        #     "arrowstyle": "-",
                        #     "shrinkA": 0.1,
                        #     "shrinkB": 0.1,
                        #     "patchA": None,
                        #     "patchB": None,
                        # },
                    )
                else:
                    rc_dict[annot] = pch.anno_simple(
                        df[annot].sort_values(key=natsort_keygen()),
                        cmap=cat_palettes[cat_counter],
                        legend_kws={
                            "frameon": False,
                            "labelspacing": 0.2,
                            "handletextpad": 0.4,
                            "color_text": False,
                        },
                        height=3,
                        rasterized=False,
                        linewidth=0,
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
            # label_side="bottom",
            # label_kws={
            #     "rotation": 90,
            #     "rotation_mode": "anchor",
            #     "horizontalalignment": "right",
            #     "verticalalignment": "center",
            # },  # for bringing the labels to bottom
            **rc_dict,
        )
    if col_annotation is not None:
        ca_dict = _annot_helper(adata.var, col_annotation)
        col_annotation = pch.HeatmapAnnotation(axis=1, **ca_dict)

    if row_split is not None and not isinstance(row_split, int):
        row_split = adata.obs[row_split]
    if col_split is not None and not isinstance(row_split, int):
        col_split = adata.var[col_split]

    cmp = pch.ClusterMapPlotter(
        data=adata.to_df(),
        left_annotation=row_annotation,
        top_annotation=col_annotation,
        row_split=row_split,
        col_split=col_split,
        cmap=cmap,
        rasterized=rasterized,
        label=label,
        legend_gap=5,
        legend_width=2,
        row_dendrogram_size=10,
        col_dendrogram_size=10,
        linewidth=linewidth,
        xticklabels_kws={"labelrotation": 90},
        # dendrogram_kws={"truncate_mode": "lastp", "p": 5},
        **kwargs,
    )
    for cbar in cmp.cbars:
        if isinstance(cbar, mpl.colorbar.Colorbar):
            cbar.outline.set_linewidth(0.3)
            cbar.ax.tick_params(size=0)
    for ax in cmp.legend_axes[0].figure.axes:
        if ax.get_ylabel() in cbar_titles:
            ax.yaxis.set_label_position("left")
    plt.setp(
        cmp.heatmap_axes[-1, 0].get_xticklabels(), rotation_mode="anchor", ha="right"
    )
    return cmp


def boxplot(data, x, y, pairs=None, **kwargs):
    """Plot the median of y categorized by x."""
    args = {
        "showfliers": False,
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
    plotting = {
        "data": data,
        "x": x,
        "y": y,
    }
    plotting.update(args)
    plotting.update(kwargs)
    ax = sns.boxplot(**plotting)
    # sns.stripplot(data=data, x=x, y=y, size=3, linewidth=0)
    print(
        "Boxplots represent the median and bottom and upper quartiles; whiskers"
        " correspond to 1.5 times the interquartile range."
    )
    if pairs is not None:
        cns._p_value_helper("Mann-Whitney", data, x, ax, plotting, pairs)


def violinplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    pairs: Optional[List[Tuple[str, str]]] = None,
    **kwargs,
):
    """Build violinplot.

    Parameters
    ----------
    data
        slam
    x
        slam
    y
        slam
    pairs
        slam, by default None
    **kwargs
        Keyword args for :func:`seaborn.violinplot`
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
    plotting = {
        "data": data,
        "x": x,
        "y": y,
    }
    plotting.update(kwargs)
    ax = sns.violinplot(linewidth=0, width=0.6, **plotting)
    plotting.update(args)
    plotting.update(kwargs)
    sns.boxplot(**plotting)
    if pairs is not None:
        cns._p_value_helper("Mann-Whitney", data, x, ax, plotting, pairs)


def barplot(data, x, y, pairs=None, addtip=False, **kwargs):
    """Plot the mean of y categorized by x."""
    args = {
        "edgecolor": None,
        "linewidth": 1,
        "ci": None,
    }
    plotting = {
        "data": data,
        "x": x,
        "y": y,
    }
    plotting.update(args)
    plotting.update(kwargs)
    ax = sns.barplot(**plotting)
    # sns.stripplot(data=data, x=x, y=y, size=3, linewidth=0)
    if addtip:
        groupedvalues = data.groupby(x).mean().reset_index()
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
        cns._p_value_helper("t-test_welch", data, x, ax, plotting, pairs)


def stackplot(data, x, y, hue, hue_order=None, width=0.5, normalize=True, pairs=None):
    """Plot the value of y categorized by x and grouped by hue."""
    df = data.pivot(index=x, columns=hue, values=y)
    df2 = df.copy()
    if hue_order is not None:
        df.columns = pd.CategoricalIndex(
            df.columns.values, ordered=True, categories=hue_order, name=hue
        )
        df = df.sort_index(axis=1)
    ax = plt.gca()
    if normalize:
        df = df.div(df.sum(axis=1), axis=0)
        ylabel = "Frequency"
    else:
        ylabel = "Count"
    ax = df.plot.bar(stacked=True, width=width, ax=ax, rot=0)
    ax.set_ylabel(ylabel)
    cns.take_legend_out()
    if pairs is not None:
        plotting = {"data": df2.T}
        pvalues = []
        if df2.shape[1] == 2:
            for pair in pairs:
                pvalues.append(stats.fisher_exact(df2.loc[list(pair)].values)[1])
            cns._p_value_helper("fisher-exact", data, x, ax, plotting, pairs, pvalues)
        else:
            for pair in pairs:
                pvalues.append(stats.chi2_contingency(df2.loc[list(pair)].values)[1])
            cns._p_value_helper("chi-squared", data, x, ax, plotting, pairs, pvalues)


def distplot(data, x):
    args = {"kde": True, "edgecolor": None}
    sns.histplot(data=data, x=x, **args)


def regplot(data, x, y):
    args = {
        "line_kws": {"color": "blue", "lw": 1.5},
        "scatter_kws": {"s": 3, "color": "black", "edgecolor": "black", "alpha": 1},
    }
    r, p = sp.stats.pearsonr(data[x], data[y])
    g = sns.regplot(data=data, x=x, y=y, **args)
    g.text(6, 4.5, rf"$\rho$={r:.2f}, $P={num2tex.num2tex(p, precision=2):.2g}$")


def piechart(data, x, hue_order=None):
    df = data[x].value_counts()
    if hue_order is None:
        hue_order = df.index
    ax = plt.gca()
    ax = df.reindex(index=hue_order).plot.pie(
        shadow=True,
        autopct="%1.0f%%",
        explode=[0] * df.shape[0],
        textprops={"fontsize": 6, "color": "white"},
        labeldistance=None,
        ax=ax,
        ylabel="",
        legend=True,
    )
    cns.take_legend_out(title=x)


def survivalplot(data, duration, event, hue):
    ax = None
    kmf = ll.KaplanMeierFitter()
    for i, group in enumerate(data[hue].unique()):
        df = data[data[hue] == group]
        kmf.fit(df[duration], df[event], label=group)
        if i != 0:
            ax = kmf.plot_survival_function(linewidth=1.2, ci_show=False)
        else:
            ax = kmf.plot_survival_function(ax=ax, linewidth=1.2, ci_show=False)

    df = data.copy()
    df[hue] = pd.Categorical(df[hue], categories=df[hue].unique()).codes + 1
    p_value = ll.statistics.multivariate_logrank_test(
        data[duration], data[hue], df[event]
    )
    ax.text(0, 0, rf"$P={num2tex.num2tex(p_value.p_value, precision=2):.2g}$")

    print("P-value was determined by two-sided log-rank test.")


def volcanoplot(data, x="log2FoldChange", y="-log10(adjp)", hue="DEG", symbol="symbol"):
    ax = sns.scatterplot(
        data=data,
        x=x,
        y=y,
        size=hue,
        sizes=[2, 2, 10, 10],
        hue=hue,
        edgecolor=None,
        palette=sns.xkcd_palette(["black", "grey", "blue", "red"]),
    )

    annotations = []
    for mode, color in [("Up", "red"), ("Down", "blue")]:
        for _, (x0, y0, t) in data.loc[data[hue] == mode, [x, y, symbol]].iterrows():
            annotations.append(plt.annotate(t, (x0, y0), color=color, size=6))
    at.adjust_text(
        annotations, arrowprops={"arrowstyle": "-", "color": "black", "lw": 0.5}
    )

    ax.spines["right"].set_visible(True)
    ax.spines["top"].set_visible(True)
    ax.set_xlabel("log2(fold change)")
    ax.set_ylabel("–log 10(adjusted p-value)")
    plt.plot(
        [0, 0],
        [0, max(data[y])],
        color="black",
        linestyle="--",
        linewidth=0.8,
        dashes=(8, 5),
    )
    cns.take_legend_out()
