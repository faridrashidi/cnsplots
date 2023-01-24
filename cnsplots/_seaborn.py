def sns_barplot():
    args = {"edgecolor": None, "linewidth": 1, "ci": None}
    return args


def sns_distplot(color="#272822"):
    args = {"hist_kws": {"width": 0.5, "alpha": 1.0, "color": color}}
    return args


def sns_boxplot():
    args = {
        "showfliers": False,
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
    return args


def sns_regplot():
    args = {
        "line_kws": {"color": "blue", "lw": 1.5},
        "scatter_kws": {"s": 3, "color": "black", "edgecolor": "black", "alpha": 1},
    }
    return args
