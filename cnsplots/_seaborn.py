import scipy as sp
import seaborn as sns
from statannotations.Annotator import Annotator

import cnsplots as cns


def sns_barplot():
    args = {"edgecolor": None, "linewidth": 1, "ci": None}
    return args


def sns_stackplot(data, x, hue, normalize=True):
    args = {
        "edgecolor": None,
        "alpha": 1,
        "shrink": 0.7,
    }
    if normalize:
        ax = sns.histplot(data=data, x=x, hue=hue, multiple="fill", **args)
        ax.set_ylabel("Frequency")
        print("P values were determined by two-sided Fisher's exact test")
        # TODO: calculate the p-value
    else:
        sns.histplot(data=data, x=x, hue=hue, multiple="stack", **args)


def sns_histplot(data, x):
    args = {"kde": True, "edgecolor": None}
    sns.histplot(data=data, x=x, **args)


def sns_boxplot(data, x, y, pairs=None, width=0.5, color=cns.colors[0]):
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

    if pairs is not None:
        annotator = Annotator(ax, pairs, **plotting)
        # https://github.com/trevismd/statannotations/blob/master/statannotations/Annotator.py#L44
        annotator.configure(
            test="Mann-Whitney",
            text_format="star",  # star, simple
            loc="inside",
            line_width=0.8,
            text_offset=-2,
            color="black",
        )
        annotator.apply_and_annotate()
        print("P values were determined by two-sided Mann-Whitney U test.")


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
