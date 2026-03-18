"""
showcase
--------

Create the showcase figures used in the README and examples gallery.

These examples group the larger overview layouts separately from the
focused per-feature examples in the rest of the gallery.
"""

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

# %%
# Load data
# ~~~~~~~~~
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
    showcase_images,
) = cns.get_showcase_data(
    include_showcase_images=True,
)


# %%
# Figure 1
# ~~~~~~~~
# A comprehensive showcase of cnsplots capabilities for the README.

cns.settings._fontweight_title = "normal"
mp = cns.multipanel(
    max_width=540, title="Figure 1", fontweight_title="bold", loc="left"
)

# Panel A: boxplot
mp.panel("A", 100, 45, pad_top=5, margin=(0, 0, 0, 30), color_cycle=[cns.VIOLET])
ax = cns.boxplot(
    data=tips_df, x="day", y="total_bill", pairs=[("Thur", "Sun"), ("Thur", "Fri")]
)
ax.set_title("Barplot")
ax.set_xlabel("")
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)

# Panel B: violinplot
mp.panel("B", 100, 45, pad_top=5, color_cycle=[cns.CHOCOLATE])
ax = cns.violinplot(data=iris_df, x="species", y="sepal_width", pairs="all")
ax.set_title("Violinplot")
ax.set_xlabel("")
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor"
)

# Panel C: stripplot
mp.panel("C", 100, 60, pad_top=5, color_cycle="BlueRed")
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
mp.panel(
    "D",
    100,
    50,
    pad_top=5,
    margin=(10, 0, 35, 20),
    color_cycle=cns.get_hexcolors_from_apalette([2, 4], "Bold"),
)
ax = cns.stackplot(data=tips_df, x="day", y="sex", pairs=[("Thur", "Sun")])
ax.set_title("Stackplot")
ax.get_legend().set_title(None)

# Panel E: barplot
mp.panel("E", 40, 80, pad_top=5, margin=(5, 0, 0, 15), color_cycle=[cns.VIOLET])
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
    pad_top=5,
    margin=(5, 0, 0, 0),
    pad_left=0,
    below="E",
    color_cycle="Ecotyper3",
)
ax = cns.pieplot(iris_df, "species", legend="right")
ax.set_title("Pieplot")
ax.get_legend().set_title(None)

# Panel G: vennplot
mp.panel(
    "G", 40, 40, pad_top=5, margin=(0, 0, 40, 5), pad_left=10, color_cycle="Tableau"
)
cns.vennplot(gene_sets, labels=("Set A", "Set B", "Set C"))
mp.get_axes("G").set_title("Vennplot")

# Panel H: donutplot
mp.panel(
    "H",
    50,
    50,
    pad_top=5,
    margin=(0, 0, 0, 10),
    pad_left=10,
    below="G",
    color_cycle="Ecotyper3",
)
ax = cns.donutplot(iris_df, "species", legend="right")
ax.set_title("Donutplot")
ax.get_legend().set_title(None)

# Panel I: regplot
mp.panel("I", 90, 90, pad_top=5)
ax = cns.regplot(data=tips_df, x="total_bill", y="tip", s=1)
ax.set_title("Regplot")

# Panel J: survivalplot
mp.panel("J", 90, 90, pad_top=5)
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
mp.panel("K", 90, 90, pad_top=5, color_cycle="Ecotyper3")
ax = cns.kdeplot(data=iris_df, x="petal_length", hue="species")
ax.get_legend().set_title(None)
ax.set_title("Kdeplot")

# Panel L: volcanoplot
mp.panel("L", 90, 90, pad_top=5, margin=(0, 0, 50, 0))
ax = cns.volcanoplot(volcano_df)
ax.set_title("Volcanoplot")

# Panel M: rocplot
mp.panel("M", 90, 90, pad_top=5, color_cycle="ECharts")
ax = cns.rocplot(roc_df, "label", ["Model A", "Model B"])
ax.legend(loc="lower right", bbox_to_anchor=(1.1, 0.0))
for text in ax.get_legend().get_texts():
    text.set_text(text.get_text().replace(" (AUC=", "\n(AUC="))
    text.set_multialignment("left")
ax.set_title("Rocplot")

# Panel N: sankeyplot
mp.panel(
    "N", 100, 30, pad_top=5, pad_left=10, margin=(10, 0, 15, 0), color_cycle="Ecotyper4"
)
ax = cns.sankeyplot(tips_df, x="day", y="sex")
ax.set_title("Sankeyplot")

# Panel O: ridgeplot
mp.panel("O", 35, 80, pad_top=3)
ax = cns.ridgeplot(data=iris_df, x="petal_length", y="species")
ax.set_title("Ridgeplot")

# Panel P: slopeplot
mp.panel("P", 65, 80, pad_top=3, margin=(10, 0, 0, 0), below="O")
ax = cns.slopeplot(data=slope_df, x="site", y="value", hue="label")
ax.set_title("Slopeplot")

# Panel Q: scatterplot
mp.newline()
mp.panel("Q", 90, 90, pad_top=5, margin=(0, 0, 40, 0), color_cycle="Set1")
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
mp.panel("R", 100, 190, pad_top=3, pad_left=10)
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
    xticklabels_rotation=20,
)
cmp.ax.set_title("Heatmapplot")

# Save final figure
cns.savefig("~/Desktop/Figure1.jpg")


# %%
# Figure 2
# ~~~~~~~~
# A multipanel image layout sized directly from the source image dimensions.

mp = cns.multipanel(
    max_width=540, title="Figure 2", fontweight_title="bold", loc="left"
)

# Panel A: load pathology image
ax = mp.panel(
    "A",
    284,
    178,
    label_left=10,
    label_top=12,
    pad_left=0,
    pad_top=5,
    margin=(0, 0, 0, 10),
)
ax.imshow(mpimg.imread(showcase_images / "image1.webp"))
ax.set_title("Pathology Image")
ax.set_axis_off()

# Panel B: load immunofluorescence image
ax = mp.panel(
    "B",
    128,
    145,
    label_left=10,
    label_top=12,
    pad_left=0,
    pad_top=5,
    margin=(10, 0, 0, 10),
)
ax.imshow(mpimg.imread(showcase_images / "image2.webp"))
ax.set_title("Immunofluorescence")
ax.set_axis_off()

# Panel C: load western blot image
ax = mp.panel(
    "C",
    128,
    145,
    label_left=10,
    label_top=12,
    pad_left=0,
    pad_top=5,
    margin=(10, 0, 0, 0),
    below="B",
)
ax.imshow(mpimg.imread(showcase_images / "image4.webp"))
ax.set_title("Western Blot")
ax.set_axis_off()

# Panel D: boxplot
mp.panel("D", 100, 60, pad_top=5, margin=(10, 0, 0, 35), color_cycle=[cns.VIOLET])
ax = cns.boxplot(
    data=tips_df, x="day", y="total_bill", pairs=[("Thur", "Sun"), ("Thur", "Fri")]
)
ax.set_title("Boxplot")
ax.set_xlabel("")
ax.set_xticklabels(
    ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
)

# Panel E: dotplot
mp.panel("E", 60, 60, pad_left=20, pad_top=3, margin=(10, 4, 0, 0), below="D")
tips_minmax = tips_df.groupby(["day", "sex"]).agg({"total_bill": ["min", "size"]})
tips_minmax.columns = ["min", "size"]
tips_minmax = tips_minmax.reset_index()
plt.sca(mp.get_axes("E"))
dp = cns.dotplot(
    tips_minmax,
    x="sex",
    y="day",
    color="size",
    size="min",
    value="size",
    # legend=False,
    xlabel="",
    ylabel="",
    xticklabels_rotation=60,
    max_s=40,
)
for label in dp.heatmap_axes[-1, 0].get_xticklabels():
    label.set_ha("center")
dp.ax_heatmap.set_title("Dotplot")

mp.newline()

# Panel F: h&e histology image
ax = mp.panel(
    "F",
    160,
    319,
    label_left=10,
    label_top=12,
    pad_left=0,
    pad_top=5,
    margin=(0, 0, 0, 0),
)
ax.imshow(mpimg.imread(showcase_images / "image3.webp"))
ax.set_title("H&E Histology")
ax.set_axis_off()

ax = mp.panel(
    "G",
    155,
    200,
    label_left=10,
    label_top=12,
    pad_left=0,
    pad_top=5,
    margin=(0, 0, 0, 0),
)
cns.placeholderplot("This is a placeholder plot\n155 ⨯ 200")
ax.set_title("Placeholder")

# Save final figure
cns.savefig("~/Desktop/Figure2.jpg")
