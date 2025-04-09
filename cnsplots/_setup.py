import matplotlib as mpl

import cnsplots as cns


def setup_matplotlib(
    color_cycle="Set1",
    color_map="parula",
    fontsize_title=8,
    fontsize_legend=7,
    linewidth_axes=0.5,
):
    def config():
        return {
            "mathtext.fontset": "custom",
            "font.family": ["Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": fontsize_title,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.01,
            "savefig.dpi": 72 * 4,
            "savefig.transparent": True,
            "svg.fonttype": "none",
            "axes.titlesize": fontsize_title,
            "axes.labelsize": fontsize_title,
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": linewidth_axes,
            "axes.edgecolor": "black",
            "axes.labelcolor": "black",
            "axes.labelpad": 2,
            "axes.titlepad": 4,
            "axes.xmargin": 0.05,
            "axes.ymargin": 0.05,
            "axes.prop_cycle": mpl.cycler(color=cns.palettes(color_cycle)),
            "image.cmap": color_map,
            "legend.fontsize": fontsize_title,
            "legend.title_fontsize": fontsize_title,
            "legend.frameon": False,
            "legend.markerscale": 0.5,
            "legend.handlelength": 0.7,
            "legend.handleheight": 0.7,
            "legend.handletextpad": 0.3,
            "xtick.labelsize": fontsize_legend,
            "xtick.bottom": True,
            "xtick.color": "black",
            "xtick.major.size": 2,
            "xtick.major.width": 0.6,
            "xtick.major.pad": 1,
            "xtick.alignment": "center",
            "ytick.labelsize": fontsize_legend,
            "ytick.left": True,
            "ytick.color": "black",
            "ytick.major.size": 2,
            "ytick.major.width": 0.6,
            "ytick.major.pad": 1,
            "ytick.alignment": "center_baseline",
        }

    for categorical in [
        "Set1",
        "Set2",
        "Set3",
        "Pastel1",
        "Pastel2",
        "Paired",
        "Dark2",
        "Accent",
        "Tableau",
        "Bold",
        "BlueRed",
        "ECharts",
        "Ecotyper1",
        "Ecotyper2",
        "Ecotyper3",
        "Ecotyper4",
        "Ecotyper5",
        "Ecotyper6",
    ]:
        if categorical not in mpl.colormaps:
            mpl.colormaps.register(
                mpl.colors.ListedColormap(cns.palettes(categorical)), name=categorical
            )
    for continues in ["parula", "gnuplot", "hot"]:
        if continues not in mpl.colormaps:
            mpl.colormaps.register(cns.palettes(continues), name=continues)

    mpl.rcParams.update(config())


def setup_scanpy():
    import scanpy

    scanpy.set_figure_params(
        scanpy=False, figsize=(2.5, 2.5), color_map="inferno", facecolor="white"
    )
