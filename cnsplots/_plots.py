import itertools

import adjustText as at
import lifelines as ll
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import PyComplexHeatmap as pch
import scipy as sp
import seaborn as sns
import statannotations.Annotator as saa


def figure(height=150, width=150):
    plt.figure(figsize=(width / 72, height / 72), dpi=72)


def heatmap(
    adata,
    row_annotation=None,
    col_annotation=None,
    row_split=None,
    col_split=None,
    rasterized=True,
    cmap="parula",
    label="value",
    **kwargs,
):
    # https://github.com/DingWB/PyComplexHeatmap/blob/main/PyComplexHeatmap/clustermap.py
    cat_palettes = ["Set1", "Dark2", "Set3"]
    cont_palettes = ["parula", "gnuplot", "bwr"]
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
                rc_dict[annot] = pch.anno_simple(
                    df[annot],
                    cmap=cat_palettes[cat_counter],
                    legend_kws={
                        "frameon": False,
                        "labelspacing": 0.2,
                        "handletextpad": 0.4,
                        "color_text": False,
                    },
                    height=3,
                    rasterized=False,
                )
                cat_counter += 1
            else:
                rc_dict[annot] = pch.anno_simple(
                    df[annot],
                    cmap=cont_palettes[cont_counter],
                    height=3,
                    rasterized=False,
                    # vmin=0.5,  # FIXME: it's ok but it doesn't change the values on colorbar!
                    # vmax=0.6,
                )
                cont_counter += 1
        return rc_dict

    if row_annotation is not None:
        rc_dict = _annot_helper(adata.obs, row_annotation)
        rc_dict["selected"] = pch.anno_label(adata.obs["selected"], colors="black")
        row_annotation = pch.HeatmapAnnotation(
            axis=0,
            # label_side="bottom",
            # label_kws={
            #     "rotation": 90,
            #     "rotation_mode": "anchor",
            #     "horizontalalignment": "right",
            #     "verticalalignment": "top",
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

    # TODO: how to control which ylables to be shown
    # TODO: change width of colorbars
    # TODO: change title colorbars to left
    # TODO: horizontal colorbars
    # TODO: change discrete legend labels order
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
        # dendrogram_kws={"truncate_mode": "lastp", "p": 5},  # FIXME: not working!
        **kwargs,
    )
    for cbar in cmp.cbars:
        if isinstance(cbar, mpl.colorbar.Colorbar):
            cbar.outline.set_linewidth(0.3)
    cmp.ax.spines[["right", "left", "top", "bottom"]].set_visible(False)
    return cmp


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


def stackplot(data, x, hue, normalize=True, pairs=None):
    args = {
        "edgecolor": None,
        "alpha": 1,
        "shrink": 0.7,
    }
    plotting = {
        "data": data,
        "x": x,
        "hue": hue,
    }
    plotting.update(args)
    if normalize:
        ax = sns.histplot(multiple="fill", **plotting)
        ax.set_ylabel("Frequency")
    else:
        sns.histplot(multiple="stack", **plotting)
    # TODO: calculate the p-value
    # print("P values were determined by two-sided Fisher's exact test")
    if pairs is not None:
        _p_value_helper("t-test_ind", data, x, ax, plotting, pairs)


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
    annotator = saa.Annotator(ax, pairs, **plotting)
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
