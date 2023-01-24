import matplotlib as mpl
import matplotlib.pyplot as plt
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
            "legend.title_fontsize": 7,
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
            "image.cmap": "viridis",
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
    ax = plt.figure(figsize=(width / 72, height / 72), dpi=72).subplots(1)
    ax.xaxis.labelpad = 1
    return ax
