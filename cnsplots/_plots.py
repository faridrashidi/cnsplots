import itertools

import lifelines as ll
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy as sp
import seaborn as sns
from statannotations.Annotator import Annotator

import cnsplots as cns


def figure(height=150, width=150):
    fig = plt.figure(figsize=(width / 72, height / 72), dpi=72)
    # ax = fig.subplots(1)
    # ax.xaxis.labelpad = 1
    # return fig


def boxplot(data, x, y, pairs=None, **kwargs):
    """Plot the median of y categorized by x."""
    args = {
        "showfliers": False,
        "linewidth": 0.8,
        "boxprops": {"edgecolor": "white"},
        "medianprops": {"color": "white"},
        "whiskerprops": {"color": "black"},
        "capprops": {"color": "white"},
        "flierprops": {
            "markerfacecolor": "purple",
            "markersize": 3,
            "markeredgecolor": "purple",
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
    plotting.update(kwargs)
    plotting.update(args)
    ax = sns.boxplot(**plotting)
    # sns.stripplot(data=data, x=x, y=y, size=3, linewidth=0)
    print(
        "Boxplots represent the median and bottom and upper quartiles; whiskers"
        " correspond to 1.5 times the interquartile range."
    )
    if pairs is not None:
        _p_value_helper("Mann-Whitney", data, x, ax, plotting, pairs)


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
    plotting.update(kwargs)
    plotting.update(args)
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
        _p_value_helper("t-test_welch", data, x, ax, plotting, pairs)


def stackplot(data, x, hue, normalize=True):
    args = {
        "edgecolor": None,
        "alpha": 1,
        "shrink": 0.7,
    }
    if normalize:
        ax = sns.histplot(data=data, x=x, hue=hue, multiple="fill", **args)
        ax.set_ylabel("Frequency")
        # TODO: calculate the p-value
        print("P values were determined by two-sided Fisher's exact test")
    else:
        sns.histplot(data=data, x=x, hue=hue, multiple="stack", **args)


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
    g.text(6, 4.5, rf"$\rho$={r:.2f}, $P$={p:.2g}")


def piechart(data, x, order=None):
    df = data[x].value_counts()
    if order is None:
        order = df.index
    df.reindex(index=order).plot.pie(
        shadow=True,
        autopct="%1.0f%%",
        explode=[0] * df.shape[0],
        textprops={"fontsize": 6, "color": "white"},
    )


def _p_value_helper(test, data, x, ax, plotting, pairs):
    if pairs == "all":
        pairs = list(itertools.combinations(data[x].unique(), 2))
    annotator = Annotator(ax, pairs, **plotting)
    annotator.configure(
        test=test,
        text_format="full",
        loc="inside",
        line_width=0.8,
        text_offset=0.5,
        color="black",
        show_test_name=False,
        pvalue_format_string="{:.1e}",
    )
    annotator.apply_and_annotate()
    if test == "Mann-Whitney":
        print("P values were determined by two-sided Mann-Whitney U test.")
    if test == "t-test_welch":
        print("P values were determined by two-sided Welch's t-test.")


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
    ax.text(0, 0, rf"$P$={p_value.p_value:.2g}")
    print("P-value was determined by two-sided log-rank test.")


def heatmap_back(adata, row_colors=None, col_colors=None, **kwargs):
    from heatmap_grammar import (
        Annotation,
        ColumnAnnotation,
        Heatmap,
        HeatmapTheme,
        Plot,
        RowAnnotation,
        aes,
        scale_color_brewer,
        scale_color_gradient,
        scale_fill_brewer,
    )

    col_annot = ColumnAnnotation(adata.var)
    if col_colors is not None:
        for annot in col_colors:
            col_annot += Annotation(geom="simple", mapping=aes(color=annot))
            if adata.var[annot].nunique() < 10:
                col_annot += scale_color_brewer(palette="Set1")
        kwargs.update({"top_annotation": col_annot})

    plot = (
        Plot().size(w=200, h=500)
        + Heatmap(adata.to_df(), **kwargs)
        + HeatmapTheme(heatmap_legend_side="bottom")
    )

    if np.unique(adata.X).shape[0] < 10:
        plot += scale_fill_brewer(palette="Set1")

    row_annot = RowAnnotation(adata.obs)
    if row_colors is not None:
        for annot in row_colors:
            row_annot += Annotation(geom="simple", mapping=aes(color=annot))
            if adata.obs[annot].nunique() < 10:
                row_annot += scale_color_brewer(palette="Set1")
            else:
                row_annot += scale_color_gradient(low="white", high="green")
        plot += row_annot

    return plot


def heatmap(
    adata, row_annotation=None, col_annotation=None, row_split=None, col_split=None
):
    from PyComplexHeatmap import ClusterMapPlotter, HeatmapAnnotation

    # TODO: frameon=False for legends
    rs = None
    if row_split is not None:
        rs = adata.obs[row_split]
    cs = None
    if col_split is not None:
        cs = adata.var[col_split]

    row_annot = None
    if row_annotation is not None:
        row_dict = {}
        for annot in row_annotation:
            row_dict[annot] = adata.obs[annot]
        row_annot = HeatmapAnnotation(axis=0, **row_dict)

    col_annot = None
    if col_annotation is not None:
        col_dict = {}
        for annot in col_annotation:
            col_dict[annot] = adata.var[annot]
        col_annot = HeatmapAnnotation(axis=1, **col_dict)

    ClusterMapPlotter(
        data=adata.to_df(),
        left_annotation=row_annot,
        top_annotation=col_annot,
        row_cluster=True,
        col_cluster=True,
        row_cluster_method="ward",
        row_cluster_metric="euclidean",
        col_cluster_method="ward",
        col_cluster_metric="euclidean",
        show_rownames=True,
        show_colnames=True,
        row_dendrogram=False,
        col_dendrogram=False,
        row_split=rs,
        col_split=cs,
        cmap="parula",
        # row_split_gap=1,
        # col_split_gap=1,
        label="value",
        # tree_kws={"col_cmap": "Set1"},
        legend_kws={},
        # xticklabels_kws={"labelrotation": 90},
        # yticklabels_kws={},
        rasterized=True,
    )
