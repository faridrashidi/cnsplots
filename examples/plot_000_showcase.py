"""
showcase
--------

Create the showcase figures used in the README and examples gallery.

These examples group the larger overview layouts separately from the
focused per-feature examples in the rest of the gallery.
"""

# %%
# Load data
# ~~~~~~~~~
import matplotlib.image as mpimg
from matplotlib.colorbar import Colorbar
from matplotlib.legend import Legend
from scipy import stats

import cnsplots as cns

(
    iris_df,
    tips_df,
    survival_df,
    blobs,
    volcano_df,
    gene_sets,
    roc_df,
    slope_df,
    confusion_df,
    line_df,
    showcase_images,
) = cns.get_showcase_data(
    include_showcase_images=True,
)


# %%
# Figure 1
# ~~~~~~~~
# A comprehensive showcase of cnsplots capabilities for the README.

cns.settings.title_fontweight = "normal"
mp = cns.multipanel(
    max_width=485, title="Figure 1", title_fontweight="bold", loc="left"
)

# Panel A: boxplot
mp.panel("A", 100, 45, color_cycle=[cns.VIOLET])
ax = cns.boxplot(
    data=tips_df, x="day", y="total_bill", pairs=[("Thur", "Sun"), ("Thur", "Fri")]
)
ax.set_title("Barplot")
ax.set_xlabel("")
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)

# Panel B: violinplot
mp.panel("B", 100, 45, color_cycle=[cns.CHOCOLATE])
ax = cns.violinplot(data=iris_df, x="species", y="sepal_width", pairs="all")
ax.set_title("Violinplot")
ax.set_xlabel("")
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor"
)

# Panel C: stripplot
mp.panel("C", 100, 60, color_cycle="BlueRed")
ax = cns.stripplot(data=tips_df, x="day", y="tip", hue="sex")
legend = ax.get_legend()
ax.legend(
    handles=legend.legend_handles,
    labels=[text.get_text() for text in legend.get_texts()],
    title=legend.get_title().get_text(),
    loc="upper left",
    bbox_to_anchor=(-0.02, 1.0),
    borderaxespad=0,
    markerscale=1,
)
ax.set_title("Stripplot")

# Panel D: stackplot
mp.panel("D", 100, 50, color_cycle=cns.get_hexcolors_from_apalette([2, 4], "Bold"))
ax = cns.stackplot(data=tips_df, x="day", y="sex", pairs=[("Thur", "Sun")])
ax.set_title("Stackplot")
ax.get_legend().set_title(None)

# Panel E: barplot
mp.panel("E", 40, 80, margin_left=35, margin_right=0, color_cycle=[cns.VIOLET])
ax = cns.barplot(
    data=tips_df,
    y="day",
    x="total_bill",
    errorbar="se",
    width=0.7,
    pairs=[("Thur", "Sun"), ("Thur", "Fri")],
)
ax.set_title("Barplot")
ax.set_ylabel("")

# Panel F: pieplot (stacked below E)
mp.panel(
    "F",
    40,
    40,
    margin_left=35,
    margin_top=10,
    margin_right=0,
    below="E",
    color_cycle="Ecotyper3",
)
ax = cns.pieplot(iris_df, "species", legend="right")
ax.set_title("Pieplot")
ax.get_legend().set_title(None)

# Panel G: vennplot
mp.panel("G", 40, 40, pad_left=55, margin_right=45, color_cycle="Tableau")
cns.vennplot(gene_sets, labels=("Set A", "Set B", "Set C"))
mp.get_axes("G").set_title("Vennplot")

# Panel H: donutplot
mp.panel("H", 50, 50, below="G", color_cycle="Ecotyper3")
ax = cns.donutplot(iris_df, "species", legend="right")
ax.set_title("Donutplot")
ax.get_legend().set_title(None)

# Panel I: regplot
mp.panel("I", 90, 90)
ax = cns.regplot(data=tips_df, x="total_bill", y="tip", s=1)
ax.set_title("Regplot")

# Panel J: survivalplot
mp.panel("J", 90, 90)
ax = cns.survivalplot(data=survival_df, duration="time", event="event", hue="group")
# Keep the showcase annotation compact by dropping the CI from the HR line.
for text in ax.texts:
    label = text.get_text()
    if label.startswith("HR ="):
        hr_line, sep, remainder = label.partition("\n")
        text.set_text(
            f"{hr_line.split(' (', 1)[0]}{sep}{remainder}" if sep else hr_line
        )
        break
ax.legend(loc="upper right", bbox_to_anchor=(1.03, 1.0), borderaxespad=0)
ax.set_title("Survivalplot")

# Panel K: kdeplot
mp.panel("K", 90, 90, color_cycle="Ecotyper3", margin_right=0)
ax = cns.kdeplot(data=iris_df, x="petal_length", hue="species")
ax.get_legend().set_title(None)
ax.set_title("Kdeplot")

# Panel L: volcanoplot
mp.panel("L", 90, 90, margin_right=60)
ax = cns.volcanoplot(volcano_df)
ax.set_title("Volcanoplot")

# Panel M: rocplot
mp.panel("M", 90, 90, margin_right=5, color_cycle="ECharts")
ax = cns.rocplot(roc_df, "label", ["Model A", "Model B"])
ax.legend(loc="lower right", bbox_to_anchor=(1.1, 0.0))
for text in ax.get_legend().get_texts():
    text.set_text(text.get_text().replace(" (AUC=", "\n(AUC="))
    text.set_multialignment("left")
ax.set_title("Rocplot")

# Panel N: sankeyplot
mp.panel("N", 100, 30, pad_left=-30, color_cycle="Ecotyper4")
ax = cns.sankeyplot(tips_df, x="day", y="sex", label_rotation=90)
ax.set_title("Sankeyplot")

# Panel O: ridgeplot
mp.panel("O", 35, 80, pad_left=110, margin_right=0)
ax = cns.ridgeplot(data=iris_df, x="petal_length", y="species")
ax.set_title("Ridgeplot")

# Panel P: slopeplot
mp.panel("P", 65, 80, below="O", margin_top=10, pad_top=-5, margin_right=0)
ax = cns.slopeplot(data=slope_df, x="site", y="value", hue="label")
ax.set_title("Slopeplot")

# Panel Q: scatterplot
mp.panel(
    "Q",
    90,
    90,
    margin_right=50,
    margin_top=-10,
    margin_bottom=20,
    color_cycle="Set1",
)
ax = cns.scatterplot(
    data=iris_df, x="sepal_length", y="sepal_width", hue="species", s=5
)
ax.set_title("Scatterplot")
ax.get_legend().set_title(None)
ax.axhline(
    y=iris_df["sepal_width"].mean(),
    color="gray",
    linestyle="--",
    dashes=(4, 3),
    linewidth=0.7,
)
ax.axvline(
    x=iris_df["sepal_length"].mean(),
    color="gray",
    linestyle="--",
    dashes=(4, 3),
    linewidth=0.7,
)
cns.take_legend_out()

# Panel R: heatmapplot
mp.panel("R", 90, 190, margin_top=-10, margin_right=0)
cmp = cns.heatmapplot(
    blobs,
    label="Z-score",
    cmap="BuRd_custom",
    row_annotation=["Ensemble"],
    col_annotation=["blobs"],
    row_cluster=True,
    col_cluster=True,
    show_rownames=True,
    show_colnames=False,
    row_dendrogram=True,
    xlabel="Genes",
    ylabel="Patients",
    legend_hpad=-2,
    legend_vpad=0,
    legend_hgap=4.5,
    legend_vgap=0,
    legend_width=3.0,
    legend_order=["Ensemble", "blobs", "Z-score"],
    xticklabels_rotation=20,
    xlabel_labelpad=0,
)
cmp.ax.set_title("Heatmapplot")

# Save final figure
cns.savefig("~/Desktop/Figure1.svg")


# %%
# Figure 2
# ~~~~~~~~
# A multipanel image layout sized directly from the source image dimensions.

mp = cns.multipanel(
    max_width=540, title="Figure 2", title_fontweight="bold", loc="left"
)

# Panel A: load pathology image
ax = mp.panel("A", 237, 149, pad_left=-70)
ax.imshow(mpimg.imread(showcase_images / "image1.webp"))
ax.set_title("Pathology Image")
ax.set_axis_off()

# Panel B: load immunofluorescence image
ax = mp.panel("B", 102, 116, pad_left=-50)
ax.imshow(mpimg.imread(showcase_images / "image2.webp"))
ax.set_title("Immunofluorescence")
ax.set_axis_off()

# Panel C: dotplot
host_c = mp.panel("C", 60, 116, pad_top=30, pad_left=4)
tips_minmax = tips_df.groupby(["day", "sex"]).agg({"total_bill": ["min", "size"]})
tips_minmax.columns = ["min", "size"]
tips_minmax = tips_minmax.reset_index()
dp = cns.dotplot(
    tips_minmax,
    x="sex",
    y="day",
    color="size",
    size="min",
    value="size",
    legend=True,
    legend_width=10,
    legend_hpad=0,
    xlabel="",
    ylabel="",
    xticklabels_rotation=30,
    xticklabels_fontsize=6,
    yticklabels_fontsize=6,
    max_s=40,
)
for label in dp.heatmap_axes[-1, 0].get_xticklabels():
    label.set_ha("right")
    label.set_rotation_mode("anchor")
dp.ax_heatmap.set_title("Dotplot")

cbar = next(obj for obj in dp.cbars if isinstance(obj, Colorbar))
size_legend = next(obj for obj in dp.cbars if isinstance(obj, Legend))
legend_ax = size_legend.axes
cbar_ax = cbar.ax

size_legend.get_title().set_fontsize(6)
for text in size_legend.get_texts():
    text.set_fontsize(6)
cbar_ax.tick_params(labelsize=6, length=0)
cbar_ax.yaxis.label.set_size(6)

original_embedded_sync = getattr(host_c, "_cnsplots_sync_embedded_axes", None)
original_detached_sync = getattr(host_c, "_cnsplots_sync_detached_legends", None)


def _sync_panel_c_dotplot() -> None:
    """Keep the dotplot and both legends inside panel C during relayout."""
    if callable(original_embedded_sync):
        original_embedded_sync()
    if callable(original_detached_sync):
        original_detached_sync()

    host_box = host_c.get_position().frozen()
    dp.ax_heatmap.set_position(
        [
            host_box.x0,
            host_box.y0,
            host_box.width * 0.49,
            host_box.height,
        ]
    )
    legend_box = [
        host_box.x0 + host_box.width * 0.70,
        host_box.y0,
        host_box.width * 0.30,
        host_box.height,
    ]
    legend_ax.set_position(legend_box)
    cbar_ax.set_position(
        [
            legend_box[0],
            host_box.y0 + host_box.height * 0.20,
            host_box.width * 0.048,
            host_box.height * 0.78,
        ]
    )
    size_legend.set_bbox_to_anchor((0.28, 0.58), transform=legend_ax.transAxes)
    legend_ax.set_axis_off()


host_c._cnsplots_sync_embedded_axes = _sync_panel_c_dotplot
host_c._cnsplots_sync_detached_legends = _sync_panel_c_dotplot
_sync_panel_c_dotplot()

# Panel D: ?
ax = mp.panel("D", 85, 85, margin_right=0)
cns.placeholderplot("Placeholder")
ax.set_title("?")

# Panel E: load western blot image
ax = mp.panel("E", 102, 116, below="B", pad_left=-50)
ax.imshow(mpimg.imread(showcase_images / "image4.webp"))
ax.set_title("Western Blot")
ax.set_axis_off()

# Panel F: lineplot
ax = mp.panel("F", 85, 85, below="C", margin_top=48)
ax = cns.lineplot(
    data=line_df,
    x="timepoint",
    y="signal",
    hue="condition",
    marker="o",
    errorbar=None,
)
legend = ax.get_legend()
if legend is not None:
    legend.remove()
ax.set_title("Lineplot")

# Panel G: qqplot
ax = mp.panel("G", 85, 85, below="D", margin_top=15, margin_right=0)
ax = cns.qqplot(iris_df, x="sepal_length", dist=stats.norm, fit=True, line="45")
ax.set_title("Qqplot")

mp.newline()

# Panel H: h&e histology image
ax = mp.panel("H", 160, 319, pad_left=-60)
ax.imshow(mpimg.imread(showcase_images / "image3.webp"))
ax.set_title("H&E Histology")
ax.set_axis_off()

# Panel I: placeholder plot
ax = mp.panel("I", 155, 175, margin_right=0)
cns.placeholderplot("A placeholder plot (155⨯175)\nYou can use to fill it up later.")
ax.set_title("Placeholder")

mp.newline()

# Panel J: lollipopplot
ax = mp.panel("J", 100, 30, color_cycle="NEJM", margin_right=15)
ax = cns.lollipopplot(data=tips_df, x="day", y="total_bill", errorbar="se")
ax.set_title("Lollipopplot")
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)

# Panel K: confusionplot
ax = mp.panel("K", 30, 30, margin_right=30)
ax = cns.confusionplot(
    data=confusion_df,
    x="pred",
    y="truth",
    add_pvalue=True,
    x_order=["Neg", "Pos"],
    y_order=["Neg", "Pos"],
    pvalue_y_pad=3.9,
    pvalue_x_pad=-0.2,
)
ax.set_title("Confusionplot")

# Panel L: ?
ax = mp.panel("L", 100, 100)
cns.placeholderplot("Placeholder")
ax.set_title("?")

# Save final figure
cns.savefig("~/Desktop/Figure2.jpg")
