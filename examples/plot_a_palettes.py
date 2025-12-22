"""
palettes
--------

plot palettes
"""

# %%
# load packages
import matplotlib.pyplot as plt
import numpy as np
import palettable
import seaborn as sns

import cnsplots as cns

# %%
# plot palettes
gradient = np.linspace(0, 1, 256)
gradient = np.vstack((gradient, gradient))


def plot_palettes(cmap_list):
    cns.figure(1500, 600)
    fig = plt.gcf()
    nrows = len(cmap_list)
    for i, name in enumerate(cmap_list):
        ax = fig.add_subplot(nrows, 1, i + 1)
        ax.pcolormesh(gradient, cmap=plt.get_cmap(name))
        ax.text(
            -0.01,
            0.5,
            name,
            va="center",
            ha="right",
            fontsize=30,
            transform=ax.transAxes,
        )
        ax.set_axis_off()


cns.setup_matplotlib()
plot_palettes(
    [
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
        "parula",
        "gnuplot",
        "hot",
        "WhYlOrRd_custom",
        "BuRd_custom",
        "OrBu_custom",
        "YlGnBu_custom",
    ]
)


# %%
# change color palette

tips = sns.load_dataset("tips")

cns.figure(color_cycle=palettable.colorbrewer.qualitative.Set1_9.hex_colors)
cns.barplot(data=tips, x="day", y="total_bill")

cns.figure(color_cycle=palettable.colorbrewer.qualitative.Accent_8.hex_colors[::-1])
cns.barplot(data=tips, x="day", y="total_bill")

cns.figure(color_cycle=cns.get_hexcolors_from_apalette([0, 2, 4, 6]))
cns.barplot(data=tips, x="day", y="total_bill")

cns.figure(
    color_cycle=cns.get_hexcolors_from_apalette(
        [5, 1, 3, 7], palette=palettable.colorbrewer.qualitative.Paired_12.hex_colors
    )
)
cns.barplot(data=tips, x="day", y="total_bill")
