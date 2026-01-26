"""
settings
--------

Configure global defaults for cnsplots.

cnsplots provides a settings module to customize global defaults
for palettes, font sizes, line widths, and verbosity. Changes to
settings affect all subsequent plotting calls.
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
# Access individual settings
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Each setting can be accessed directly.
print(f"palette_qual: {cns.settings.palette_qual}")
print(f"palette_seq: {cns.settings.palette_seq}")
print(f"fontsize_title: {cns.settings.fontsize_title}")
print(f"fontsize_legend: {cns.settings.fontsize_legend}")
print(f"linewidth_axes: {cns.settings.linewidth_axes}")
print(f"verbosity: {cns.settings.verbosity}")


# %%
# Plot with default settings
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# First, let's see how plots look with default settings.
cns.figure(150, 150)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Default Settings")


# %%
# Change the default palette
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set a different qualitative palette for all subsequent plots.
cns.settings.palette_qual = "Set2"

cns.figure(150, 150)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("palette_qual = 'Set2'")


# %%
# Change font sizes
# ~~~~~~~~~~~~~~~~~
# Increase font sizes for larger figures or presentations.
cns.settings.fontsize_title = 10
cns.settings.fontsize_legend = 9

cns.figure(150, 150)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Larger Font Sizes")


# %%
# Change axis line width
# ~~~~~~~~~~~~~~~~~~~~~~
# Make axis lines thicker or thinner.
cns.settings.linewidth_axes = 1.0

cns.figure(150, 150)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Thicker Axis Lines")


# %%
# Reset all settings to defaults
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Use reset() to restore all settings to their original values.
cns.settings.reset()

cns.figure(150, 150)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Back to Defaults")


# %%
# Suppress output with verbosity
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set verbosity to 0 to suppress print statements from cnsplots functions.
cns.settings.verbosity = 0

# Functions that would normally print will now be silent
# (This is useful for batch processing or notebooks)


# %%
# Restore verbosity
# ~~~~~~~~~~~~~~~~~
cns.settings.verbosity = 1


# %%
# Combine multiple settings
# ~~~~~~~~~~~~~~~~~~~~~~~~~
# Configure multiple settings for a custom style.
cns.settings.palette_qual = "Dark2"
cns.settings.palette_seq = "parula"
cns.settings.fontsize_title = 9
cns.settings.fontsize_legend = 8
cns.settings.linewidth_axes = 0.75

cns.figure(150, 150)
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Custom Style")


# %%
# Settings persist across calls
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Once set, settings apply to all subsequent plots.
cns.figure(150, 150)
ax = cns.barplot(data=tips, x="day", y="total_bill")
ax.set_title("Same Custom Style")


# %%
# Override settings per-call
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# You can still override settings for individual calls.
cns.figure(150, 150, color_cycle="Tableau")
ax = cns.boxplot(data=tips, x="day", y="total_bill")
ax.set_title("Per-call Override: Tableau")


# %%
# Reset for clean state
# ~~~~~~~~~~~~~~~~~~~~~
cns.settings.reset()
print("Settings reset to defaults:")
print(cns.settings)
