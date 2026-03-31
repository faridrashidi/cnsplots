# Settings

`cns.settings` is the public settings object for package-wide cnsplots defaults.
Update its attributes to change styling, export behavior, setup helpers, figure
helpers, and multipanel defaults for subsequent plotting calls.

Changes to `cns.settings` are global until you either call
`cns.settings.reset()` or temporarily override a subset of values inside
`cns.settings.context(...)`.

See the {doc}`API landing page <api>` for the broader API reference and the
runnable {doc}`settings example <examples/settings>` for a gallery-backed tour
of these defaults in practice.

## Quickstart

Inspect the current settings object:

```python
import cnsplots as cns

print(cns.settings)
```

Assign a new global default:

```python
cns.settings.title_fontsize = 10
cns.settings.palette_qual = "Set2"
```

Reset back to the package defaults:

```python
cns.settings.reset()
```

Apply temporary overrides inside a context manager:

```python
with cns.settings.context(
    palette_qual="Dark2",
    figure_width=200,
    figure_height=120,
):
    ...
```

## Methods

```{eval-rst}
.. automethod:: cnsplots._settings.CNSSettings.reset

.. automethod:: cnsplots._settings.CNSSettings.context
```

## Core Style And Typography

These defaults shape the package-wide visual style, text rendering, and logging
verbosity used by later helper and plotting calls.

```{eval-rst}
.. autoattribute:: cnsplots._settings.CNSSettings.palette_qual
.. autoattribute:: cnsplots._settings.CNSSettings.palette_seq
.. autoattribute:: cnsplots._settings.CNSSettings.title_fontsize
.. autoattribute:: cnsplots._settings.CNSSettings.title_fontweight
.. autoattribute:: cnsplots._settings.CNSSettings.verbosity
.. autoattribute:: cnsplots._settings.CNSSettings.mathtext_fontset
.. autoattribute:: cnsplots._settings.CNSSettings.font_family
.. autoattribute:: cnsplots._settings.CNSSettings.font_sans_serif
```

## Export And Backend Defaults

These settings control the default save behavior and font embedding choices for
exported figures.

```{eval-rst}
.. autoattribute:: cnsplots._settings.CNSSettings.savefig_bbox
.. autoattribute:: cnsplots._settings.CNSSettings.savefig_pad_inches
.. autoattribute:: cnsplots._settings.CNSSettings.savefig_dpi
.. autoattribute:: cnsplots._settings.CNSSettings.savefig_transparent
.. autoattribute:: cnsplots._settings.CNSSettings.svg_fonttype
.. autoattribute:: cnsplots._settings.CNSSettings.pdf_fonttype
```

## Axes, Ticks, Legends, And P-Value Annotations

These defaults are consumed by `setup_matplotlib()`, `setup_ax()`, plot
formatting helpers, and annotation utilities.

```{eval-rst}
.. autoattribute:: cnsplots._settings.CNSSettings.axes_linewidth
.. autoattribute:: cnsplots._settings.CNSSettings.axes_titlelocation
.. autoattribute:: cnsplots._settings.CNSSettings.axes_grid
.. autoattribute:: cnsplots._settings.CNSSettings.axes_spines_top
.. autoattribute:: cnsplots._settings.CNSSettings.axes_spines_right
.. autoattribute:: cnsplots._settings.CNSSettings.axes_edgecolor
.. autoattribute:: cnsplots._settings.CNSSettings.axes_labelcolor
.. autoattribute:: cnsplots._settings.CNSSettings.axes_labelpad
.. autoattribute:: cnsplots._settings.CNSSettings.axes_titlepad
.. autoattribute:: cnsplots._settings.CNSSettings.axes_xmargin
.. autoattribute:: cnsplots._settings.CNSSettings.axes_ymargin
.. autoattribute:: cnsplots._settings.CNSSettings.legend_fontsize
.. autoattribute:: cnsplots._settings.CNSSettings.legend_title_fontsize
.. autoattribute:: cnsplots._settings.CNSSettings.legend_frameon
.. autoattribute:: cnsplots._settings.CNSSettings.legend_markerscale
.. autoattribute:: cnsplots._settings.CNSSettings.legend_handlelength
.. autoattribute:: cnsplots._settings.CNSSettings.legend_handleheight
.. autoattribute:: cnsplots._settings.CNSSettings.legend_handletextpad
.. autoattribute:: cnsplots._settings.CNSSettings.pvalue_format
.. autoattribute:: cnsplots._settings.CNSSettings.pvalue_fontsize
.. autoattribute:: cnsplots._settings.CNSSettings.annotation_auto_contrast
.. autoattribute:: cnsplots._settings.CNSSettings.xtick_bottom
.. autoattribute:: cnsplots._settings.CNSSettings.xtick_color
.. autoattribute:: cnsplots._settings.CNSSettings.xtick_major_size
.. autoattribute:: cnsplots._settings.CNSSettings.xtick_major_width
.. autoattribute:: cnsplots._settings.CNSSettings.xtick_major_pad
.. autoattribute:: cnsplots._settings.CNSSettings.xtick_alignment
.. autoattribute:: cnsplots._settings.CNSSettings.xtick_labelrotation
.. autoattribute:: cnsplots._settings.CNSSettings.ytick_left
.. autoattribute:: cnsplots._settings.CNSSettings.ytick_color
.. autoattribute:: cnsplots._settings.CNSSettings.ytick_major_size
.. autoattribute:: cnsplots._settings.CNSSettings.ytick_major_width
.. autoattribute:: cnsplots._settings.CNSSettings.ytick_major_pad
.. autoattribute:: cnsplots._settings.CNSSettings.ytick_alignment
.. autoattribute:: cnsplots._settings.CNSSettings.ytick_labelrotation
.. autoattribute:: cnsplots._settings.CNSSettings.setup_ax_colorbar_label
```

## Scanpy / ggplot Integration Defaults

These values feed the integration helpers that style scanpy figures and
generate ggplot theme defaults.

```{eval-rst}
.. autoattribute:: cnsplots._settings.CNSSettings.scanpy_use_default_style
.. autoattribute:: cnsplots._settings.CNSSettings.scanpy_figsize
.. autoattribute:: cnsplots._settings.CNSSettings.scanpy_facecolor
.. autoattribute:: cnsplots._settings.CNSSettings.ggplot_fontsize
.. autoattribute:: cnsplots._settings.CNSSettings.ggplot_font_family
.. autoattribute:: cnsplots._settings.CNSSettings.ggplot_font_face
.. autoattribute:: cnsplots._settings.CNSSettings.ggplot_text_color
```

## Figure, Multipanel, And Helper Defaults

These defaults power figure sizing, multipanel layout, panel labels, and
legend-placement helpers when explicit arguments are omitted.

```{eval-rst}
.. autoattribute:: cnsplots._settings.CNSSettings.figure_width
.. autoattribute:: cnsplots._settings.CNSSettings.figure_height
.. autoattribute:: cnsplots._settings.CNSSettings.figure_dpi
.. autoattribute:: cnsplots._settings.CNSSettings.multipanel_max_width
.. autoattribute:: cnsplots._settings.CNSSettings.multipanel_title_loc
.. autoattribute:: cnsplots._settings.CNSSettings.multipanel_title_height_min
.. autoattribute:: cnsplots._settings.CNSSettings.multipanel_title_height_pad
.. autoattribute:: cnsplots._settings.CNSSettings.panel_width
.. autoattribute:: cnsplots._settings.CNSSettings.panel_height
.. autoattribute:: cnsplots._settings.CNSSettings.panel_pad_left
.. autoattribute:: cnsplots._settings.CNSSettings.panel_pad_top
.. autoattribute:: cnsplots._settings.CNSSettings.panel_margin_top
.. autoattribute:: cnsplots._settings.CNSSettings.panel_margin_bottom
.. autoattribute:: cnsplots._settings.CNSSettings.panel_margin_left
.. autoattribute:: cnsplots._settings.CNSSettings.panel_margin_right
.. autoattribute:: cnsplots._settings.CNSSettings.panel_label_fontname
.. autoattribute:: cnsplots._settings.CNSSettings.panel_label_fontweight
.. autoattribute:: cnsplots._settings.CNSSettings.legend_out_bbox_to_anchor
.. autoattribute:: cnsplots._settings.CNSSettings.legend_out_loc
.. autoattribute:: cnsplots._settings.CNSSettings.legend_out_markerscale
```
