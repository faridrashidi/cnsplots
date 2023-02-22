import altair as alt
import matplotlib as mpl

import cnsplots as cns


def setup_matplotlib(color_cycle="Set1", color_map="parula"):
    def config():
        return {
            "mathtext.fontset": "custom",
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
            "savefig.dpi": 72 * 4,
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
            "axes.prop_cycle": mpl.cycler(color=cns.palettes(color_cycle)),
            "image.cmap": color_map,
            "legend.frameon": False,
            "legend.markerscale": 0.5,
            "legend.handlelength": 0.7,
            "legend.handleheight": 0.7,
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

    for categorical in ["Set1", "Tableau", "Bold", "BlueRed", "ECharts"]:
        if categorical not in mpl.colormaps:
            mpl.colormaps.register(
                mpl.colors.ListedColormap(cns.palettes(categorical)), name=categorical
            )
    for continues in ["parula", "gnuplot"]:
        if continues not in mpl.colormaps:
            mpl.colormaps.register(cns.palettes(continues), name=continues)

    mpl.rcParams.update(config())


def setup_altair():
    def config():
        return {
            "config": {
                "font": "Helvetica",
                "padding": 0,
                # 'background': None,
                "scheme": "set1",
                "color": {
                    "field": "color",
                    "type": "Set1",
                },
                "view": {
                    "strokeWidth": 0,
                },
                "title": {
                    "fontSize": 7,
                    "offset": 3,
                    "fontWeight": "normal",
                },
                "axis": {
                    "grid": False,
                    "domainColor": "black",
                    "domainWidth": 0.8,
                    "tickColor": "black",
                    "tickSize": 2,
                    "tickWidth": 0.6,
                    "labelFontWeight": "normal",
                    "titleFontWeight": "normal",
                    "labelFontSize": 6,
                    "titleFontSize": 7,
                },
                # "axisX": {
                #     "labelAlign": "center",
                #     "titlePadding": 2,
                #     "labelPadding": 1.5,
                # },
                "range": {
                    "category": cns.colors,
                    "heatmap": {"scheme": "viridis"},
                    "ordinal": {"scheme": "set1"},
                    "ramp": {"scheme": "set1"},
                    "diverging": {"scheme": "set1"},
                },
                "legend": {
                    "labelFontWeight": "normal",
                    "titleFontWeight": "normal",
                    "labelFontSize": 6,
                    "titleFontSize": 7,
                    "labelBaseline": "middle",
                    "symbolSize": 40,
                    "symbolOpacity": 1,
                    "symbolStrokeWidth": 0,
                },
                "boxplot": {
                    "outliers": {
                        "size": 8,
                        "filled": True,
                    },
                },
                "mark": {
                    "color": cns.colors[0],
                    "opacity": 1,
                },
                # "arc": {"fill": cns.colors[0]},
                # "group": {"fill": cns.colors[0]},
                "area": {"fill": cns.colors[0], "line": True, "fillOpacity": 0.1},
                # "circle": {
                #     "fill": cns.colors[0],
                #     "stroke": cns.colors[0],
                #     "strokeWidth": 0.5,
                # },
                "line": {"strokeWidth": 1.2},
                # "path": {"stroke": cns.colors[0]},
                "point": {"filled": True},
                "text": {
                    "size": 6,
                    "baseline": "middle",
                },
                # "rect": {"fill": cns.colors[0]},
                # "shape": {"stroke": cns.colors[0]},
                # "symbol": {
                #     "fill": cns.colors[0],
                #     "opacity": 1,
                #     "shape": "circle",
                #     "size": 40,
                #     "strokeWidth": 1,
                # },
                "bar": {
                    # "size": 40,
                    # "binSpacing": 1,
                    # "continuousBandSize": 30,
                    # "discreteBandSize": 30,
                    "stroke": False,
                },
                # "encoding": {
                #     "y": {"scale": {"zero": False}},
                # },
            }
        }

    alt.themes.register("config", config)
    alt.themes.enable("config")
    alt.data_transformers.disable_max_rows()
