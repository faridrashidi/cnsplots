"""
Figure Setup
------------

Configure figure dimensions, styling, and export options.

cnsplots provides precise control over figure appearance for
publication-ready outputs. This example covers figure creation,
matplotlib configuration, and saving figures in various formats.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import matplotlib.pyplot as plt

import cnsplots as cns

tips = cns.datasets.load_dataset("tips")
iris = cns.datasets.load_dataset("iris")


# %%
# Basic figure creation
# ~~~~~~~~~~~~~~~~~~~~~
# Create a figure with specified dimensions in points (1/72 inch).
# figure(width, height) uses width-first order and sizes the whole canvas.
# Points are the legacy logical 72-DPI units; existing calls keep their size.
# The returned Matplotlib Figure is also the current figure used by subsequent
# plotting calls. Display and export DPI set pixel resolution, not physical size.
fig = cns.figure(150, 150)
ax = cns.placeholderplot("150x150 pt Figure")
ax.set_title("Figure Setup")


# %%
# Physical units and raster resolution
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ``unit="pt"`` (default), ``unit="in"``, and ``unit="mm"`` apply to explicitly
# supplied dimensions. Omitted dimensions keep settings values in points.
# These three calls all create a 2 x 1 inch canvas:
for width, height, unit in [(144, 72, "pt"), (2, 1, "in"), (50.8, 25.4, "mm")]:
    fig = cns.figure(width, height, unit=unit)
    print(fig.get_size_inches())  # [2. 1.]
    plt.close(fig)

fig = cns.figure(100, 150)
print(fig.get_size_inches())  # [1.38888889 2.08333333]
print(fig.canvas.get_width_height())  # (200, 300) at default display DPI 144
ax = cns.placeholderplot("100x150 pt Canvas")
# At the default export DPI of 288, bbox_inches=None preserves a 400 x 600 px
# full canvas. Default tight cropping instead encloses the artists and adds
# pad_inches in inches, so the saved dimensions can differ from the canvas.
# cns.savefig("full-canvas.png", fig=fig, bbox_inches=None)


# %%
# Different figure sizes
# ~~~~~~~~~~~~~~~~~~~~~~
# Adjust figure dimensions for different purposes.
cns.figure(80, 100)  # Small/compact
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Small Figure")


# %%
# Wider figure for more categories
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(200, 100)  # Wide
ax = cns.boxplot(data=tips, x="day", y="total_bill", hue="sex")
cns.take_legend_out()
ax.set_title("Wide Figure")


# %%
# Square figure for scatter plots
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(150, 150)  # Square
ax = cns.scatterplot(data=iris, x="sepal_length", y="sepal_width", hue="species", s=10)
cns.take_legend_out()
ax.set_title("Square Figure")


# %%
# Using different color palettes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Pass palette name as third argument to ``figure()``.
cns.figure(100, 150, "Tableau")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Tableau Palette")


# %%
# Set1 palette
# ~~~~~~~~~~~~
cns.figure(100, 150, "Set1")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Set1 Palette")


# %%
# Set2 palette
# ~~~~~~~~~~~~
cns.figure(100, 150, "Set2")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Set2 Palette")


# %%
# Bold palette
# ~~~~~~~~~~~~
cns.figure(100, 150, "Bold")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Bold Palette")


# %%
# BlueRed diverging palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(100, 150, "BlueRed")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("BlueRed Palette")


# %%
# Using palettes() function
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Get palette colors programmatically.
cns.figure(100, 150, color_cycle="Ecotyper1")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Ecotyper1 Palette")


# %%
# Custom color list
# ~~~~~~~~~~~~~~~~~
# Pass a list of specific colors.
custom_colors = [cns.RED, cns.BLUE, cns.GREEN, cns.ORANGE]
cns.figure(100, 150, color_cycle=custom_colors)
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Custom Color List")


# %%
# Using color constants
# ~~~~~~~~~~~~~~~~~~~~~
# cnsplots provides named color constants.
print("Available color constants:")
print(f"  RED: {cns.RED}")
print(f"  BLUE: {cns.BLUE}")
print(f"  GREEN: {cns.GREEN}")
print(f"  ORANGE: {cns.ORANGE}")
print(f"  PURPLE: {cns.PURPLE}")
print(f"  YELLOW: {cns.YELLOW}")
print(f"  PINK: {cns.PINK}")
print(f"  GRAY: {cns.GRAY}")


# %%
# Selecting specific colors from palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``get_palette_colors()`` to pick specific colors; the default is Set1.
# The original ``get_hexcolors_from_apalette()`` name remains supported.
selected_colors = cns.get_palette_colors([0, 2, 4, 6])
cns.figure(100, 150, color_cycle=selected_colors)
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Selected Colors from Set1")


# %%
# Taking legend outside the plot
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``take_legend_out()`` to move legend to the right margin.
# Small figures can expand on draw so the outside legend is not clipped.
cns.figure(100, 180)
ax = cns.boxplot(data=tips, x="day", y="total_bill", hue="sex")
cns.take_legend_out()
ax.set_title("Legend Outside")


# %%
# Legend with custom title
# ~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(100, 180)
ax = cns.boxplot(data=tips, x="day", y="total_bill", hue="sex")
cns.take_legend_out(title="Gender")
ax.set_title("Legend with Title")


# %%
# Adding panel labels manually
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``add_panel_label()`` for manual figure composition.
cns.figure(100, 150)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
cns.add_panel_label("A")
ax.set_title("With Panel Label")


# %%
# Panel label with custom padding
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(100, 150)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
cns.add_panel_label("B", pad_left=14, pad_top=4)
ax.set_title("Custom Label Padding")


# %%
# Setup matplotlib manually
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``setup_matplotlib()`` for manual configuration.
# This is automatically called by ``figure()`` but can be
# used independently for custom workflows.
cns.setup_matplotlib()
fig, ax = plt.subplots(figsize=(2, 1.5))
ax.bar(["A", "B", "C", "D"], [10, 15, 12, 18])
ax.set_title("Manual Setup")


# %%
# Setup with custom parameters
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.setup_matplotlib(
    title_fontsize=10,
    legend_fontsize=8,
    axes_linewidth=0.8,
)
fig, ax = plt.subplots(figsize=(2, 1.5))
ax.bar(["A", "B", "C", "D"], [10, 15, 12, 18])
ax.set_title("Custom Font Sizes")


# %%
# Saving figures
# ~~~~~~~~~~~~~~
# Use ``savefig()`` to save figures in various formats.
# Supported formats: PDF, PNG, SVG, EPS, JPG. Keep the returned figure so it
# can be saved even when another figure becomes current.
fig = cns.figure(100, 150)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Save Example")

# Example save commands (commented to avoid creating files):
# cns.savefig("figure.pdf", fig=fig)   # PDF for publications
# cns.savefig("figure.svg", fig=fig)   # SVG for editing in Illustrator
# cns.savefig("figure.png", fig=fig, dpi=300, transparent=False)
# cns.savefig("figure-tight.pdf", fig=fig, bbox_inches="tight", pad_inches=0.1)
# cns.savefig("figure-full.pdf", fig=fig, bbox_inches=None)  # Full canvas
# cns.savefig("~/Desktop/figure.pdf")  # Supports ~ expansion
# Omitted options use cns.settings. Per-save overrides leave settings unchanged.
# Padding is in inches and applies only to tight cropping.


# %%
# Figure dimensions reference
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Example publication widths (check the target journal's current guidelines):
#
# - 89 mm = ~252 pt
# - 120 mm = ~340 pt
# - 183 mm = ~519 pt
# - 178 mm = ~505 pt
#
# The default multipanel max_width=540 pt corresponds to 190.5 mm.
# Use bbox_inches=None on export to preserve the requested canvas size.

cns.figure(width=89, height=53, unit="mm")
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Single Column Width (89mm)")
