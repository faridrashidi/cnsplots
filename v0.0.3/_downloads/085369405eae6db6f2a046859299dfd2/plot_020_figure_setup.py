"""
figure_setup
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
import seaborn as sns

import cnsplots as cns

tips = sns.load_dataset("tips")
iris = sns.load_dataset("iris")


# %%
# Basic figure creation
# ~~~~~~~~~~~~~~~~~~~~~
# Create a figure with specified dimensions in pixels.
# Default is 150x150 pixels at 72 DPI base (144 DPI actual).
cns.figure(150, 150, [cns.GRAY])
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("150x150 Figure")


# %%
# Different figure sizes
# ~~~~~~~~~~~~~~~~~~~~~~
# Adjust figure dimensions for different purposes.
cns.figure(100, 80)  # Small/compact
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
cns.figure(150, 100, "Tableau")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Tableau Palette")


# %%
# Set1 palette
# ~~~~~~~~~~~~
cns.figure(150, 100, "Set1")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Set1 Palette")


# %%
# Set2 palette
# ~~~~~~~~~~~~
cns.figure(150, 100, "Set2")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Set2 Palette")


# %%
# Bold palette
# ~~~~~~~~~~~~
cns.figure(150, 100, "Bold")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Bold Palette")


# %%
# BlueRed diverging palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(150, 100, "BlueRed")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("BlueRed Palette")


# %%
# Using palettes() function
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Get palette colors programmatically.
cns.figure(150, 100, color_cycle="Ecotyper1")
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Ecotyper1 Palette")


# %%
# Custom color list
# ~~~~~~~~~~~~~~~~~
# Pass a list of specific colors.
custom_colors = [cns.RED, cns.BLUE, cns.GREEN, cns.ORANGE]
cns.figure(150, 100, color_cycle=custom_colors)
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
# Use ``get_hexcolors_from_apalette()`` to pick specific colors.
selected_colors = cns.get_hexcolors_from_apalette([0, 2, 4, 6])
cns.figure(150, 100, color_cycle=selected_colors)
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Selected Colors from Set1")


# %%
# Taking legend outside the plot
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``take_legend_out()`` to move legend to the right margin.
cns.figure(180, 100)
ax = cns.boxplot(data=tips, x="day", y="total_bill", hue="sex")
cns.take_legend_out()
ax.set_title("Legend Outside")


# %%
# Legend with custom title
# ~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(180, 100)
ax = cns.boxplot(data=tips, x="day", y="total_bill", hue="sex")
cns.take_legend_out(title="Gender")
ax.set_title("Legend with Title")


# %%
# Adding panel labels manually
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use ``add_panel_label()`` for manual figure composition.
cns.figure(150, 100)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
cns.add_panel_label("A")
ax.set_title("With Panel Label")


# %%
# Panel label with custom position
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cns.figure(150, 100)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
cns.add_panel_label("B", offset_x=-0.15, offset_y=1.05)
ax.set_title("Custom Label Position")


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
    fontsize_title=10,
    fontsize_legend=8,
    linewidth_axes=0.8,
)
fig, ax = plt.subplots(figsize=(2, 1.5))
ax.bar(["A", "B", "C", "D"], [10, 15, 12, 18])
ax.set_title("Custom Font Sizes")


# %%
# Saving figures
# ~~~~~~~~~~~~~~
# Use ``savefig()`` to save figures in various formats.
# Supported formats: PDF, PNG, SVG, EPS, JPG
cns.figure(150, 100)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Save Example")

# Example save commands (commented to avoid creating files):
# cns.savefig("figure.pdf")   # PDF for publications
# cns.savefig("figure.svg")   # SVG for editing in Illustrator
# cns.savefig("figure.png")   # PNG for presentations
# cns.savefig("~/Desktop/figure.pdf")  # Supports ~ expansion


# %%
# Figure dimensions reference
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Common figure sizes for different purposes:
#
# - Single column (Nature/Science): max 89mm = ~252 pixels
# - 1.5 column: max 120mm = ~340 pixels
# - Double column: max 183mm = ~518 pixels
# - Full page: max 178mm = ~504 pixels (with margins)
#
# cnsplots uses pixels at 72 DPI base for sizing.
# The default max_width=540 in multipanel matches double column.

cns.figure(252, 150)  # Single column width
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Single Column Width (89mm)")
