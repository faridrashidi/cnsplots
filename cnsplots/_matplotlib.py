import matplotlib.pyplot as plt
import seaborn as sns

import cnsplots as cns


def setup_matplotlib():
    styles_path = cns.__path__[0]
    stylesheets = plt.style.core.read_style_directory(styles_path)
    plt.style.core.update_nested_dict(plt.style.library, stylesheets)
    plt.style.core.available[:] = sorted(plt.style.library.keys())
    plt.style.use("CNS")


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
