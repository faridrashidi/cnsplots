import itertools

import lifelines as ll
import matplotlib.pyplot as plt
import pandas as pd
import scipy as sp
import seaborn as sns
from statannotations.Annotator import Annotator

import cnsplots as cns


def figure(height=150, width=150):
    ax = plt.figure(figsize=(width / 72, height / 72), dpi=72).subplots(1)
    ax.xaxis.labelpad = 1
    return ax


def boxplot(data, x, y, pairs=None, width=0.5, color=cns.colors[0]):
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
    _p_value_helper("Mann-Whitney", data, x, ax, plotting, pairs)


def barplot(data, x, y, pairs=None, color=cns.colors[0], addtip=False):
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


def heatmap(adata, output_file=None):
    import rpy2.robjects as ro
    from IPython.display import Image, display
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.lib import grdevices
    from rpy2.robjects.packages import importr

    pheatmap = importr("pheatmap")

    data = adata.to_df()

    with ro.conversion.localconverter(ro.default_converter + pandas2ri.converter):
        data = ro.conversion.py2rpy(data)

    plot = pheatmap.pheatmap(data)

    from rpy2.ipython.ggplot import image_png

    image_png(plot)

    # with ro.lib.grdevices.render_to_bytesio(
    #     grdevices.png, width=1024, height=896, res=150
    # ) as image:
    #     ro.r.show(plot)
    #     display(Image(data=image.getvalue(), embed=True, retina=True))

    # with grdevices.render_to_bytesio(
    #     grdevices.png, width=width, height=height, res=dpi
    # ) as image:
    #     p = ro.r(cmd)
    #     ro.r.show(p)
    #     if output_file is not None:
    #         ro.r.ggsave(
    #             plot=p,
    #             filename=output_file,
    #             # width=width / dpi,
    #             # height=height / dpi,
    #             units="in",
    #             # dpi=dpi,
    #             limitsize=False,
    #         )
