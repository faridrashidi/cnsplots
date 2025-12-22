import matplotlib as mpl

import cnsplots as cns
from cnsplots._utils import (
    FONTSIZE_LEGEND,
    FONTSIZE_TITLE,
    LINEWIDTH_AXES,
    PALETTE_QUAL,
    PALETTE_SEQ,
)


def setup_matplotlib(
    color_cycle=PALETTE_QUAL,
    color_map=PALETTE_SEQ,
    fontsize_title=FONTSIZE_TITLE,
    fontsize_legend=FONTSIZE_LEGEND,
    linewidth_axes=LINEWIDTH_AXES,
):
    def config():
        return {
            "mathtext.fontset": "custom",
            "font.family": "sans-serif",
            "font.sans-serif": "Helvetica",
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
    for continues in [
        "parula",
        "gnuplot",
        "hot",
        "WhYlOrRd_custom",
        "BuRd_custom",
        "OrBu_custom",
        "YlGnBu_custom",
    ]:
        if continues not in mpl.colormaps:
            mpl.colormaps.register(cns.palettes(continues), name=continues)

    mpl.rcParams.update(config())


def setup_scanpy():
    import scanpy

    setup_matplotlib()
    scanpy.set_figure_params(scanpy=False, figsize=(2.5, 2.5), facecolor="white")


def setup_ax(
    ax,
    fontsize_title=FONTSIZE_TITLE,
    fontsize_legend=FONTSIZE_LEGEND,
    linewidth_axes=LINEWIDTH_AXES,
    colorbar_label="FDR q-val",
):
    mpl.rcParams.update(
        {
            "mathtext.fontset": "custom",
            "font.family": "sans-serif",
            "font.sans-serif": "Helvetica",
        }
    )
    ax.set_title(ax.get_title(), fontsize=fontsize_title, pad=4)
    ax.set_xlabel(ax.get_xlabel(), fontsize=fontsize_title, color="black")
    ax.set_ylabel(ax.get_ylabel(), fontsize=fontsize_title, color="black")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_linewidth(linewidth_axes)
    ax.spines["left"].set_linewidth(linewidth_axes)
    ax.spines["bottom"].set_color("black")
    ax.spines["left"].set_color("black")
    ax.tick_params(
        axis="x",
        labelsize=fontsize_legend,
        colors="black",
        length=2,
        width=0.6,
        pad=1,
        labelrotation=0,
    )
    ax.tick_params(
        axis="y",
        labelsize=fontsize_legend,
        colors="black",
        length=2,
        width=0.6,
        pad=1,
        labelrotation=0,
    )
    ax.grid(False)
    ax.margins(x=0.05, y=0.05)
    cbar = ax.collections[0].colorbar if ax.collections else None
    if cbar is not None:
        cbar.ax.tick_params(labelsize=fontsize_legend)
        if colorbar_label:
            cbar.set_label(colorbar_label, fontsize=fontsize_title, color="black")


def setup_ggplot():
    return """
    fontsize <- 10
    theme_custom <- theme(
      text = element_text(
        size = fontsize,
        color = 'black',
        family = "sans",
        face = "plain"
      ),
      panel.grid.major = element_blank(),
      panel.grid.minor = element_blank(),

      axis.text.x = element_text(
        size = fontsize,
        color = 'black'
      ),
      axis.text.y = element_text(
        size = fontsize,
        color = 'black'
      ),

      axis.title.x = element_text(
        size = fontsize,
        color = 'black'
      ),
      axis.title.y = element_text(
        size = fontsize,
        color = 'black'
      ),

      axis.title = element_text(
        size = fontsize,
        color = 'black',
        face = "plain"
      ),

      plot.title = element_text(
        size = fontsize,
        color = 'black',
        face = "plain"
      ),

      legend.text = element_text(size = fontsize),
      legend.title = element_text(size = fontsize)
    )
    """
