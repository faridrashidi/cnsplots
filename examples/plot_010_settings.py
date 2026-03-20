"""
settings
--------

Configure global defaults for cnsplots.

cnsplots provides a ``settings`` object to customize global defaults for
plot styling, export behavior, figure helpers, multipanel layout, and
annotation helpers such as legends and panel labels.
Changes to settings affect all subsequent plotting calls until you reset
them or override them inside ``settings.context()``.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")


# %%
# View current settings
# ~~~~~~~~~~~~~~~~~~~~~
# The settings object shows all configurable parameters.
print(cns.settings)


# %%
# Access representative settings
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Settings now cover setup defaults, figure helpers, and multipanel helpers.
print(f"palette_qual: {cns.settings.palette_qual}")
print(f"title_fontsize: {cns.settings.title_fontsize}")
print(f"savefig_dpi: {cns.settings.savefig_dpi}")
print(
    "figure defaults: "
    f"{cns.settings.figure_width} x {cns.settings.figure_height} px "
    f"at {cns.settings.figure_dpi} dpi"
)
print(f"scanpy_figsize: {cns.settings.scanpy_figsize}")
print(f"multipanel_max_width: {cns.settings.multipanel_max_width}")
print(f"panel defaults: {cns.settings.panel_width} x {cns.settings.panel_height} px")
print(f"legend_out_bbox_to_anchor: {cns.settings.legend_out_bbox_to_anchor}")
print(
    "panel_label_padding: "
    f"({cns.settings.panel_pad_left}, {cns.settings.panel_pad_top}) px"
)


# %%
# Plot with default settings
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Start from the package defaults.
cns.settings.reset()

cns.figure()
ax = cns.placeholderplot("Settings")
ax.set_title("Settings")


# %%
# Change the core plotting style
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# The original palette, font, and spine settings still work as before.
cns.settings.reset()
cns.settings.palette_qual = "Set2"
cns.settings.palette_seq = "parula"
cns.settings.title_fontsize = 10
cns.settings.title_fontweight = "normal"
cns.settings.fontsize_legend = 9
cns.settings.axes_linewidth = 1.0

cns.figure()
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Core Style Defaults")


# %%
# Change setup and figure defaults
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Settings can now control default figure size, dpi, legend sizing,
# axis title placement, and tick styling for setup functions.
cns.settings.reset()
cns.settings.figure_width = 220
cns.settings.figure_height = 140
cns.settings.figure_dpi = 180
cns.settings.legend_fontsize = 8
cns.settings.legend_title_fontsize = 9
cns.settings.axes_titlelocation = "left"
cns.settings.axes_edgecolor = "#444444"
cns.settings.axes_labelcolor = "#444444"
cns.settings.xtick_labelrotation = 20
cns.settings.xtick_alignment = "right"

cns.figure()
ax = cns.scatterplot(data=tips, x="total_bill", y="tip", hue="day", s=12)
ax.set_title("Figure + Setup Defaults")


# %%
# Change helper defaults
# ~~~~~~~~~~~~~~~~~~~~~~
# Helper settings cover legend placement plus panel label typography
# and padding.
cns.settings.reset()
cns.settings.legend_out_bbox_to_anchor = (1.05, 1.0)
cns.settings.legend_out_loc = "upper left"
cns.settings.legend_out_markerscale = 1.2
cns.settings.panel_label_fontname = "DejaVu Sans"
cns.settings.panel_label_fontweight = "normal"
cns.settings.panel_pad_left = 18
cns.settings.panel_pad_top = 4

cns.figure()
ax = cns.scatterplot(data=tips, x="total_bill", y="tip", hue="time", s=14)
cns.take_legend_out(title="Time")
cns.add_panel_label("A")
ax.set_title("Legend + Panel Label Defaults")


# %%
# Change multipanel defaults
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# ``multipanel()`` and ``panel()`` now read their omitted defaults from
# ``cns.settings`` as well. In multipanel layouts, ``panel_pad_left`` is the
# extra gap between the panel label and the rendered left-side y-axis text.
cns.settings.reset()
cns.settings.multipanel_max_width = 320
cns.settings.multipanel_title_loc = "left"
cns.settings.panel_width = 130
cns.settings.panel_height = 120
cns.settings.panel_pad_left = 36
cns.settings.panel_pad_top = 16
cns.settings.panel_margin_top = 0
cns.settings.panel_margin_bottom = 16
cns.settings.panel_margin_left = 8
cns.settings.panel_margin_right = 10
cns.settings.panel_label_fontname = "DejaVu Sans"

mp = cns.multipanel(title="Settings-driven Multipanel")
ax = mp.panel()
cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Panel A")

ax = mp.panel()
cns.barplot(data=tips, x="day", y="tip")
ax.set_title("Panel B")


# %%
# Temporarily override settings with a context manager
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ``settings.context()`` works with the new setup/helper defaults too.
cns.settings.reset()

with cns.settings.context(
    palette_qual="Dark2",
    figure_width=200,
    figure_height=120,
    axes_titlelocation="left",
    panel_label_fontweight="normal",
):
    cns.figure()
    ax = cns.boxplot(data=tips, x="day", y="tip")
    cns.add_panel_label("B")
    ax.set_title("Context Manager Override")

# Settings are restored after the context block
print(f"After context: palette_qual={cns.settings.palette_qual}")
print(
    "After context: "
    f"figure={cns.settings.figure_width} x {cns.settings.figure_height} px"
)
print(f"After context: panel_label_fontweight={cns.settings.panel_label_fontweight}")


# %%
# Override settings per-call
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Explicit function arguments still override the global defaults.
cns.settings.reset()
cns.settings.figure_width = 220
cns.settings.figure_height = 140

cns.figure(150, 150, color_cycle="Tableau")
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Per-call Override: 150 x 150, Tableau")


# %%
# Reset for a clean state
# ~~~~~~~~~~~~~~~~~~~~~~~
cns.settings.reset()
print("Settings reset to defaults:")
print(cns.settings)
