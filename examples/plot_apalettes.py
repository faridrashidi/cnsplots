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
    nrows = len(cmap_list)
    figh = (nrows + (nrows - 1) * 0.2) * 3
    _, axs = plt.subplots(nrows=nrows + 1, figsize=(40, figh))
    for ax, name in zip(axs, cmap_list):
        ax.imshow(gradient, aspect="auto", cmap=plt.get_cmap(name))
        ax.text(
            -0.01,
            0.5,
            name,
            va="center",
            ha="right",
            fontsize=120,
            transform=ax.transAxes,
        )
    for ax in axs:
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
        "parula",
        "gnuplot",
    ]
)


# %%
# change color palette

tips = sns.load_dataset("tips")

cns.figure(color_cycle=palettable.colorbrewer.qualitative.Set1_9.hex_colors)
cns.barplot(data=tips, x="day", y="total_bill")

cns.figure(color_cycle=palettable.colorbrewer.qualitative.Set1_9.hex_colors[::-1])
cns.barplot(data=tips, x="day", y="total_bill")

cns.figure(color_cycle=cns.get_specific_hex_colors_from_set1([0, 2, 4, 6]))
cns.barplot(data=tips, x="day", y="total_bill")
