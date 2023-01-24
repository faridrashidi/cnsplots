import altair as alt

import cnsplots as cns


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
