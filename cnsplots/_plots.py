import itertools

import matplotlib.pyplot as plt
import scipy as sp
import seaborn as sns
from statannotations.Annotator import Annotator

import cnsplots as cns


def figure(height=150, width=150):
    ax = plt.figure(figsize=(width / 72, height / 72), dpi=72).subplots(1)
    ax.xaxis.labelpad = 1
    return ax


def sns_boxplot(data, x, y, pairs=None, width=0.5, color=cns.colors[0]):
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
    }
    plotting = {
        "data": data,
        "x": x,
        "y": y,
        "width": width,
        "color": color,
    }
    plotting.update(args)
    ax = sns.boxplot(**plotting)
    # sns.stripplot(data=data, x=x, y=y, size=3, linewidth=0)
    print(
        "Boxplots represent the median and bottom and upper quartiles; whiskers"
        " correspond to 1.5 times the interquartile range."
    )
    _p_value("Mann-Whitney", data, x, ax, plotting, pairs)


def sns_barplot(data, x, y, pairs=None, color=cns.colors[0], addtip=False):
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
        "color": color,
    }
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

    _p_value("t-test_welch", data, x, ax, plotting, pairs)


def sns_stackplot(data, x, hue, normalize=True):
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


def sns_distplot(data, x):
    args = {"kde": True, "edgecolor": None}
    sns.histplot(data=data, x=x, **args)


def sns_regplot(data, x, y):
    args = {
        "line_kws": {"color": "blue", "lw": 1.5},
        "scatter_kws": {"s": 3, "color": "black", "edgecolor": "black", "alpha": 1},
    }
    r, p = sp.stats.pearsonr(data[x], data[y])
    g = sns.regplot(data=data, x=x, y=y, **args)
    g.text(6, 4.5, rf"$\rho$={r:.2f}, $P$={p:.2g}")


def plt_piechart(data, x, order=None):
    df = data[x].value_counts()
    if order is None:
        order = df.index
    df.reindex(index=order).plot.pie(
        shadow=True,
        autopct="%1.0f%%",
        explode=[0] * df.shape[0],
        textprops={"fontsize": 6, "color": "white"},
    )


def _p_value(test, data, x, ax, plotting, pairs):
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
