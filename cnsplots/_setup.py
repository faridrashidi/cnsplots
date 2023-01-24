import altair as alt

import cnsplots as cns
import matplotlib as mpl
from cycler import cycler


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


def setup_altair():
    def config():
        # https://altair-viz.github.io/user_guide/configuration.html
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
