from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from enum import Enum
from typing import Any, Literal, cast, overload

import itertools
import math
import os
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import num2tex
import numpy as np
import pandas as pd
import scipy.stats as stats
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import Colormap
from matplotlib.figure import Figure
from matplotlib.typing import ColorType
from seaborn._base import categorical_order, infer_orient
from statannotations.Annotator import Annotator
from statannotations.PValueFormat import PValueFormat
from statsmodels.stats.multitest import multipletests

import cnsplots._palettes as _palettes
from cnsplots._comparison_types import HueComparisons
from cnsplots._settings import settings
from cnsplots._setup import setup_matplotlib
from cnsplots._sizing import _SizeUnit, _dimension_to_points
from cnsplots._svg import _save_svg

logger = logging.getLogger(__name__)

_QualitativePaletteName = Literal[
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
    "Cell",
    "Nature",
    "Science",
    "Lancet",
    "NEJM",
    "JAMA",
    "JCO",
    "OkabeIto",
    "TolBright",
    "TolMuted",
    "ECharts",
    "Ecotyper1",
    "Ecotyper2",
    "Ecotyper3",
    "Ecotyper4",
    "Ecotyper5",
    "Ecotyper6",
]
_ContinuousPaletteName = Literal[
    "BuRd_custom",
    "WhYlOrRd_custom",
    "OrBu_custom",
    "YlGnBu_custom",
    "parula",
]
_RGBColor = tuple[float, float, float]
_P_ADJUST_METHODS = ("bonferroni", "holm", "fdr_bh", "fdr_by")
_PAIRED_TESTS = ("t-test_paired", "Wilcoxon")
_COMPARISON_COLUMNS = [
    "group1",
    "group2",
    "test",
    "alternative",
    "paired",
    "n1",
    "n2",
    "pvalue_raw",
    "pvalue_adjusted",
    "p_adjust",
    "pvalue_annotation",
    "significant",
    "annotation",
]

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


def _legend_fontsize() -> int | float:
    """Return the configured legend font size, falling back to title size."""
    legend_fontsize = settings.legend_fontsize
    if legend_fontsize is None:
        return settings.title_fontsize
    return legend_fontsize


def _resize_legend_markers(
    legend: Any,
    scatter_size: float,
    *,
    marker_size: float | None = None,
) -> None:
    """Resize scatter and line-marker handles in a legend when supported."""
    if legend is None:
        return
    if marker_size is None:
        marker_size = 2 * math.sqrt(scatter_size / math.pi)
    for handle in legend.legend_handles:
        set_sizes = getattr(handle, "set_sizes", None)
        if callable(set_sizes):
            set_sizes([scatter_size])
            continue
        set_markersize = getattr(handle, "set_markersize", None)
        if callable(set_markersize):
            set_markersize(marker_size)


def _annotation_text_color(color: Any) -> str:
    """Return a readable annotation color for a background fill."""
    if not settings.annotation_auto_contrast:
        return "white"

    r, g, b, _ = mcolors.to_rgba(color)
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "white" if luminance < 0.5 else "black"


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


class _HostRelativeAxesLocator:
    """Locate an axes within a live host while exposing its SubplotSpec."""

    def __init__(
        self,
        host_ax: Axes,
        layout: tuple[float, float, float, float],
        *,
        use_original_position: bool = True,
    ) -> None:
        self._host_ax = host_ax
        self._layout = layout
        self._use_original_position = use_original_position

    def get_subplotspec(self):
        return self._host_ax.get_subplotspec()

    def __call__(self, _ax: Any, _renderer: Any) -> mtransforms.Bbox:
        host_pos = self._host_ax.get_position(
            original=self._use_original_position
        ).frozen()
        x0, y0, width, height = self._layout
        return mtransforms.Bbox.from_bounds(
            host_pos.x0 + host_pos.width * x0,
            host_pos.y0 + host_pos.height * y0,
            host_pos.width * width,
            host_pos.height * height,
        )


def _anchor_axes_to_host(
    host_ax: Axes,
    axes: Sequence[Axes],
    *,
    use_original_position: bool = True,
) -> None:
    """Keep helper axes at fixed positions relative to a live host axes."""
    host_pos = host_ax.get_position(original=use_original_position).frozen()
    if host_pos.width <= 0 or host_pos.height <= 0:
        return

    child_axes = [
        child_ax
        for child_ax in axes
        if child_ax is not host_ax and child_ax.figure is host_ax.figure
    ]
    if not child_axes:
        return

    child_positions = [
        child_ax.get_position(original=True).frozen() for child_ax in child_axes
    ]
    source_pos = mtransforms.Bbox.union(child_positions)
    if source_pos.width <= 0 or source_pos.height <= 0:
        source_pos = host_pos

    host_spec = host_ax.get_subplotspec()
    layouts = []
    for child_ax, child_pos in zip(child_axes, child_positions):
        layout = (
            float((child_pos.x0 - source_pos.x0) / source_pos.width),
            float((child_pos.y0 - source_pos.y0) / source_pos.height),
            float(child_pos.width / source_pos.width),
            float(child_pos.height / source_pos.height),
        )
        locator = _HostRelativeAxesLocator(
            host_ax,
            layout,
            use_original_position=use_original_position,
        )
        existing_locator = child_ax.get_axes_locator()

        if host_spec is None:
            setattr(child_ax, "_subplotspec", None)
            child_ax.set_in_layout(False)
        else:
            child_ax.set_subplotspec(host_spec)
            child_ax.set_in_layout(True)

        if (
            existing_locator is not None
            and type(existing_locator).__name__ == "_ColorbarAxesLocator"
        ):
            setattr(existing_locator, "_orig_locator", locator)
            installed_locator = existing_locator
        else:
            installed_locator = locator
        child_ax.set_axes_locator(installed_locator)
        layouts.append((child_ax, installed_locator))

    def _sync_axes() -> None:
        for child_ax, locator in layouts:
            if child_ax.figure is not host_ax.figure:
                continue
            locate = cast(Callable[[Any, Any], mtransforms.Bbox], locator)
            child_ax.set_position(locate(child_ax, None), which="active")
            child_ax.set_in_layout(host_spec is not None)

    _chain_axes_sync_hook(host_ax, _sync_axes)
    _sync_axes()


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


class _SavefigDefault(Enum):
    SETTINGS = "settings"


def figure(
    width: int | float | None = None,
    height: int | float | None = None,
    color_cycle: str | Sequence[ColorType] | None = None,
    color_map: str | None = None,
    *,
    unit: _SizeUnit = "pt",
) -> Figure:
    """
    Initialize a new figure with custom size and styling.

    This function creates a new matplotlib figure with specified dimensions and
    applies the cnsplots style configuration including color palette and colormap.

    Parameters
    ----------
    width : int or float, optional
        Full figure width in ``unit``. If None, use cns.settings.figure_width
        in points (default: 150), regardless of ``unit``.
    height : int or float, optional
        Full figure height in ``unit``. If None, use cns.settings.figure_height
        in points (default: 150), regardless of ``unit``.
    color_cycle : str, default: None
        Name of the qualitative color palette to use for the color cycle.
        If None, uses cns.settings.palette_qual.
        Options include: 'Ecotyper1', 'Set1', 'Set2', 'Dark2', 'Tableau', etc.
    color_map : str, default: None
        Name of the sequential colormap to use for continuous data.
        If None, uses cns.settings.palette_seq.
        Options include: 'gnuplot', 'parula', 'bwr', 'hot', etc.
    unit : {'pt', 'in', 'mm'}, default: 'pt'
        Unit for explicitly supplied width and height: points (1/72 inch),
        inches, or millimeters. The default preserves legacy numerical sizes.

    Returns
    -------
    matplotlib.figure.Figure
        The newly created figure, which is also the current pyplot figure.

    Raises
    ------
    TypeError
        If a dimension is not numeric or is a boolean.
    ValueError
        If a dimension is nonpositive or nonfinite, or the unit is unsupported.

    See Also
    --------
    multipanel : Create multi-panel figures with automatic layout.
    savefig : Save the current figure to a file.
    setup_matplotlib : Configure matplotlib styling.

    Notes
    -----
    Default dimensions are logical 72-DPI units, numerically equal to points:
    inches = points / 72. They describe the full canvas, including space around
    the axes. In contrast, ``multipanel.panel`` sizes describe the axes area.

    Display pixels = inches * ``cns.settings.figure_dpi`` (default: 144).
    Thus ``figure(100, 150)`` has size ``(100 / 72, 150 / 72)`` inches and a
    200 by 300 pixel canvas at the default display DPI. Export uses
    ``cns.settings.savefig_dpi`` (default: 288), yielding 400 by 600 pixels
    when saved with ``bbox_inches=None``. The default tight export instead
    crops to artists plus ``pad_inches`` (in inches), so its dimensions can
    differ from the full canvas. DPI does not change the physical figure size.

    This function previously returned None. Callers that ignore the return value
    continue to work; callers or type checks relying on None must be updated.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.figure(width=300, height=200)
    >>> cns.boxplot(data=df, x="group", y="value")
    >>> cns.savefig("plot.pdf")

    >>> # With custom color scheme
    >>> cns.figure(width=150, height=150, color_cycle="Set2", color_map="parula")
    >>> cns.heatmapplot(adata)

    >>> # Equivalent physical sizes
    >>> fig = cns.figure(50.8, 25.4, unit="mm")
    >>> fig = cns.figure(2, 1, unit="in")
    >>> fig = cns.figure(144, 72, unit="pt")
    """
    width = _dimension_to_points("width", width, unit, default=settings.figure_width)
    height = _dimension_to_points(
        "height", height, unit, default=settings.figure_height
    )
    if color_cycle is None:
        color_cycle = settings.palette_qual
    if color_map is None:
        color_map = settings.palette_seq
    setup_matplotlib(color_cycle, color_map)
    return plt.figure(figsize=(width / 72, height / 72), dpi=settings.figure_dpi)


def savefig(
    filepath: str | os.PathLike[str],
    *,
    fig: Figure | None = None,
    dpi: float | None = None,
    transparent: bool | None = None,
    bbox_inches: Literal["tight"] | mtransforms.Bbox | None | _SavefigDefault = (
        _SavefigDefault.SETTINGS
    ),
    pad_inches: float | None = None,
) -> None:
    """
    Save a figure to a file, creating directories if needed.

    This function saves a matplotlib figure to the specified file path,
    automatically creating any missing parent directories.

    Parameters
    ----------
    filepath : str
        Path where the figure should be saved. Can include home directory shorthand
        (~). The file format is determined by the extension (e.g., .pdf, .png, .svg).
    fig : matplotlib.figure.Figure, optional
        Figure to export. If None, use the current pyplot figure. Exporting an
        explicit figure does not change the current figure selection.
    dpi : float, optional
        Positive, finite export resolution. If None, use cns.settings.savefig_dpi.
        Vector geometry retains its physical size; DPI controls rasterized content.
    transparent : bool, optional
        Whether figure and axes backgrounds are transparent. If None, use
        cns.settings.savefig_transparent. Format support follows matplotlib.
    bbox_inches : {'tight', None} or matplotlib.transforms.Bbox, optional
        Export bounds in inches. If omitted, use cns.settings.savefig_bbox
        ('tight' crops to the artists; other configured modes use the full figure).
        Explicit None saves the full figure, even when the configured default is
        'tight'. A Bbox specifies a fixed region in inches.
    pad_inches : float, optional
        Non-negative, finite padding around tight bounds, in inches. If None, use
        cns.settings.savefig_pad_inches. Ignored for full-figure or fixed bounds.

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
    supported by matplotlib.figure.Figure.savefig). Explicit options take
    precedence over current cnsplots settings. Other options retain matplotlib's
    backend defaults. Settings, rcParams, figure DPI, and canvas are preserved,
    including when export fails. This does not make matplotlib thread-safe.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.figure()
    >>> cns.boxplot(data=df, x="group", y="value")
    >>> cns.savefig("~/results/figures/boxplot.pdf")

    >>> # Save in multiple formats
    >>> cns.savefig("plot.png")
    >>> cns.savefig("plot.svg")

    >>> # Export a retained figure with per-call options
    >>> fig = cns.figure(width=300, height=200)
    >>> cns.boxplot(data=df, x="group", y="value")
    >>> cns.savefig("plot.png", fig=fig, dpi=300, transparent=False, bbox_inches=None)
    """
    if dpi is None:
        dpi = settings.savefig_dpi
    if isinstance(dpi, bool) or not isinstance(dpi, (int, float)):
        raise TypeError("dpi must be a number")
    if not math.isfinite(dpi) or dpi <= 0:
        raise ValueError("dpi must be positive and finite")
    if transparent is None:
        transparent = settings.savefig_transparent
    if not isinstance(transparent, bool):
        raise TypeError("transparent must be a boolean")
    if pad_inches is None:
        pad_inches = settings.savefig_pad_inches
    if isinstance(pad_inches, bool) or not isinstance(pad_inches, (int, float)):
        raise TypeError("pad_inches must be a number")
    if not math.isfinite(pad_inches) or pad_inches < 0:
        raise ValueError("pad_inches must be non-negative and finite")
    if bbox_inches is _SavefigDefault.SETTINGS:
        bbox_inches = "tight" if settings.savefig_bbox == "tight" else None
    if not (
        bbox_inches is None
        or isinstance(bbox_inches, mtransforms.Bbox)
        or (isinstance(bbox_inches, str) and bbox_inches == "tight")
    ):
        raise ValueError("bbox_inches must be 'tight', None, or a Bbox")

    filepath = Path(filepath).expanduser()
    if filepath.parent != Path("."):
        filepath.parent.mkdir(parents=True, exist_ok=True)
    if fig is None:
        fig = plt.gcf()
    for ax in fig.get_axes():
        apply_unicode_font(ax)
    target_dpi = float(dpi)
    original_dpi = fig.dpi
    original_canvas = fig.canvas
    root, ext = os.path.splitext(filepath)
    try:
        if target_dpi != original_dpi:
            fig.set_dpi(target_dpi)
        fig.canvas.draw()
        export_bbox = _get_export_bbox_inches(
            fig, bbox_inches=bbox_inches, pad_inches=pad_inches
        )
        savefig_kwargs: dict[str, Any] = {
            "dpi": target_dpi,
            "transparent": transparent,
            "bbox_inches": export_bbox,
            "pad_inches": 0,
        }
        if ext.lower() == ".svg":
            _save_svg(str(filepath), root, fig=fig, **savefig_kwargs)
        else:
            if ext.lower() == ".pdf":
                fonttools_logger = logging.getLogger("fontTools")
                previous_level = fonttools_logger.level
                try:
                    fonttools_logger.setLevel(
                        max(fonttools_logger.getEffectiveLevel(), logging.ERROR)
                    )
                    fig.savefig(filepath, **savefig_kwargs)
                finally:
                    fonttools_logger.setLevel(previous_level)
            else:
                fig.savefig(filepath, **savefig_kwargs)
    finally:
        fig.set_canvas(original_canvas)
        if fig.dpi != original_dpi:
            fig.set_dpi(original_dpi)
    # Refresh the original canvas after success without masking export failures.
    fig.canvas.draw()


def _get_export_bbox_inches(
    fig: Figure,
    *,
    bbox_inches: Literal["tight"] | mtransforms.Bbox | None,
    pad_inches: float,
) -> mtransforms.Bbox:
    """Return a shared export bbox so raster and vector outputs align."""
    if isinstance(bbox_inches, mtransforms.Bbox):
        return bbox_inches.frozen()
    if bbox_inches is None:
        # Passing None to Figure.savefig would reapply rcParams['savefig.bbox'].
        return fig.bbox_inches.frozen()

    original_canvas = fig.canvas
    agg_canvas = FigureCanvasAgg(fig)
    try:
        agg_canvas.draw()
        bbox_inches = fig.get_tightbbox(agg_canvas.get_renderer())
        if bbox_inches is None:
            return fig.bbox_inches.frozen()
        if pad_inches:
            bbox_inches = bbox_inches.padded(pad_inches)
        return mtransforms.Bbox.from_extents(*bbox_inches.extents)
    finally:
        fig.set_canvas(original_canvas)


def take_legend_out(
    title: str | None = None,
    *,
    ax: Axes | None = None,
) -> None:
    """
    Move the legend outside the plot area to the upper-left of the right margin.

    This function repositions the current axes legend to appear outside and to
    the right of the plot area, preventing overlap with the plotted data.

    Parameters
    ----------
    title : str, optional
        Title for the legend. If None, uses the existing legend title from
        the current axes.
    ax : matplotlib.axes.Axes, optional
        Axes whose legend should be moved. Defaults to the current Axes.

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
    if ax is None:
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
    ax.legend(
        handles=handles,
        labels=labels,
        bbox_to_anchor=settings.legend_out_bbox_to_anchor,
        loc=settings.legend_out_loc,
        title=title,
        markerscale=settings.legend_out_markerscale,
    )


def add_panel_label(
    name: str = "A",
    pad_left: int | float | None = None,
    pad_top: int | float | None = None,
) -> None:
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

    The label uses the configured font family (bold) at 8pt size
    (``title_fontsize``) for consistency with publication standards. Set
    ``panel_label_fontname`` to explicitly override the family.

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
        pad_left = settings.panel_pad_left
    if pad_top is None:
        pad_top = settings.panel_pad_top

    ax = plt.gca()
    fig = ax.figure
    transform = ax.transAxes + mtransforms.ScaledTranslation(
        -pad_left / fig.dpi,
        pad_top / fig.dpi,
        fig.dpi_scale_trans,
    )

    font_kwargs: dict[str, Any] = {}
    if settings.panel_label_fontname is not None:
        font_kwargs["fontname"] = settings.panel_label_fontname

    ax.text(
        0,
        1,
        name,
        transform=transform,
        fontsize=settings.title_fontsize,
        fontweight=settings.panel_label_fontweight,
        ha="right",
        va="bottom",
        **font_kwargs,
    )


def get_palette_colors(
    indices: Sequence[int],
    palette: str | Sequence[ColorType] | None = None,
) -> list[str]:
    """
    Extract specific colors from a palette by index.

    This function retrieves a subset of colors from a color palette based on
    the provided indices.

    Parameters
    ----------
    indices : sequence of int
        Indices specifying which colors to extract, in the requested order.
        Indices are 0-based; negative indices and repeated indices are supported.
    palette : str or sequence of colors, optional
        Either a palette name (str) that can be resolved by the palettes() function,
        or a sequence of Matplotlib colors. Defaults to Set1, resolved on each call.

    Returns
    -------
    list
        List of hex color codes corresponding to the requested indices.

    See Also
    --------
    palettes : Get a complete color palette by name.
    get_hexcolors_from_apalette : Compatible wrapper using the old parameter name.

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
    >>> colors = cns.get_palette_colors([0, 1], "Set1")
    >>> colors
    ['#e41a1c', '#377eb8']

    >>> # Extract specific colors from custom palette
    >>> custom = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    >>> selected = cns.get_palette_colors([0, 2], custom)
    >>> selected
    ['#ff0000', '#0000ff']
    """
    if palette is None:
        palette = "Set1"
    colors = (
        cast(Sequence[ColorType], palettes(palette))
        if isinstance(palette, str)
        else palette
    )
    return [mcolors.to_hex(colors[index]) for index in indices]


def get_hexcolors_from_apalette(
    alist: Sequence[int],
    palette: str | Sequence[ColorType] | None = None,
) -> list[str]:
    """Extract palette colors using the original, compatible API.

    Parameters
    ----------
    alist : sequence of int
        Zero-based indices to select, including negative or repeated indices.
    palette : str or sequence of colors, optional
        Palette name or explicit Matplotlib colors. Defaults to Set1, resolved
        on each call.

    Returns
    -------
    list of str
        Selected hexadecimal colors in the requested order.

    See Also
    --------
    get_palette_colors : Preferred name for palette color selection.

    Notes
    -----
    This wrapper preserves positional calls and the ``alist`` and ``palette``
    keyword arguments. It returns the same colors as ``get_palette_colors``.
    """
    return get_palette_colors(alist, palette)


def _is_qualitative_cmap(cmap_name):
    if isinstance(cmap_name, list) or isinstance(cmap_name, dict):
        return True
    else:
        cmap = plt.get_cmap(cmap_name)
        return cmap.N < 33


def _get_hex_colors_from_colorbar(cmap_name, n_colors):
    cmap = mpl.colormaps[cmap_name]
    return [mcolors.to_hex(cmap(value)) for value in np.linspace(0, 1, n_colors)]


def _remove_edge_from_legend_items(ax):
    handles, labels = ax.get_legend_handles_labels()
    for handle in handles:
        if hasattr(handle, "set_edgecolor"):
            handle.set_edgecolor("none")
    ax.legend(handles, labels)


def _has_non_ascii(text):
    return bool(re.search(r"[^\x00-\x7F]", text))


def apply_unicode_font(ax: Axes | None = None, font: str = "DejaVu Sans") -> None:
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


def _add_count_helper(data, attr, ax, axis="x"):
    counts = data[attr].astype(str).value_counts()
    if axis == "x":
        tick_labels = ax.get_xticklabels()
        tick_positions = ax.get_xticks()
        set_ticks = ax.set_xticks
        set_ticklabels = ax.set_xticklabels
    elif axis == "y":
        tick_labels = ax.get_yticklabels()
        tick_positions = ax.get_yticks()
        set_ticks = ax.set_yticks
        set_ticklabels = ax.set_yticklabels
    else:
        raise ValueError("axis must be 'x' or 'y'")

    new_tick_labels = []
    for label in tick_labels:
        label_text = label.get_text()
        if label_text not in counts:
            label_text = re.sub(r"\n\(n=\d+\)$", "", label_text)
        n = int(counts.get(label_text, 0))
        new_tick_labels.append(f"{label_text}\n(n={n})")
    set_ticks(tick_positions)
    set_ticklabels(new_tick_labels)


def _validate_statistical_options(test, p_adjust, *, valid_tests):
    if test not in valid_tests:
        choices = ", ".join(repr(value) for value in valid_tests)
        raise ValueError(f"test must be one of: {choices}")
    if p_adjust is not None and p_adjust not in _P_ADJUST_METHODS:
        choices = ", ".join(repr(value) for value in _P_ADJUST_METHODS)
        raise ValueError(f"p_adjust must be one of: {choices}, or None")


def _resolve_categorical_orientation(data, x, y, orient=None):
    """Use Seaborn's orientation rules, normalized for statannotations."""
    return "h" if infer_orient(data[x], data[y], orient) == "y" else "v"


def _validate_paired_subject(data, test, subject):
    if test in _PAIRED_TESTS:
        if not isinstance(subject, str) or subject not in data.columns:
            raise ValueError(
                "Paired tests require subject to name a column in data; "
                f"got {subject!r}."
            )
    elif subject is not None:
        raise ValueError("subject is only supported with paired tests.")


def _align_paired_comparisons(annotator, data, plotting, subject):
    """Replace each contrast's test samples without changing its plot geometry."""
    category, value = (
        (plotting["y"], plotting["x"])
        if plotting["orient"] == "h"
        else (plotting["x"], plotting["y"])
    )
    hue = plotting.get("hue")
    columns = [category, value, subject] + ([] if hue is None else [hue])
    complete = data.dropna(subset=columns)
    categories = complete[category].map(annotator._plotter.plotter.formatter)
    for first, second in annotator._struct_pairs:
        samples = []
        for struct in (first, second):
            group = struct["group"]
            selected = categories == group[0]
            if len(group) > 1:
                selected &= complete[hue] == group[1]
            sample = complete.loc[selected].set_index(subject, drop=False)[value]
            if sample.index.has_duplicates:
                raise ValueError(
                    f"Duplicate subject observations in compared group {group!r}."
                )
            samples.append(sample)
        aligned = pd.concat(samples, axis=1, join="inner")
        if len(aligned) < 2:
            raise ValueError(
                "Paired tests require at least two complete subject pairs."
            )
        values = aligned.to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("Paired tests require finite values in matched pairs.")
        if (values[:, 0] == values[:, 1]).all():
            raise ValueError("Paired tests require at least one nonzero difference.")
        # Sort by values for reproducible reductions regardless of row/ID order.
        values = values[np.lexsort((values[:, 1], values[:, 0]))]
        first["group_data"], second["group_data"] = values.T


def _prepare_categorical_plot_data(plotting):
    """Share complete displayed rows across rendering, summaries, and counts."""
    data = plotting["data"]
    x, y, hue = plotting["x"], plotting["y"], plotting.get("hue")
    plotting["orient"] = _resolve_categorical_orientation(
        data, x, y, plotting.get("orient")
    )
    category = y if plotting["orient"] == "h" else x
    # Resolve levels before cleaning so empty categories keep their tick positions.
    plotting["order"] = categorical_order(data[category], plotting.get("order"))
    columns = [x, y] if hue is None else [x, y, hue]
    cleaned = data.dropna(subset=columns)
    cleaned = cleaned.loc[cleaned[category].isin(plotting["order"])]
    if hue is not None:
        plotting["hue_order"] = categorical_order(data[hue], plotting.get("hue_order"))
        cleaned = cleaned.loc[cleaned[hue].isin(plotting["hue_order"])]
    if cleaned.empty:
        raise ValueError(
            "No complete observations remain in the selected category and hue levels."
        )
    plotting["data"] = cleaned
    return cleaned


class _PValueFormatter(PValueFormat):
    """Format p-value annotations with explicit, per-instance configuration."""

    def __init__(self, resolved_format: str, fontsize: str | int | float) -> None:
        super().__init__()
        self._resolved_format = resolved_format
        self.fontsize = fontsize
        self.p_capitalized = True

    def format_data(self, result):
        if self._resolved_format == "full":
            text = f"{result.test_short_name} " if self.show_test_name else ""
            return r"${}P = {}{}$".format("{}", self.pvalue_format_string, "{}").format(
                text, num2tex.num2tex(result.pvalue), result.significance_suffix
            )

        if self._resolved_format == "threshold":
            pvalue_threshold_labels = (
                (1e-4, "P < 0.0001"),
                (1e-3, "P < 0.001"),
                (1e-2, "P < 0.01"),
                (0.05, "P < 0.05"),
            )
            for threshold, label in pvalue_threshold_labels:
                if result.pvalue <= threshold:
                    adjust = getattr(result, "adjust", None)
                    return adjust(label) if callable(adjust) else label
            adjust = getattr(result, "adjust", None)
            return adjust("P > 0.05") if callable(adjust) else "P > 0.05"

        return super().format_data(result)


def get_comparison_results(ax: Axes | None = None) -> pd.DataFrame:
    """Return the results used by the latest categorical annotations on an axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes, optional
        Axes returned by boxplot, violinplot, barplot, lollipopplot, or stackplot.
        Defaults to the current axes. The plot must have been called with pairs.

    Returns
    -------
    pandas.DataFrame
        A detached table with one row per comparison, in annotation drawing
        order (shorter brackets first). ``group1`` and ``group2`` follow the
        categorical axis order, not necessarily the supplied pair order. They
        are category labels, or ``(category, hue)`` tuples for hue comparisons.
        ``test``, ``alternative``, and ``paired`` identify the test;
        ``t-test_paired`` and ``Wilcoxon`` use subject-aligned observations
        (``paired=True``). Other tests use independent observations.
        ``alternative`` is ``'two-sided'`` for continuous tests and 2-by-2 Fisher
        tests, and None for chi-squared and larger Fisher independence tests.
        ``n1`` and ``n2`` count contributing observations; for paired tests both
        equal the number of complete matched pairs, including zero differences
        discarded from Wilcoxon ranks. ``pvalue_raw`` and
        ``pvalue_adjusted`` contain raw and corrected p-values; without correction
        they are equal and ``p_adjust`` is None. ``pvalue_annotation``,
        ``significant``, and ``annotation`` describe the exact rendered result.
        No effect size is estimated. Returns an empty table with these columns
        if there are no stored comparisons or their annotations were removed.

    Notes
    -----
    Results come from the same computation used for rendering; this accessor
    does not rerun tests. Each call returns a copy. On reused axes only the latest
    comparison call is returned; a plot without pairs does not replace it.
    Clearing the axes also clears the available results.

    Continuous plots exclude rows missing x, y, or hue and levels excluded by
    order/hue_order, just as rendering does. Stackplot tests use original counts
    of complete category/stack rows, before normalization or n_factor scaling;
    these can differ from its raw category tick counts when stack values are
    missing. Correction covers all resolved pairs in one plot call, including
    all categories for pairs='hue', and does not extend across plot calls.

    Paired tests additionally exclude missing subject identifiers and incomplete
    pairs separately for each contrast. Duplicate subjects within either compared
    group among complete displayed rows raise ValueError. At least two matched
    pairs with finite values and at least one nonzero difference are required.
    Plot summaries and tick counts can include observations excluded by pairing.

    Existing statannotations display semantics are preserved: Bonferroni uses
    adjusted p-values in labels; Holm and FDR methods display raw p-values with
    a nonsignificance suffix when correction removes significance. Use
    pvalue_adjusted for the numerical corrected values for every method.

    Examples
    --------
    >>> ax = cns.boxplot(df, x="group", y="value", pairs="all", p_adjust="holm")
    >>> comparisons = cns.get_comparison_results(ax)
    >>> comparisons.to_csv("comparisons.csv", index=False)
    """
    if ax is None:
        ax = plt.gca()
    stored = getattr(ax, "_cnsplots_comparison_results", None)
    if stored is None:
        return pd.DataFrame(columns=pd.Index(_COMPARISON_COLUMNS))
    results, artists = stored
    if not artists or any(artist not in ax.texts for artist in artists):
        return pd.DataFrame(columns=pd.Index(_COMPARISON_COLUMNS))
    return results.copy(deep=True)


def _collect_comparison_results(annotator, test, correction, p_adjust, contingency):
    """Correct the computed results in place and snapshot them before rendering."""
    annotations = annotator.annotations
    results = [annotation.data for annotation in annotations]
    raw = np.asarray([result.pvalue for result in results])
    if test in _PAIRED_TESTS and not np.isfinite(raw).all():
        raise ValueError("Paired test returned a nonfinite p-value.")
    adjusted = raw.copy()
    if correction is not None:
        adjusted = multipletests(raw, method=p_adjust)[1]
        if correction.type == 0:
            for result, pvalue in zip(results, correction(raw)):
                result.pvalue = pvalue
        correction.apply(results)

    rows = []
    for annotation, pvalue_raw, pvalue_adjusted in zip(annotations, raw, adjusted):
        first, second = annotation.structs
        group1, group2 = first["group"], second["group"]
        if contingency is None:
            n1, n2 = len(first["group_data"]), len(second["group_data"])
        else:
            n1 = int(contingency.loc[group1[0]].sum())
            n2 = int(contingency.loc[group2[0]].sum())
        alternative = (
            None
            if test == "chi-squared"
            or (contingency is not None and contingency.shape[1] != 2)
            else "two-sided"
        )
        rows.append(
            {
                "group1": group1[0] if len(group1) == 1 else group1,
                "group2": group2[0] if len(group2) == 1 else group2,
                "test": test,
                "alternative": alternative,
                "paired": test in _PAIRED_TESTS,
                "n1": n1,
                "n2": n2,
                "pvalue_raw": pvalue_raw,
                "pvalue_adjusted": pvalue_adjusted,
                "p_adjust": p_adjust,
                "pvalue_annotation": annotation.data.pvalue,
                "significant": annotation.data.is_significant,
                "annotation": annotation.text,
            }
        )
    return pd.DataFrame(rows, columns=pd.Index(_COMPARISON_COLUMNS))


def _p_value_helper(
    test,
    data,
    ax,
    plotting,
    pairs: HueComparisons,
    contingency=None,
    format=None,
    label_clearance=None,
    p_adjust=None,
    subject=None,
):
    resolved_format = settings.pvalue_format if format is None else format
    if resolved_format not in {"star", "threshold", "full"}:
        raise ValueError("format must be one of: 'star', 'threshold', 'full'")

    pvalue_fontsize = settings.pvalue_fontsize

    plotting["orient"] = _resolve_categorical_orientation(
        data, plotting["x"], plotting["y"], plotting.get("orient")
    )
    primary_col = plotting["y"] if plotting["orient"] == "h" else plotting["x"]
    present_levels = data[primary_col].dropna().unique()
    primary_levels = [
        level
        for level in categorical_order(data[primary_col], plotting.get("order"))
        if level in present_levels
    ]

    if pairs == "all":
        pairs = list(itertools.combinations(primary_levels, 2))
    elif pairs == "hue":
        hue_col = plotting.get("hue")
        if hue_col is None:
            raise ValueError(
                "`pairs='hue'` requires a hue column in the plotting data."
            )
        hue_levels = categorical_order(data[hue_col], plotting.get("hue_order"))
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

    line_offset_to_group = None
    if label_clearance is not None and settings.pvalue_loc == "inside":
        # statannotations expands the value axis as it stacks brackets. Account
        # for that scaling so the requested on-screen label clearance remains.
        annotation_step = 0.07 + label_clearance
        expansion = 1.04 * (1 + len(pairs) * annotation_step)
        denominator = max(1 - 1.04 * label_clearance, 0.1)
        line_offset_to_group = label_clearance * expansion / denominator

    contingency_tables = None
    if contingency is not None:
        contingency = contingency.fillna(0)
        contingency_tables = []
        for pair in pairs:
            if len(pair) != 2 or pair[0] == pair[1]:
                raise ValueError(
                    "Contingency-table comparisons require exactly two distinct "
                    "levels per pair."
                )
            missing_levels = [level for level in pair if level not in contingency.index]
            if missing_levels:
                raise ValueError(
                    "Contingency-table pair contains levels absent from the data: "
                    f"{missing_levels}."
                )
            table = contingency.loc[list(pair)].to_numpy(dtype=float)
            if table.shape[0] < 2 or table.shape[1] < 2:
                raise ValueError(
                    "Contingency-table comparisons require at least two rows and "
                    "two columns."
                )
            if not np.isfinite(table).all() or (table < 0).any():
                raise ValueError(
                    "Contingency-table cells must contain finite, nonnegative counts."
                )
            if (table.sum(axis=0) == 0).any() or (table.sum(axis=1) == 0).any():
                raise ValueError(
                    "Contingency-table comparisons require nonzero row and column "
                    "margins."
                )
            contingency_tables.append(table)

    annotator = Annotator(ax, pairs, **plotting)
    annotator._pvalue_format = _PValueFormatter(resolved_format, pvalue_fontsize)
    annotator.configure(
        test=test if contingency is None else None,
        comparisons_correction=p_adjust,
        text_format="full" if resolved_format == "full" else "star",
        loc=settings.pvalue_loc,
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
        assert contingency_tables is not None
        for table in contingency_tables:
            pvalues.append(stats.fisher_exact(table)[1])
    if test == "chi-squared":
        assert contingency_tables is not None
        for table in contingency_tables:
            pvalues.append(stats.chi2_contingency(table)[1])

    # Preserve raw values before statannotations' type-0 corrections overwrite
    # them. Apply the same correction to these results once, then render them.
    correction = annotator.comparisons_correction
    annotator.comparisons_correction = None
    if contingency is None:
        if test in _PAIRED_TESTS:
            _align_paired_comparisons(annotator, data, plotting, subject)
        annotator.apply_test()
    else:
        annotator.set_pvalues(pvalues=pvalues)
    results = _collect_comparison_results(
        annotator, test, correction, p_adjust, contingency
    )
    annotator.comparisons_correction = correction

    text_start = len(ax.texts)
    if line_offset_to_group is None:
        annotator.annotate()
    else:
        annotator.annotate(line_offset_to_group=line_offset_to_group)
    ax._cnsplots_comparison_results = (results, tuple(ax.texts)[text_start:])

    if test == "Mann-Whitney":
        logger.info("P-values were determined by two-sided Mann-Whitney U test.")
    if test == "t-test_welch":
        logger.info("P-values were determined by two-sided Welch's t-test.")
    if test == "t-test_paired":
        logger.info(
            "P-values were determined by a two-sided subject-aligned paired t-test."
        )
    if test == "Wilcoxon":
        logger.info(
            "P-values were determined by a two-sided subject-aligned Wilcoxon "
            "signed-rank test."
        )
    if test == "fisher-exact":
        logger.info("P-values were determined by two-sided Fisher's exact test.")
    if test == "chi-squared":
        logger.info("P-values were determined by two-sided Chi-squared test.")


def register_palette(name: str, colors: Sequence[ColorType]) -> None:
    """Register a custom qualitative palette for the current Python process.

    Parameters
    ----------
    name : str
        Nonblank, case-sensitive palette name. Existing cnsplots and Matplotlib
        palette names cannot be replaced.
    colors : sequence of Matplotlib colors
        Nonempty sequence of valid colors. Colors are copied into immutable RGB
        tuples so later changes to the input cannot alter the palette.

    Raises
    ------
    TypeError
        If ``name`` is not a string or ``colors`` is not a color sequence.
    ValueError
        If the name is blank or already in use, or colors are empty or invalid.

    See Also
    --------
    available_palettes : List built-in and registered palette names.
    palettes : Resolve a palette by name.

    Notes
    -----
    Registered palettes are available to :func:`palettes`, :func:`figure`, and
    :func:`get_palette_colors` until the Python process exits. Each
    lookup returns a fresh palette. Registration does not persist to disk.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.register_palette("MyPalette", ["#336699", "#CC6633"])
    >>> cns.palettes("MyPalette")
    [(0.2, 0.4, 0.6), (0.8, 0.4, 0.2)]
    """
    if not isinstance(name, str):
        raise TypeError("name must be a string.")
    if not name.strip():
        raise ValueError("name must not be blank.")
    if name in _palettes._PALETTE_REGISTRY or name in mpl.colormaps:
        raise ValueError(f"Palette name {name!r} is already in use.")
    if isinstance(colors, (str, bytes)) or not isinstance(colors, Sequence):
        raise TypeError("colors must be a sequence of Matplotlib colors.")
    if not colors:
        raise ValueError("colors must not be empty.")
    try:
        copied_colors = tuple(mcolors.to_rgb(color) for color in colors)
    except (TypeError, ValueError) as exc:
        raise ValueError("colors must contain valid Matplotlib colors.") from exc
    if not all(math.isfinite(channel) for color in copied_colors for channel in color):
        raise ValueError("colors must contain finite RGB values.")
    _palettes._PALETTE_REGISTRY[name] = _palettes._PaletteSpec(
        "qualitative", lambda: sns.color_palette(copied_colors)
    )


@overload
def palettes(color: _QualitativePaletteName) -> list[_RGBColor]: ...


@overload
def palettes(color: _ContinuousPaletteName) -> Colormap: ...


@overload
def palettes(color: Sequence[ColorType]) -> list[_RGBColor]: ...


@overload
def palettes(color: str) -> list[_RGBColor] | Colormap: ...


def palettes(color: str | Sequence[ColorType]) -> list[_RGBColor] | Colormap:
    """
    Get a color palette by name.

    This function returns a predefined color palette as a list of colors in
    matplotlib-compatible format. Supports ColorBrewer palettes, custom scientific
    palettes, and specialized colormaps.

    Parameters
    ----------
    color : str or list
        Palette name or list of color values. If a list is provided, it is
        converted to a seaborn color palette. Registered custom palette names
        are also accepted; use :func:`available_palettes` to discover names.

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
    available_palettes : List built-in and registered palette names.
    register_palette : Register a custom qualitative palette.
    get_palette_colors : Extract specific colors from a palette by index.
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
    if not isinstance(color, str):
        return sns.color_palette(color)
    spec = _palettes._PALETTE_REGISTRY.get(color)
    if spec is None:
        raise RuntimeError("Wrong Choice!")
    return spec.factory()
