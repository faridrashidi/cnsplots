import altair as alt


def setup_altair():
    def config():
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
                    # 'height': 100,
                    # 'width': 100,
                    "strokeWidth": 0,
                },
                "axis": {
                    "grid": False,
                    "domainColor": "black",
                    "domainWidth": 0.6,
                    "tickColor": "black",
                    "tickSize": 2,
                    "tickWidth": 0.3,
                    "labelFontWeight": "normal",
                    "titleFontWeight": "normal",
                    "labelFontSize": 7,
                    "titleFontSize": 8,
                },
                "range": {
                    "category": {"scheme": "set1"},
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
                "mark": {
                    "color": "black",
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
