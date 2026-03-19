from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
    from matplotlib.axes import Axes

import itertools
import operator
import os
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib.backend_bases import DrawEvent
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.legend  # noqa: F401  # ensure submodule is importable for isinstance checks
import num2tex
import palettable
import pandas as pd
import scipy.stats as stats
import seaborn as sns
from statannotations.Annotator import Annotator
from statannotations.PValueFormat import PValueFormat
from statannotations.utils import DEFAULT

import cnsplots as cns
from cnsplots._svg import _save_svg

RED = "#D6372E"
BLUE = "#5189BB"
GREEN = "#70B460"
PURPLE = "#985EA8"
ORANGE = "#F08F35"
YELLOW = "#FADD4B"
BROWN = "#9C5732"
PINK = "#E787E5"
GRAY = "#A3A3A3"
VIOLET = "#442288"
CHOCOLATE = "#662506"

_FIGURE_AUTOFIT_TOLERANCE_PX = 0.8
_FIGURE_AUTOFIT_MAX_PASSES = 3


class _FigureAutofitManager:
    """Grow cns.figure canvases when rendered artists overflow the figure bbox."""

    def __init__(self, fig):
        self.fig = fig
        self._min_width_px = float(fig.get_figwidth() * fig.dpi)
        self._min_height_px = float(fig.get_figheight() * fig.dpi)
        self._draw_event_cid = None
        self._is_relayout_in_draw = False
        self._connect_draw_handler()

    def _connect_draw_handler(self):
        if self._draw_event_cid is not None:
            return
        self._draw_event_cid = self.fig.canvas.mpl_connect("draw_event", self._on_draw)

    def _get_canvas_renderer(self, canvas):
        """Return the canvas renderer when the backend exposes it."""
        get_renderer = getattr(canvas, "get_renderer", None)
        if not callable(get_renderer):
            return None
        return get_renderer()

    def _get_artist_bbox(self, artist, renderer):
        """Get a rendered bbox for an artist when available."""
        get_tightbbox = getattr(artist, "get_tightbbox", None)
        if callable(get_tightbbox):
            bbox = get_tightbbox(renderer=renderer)
            if bbox is not None:
                return bbox
        get_window_extent = getattr(artist, "get_window_extent", None)
        if callable(get_window_extent):
            try:
                return get_window_extent(renderer=renderer)
            except TypeError:
                return get_window_extent()
        return None

    def _iter_figure_artists(self):
        """Yield figure-level artists that can overflow the canvas."""
        yield from self.fig.texts
        yield from self.fig.legends
        for artist in self.fig.artists:
            if artist not in self.fig.texts and artist not in self.fig.legends:
                yield artist

    def _iter_axes_artists(self, ax):
        """Yield axes-level artists that can overflow the canvas."""
        axis_is_visible = getattr(ax, "axison", True)

        for title_name in ("title", "_left_title", "_right_title"):
            title = getattr(ax, title_name, None)
            if title is not None:
                yield title

        if axis_is_visible:
            yield ax.xaxis.label
            yield ax.yaxis.label
            yield ax.xaxis.get_offset_text()
            yield ax.yaxis.get_offset_text()
            yield from ax.get_xticklabels()
            yield from ax.get_yticklabels()

        legend = ax.get_legend()
        if legend is not None:
            yield legend

        if not axis_is_visible:
            # Axis-off helper axes can still contain important clipped content
            # such as dendrograms or detached legends; count their panel bounds.
            yield ax.patch

        yield from ax.texts

        for artist in (*ax.lines, *ax.collections, *ax.patches, *ax.artists):
            if not axis_is_visible:
                yield artist
                continue
            get_clip_on = getattr(artist, "get_clip_on", None)
            if callable(get_clip_on) and not get_clip_on():
                yield artist

    def _iter_axes_non_title_artists(self, ax):
        """Yield axes artists that can move with the axes during tightening."""
        yield ax.xaxis.label
        yield ax.yaxis.label
        yield ax.xaxis.get_offset_text()
        yield ax.yaxis.get_offset_text()
        yield from ax.get_xticklabels()
        yield from ax.get_yticklabels()

        legend = ax.get_legend()
        if legend is not None:
            yield legend

        if not getattr(ax, "axison", True):
            yield ax.patch

        yield from ax.texts

        for artist in (*ax.lines, *ax.collections, *ax.patches, *ax.artists):
            get_clip_on = getattr(artist, "get_clip_on", None)
            if callable(get_clip_on) and not get_clip_on():
                yield artist

    def _figure_has_expanded(self):
        """Report whether the current canvas is larger than the requested minimum."""
        fig_bbox = self.fig.bbox.frozen()
        return (
            float(fig_bbox.width) > self._min_width_px + _FIGURE_AUTOFIT_TOLERANCE_PX
            or float(fig_bbox.height)
            > self._min_height_px + _FIGURE_AUTOFIT_TOLERANCE_PX
        )

    def _get_content_bbox(self, renderer):
        """Return the union bbox of all visible figure content."""
        artists = list(self._iter_figure_artists())
        for ax in self.fig.get_axes():
            artists.extend(self._iter_axes_artists(ax))

        bboxes = []
        for artist in artists:
            get_visible = getattr(artist, "get_visible", None)
            if callable(get_visible) and not get_visible():
                continue
            bbox = self._get_artist_bbox(artist, renderer)
            if bbox is None:
                continue
            if bbox.width <= 0 and bbox.height <= 0:
                continue
            bboxes.append(bbox.frozen())

        if not bboxes:
            return None
        return mtransforms.Bbox.union(bboxes)

    def _measure_overflow_px(self, renderer):
        """Measure how far visible artists extend past the current figure bbox."""
        fig_bbox = self.fig.bbox.frozen()
        content_bbox = self._get_content_bbox(renderer)
        if content_bbox is None:
            return 0.0, 0.0, 0.0, 0.0

        return tuple(
            max(0.0, value)
            for value in (
                float(fig_bbox.x0 - content_bbox.x0),
                float(content_bbox.x1 - fig_bbox.x1),
                float(fig_bbox.y0 - content_bbox.y0),
                float(content_bbox.y1 - fig_bbox.y1),
            )
        )

    def _run_axes_sync_hooks(self, attr_name):
        """Run unique axes resize hooks exposed under the given attribute name."""
        syncers = []
        seen = set()
        for ax in self.fig.get_axes():
            sync = getattr(ax, attr_name, None)
            if not callable(sync):
                continue
            sync_id = id(sync)
            if sync_id in seen:
                continue
            seen.add(sync_id)
            syncers.append(sync)

        for sync in syncers:
            sync()

    def _resize_canvas(self, left, right, bottom, top):
        """Resize the canvas and keep existing axes at their current pixel size."""
        fig_bbox = self.fig.bbox.frozen()
        current_width_px = float(fig_bbox.width)
        current_height_px = float(fig_bbox.height)
        if current_width_px <= 0 or current_height_px <= 0:
            return False

        axes_positions = []
        for ax in self.fig.get_axes():
            x0, y0, width, height = ax.get_position().bounds
            axes_positions.append(
                (
                    ax,
                    x0 * current_width_px,
                    y0 * current_height_px,
                    width * current_width_px,
                    height * current_height_px,
                )
            )

        new_width_px = current_width_px + left + right
        new_height_px = current_height_px + bottom + top
        if new_width_px <= 0 or new_height_px <= 0:
            return False
        self.fig.set_size_inches(
            new_width_px / self.fig.dpi,
            new_height_px / self.fig.dpi,
            forward=True,
        )

        for ax, x0_px, y0_px, width_px, height_px in axes_positions:
            ax.set_position(
                [
                    (x0_px + left) / new_width_px,
                    (y0_px + bottom) / new_height_px,
                    width_px / new_width_px,
                    height_px / new_height_px,
                ]
            )
        self._run_axes_sync_hooks("_cnsplots_sync_detached_legends")
        return True

    def _grow_canvas(self, left, right, bottom, top):
        """Increase canvas size and keep existing axes at their current pixel size."""
        return self._resize_canvas(left, right, bottom, top)

    def _tighten_single_axes_horizontal_layout(self, renderer):
        """Reduce excess left margin for expanded single-axes figures."""
        axes = self.fig.get_axes()
        if len(axes) != 1:
            return False

        ax = axes[0]
        fig_bbox = self.fig.bbox.frozen()
        leftmost = None
        for artist in self._iter_axes_non_title_artists(ax):
            get_visible = getattr(artist, "get_visible", None)
            if callable(get_visible) and not get_visible():
                continue
            bbox = self._get_artist_bbox(artist, renderer)
            if bbox is None:
                continue
            if bbox.width <= 0 and bbox.height <= 0:
                continue
            leftmost = (
                float(bbox.x0) if leftmost is None else min(leftmost, float(bbox.x0))
            )

        if leftmost is None:
            return False

        shift_left_px = max(0.0, leftmost - float(fig_bbox.x0))
        if shift_left_px <= _FIGURE_AUTOFIT_TOLERANCE_PX:
            return False

        axes_bbox = ax.get_window_extent(renderer=renderer)
        axes_width_px = float(axes_bbox.width)
        if axes_width_px <= 0:
            return False

        fig_width_px = float(fig_bbox.width)
        position = list(ax.get_position().bounds)
        shift_fraction = shift_left_px / fig_width_px
        if position[0] - shift_fraction < 0:
            shift_fraction = position[0]
            shift_left_px = shift_fraction * fig_width_px
        if shift_left_px <= _FIGURE_AUTOFIT_TOLERANCE_PX:
            return False

        ax.set_position(
            [
                position[0] - shift_fraction,
                position[1],
                position[2],
                position[3],
            ]
        )
        self._run_axes_sync_hooks("_cnsplots_sync_detached_legends")

        updated_axes_bbox = ax.get_window_extent(renderer=renderer)
        updated_axes_width_px = float(updated_axes_bbox.width)
        if updated_axes_width_px <= 0:
            return True

        center_title = ax.title
        if center_title.get_text():
            centered_x = (
                (float(fig_bbox.width) / 2.0) - float(updated_axes_bbox.x0)
            ) / updated_axes_width_px
            center_title.set_x(centered_x)

        for title_name in ("_left_title", "_right_title"):
            title = getattr(ax, title_name, None)
            if title is None or not title.get_text():
                continue
            title.set_x(title.get_position()[0] + shift_left_px / updated_axes_width_px)

        return True

    def _crop_canvas_to_content(self, renderer):
        """Trim outer canvas whitespace back to the tight content bbox."""
        fig_bbox = self.fig.bbox.frozen()
        content_bbox = self._get_content_bbox(renderer)
        if content_bbox is None:
            return False

        crop_left = max(0.0, float(content_bbox.x0 - fig_bbox.x0))
        crop_right = max(0.0, float(fig_bbox.x1 - content_bbox.x1))
        crop_bottom = max(0.0, float(content_bbox.y0 - fig_bbox.y0))
        crop_top = max(0.0, float(fig_bbox.y1 - content_bbox.y1))
        if (
            max(crop_left, crop_right, crop_bottom, crop_top)
            <= _FIGURE_AUTOFIT_TOLERANCE_PX
        ):
            return False

        return self._resize_canvas(
            -crop_left,
            -crop_right,
            -crop_bottom,
            -crop_top,
        )

    def _on_draw(self, event):
        """Relayout once after draw when axes decorations overflow the figure."""
        if self._is_relayout_in_draw or not cns.settings.figure_autofit:
            return
        if not isinstance(event, DrawEvent):
            return
        canvas = event.canvas
        if canvas is not self.fig.canvas:
            return
        renderer = event.renderer

        left, right, bottom, top = self._measure_overflow_px(renderer)
        needs_growth = max(left, right, bottom, top) > _FIGURE_AUTOFIT_TOLERANCE_PX
        if not needs_growth and not self._figure_has_expanded():
            return

        self._is_relayout_in_draw = True
        try:
            for _ in range(_FIGURE_AUTOFIT_MAX_PASSES):
                left, right, bottom, top = self._measure_overflow_px(renderer)
                if max(left, right, bottom, top) <= _FIGURE_AUTOFIT_TOLERANCE_PX:
                    break
                self._grow_canvas(left, right, bottom, top)
                canvas.draw()
                renderer = self._get_canvas_renderer(canvas)
                if renderer is None:
                    break
            if renderer is not None and self._figure_has_expanded():
                if self._tighten_single_axes_horizontal_layout(renderer):
                    canvas.draw()
                    renderer = self._get_canvas_renderer(canvas)
                if renderer is not None and self._crop_canvas_to_content(renderer):
                    canvas.draw()
        finally:
            self._is_relayout_in_draw = False


def _attach_figure_autofit(fig):
    """Attach the single-figure autofit manager to a figure once."""
    if getattr(fig, "_cnsplots_autofit_manager", None) is None:
        fig._cnsplots_autofit_manager = _FigureAutofitManager(fig)


def _preflight_autofit_for_export(fig):
    """Run autofit once with an Agg renderer so exports are backend-independent."""
    manager = getattr(fig, "_cnsplots_autofit_manager", None)
    if manager is None or not cns.settings.figure_autofit:
        return

    original_canvas = fig.canvas
    try:
        agg_canvas = FigureCanvasAgg(fig)
        agg_canvas.draw()
        manager._on_draw(DrawEvent("draw_event", agg_canvas, agg_canvas.get_renderer()))
    finally:
        fig.set_canvas(original_canvas)


def _chain_axes_sync_hook(
    ax: Axes,
    sync: Callable[[], None],
    attr_name: str = "_cnsplots_sync_embedded_axes",
) -> Callable[[], None]:
    """Append a host-axes sync hook without replacing an existing one."""
    existing_sync = getattr(ax, attr_name, None)
    if callable(existing_sync):

        def _chained_sync() -> None:
            existing_sync()
            sync()

        setattr(ax, attr_name, _chained_sync)
        return _chained_sync

    setattr(ax, attr_name, sync)
    return sync


def _capture_detached_axes_layout(
    host_ax: Axes,
    existing_axes: Sequence[Axes] | None = None,
    *,
    detached_axes: Sequence[Axes] | None = None,
):
    """Record helper axes relative to a host axes and sync them on relayout."""
    if detached_axes is None:
        existing_ids = {id(host_ax)} | {
            id(ax) for ax in ([] if existing_axes is None else existing_axes)
        }
        detached_axes = [ax for ax in host_ax.figure.axes if id(ax) not in existing_ids]

    host_pos = host_ax.get_position().frozen()
    had_layouts = hasattr(host_ax, "_cnsplots_detached_axes_layout")
    layouts = getattr(host_ax, "_cnsplots_detached_axes_layout", [])
    tracked_ids = {id(host_ax)} | {id(layout["ax"]) for layout in layouts}
    new_layouts = []

    for detached_ax in detached_axes:
        if getattr(detached_ax, "figure", None) is not host_ax.figure:
            continue
        if id(detached_ax) in tracked_ids:
            continue
        detached_pos = detached_ax.get_position().frozen()
        new_layouts.append(
            {
                "ax": detached_ax,
                "x0": float((detached_pos.x0 - host_pos.x0) / host_pos.width),
                "y0": float((detached_pos.y0 - host_pos.y0) / host_pos.height),
                "width": float(detached_pos.width / host_pos.width),
                "height": float(detached_pos.height / host_pos.height),
            }
        )
        set_axes_locator = getattr(detached_ax, "set_axes_locator", None)
        if callable(set_axes_locator):
            set_axes_locator(None)
        tracked_ids.add(id(detached_ax))

    if not new_layouts:
        return []

    layouts.extend(new_layouts)
    setattr(host_ax, "_cnsplots_detached_axes_layout", layouts)

    if not had_layouts:

        def _sync_detached_axes() -> None:
            current_host_pos = host_ax.get_position().frozen()
            for layout in getattr(host_ax, "_cnsplots_detached_axes_layout", []):
                detached_ax = layout["ax"]
                if getattr(detached_ax, "figure", None) is not host_ax.figure:
                    continue
                detached_ax.set_position(
                    [
                        current_host_pos.x0 + current_host_pos.width * layout["x0"],
                        current_host_pos.y0 + current_host_pos.height * layout["y0"],
                        current_host_pos.width * layout["width"],
                        current_host_pos.height * layout["height"],
                    ]
                )

        _chain_axes_sync_hook(host_ax, _sync_detached_axes)
    return new_layouts


def figure(height=None, width=None, color_cycle=None, color_map=None):
    """
    Initialize a new figure with custom size and styling.

    This function creates a new matplotlib figure with specified dimensions and
    applies the cnsplots style configuration including color palette and colormap.

    Parameters
    ----------
    height : int, default: 150
        Height of the figure in pixels.
    width : int, default: 150
        Width of the figure in pixels.
    color_cycle : str, default: None
        Name of the qualitative color palette to use for the color cycle.
        If None, uses cns.settings.palette_qual.
        Options include: 'Ecotyper1', 'Set1', 'Set2', 'Dark2', 'Tableau', etc.
    color_map : str, default: None
        Name of the sequential colormap to use for continuous data.
        If None, uses cns.settings.palette_seq.
        Options include: 'gnuplot', 'parula', 'bwr', 'hot', etc.

    Returns
    -------
    None
        This function creates a figure and returns nothing.

    See Also
    --------
    multipanel : Create multi-panel figures with automatic layout.
    savefig : Save the current figure to a file.
    setup_matplotlib : Configure matplotlib styling.

    Notes
    -----
    The function converts pixel dimensions to inches assuming 72 DPI base resolution
    and sets the actual DPI to 144 for high-quality output.

    The figure size formula: inches = pixels / 72, with DPI = 144

    Dimensions are interpreted as ``height, width`` in pixels. When
    ``cns.settings.figure_autofit`` is enabled, the requested size is the
    minimum canvas size and the rendered figure may grow on draw if visible
    decorations would otherwise be clipped.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.figure(height=200, width=300)
    >>> cns.boxplot(data=df, x="group", y="value")
    >>> cns.savefig("plot.pdf")

    >>> # With custom color scheme
    >>> cns.figure(height=150, width=150, color_cycle="Set2", color_map="parula")
    >>> cns.heatmapplot(adata)
    """
    if height is None:
        height = cns.settings.figure_height
    if width is None:
        width = cns.settings.figure_width
    if color_cycle is None:
        color_cycle = cns.settings.palette_qual
    if color_map is None:
        color_map = cns.settings.palette_seq
    cns.setup_matplotlib(color_cycle, color_map)
    fig = plt.figure(figsize=(width / 72, height / 72), dpi=cns.settings.figure_dpi)
    if cns.settings.figure_autofit:
        _attach_figure_autofit(fig)


def savefig(filepath):
    """
    Save the current figure to a file, creating directories if needed.

    This function saves the current matplotlib figure to the specified file path,
    automatically creating any missing parent directories.

    Parameters
    ----------
    filepath : str
        Path where the figure should be saved. Can include home directory shorthand
        (~). The file format is determined by the extension (e.g., .pdf, .png, .svg).

    Returns
    -------
    None
        This function saves the figure and returns nothing.

    See Also
    --------
    figure : Initialize a new figure with custom size and styling.
    multipanel : Create multi-panel figures.

    Notes
    -----
    The function automatically:

    - Expands user home directory (~) in the path
    - Creates parent directories when the path includes them
    - Determines the file format from the file extension
    - Uses an Illustrator-optimized SVG export path when MuPDF's ``mutool``
      is available, and falls back to matplotlib SVG output otherwise

    Supported formats include: PDF, PNG, SVG, JPG, EPS, and more (any format
    supported by matplotlib.pyplot.savefig).

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.figure()
    >>> cns.boxplot(data=df, x="group", y="value")
    >>> cns.savefig("~/results/figures/boxplot.pdf")

    >>> # Save in multiple formats
    >>> cns.savefig("plot.png")
    >>> cns.savefig("plot.svg")
    """
    filepath = Path(filepath).expanduser()
    if filepath.parent != Path("."):
        filepath.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.gcf()
    for ax in fig.get_axes():
        apply_unicode_font(ax)
    target_dpi = float(cns.settings.savefig_dpi)
    original_dpi = fig.dpi
    root, ext = os.path.splitext(filepath)
    try:
        if target_dpi != original_dpi:
            fig.set_dpi(target_dpi)
        _preflight_autofit_for_export(fig)
        fig.canvas.draw()
        if ext.lower() == ".svg":
            _save_svg(str(filepath), root)
        else:
            plt.savefig(filepath, dpi=target_dpi)
    finally:
        if fig.dpi != original_dpi:
            fig.set_dpi(original_dpi)
            fig.canvas.draw()


def take_legend_out(title=None):
    """
    Move the legend outside the plot area to the upper-left of the right margin.

    This function repositions the current axes legend to appear outside and to
    the right of the plot area, preventing overlap with the plotted data.

    Parameters
    ----------
    title : str, optional
        Title for the legend. If None, uses the existing legend title from
        the current axes.

    Returns
    -------
    None
        This function modifies the current legend and returns nothing.

    See Also
    --------
    figure : Initialize a new figure.
    multipanel : Create multi-panel figures with automatic layout.

    Notes
    -----
    The legend is positioned with:
    - bbox_to_anchor=(1, 1.02): Slight offset above the upper-right corner
    - loc='upper left': Legend's upper-left corner is anchored to that point

    This ensures the legend appears just to the right of the plot area without
    obscuring data points.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.figure()
    >>> cns.scatterplot(data=df, x="PC1", y="PC2", hue="cell_type")
    >>> cns.take_legend_out()

    >>> # With custom title
    >>> cns.barplot(data=df, x="treatment", y="response", hue="batch")
    >>> cns.take_legend_out(title="Batch")
    """
    ax = plt.gca()
    legend = ax.get_legend()
    handles = None
    labels = None
    if legend is not None:
        handles = legend.legend_handles
        labels = [t.get_text() for t in legend.texts]
        if title is None:
            title = legend.get_title().get_text()
    if title is None:
        title = ""
    plt.legend(
        handles=handles,
        labels=labels,
        bbox_to_anchor=cns.settings.legend_out_bbox_to_anchor,
        loc=cns.settings.legend_out_loc,
        title=title,
        markerscale=cns.settings.legend_out_markerscale,
    )


def add_panel_label(name="A", pad_left=None, pad_top=None):
    """
    Add a panel label (e.g., 'A', 'B', 'C') to the current axes.

    This function adds a bold text label to the current axes, typically used
    for labeling panels in multi-panel figures for publication.

    Parameters
    ----------
    name : str, default: 'A'
        The label text to display (typically a single letter).
    pad_left : float, default: 20
        Horizontal padding in pixels from the axes left edge to the label's
        right edge. Positive values place the label to the left of the axes.
        This helper only offsets the label artist; it does not reserve extra
        layout space for y-axis text.
    pad_top : float, default: 0
        Vertical padding in pixels from the axes top edge to the label's
        bottom edge. Positive values place the label above the axes.

    Returns
    -------
    None
        This function adds text to the axes and returns nothing.

    See Also
    --------
    multipanel : Create multi-panel figures with automatic labeling.
    figure : Initialize a new figure.

    Notes
    -----
    The label is positioned relative to the axes' top-left corner using pixel
    padding. The label's right edge sits ``pad_left`` pixels to the left of the
    axes, and the label's bottom edge sits ``pad_top`` pixels above the axes.

    Unlike ``multipanel.panel()``, this helper does not measure rendered axis
    decorations or relayout the figure. It is purely an axes-relative offset.

    The label uses Arial font (bold) at 8pt size (`title_fontsize`) for
    consistency with publication standards.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.figure()
    >>> cns.boxplot(data=df, x="group", y="value")
    >>> cns.add_panel_label("A")

    >>> # Custom positioning
    >>> cns.figure()
    >>> cns.barplot(data=df, x="treatment", y="response")
    >>> cns.add_panel_label("B", pad_left=24, pad_top=6)
    """
    if pad_left is None:
        pad_left = cns.settings.panel_pad_left
    if pad_top is None:
        pad_top = cns.settings.panel_pad_top

    ax = plt.gca()
    fig = ax.figure
    transform = ax.transAxes + mtransforms.ScaledTranslation(
        -pad_left / fig.dpi,
        pad_top / fig.dpi,
        fig.dpi_scale_trans,
    )

    ax.text(
        0,
        1,
        name,
        transform=transform,
        fontsize=cns.settings.title_fontsize,
        fontname=cns.settings.panel_label_fontname,
        fontweight=cns.settings.panel_label_fontweight,
        ha="right",
        va="bottom",
    )


def get_hexcolors_from_apalette(
    alist, palette=palettable.colorbrewer.qualitative.Set1_9.hex_colors
):
    """
    Extract specific colors from a palette by index.

    This function retrieves a subset of colors from a color palette based on
    the provided indices.

    Parameters
    ----------
    alist : list of int
        List of indices specifying which colors to extract from the palette.
        Indices are 0-based.
    palette : str or list, default: Set1_9.hex_colors
        Either a palette name (str) that can be resolved by the palettes() function,
        or a list of hex color codes.

    Returns
    -------
    list
        List of hex color codes corresponding to the requested indices.

    See Also
    --------
    palettes : Get a complete color palette by name.

    Notes
    -----
    When palette is a string, it is first resolved to a list of colors using
    the palettes() function, which supports many predefined palettes including:
    - ColorBrewer palettes: 'Set1', 'Set2', 'Set3', 'Dark2', 'Paired', etc.
    - Custom palettes: 'Ecotyper1'-'Ecotyper6', 'BlueRed', 'ECharts', etc.

    When palette is a list, colors are extracted directly by index.

    Examples
    --------
    >>> import cnsplots as cns
    >>> # Extract first two colors from Set1
    >>> colors = cns.get_hexcolors_from_apalette([0, 1], "Set1")
    >>> colors
    ['#E41A1C', '#377EB8']

    >>> # Extract specific colors from custom palette
    >>> custom = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    >>> selected = cns.get_hexcolors_from_apalette([0, 2], custom)
    >>> selected
    ['#FF0000', '#0000FF']
    """
    if isinstance(palette, str):
        colors = palettes(palette)
        return list(operator.itemgetter(*alist)(colors))
    else:
        return list(operator.itemgetter(*alist)(palette))


def _is_qualitative_cmap(cmap_name):
    if isinstance(cmap_name, list) or isinstance(cmap_name, dict):
        return True
    else:
        cmap = plt.get_cmap(cmap_name)
        return cmap.N < 33


def _get_hex_colors_from_colorbar(cmap_name, n_colors):
    cmap = plt.cm.get_cmap(cmap_name)
    if _is_qualitative_cmap(cmap_name):
        colors = [mcolors.to_hex(cmap(i)) for i in range(0, n_colors)]
    else:
        colors = [mcolors.to_hex(cmap(i)) for i in range(0, cmap.N, cmap.N // n_colors)]
    return colors


def _remove_edge_from_legend_items(ax):
    handles, labels = ax.get_legend_handles_labels()
    for handle in handles:
        if hasattr(handle, "set_edgecolor"):
            handle.set_edgecolor("none")
    ax.legend(handles, labels)


def _has_non_ascii(text):
    return bool(re.search(r"[^\x00-\x7F]", text))


def apply_unicode_font(ax=None, font="DejaVu Sans"):
    """
    Set font to a Unicode-compatible font for text elements containing non-ASCII characters.

    Scans all text elements (title, axis labels, tick labels, legend, and annotations)
    on the given axes and switches their font to the specified fallback font if they
    contain non-ASCII characters (e.g., arrows like \u2192, Greek letters, etc.).

    Parameters
    ----------
    ax : matplotlib.axes.Axes, optional
        The axes to process. If None, uses the current axes.
    font : str, default: 'DejaVu Sans'
        The fallback font to use for text containing non-ASCII characters.
    """
    if ax is None:
        ax = plt.gca()
    text_objects = (
        [ax.title, ax.xaxis.label, ax.yaxis.label]
        + ax.get_xticklabels()
        + ax.get_yticklabels()
        + list(ax.texts)
    )
    legend = ax.get_legend()
    if legend is not None:
        text_objects.append(legend.get_title())
        text_objects.extend(legend.get_texts())
    for text_obj in text_objects:
        if _has_non_ascii(text_obj.get_text()):
            text_obj.set_fontfamily(font)


def _addcount_helper(data, attr, ax):
    xtick_labels = ax.get_xticklabels()
    tick_positions = ax.get_xticks()
    new_xtick_labels = []
    for label in xtick_labels:
        n = len(data[data[attr] == label.get_text()])
        new_xtick_labels.append(f"{label.get_text()}\n(n={n})")
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(new_xtick_labels)


def _p_value_helper(test, data, ax, plotting, pairs, contingency=None, format="star"):
    # format {star, full}
    class PValueFormatNew(PValueFormat):
        def __init__(self):
            super(PValueFormat, self).__init__()
            self._pvalue_format_string = "{:.3e}"
            self._simple_format_string = "{:.2f}"
            self._text_format = "star"
            self.fontsize = "small"
            self._default_pvalue_thresholds = True
            self._pvalue_thresholds = self._get_pvalue_thresholds(DEFAULT)
            self._correction_format = "{star} ({suffix})"
            self.show_test_name = True

        if format == "full":

            def format_data(self, result):
                text = f"{result.test_short_name} " if self.show_test_name else ""
                if result.pvalue > 0.05:
                    return "ns"
                return r"${}P = {}{}$".format(
                    "{}", self.pvalue_format_string, "{}"
                ).format(
                    text, num2tex.num2tex(result.pvalue), result.significance_suffix
                )

    x_is_numeric = pd.api.types.is_numeric_dtype(data[plotting["x"]])
    if x_is_numeric:
        plotting["orient"] = "h"
        primary_col = plotting["y"]
    else:
        primary_col = plotting["x"]

    primary_levels = list(pd.unique(data[primary_col].dropna()))
    order = plotting.get("order")
    if order is not None:
        primary_levels = [level for level in order if level in primary_levels]

    if pairs == "all":
        pairs = list(itertools.combinations(primary_levels, 2))
    elif pairs == "hue":
        hue_col = plotting.get("hue")
        if hue_col is None:
            raise ValueError(
                "`pairs='hue'` requires a hue column in the plotting data."
            )
        hue_levels = list(pd.unique(data[hue_col].dropna()))
        hue_order = plotting.get("hue_order")
        if hue_order is not None:
            hue_levels = [level for level in hue_order if level in hue_levels]
        hue_pairs = []
        for category in primary_levels:
            subset = data[data[primary_col] == category]
            present_hues = [
                level
                for level in hue_levels
                if level in pd.unique(subset[hue_col].dropna())
            ]
            hue_pairs.extend(
                ((category, first), (category, second))
                for first, second in itertools.combinations(present_hues, 2)
            )
        pairs = hue_pairs

    annotator = Annotator(ax, pairs, **plotting)
    annotator._pvalue_format = PValueFormatNew()
    annotator.configure(
        test=test if contingency is None else None,
        text_format=format,
        loc="inside",
        line_width=0.5,
        line_offset=0,
        line_offset_to_group=0,
        text_offset=0,
        color="black",
        show_test_name=False,
        pvalue_format_string="{:.1e}",
        use_fixed_offset=True,
        verbose=0,
    )

    pvalues = []
    if test == "fisher-exact":
        assert contingency is not None
        for pair in pairs:
            pvalues.append(stats.fisher_exact(contingency.loc[list(pair)].values)[1])
    if test == "chi-squared":
        assert contingency is not None
        for pair in pairs:
            pvalues.append(
                stats.chi2_contingency(contingency.loc[list(pair)].values)[1]
            )

    if contingency is None:
        annotator.apply_and_annotate()
    else:
        annotator.set_pvalues(pvalues=pvalues)
        annotator.annotate()

    if test == "Mann-Whitney":
        print("   ---> P-values were determined by two-sided Mann-Whitney U test.")
    if test == "t-test_welch":
        print("   ---> P-values were determined by two-sided Welch's t-test.")
    if test == "fisher-exact":
        print("   ---> P-values were determined by two-sided Fisher's exact test.")
    if test == "chi-squared":
        print("   ---> P-values were determined by two-sided Chi-squared test.")


def get_showcase_data(
    *,
    include_showcase_images: bool = False,
    caller_file: str | os.PathLike[str] | None = None,
):
    """
    Load synthetic showcase datasets and optionally resolve the image asset directory.

    Parameters
    ----------
    include_showcase_images : bool, default: False
        When True, append the showcase image assets directory to the returned tuple.
    caller_file : path-like or None, default: None
        File path used to seed the assets-directory search. When omitted, the
        caller frame's ``__file__`` is used when available.
    """
    import numpy as np
    import pandas as pd
    import scanpy as sc
    import seaborn as sns

    resolved_caller_file = caller_file
    if resolved_caller_file is None:
        import inspect

        frame = inspect.currentframe()
        try:
            caller_frame = None if frame is None else frame.f_back
            resolved_caller_file = (
                None if caller_frame is None else caller_frame.f_globals.get("__file__")
            )
        finally:
            del frame

    def _resolve_showcase_images() -> Path:
        search_roots = []
        if resolved_caller_file is not None:
            search_roots.append(Path(resolved_caller_file).resolve().parent)

        cwd = Path.cwd().resolve()
        search_roots.extend([cwd, *cwd.parents])

        seen = set()
        for root in search_roots:
            for candidate in (root / "assets", root / "examples" / "assets"):
                if candidate in seen:
                    continue
                seen.add(candidate)
                if candidate.exists():
                    return candidate

        msg = "Could not locate examples/assets"
        raise FileNotFoundError(msg)

    np.random.seed(42)
    survival_data = []
    for grp, scale in [("Treatment", 36), ("Control", 24)]:
        times = np.random.exponential(scale=scale, size=50)
        events = np.random.binomial(1, 0.7, 50)
        for t, e in zip(times, events):
            survival_data.append({"time": t, "event": e, "group": grp})
    survival_df = pd.DataFrame(survival_data)
    survival_df["age"] = np.random.normal(60, 10, len(survival_df)).astype(int)
    survival_df["stage"] = np.random.choice(["I", "II", "III"], len(survival_df))

    iris_df = sns.load_dataset("iris")
    tips_df = sns.load_dataset("tips")
    blobs = sc.datasets.blobs()
    blobs.obs["TP53"] = np.random.random(blobs.shape[0])
    blobs.obs["KRAS"] = np.random.random(blobs.shape[0])
    blobs.var["Ensemble"] = [f"ens{x}" for x in np.random.randint(0, 3, blobs.shape[1])]
    blobs.obs["Selected"] = np.where(blobs.obs["TP53"] > 0.95, "o", None)
    blobs.obs["Cluster"] = pd.Categorical(
        [f"C{x}" for x in np.random.randint(0, 4, blobs.shape[0])]
    )
    blobs.X = blobs.X - blobs.X.mean()

    # Volcano plot data
    n_genes = 500
    logfc = np.random.normal(0, 1.5, n_genes)
    pvals = 10 ** (-np.abs(logfc) * np.random.uniform(0.5, 3, n_genes))
    pvals = np.clip(pvals, 1e-50, 1)
    volcano_df = pd.DataFrame(
        {
            "log2FoldChange": logfc,
            "-log10(adjp)": -np.log10(pvals),
            "symbol": [f"Gene{i}" for i in range(n_genes)],
        }
    )

    # Venn plot data
    gene_sets = [
        set(f"Gene{i}" for i in np.random.choice(200, 80, replace=False)),
        set(f"Gene{i}" for i in np.random.choice(200, 90, replace=False)),
        set(f"Gene{i}" for i in np.random.choice(200, 70, replace=False)),
    ]

    # Slop data
    slope_df = np.concatenate(
        [
            [np.random.normal(loc=1, size=15), 15 * ["site1"], 15 * ["healthy"]],
            [np.random.normal(loc=3, size=15), 15 * ["site2"], 15 * ["healthy"]],
            [np.random.normal(loc=0, size=15), 15 * ["site3"], 15 * ["healthy"]],
            [np.random.normal(loc=1, size=15), 15 * ["site1"], 15 * ["disease"]],
            [np.random.normal(loc=1, size=15), 15 * ["site2"], 15 * ["disease"]],
            [np.random.normal(loc=3, size=15), 15 * ["site3"], 15 * ["disease"]],
        ],
        axis=1,
    )
    slope_df = pd.DataFrame(
        columns=pd.Index(["value", "site", "label"]), data=slope_df.T
    )
    slope_df["value"] = slope_df["value"].astype(float)

    # ROC data
    y_true = np.random.binomial(1, 0.4, 200)
    roc_df = pd.DataFrame(
        {
            "label": y_true,
            "Model A": y_true * 0.5
            + (1 - y_true) * 0.3
            + np.random.normal(0, 0.25, 200),
            "Model B": y_true * 0.6
            + (1 - y_true) * 0.2
            + np.random.normal(0, 0.2, 200),
        }
    )

    # Confusion matrix data
    confusion_df = pd.DataFrame(
        {
            "truth": ["Neg"] * 18 + ["Pos"] * 12,
            "pred": ["Neg"] * 15 + ["Pos"] * 3 + ["Neg"] * 2 + ["Pos"] * 10,
        }
    )

    # Line plot data
    line_df = pd.DataFrame(
        {
            "timepoint": list(range(6)) * 2,
            "signal": [
                0.15,
                0.22,
                0.38,
                0.55,
                0.64,
                0.72,
                0.12,
                0.18,
                0.29,
                0.36,
                0.43,
                0.50,
            ],
            "condition": ["Control"] * 6 + ["Treatment"] * 6,
        }
    )

    data = (
        iris_df,
        tips_df,
        survival_df,
        blobs.T,
        volcano_df,
        gene_sets,
        roc_df,
        slope_df,
        confusion_df,
        line_df,
    )
    if include_showcase_images:
        return (*data, _resolve_showcase_images())
    return data


def palettes(color):
    """
    Get a color palette by name.

    This function returns a predefined color palette as a list of colors in
    matplotlib-compatible format. Supports ColorBrewer palettes, custom scientific
    palettes, and specialized colormaps.

    Parameters
    ----------
    color : str or list
        Palette name or list of color values. If a list is provided, it is
        converted to a seaborn color palette.

        **Supported palette names:**

        **ColorBrewer Qualitative:**
        - 'Set1', 'Set2', 'Set3'
        - 'Pastel1', 'Pastel2'
        - 'Paired'
        - 'Dark2'
        - 'Accent'

        **Other Qualitative:**
        - 'Cell': Custom Cell-inspired journal palette
        - 'Nature': Nature Reviews Cancer-inspired palette
        - 'Science': Science-inspired journal palette
        - 'Tableau': Tableau 10 colors
        - 'Bold': Cartographic bold colors
        - 'BlueRed': Tableau blue-red diverging palette
        - 'ECharts': ECharts library default colors
        - 'Ecotyper1'-'Ecotyper6': Custom palettes for cell type visualization

        **Sequential/Diverging (for use with colormaps):**
        - 'BuRd_custom': Custom blue-white-red diverging
        - 'WhYlOrRd_custom': White-yellow-orange-red sequential
        - 'OrBu_custom': Orange-white-blue diverging
        - 'YlGnBu_custom': Yellow-green-blue sequential
        - 'parula': MATLAB parula colormap

    Returns
    -------
    list or matplotlib.colors.LinearSegmentedColormap
        For qualitative palettes: list of RGB tuples or color objects
        For sequential/diverging palettes: LinearSegmentedColormap object

    See Also
    --------
    get_hexcolors_from_apalette : Extract specific colors from a palette by index.
    figure : Initialize a figure with custom color cycle.

    Notes
    -----
    Ecotyper palettes are custom color schemes designed for biological data
    visualization, particularly for distinguishing cell types and molecular
    subtypes in tumor microenvironment studies.

    The function returns:
    - Qualitative palettes as lists of matplotlib color objects (RGB tuples)
    - Sequential/diverging palettes as LinearSegmentedColormap objects

    Examples
    --------
    >>> import cnsplots as cns
    >>> # Get Set1 palette
    >>> colors = cns.palettes("Set1")
    >>> len(colors)
    9

    >>> # Get Ecotyper1 palette
    >>> eco_colors = cns.palettes("Ecotyper1")

    >>> # Use parula colormap
    >>> parula_cmap = cns.palettes("parula")

    >>> # Pass a custom list
    >>> custom = ["#FF0000", "#00FF00", "#0000FF"]
    >>> palette = cns.palettes(custom)
    """
    if isinstance(color, list):
        return sns.color_palette(color)
    else:
        if color == "Set1":
            return palettable.colorbrewer.qualitative.Set1_9.mpl_colors
        elif color == "Set2":
            return palettable.colorbrewer.qualitative.Set2_8.mpl_colors
        elif color == "Set3":
            return palettable.colorbrewer.qualitative.Set3_12.mpl_colors
        elif color == "Pastel1":
            return palettable.colorbrewer.qualitative.Pastel1_9.mpl_colors
        elif color == "Pastel2":
            return palettable.colorbrewer.qualitative.Pastel2_8.mpl_colors
        elif color == "Paired":
            return palettable.colorbrewer.qualitative.Paired_12.mpl_colors
        elif color == "Dark2":
            return palettable.colorbrewer.qualitative.Dark2_8.mpl_colors
        elif color == "Accent":
            return palettable.colorbrewer.qualitative.Accent_8.mpl_colors
        elif color == "Tableau":
            return palettable.tableau.Tableau_10.mpl_colors
        elif color == "Bold":
            return palettable.cartocolors.qualitative.Bold_10.mpl_colors
        elif color == "BlueRed":
            return palettable.tableau.BlueRed_6.mpl_colors
        elif color == "Cell":
            colors = [
                "#C84C3A",
                "#2F7E8F",
                "#E1A22E",
                "#4E5A8A",
                "#5F9862",
                "#D07A6A",
                "#8B6FA8",
                "#7B8C9E",
                "#B85F7A",
                "#6B6B6B",
            ]
            return sns.color_palette(colors)
        elif color == "Nature":
            colors = [
                "#E64B35",
                "#4DBBD5",
                "#00A087",
                "#3C5488",
                "#F39B7F",
                "#8491B4",
                "#91D1C2",
                "#DC0000",
                "#7E6148",
                "#B09C85",
            ]
            return sns.color_palette(colors)
        elif color == "Science":
            colors = [
                "#3B4992",
                "#EE0000",
                "#008B45",
                "#631879",
                "#008280",
                "#BB0021",
                "#5F559B",
                "#A20056",
                "#808180",
                "#1B1919",
            ]
            return sns.color_palette(colors)
        elif color == "Lancet":
            colors = [
                "#00468B",
                "#ED0000",
                "#42B540",
                "#0099B4",
                "#925E9F",
                "#FDAF91",
                "#AD002A",
                "#ADB6B6",
                "#1B1919",
            ]
            return sns.color_palette(colors)
        elif color == "NEJM":
            colors = [
                "#BC3C29",
                "#0072B5",
                "#E18727",
                "#20854E",
                "#7876B1",
                "#6F99AD",
                "#FFDC91",
                "#EE4C97",
            ]
            return sns.color_palette(colors)
        elif color == "JAMA":
            colors = [
                "#374E55",
                "#DF8F44",
                "#00A1D5",
                "#B24745",
                "#79AF97",
                "#6A6599",
                "#80796B",
            ]
            return sns.color_palette(colors)
        elif color == "JCO":
            colors = [
                "#0073C2",
                "#EFC000",
                "#868686",
                "#CD534C",
                "#7AA6DC",
                "#003C67",
                "#8F7700",
                "#3B3B3B",
                "#A73030",
                "#4A6990",
            ]
            return sns.color_palette(colors)
        elif color == "OkabeIto":
            colors = [
                "#E69F00",
                "#56B4E9",
                "#009E73",
                "#F0E442",
                "#0072B2",
                "#D55E00",
                "#CC79A7",
                "#000000",
            ]
            return sns.color_palette(colors)
        elif color == "TolBright":
            colors = [
                "#4477AA",
                "#EE6677",
                "#228833",
                "#CCBB44",
                "#66CCEE",
                "#AA3377",
                "#BBBBBB",
            ]
            return sns.color_palette(colors)
        elif color == "TolMuted":
            colors = [
                "#332288",
                "#88CCEE",
                "#44AA99",
                "#117733",
                "#999933",
                "#DDCC77",
                "#CC6677",
                "#882255",
                "#AA4499",
                "#DDDDDD",
            ]
            return sns.color_palette(colors)
        elif color == "ECharts":
            colors = [
                "#5470c6",
                "#91cc75",
                "#fac858",
                "#ee6666",
                "#9a60b4",
                "#73c0de",
                "#3ba272",
                "#fc8452",
                "#27727b",
                "#ea7ccc",
                "#d7504b",
                "#e87c25",
                "#b5c334",
                "#fe8463",
                "#26c0c0",
                "#f4e001",
            ]
            return sns.color_palette(colors)
        elif color == "Ecotyper1":
            colors = [
                "#D6372E",
                "#5189BB",
                "#70B460",
                "#985EA8",
                "#F08F35",
                "#FADD4B",
                "#A3A3A3",
                "#B7D3E5",
                "#E6D8C2",
            ]
            return sns.color_palette(colors)
        elif color == "Ecotyper2":
            colors = ["#EB7D5B", "#FED23F", "#B5D33D", "#6CA2EA", "#442288"]
            return sns.color_palette(colors)
        elif color == "Ecotyper3":
            colors = [
                "#D13570",
                "#569AB4",
                "#70AC58",
                "#74509D",
                "#ED7E30",
                "#F5C945",
                "#9C5732",
                "#E787E5",
            ]
            return sns.color_palette(colors)
        elif color == "Ecotyper4":
            colors = [
                "#386cb0",
                "#fdb462",
                "#7fc97f",
                "#ef3b2c",
                "#662506",
                "#a6cee3",
                "#fb9a99",
                "#984ea3",
                "#ffff33",
            ]
            return sns.color_palette(colors)
        elif color == "Ecotyper5":
            colors = [
                "#E41A71",
                "#379DB8",
                "#5BAF4A",
                "#7B4EA3",
                "#FF7600",
                "#FFC800",
                "#A65328",
                "#F781EC",
                "#999999",
                "#A6DCE3",
                "#BBDF8A",
                "#FB9A99",
                "#FDB96F",
                "#BEB2D6",
                "#1B9E5E",
                "#D95802",
                "#707EB3",
                "#E729D3",
                "#E69F02",
                "#8DD3B9",
                "#FFFAB3",
                "#BABFDA",
                "#FB7F72",
                "#80C5D3",
                "#FDAE62",
                "#BEDE69",
                "#FCCDF7",
            ]
            return sns.color_palette(colors)
        elif color == "Ecotyper6":
            colors = [
                "#FDC086",
                "#386CB0",
                "#F0027F",
                "#FFFF99",
                "#BF5B17",
                "#7FC97F",
                "lightblue",
                "#BEAED4",
                "#66C2A5",
                "#FC8D62",
                "#8DA0CB",
                "#E78AC3",
                "#A6D854",
                "#FFD92F",
                "#E5C494",
                "#B3B3B3",
                "#FBB4AE",
                "#B3CDE3",
                "#CCEBC5",
                "#DECBE4",
                "#FED9A6",
                "#FFFFCC",
                "#E5D8BD",
                "#FDDAEC",
            ]
            return sns.color_palette(colors)
        elif color == "BuRd_custom":
            cm_data = [
                [0.0588, 0.3412, 0.6157],
                [0.1220, 0.3940, 0.6610],
                [0.1843, 0.4471, 0.7059],
                [0.2650, 0.5000, 0.7450],
                [0.3451, 0.5529, 0.7843],
                [0.5412, 0.6902, 0.8667],
                [0.7294, 0.8275, 0.9333],
                [0.8863, 0.9255, 0.9765],
                [0.9500, 0.9700, 0.9900],
                [1.0000, 1.0000, 1.0000],
                [0.9900, 0.9500, 0.9400],
                [0.9882, 0.9020, 0.8863],
                [0.9650, 0.8200, 0.7900],
                [0.9412, 0.7412, 0.6980],
                [0.9080, 0.6330, 0.5840],
                [0.8745, 0.5255, 0.4706],
                [0.7961, 0.3137, 0.2784],
                [0.7137, 0.1216, 0.1686],
                [0.6196, 0.0588, 0.1373],
            ]
            return mpl.colors.LinearSegmentedColormap.from_list("BuRd_custom", cm_data)
        elif color == "WhYlOrRd_custom":
            cm_data = [
                [1.0000, 1.0000, 1.0000],
                [1.0000, 1.0000, 0.8500],
                [1.0000, 0.9800, 0.7000],
                [1.0000, 0.9400, 0.5000],
                [1.0000, 0.8500, 0.3000],
                [0.9961, 0.7200, 0.2000],
                [0.9961, 0.5500, 0.1000],
                [0.9922, 0.4000, 0.0500],
                [0.9882, 0.2500, 0.0200],
                [0.9500, 0.1500, 0.0100],
                [0.9000, 0.0800, 0.0100],
                [0.8000, 0.0200, 0.0100],
                [0.6500, 0.0000, 0.0100],
                [0.5019, 0.0000, 0.0000],
                [0.4000, 0.0000, 0.0000],
            ]
            return mpl.colors.LinearSegmentedColormap.from_list(
                "WhYlOrRd_custom", cm_data
            )
        elif color == "OrBu_custom":
            cm_data = [
                [0.8500, 0.3800, 0.0500],
                [1.0000, 0.4980, 0.0549],
                [1.0000, 0.5841, 0.2169],
                [1.0000, 0.6702, 0.3790],
                [1.0000, 0.7563, 0.5410],
                [1.0000, 0.8424, 0.7031],
                [1.0000, 0.9284, 0.8651],
                [1.0000, 1.0000, 1.0000],
                [0.8608, 0.9235, 0.9745],
                [0.7216, 0.8471, 0.9490],
                [0.5824, 0.7706, 0.9235],
                [0.4431, 0.6941, 0.8980],
                [0.3039, 0.6176, 0.8725],
                [0.1647, 0.5412, 0.8471],
                [0.1216, 0.4667, 0.7059],
            ]
            return mpl.colors.LinearSegmentedColormap.from_list("OrBu_custom", cm_data)
        elif color == "YlGnBu_custom":
            cm_data = [
                [1.00, 1.00, 0.80],
                [0.98, 0.99, 0.75],
                [0.95, 0.98, 0.70],
                [0.91, 0.97, 0.66],
                [0.87, 0.96, 0.62],
                [0.83, 0.95, 0.59],
                [0.77, 0.93, 0.58],
                [0.71, 0.91, 0.59],
                [0.64, 0.89, 0.62],
                [0.56, 0.87, 0.66],
                [0.48, 0.84, 0.69],
                [0.40, 0.81, 0.72],
                [0.32, 0.78, 0.74],
                [0.26, 0.74, 0.76],
                [0.21, 0.70, 0.77],
                [0.18, 0.65, 0.78],
                [0.15, 0.60, 0.78],
                [0.13, 0.55, 0.78],
                [0.12, 0.50, 0.76],
                [0.13, 0.44, 0.73],
                [0.13, 0.39, 0.70],
                [0.14, 0.33, 0.66],
                [0.14, 0.28, 0.62],
                [0.14, 0.22, 0.58],
                [0.05, 0.18, 0.52],
                [0.03, 0.15, 0.45],
            ]
            return mpl.colors.LinearSegmentedColormap.from_list(
                "YlGnBu_custom", cm_data
            )
        elif color == "parula":
            cm_data = [
                [0.2081, 0.1663, 0.5292],
                [0.2116, 0.1898, 0.5777],
                [0.2123, 0.2138, 0.6270],
                [0.2081, 0.2386, 0.6771],
                [0.1959, 0.2645, 0.7279],
                [0.1707, 0.2919, 0.7792],
                [0.1253, 0.3242, 0.8303],
                [0.0591, 0.3598, 0.8683],
                [0.0117, 0.3875, 0.8820],
                [0.0060, 0.4086, 0.8828],
                [0.0165, 0.4266, 0.8786],
                [0.0329, 0.4430, 0.8720],
                [0.0498, 0.4586, 0.8641],
                [0.0629, 0.4737, 0.8554],
                [0.0723, 0.4887, 0.8467],
                [0.0779, 0.5040, 0.8384],
                [0.0793, 0.5200, 0.8312],
                [0.0749, 0.5375, 0.8263],
                [0.0641, 0.5570, 0.8240],
                [0.0488, 0.5772, 0.8228],
                [0.0343, 0.5966, 0.8199],
                [0.0265, 0.6137, 0.8135],
                [0.0239, 0.6287, 0.8038],
                [0.0231, 0.6418, 0.7913],
                [0.0228, 0.6535, 0.7768],
                [0.0267, 0.6642, 0.7607],
                [0.0384, 0.6743, 0.7436],
                [0.0590, 0.6838, 0.7254],
                [0.0843, 0.6928, 0.7062],
                [0.1133, 0.7015, 0.6859],
                [0.1453, 0.7098, 0.6646],
                [0.1801, 0.7177, 0.6424],
                [0.2178, 0.7250, 0.6193],
                [0.2586, 0.7317, 0.5954],
                [0.3022, 0.7376, 0.5712],
                [0.3482, 0.7424, 0.5473],
                [0.3953, 0.7459, 0.5244],
                [0.4420, 0.7481, 0.5033],
                [0.4871, 0.7491, 0.4840],
                [0.5300, 0.7491, 0.4661],
                [0.5709, 0.7485, 0.4494],
                [0.6099, 0.7473, 0.4337],
                [0.6473, 0.7456, 0.4188],
                [0.6834, 0.7435, 0.4044],
                [0.7184, 0.7411, 0.3905],
                [0.7525, 0.7384, 0.3768],
                [0.7858, 0.7356, 0.3633],
                [0.8185, 0.7327, 0.3498],
                [0.8507, 0.7299, 0.3360],
                [0.8824, 0.7274, 0.3217],
                [0.9139, 0.7258, 0.3063],
                [0.9450, 0.7261, 0.2886],
                [0.9739, 0.7314, 0.2666],
                [0.9938, 0.7455, 0.2403],
                [0.9990, 0.7653, 0.2164],
                [0.9955, 0.7861, 0.1967],
                [0.9880, 0.8066, 0.1794],
                [0.9789, 0.8271, 0.1633],
                [0.9697, 0.8481, 0.1475],
                [0.9626, 0.8705, 0.1309],
                [0.9589, 0.8949, 0.1132],
                [0.9598, 0.9218, 0.0948],
                [0.9661, 0.9514, 0.0755],
                [0.9763, 0.9831, 0.0538],
            ]
            return mpl.colors.LinearSegmentedColormap.from_list("parula", cm_data)
        else:
            return RuntimeError("Wrong Choice!")
