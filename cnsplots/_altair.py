import altair as alt

import cnsplots as cns


def setup_altair():
    def config():
        # https://altair-viz.github.io/user_guide/configuration.html
        return {
            "config": {
                "font": "Helvetica",
                # 'background': None,
                "scheme": "set1",
                "color": {
                    "field": "color",
                    "type": "Set1",
                },
                "view": {
                    "strokeWidth": 0,
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
                    "labelFontSize": 7,
                    "titleFontSize": 8,
                },
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
                    "labelFontSize": 7,
                    "titleFontSize": 8,
                    "symbolOpacity": 1,
                    "symbolStrokeWidth": 0,
                },
                "boxplot": {
                    "outliers": {
                        "size": 8,
                        "filled": True,
                    },
                },
                "area": {"line": True, "fillOpacity": 0.4},
                "mark": {
                    "color": cns.colors[0],
                },
                # "mark": {
                #     "filled": True,
                #     "opacity": 1,
                #     "type": "point",
                # },
            }
        }

    alt.themes.register("config", config)
    alt.themes.enable("config")
    alt.data_transformers.disable_max_rows()
