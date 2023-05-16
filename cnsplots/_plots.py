from typing import List, Optional, Tuple

import adjustText as at
import lifelines as ll
import matplotlib as mpl
import matplotlib.gridspec as grid_spec
import matplotlib.pyplot as plt
import matplotlib_venn as venn
import num2tex
import numpy as np
import palettable
import pandas as pd
import PyComplexHeatmap as pch
import scipy as sp
import seaborn as sns
import upsetplot as usp
from natsort import natsort_keygen
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

import cnsplots as cns
import cnsplots._helper_heatmap as helper_heatmap
import cnsplots._helper_phylo as helper_phylo
import cnsplots._helper_sankey as helper_sankey


def heatmapplot(
    adata,
    row_annotation=None,
    col_annotation=None,
    row_cluster=False,
    col_cluster=False,
    row_split=None,
    col_split=None,
    rasterized=True,
    cmap="parula",
    label="value",
    linewidth=0,
    legend_width=20,
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
            **rc_dict,
        )
    if col_annotation is not None:
        ca_dict = _annot_helper(adata.var, col_annotation)
        col_annotation = pch.HeatmapAnnotation(axis=1, **ca_dict)

    if row_split is not None and not isinstance(row_split, int):
        row_split = adata.obs[row_split]
    if col_split is not None and not isinstance(row_split, int):
        col_split = adata.var[col_split]

    cmp = helper_heatmap.ClusterMapPlotterNew(
        data=adata.to_df(),
        left_annotation=row_annotation,
        top_annotation=col_annotation,
        row_cluster=row_cluster,
        col_cluster=col_cluster,
        row_split=row_split,
        col_split=col_split,
        cmap=cmap,
        rasterized=rasterized,
        label=label,
        legend_gap=5,
        row_dendrogram_size=10,
        col_dendrogram_size=10,
        linewidth=linewidth,
        xticklabels_kws={"labelrotation": 90},
        legend_width=legend_width,
        **kwargs,
    )
    for cbar in cmp.cbars:
        if isinstance(cbar, mpl.colorbar.Colorbar):
            cbar.outline.set_linewidth(0.3)
            cbar.ax.tick_params(size=0)
    for ax in cmp.legend_axes[0].figure.axes:
        if ax.get_ylabel() in cbar_titles:
            ax.yaxis.set_label_position("left")
            # if ax.get_ylabel() == "value":
            #     ax.set_aspect(0.5)
            # else:
            #     ax.set_aspect(12)
    plt.setp(
        cmp.heatmap_axes[-1, 0].get_xticklabels(), rotation_mode="anchor", ha="right"
    )
    return cmp


def boxplot(
    data: pd.DataFrame,
    x: str,
    y: str,
    pairs: Optional[List[Tuple[str, str]]] = None,
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
    **kwargs
        Keyword arguments passed to the `seaborn.boxplot` function.

    Returns
    -------
    None
        This function creates a plot and does not return anything.
    """
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
    args = {"edgecolor": None, "linewidth": 1, "ci": None}
    plotting = {"data": data, "x": x, "y": y}
    plotting.update(args)
    plotting.update(kwargs)
    ax = sns.barplot(**plotting)
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
        cns._utils._p_value_helper("t-test_welch", data, ax, plotting, pairs)


def stackplot(
    data,
    x,
    y,
    hue,
    order=None,
    hue_order=None,
    width=0.5,
    normalize=True,
    pairs=None,
    ascending=False,
):
    """Plot the value of y categorized by x and grouped by hue."""
    barh = pd.api.types.is_numeric_dtype(data[x])
    if barh:
        df = data.pivot(index=y, columns=hue, values=x)
    else:
        df = data.pivot(index=x, columns=hue, values=y)
    contingency = df.copy()
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
    # if order:
    #     order = df.sort_values(order, ascending=ascending).index
    # else:
    #     order = df.index
    if barh:
        ax = df.reindex(index=order).plot.barh(stacked=True, width=width, ax=ax, rot=0)
    else:
        ax = df.reindex(index=order).plot.bar(stacked=True, width=width, ax=ax, rot=0)
    ax.set_ylabel(ylabel)
    cns.take_legend_out()
    if pairs is not None:
        plotting = {"data": data, "x": x, "y": y, "order": order}
        if contingency.shape[1] == 2:
            cns._utils._p_value_helper(
                "fisher-exact", data, ax, plotting, pairs, contingency
            )
        else:
            cns._utils._p_value_helper(
                "chi-squared", data, ax, plotting, pairs, contingency
            )


def distplot(data, x):
    args = {"kde": True, "edgecolor": None}
    sns.histplot(data=data, x=x, **args)


def regplot(data, x, y):
    args = {
        "line_kws": {"color": "blue", "lw": 1.5},
        "scatter_kws": {"s": 3, "color": "black", "edgecolor": "black", "alpha": 1},
    }
    rho, p_value = sp.stats.pearsonr(data[x], data[y])
    ax = sns.regplot(data=data, x=x, y=y, **args)

    fig = plt.gcf()
    ax2 = fig.add_axes(ax.get_position(), frameon=False)
    ax2.tick_params(labelcolor="none", top=False, bottom=False, left=False, right=False)
    ax2.text(
        1, 1.02, rf"$\rho$={rho:.2f}, $P={num2tex.num2tex(p_value, precision=2):.2g}$"
    )


def pieplot(data, x, hue_order=None):
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
    cns.take_legend_out()
    cns._utils._remove_edge_from_legend_items(ax)


def survivalplot(data, duration, event, hue):
    ax = None
    kmf = ll.KaplanMeierFitter()
    for i, group in enumerate(data[hue].unique()):
        df = data[data[hue] == group]
        label = f"{group} (n={df.shape[0]})"
        kmf.fit(df[duration], df[event], label=label)
        if i != 0:
            ax = kmf.plot_survival_function(
                linewidth=1.2, ci_show=False, show_censors=True, censor_styles={"ms": 3}
            )
        else:
            ax = kmf.plot_survival_function(
                ax=ax,
                linewidth=1.2,
                ci_show=False,
                show_censors=True,
                censor_styles={"ms": 3},
            )
    plt.ylim(-0.05, 1.01)
    plt.ylabel("Overall survival probability")

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


def stripplot(data, x, y, size, **kwargs):
    ax = sns.stripplot(data=data, x=x, y=y, size=size, **kwargs)
    sns.boxplot(
        data=data,
        x=x,
        y=y,
        medianprops={"visible": True, "color": "black", "lw": 1},
        whiskerprops={"visible": False},
        zorder=10,
        showfliers=False,
        showbox=False,
        showcaps=False,
        width=0.3,
        ax=ax,
    )


def histplot(**kwargs):
    sns.histplot(**kwargs)


def lineplot(**kwargs):
    sns.lineplot(**kwargs)


def scatterplot(data, x, y, s=7, **kwargs):
    sns.scatterplot(data=data, x=x, y=y, s=s, **kwargs)


def upsetplot(data, **kwargs):
    usp.plot(data, **kwargs)


def vennplot(lists, labels):
    if len(lists) == 2:
        areas = ["10", "01", "11"]
        func = venn.venn2
        names = ["A", "B"]
    else:
        areas = ["100", "010", "001", "110", "101", "011", "111"]
        func = venn.venn3
        names = ["A", "B", "C"]
    ax = func(
        lists,
        labels,
        set_colors=cns.palettes("Set1"),
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
    cm = confusion_matrix(data[x], data[y], labels=labels)
    cmd = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)

    ax = plt.gca()
    cmd.plot(ax=ax, cmap=plt.cm.Blues)
    cmd.ax_.spines["right"].set_visible(True)
    cmd.ax_.spines["top"].set_visible(True)
    cmd.ax_.set_xlabel(y)
    cmd.ax_.set_ylabel(x)
    plt.yticks(rotation=90, va="center")
    colorbar = cmd.ax_.images[-1].colorbar
    # colorbar.outline.set_linewidth(0.3)
    # colorbar.ax.set_aspect(0.5)
    # colorbar.ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=5))
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
    helper_phylo.phyloplot(adata)


def hazardplot():
    from lifelines import CoxPHFitter
    from lifelines.datasets import load_waltons
    from sklearn import preprocessing

    waltons = load_waltons()
    le = preprocessing.LabelEncoder()
    waltons["group"] = le.fit_transform(waltons["group"])
    cph = CoxPHFitter()
    cph.fit(waltons, duration_col="T", event_col="E")
    return cph.summary


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
        ax = sns.distplot(x_v, hist=False, ax=ax_objs[-1], color="#f0f0f0")
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

        ax.scatter(len(h) * [x1 - 0.01], h, c=blue, s=10, lw=0.5, label=hues[0])
        ax.scatter(len(d) * [x2 + 0.01], d, c=red, s=10, lw=0.5, label=hues[1])

        i += 1

    ax.set_xticks([1, 2, 3])
    _ = ax.set_xticklabels(sites)

    handles, labels = ax.get_legend_handles_labels()
    lgd = ax.legend(
        handles[0:2],
        labels[0:2],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.25),
        ncol=2,
        scatterpoints=1,
    )
    lgd.legendHandles[0]._sizes = [30]
    lgd.legendHandles[1]._sizes = [30]
