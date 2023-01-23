import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from cycler import cycler
import cnsplots as cns


def setup_matplotlib():
    def config():
        # https://matplotlib.org/stable/tutorials/introductory/customizing.html#the-default-matplotlibrc-file
        return {
            "font.family": "sans-serif",
            "font.sans-serif": "Helvetica",
            "font.size": 7,
            "axes.titlesize": 7,
            "axes.labelsize": 7,
            "xtick.labelsize": 6,
            "ytick.labelsize": 6,
            "legend.fontsize": 6,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0,
            "savefig.dpi": 72,
            "savefig.transparent": True,
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
            "axes.edgecolor": "black",
            "axes.labelcolor": "black",
            "axes.labelpad": 2,
            "axes.titlepad": 4,
            "axes.xmargin": 0.05,
            "axes.ymargin": 0.05,
            "axes.prop_cycle": cycler("color", cns.colors),
            "legend.frameon": False,
            "legend.markerscale": 0.5,
            "xtick.bottom": True,
            "xtick.color": "black",
            "xtick.major.size": 2,
            "xtick.major.width": 0.6,
            "xtick.major.pad": 1,
            "xtick.alignment": "center",
            "ytick.left": True,
            "ytick.color": "black",
            "ytick.major.size": 2,
            "ytick.major.width": 0.6,
            "ytick.major.pad": 1,
            "ytick.alignment": "center_baseline",
        }

    mpl.rcParams.update(config())


def figure(height=150, width=150):
    ax = plt.figure(figsize=(height / 72, width / 72), dpi=72).subplots(1)
    ax.xaxis.labelpad = 1
    return ax


def barplot(df, x, y):
    args = {
        "edgecolor": "black",
        "linewidth": 1,
        "ci": None,
        # palette=data.set_index(x)[color].to_dict() if color is not None else None,
    }
    g = sns.barplot(data=df, x=x, y=y, **args)

    # adding values to the bars
    groupedvalues = df.groupby(x).mean().reset_index()
    for _, row in groupedvalues.iterrows():
        g.text(
            row.name,
            row[y] + 0.05,
            round(row[y], 2),
            color="black",
            ha="center",
            rotation=0,
            size=6,
        )


def distplot(color="#272822"):
    args = {"hist_kws": {"width": 0.5, "alpha": 1.0, "color": color}}
    return args


def boxplot():
    args = {
        "boxprops": {"facecolor": "white", "edgecolor": "orange"},
        "medianprops": {"color": "red"},
        "whiskerprops": {"color": "blue"},
        "capprops": {"color": "green"},
        "flierprops": {
            "markerfacecolor": "purple",
            "markersize": 3,
            "markeredgecolor": "purple",
            "marker": "o",
            "linewidth": 0,
        },
    }
    return args


def regplot():
    args = {
        "line_kws": {"color": "blue", "lw": 3},
        "scatter_kws": {"s": 3, "color": "black", "edgecolor": "black", "alpha": 1},
    }
    return args
