"""Multipanel figure creation for CNSPlots."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, cast

from matplotlib.backend_bases import DrawEvent, Event, RendererBase

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.text import Text
    from matplotlib.transforms import Bbox

import matplotlib.pyplot as plt
from matplotlib import transforms as mtransforms

import cnsplots._utils as utils
from cnsplots._settings import settings
from cnsplots._setup import setup_matplotlib

_LEFT_DECORATION_TOLERANCE_PX = 0.5
_RELAYOUT_MAX_PASSES = 3


def _validate_positive_finite_dimension(
    name: str,
    value: int | float,
) -> int | float:
    """Validate a dimension used to construct a matplotlib figure or axes."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return value


@dataclass
class _Panel:
    """Typed panel state with compatibility for legacy mapping-style access."""

    label: str
    width: int | float
    height: int | float
    pad_left: int | float
    pad_top: int | float
    margin_left: int | float
    margin_top: int | float
    margin_right: int | float
    margin_bottom: int | float
    left_decoration_width_px: float = 0.0
    label_width_px: float = 0.0
    label_height_px: float = 0.0
    top_decoration_height_px: float = 0.0
    _below: str | None = None
    _is_spacer: bool = False
    known_figure_axes_ids: set[int] | None = None

    def __getitem__(self, key: str) -> Any:
        """Support existing private consumers that index panel state as a dict."""
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Support existing private consumers that update panel measurements."""
        setattr(self, key, value)

    def __contains__(self, key: object) -> bool:
        """Report whether a legacy mapping key currently has a value."""
        return isinstance(key, str) and getattr(self, key, None) is not None

    def get(self, key: str, default: Any = None) -> Any:
        """Return a legacy mapping value without exposing storage details."""
        if key == "known_figure_axes_ids" and self.known_figure_axes_ids is None:
            return default
        return getattr(self, key, default)

    def pop(self, key: str, default: Any = None) -> Any:
        """Clear the optional axes snapshot used by legacy private consumers."""
        if key != "known_figure_axes_ids":
            return default
        value = self.known_figure_axes_ids
        self.known_figure_axes_ids = None
        if value is None:
            return default
        return value


@dataclass(frozen=True)
class _PanelGeometry:
    """Immutable inputs needed by the pure layout phase."""

    label: str
    width: float
    height: float
    margin_left: float
    margin_top: float
    left_reserve: float
    top_reserve: float
    total_width: float
    total_height: float
    below: str | None
    is_spacer: bool


@dataclass(frozen=True)
class _PanelLayout:
    """Calculated rows, heights, and axes positions for a panel collection."""

    rows: tuple[tuple[int, ...], ...]
    row_heights: tuple[float, ...]
    positions: tuple[tuple[float, float], ...]


def _layout_panels(
    panels: tuple[_PanelGeometry, ...],
    max_width: float,
    title_height: float,
) -> _PanelLayout:
    """Calculate panel layout without mutating panel or multipanel state."""
    label_to_index: dict[str, int] = {}
    for idx, panel in enumerate(panels):
        if panel.label in label_to_index:
            raise ValueError(f"Panel label {panel.label!r} already exists")
        label_to_index[panel.label] = idx

    children: list[list[int]] = [[] for _ in panels]
    for idx, panel in enumerate(panels):
        if panel.below is None:
            continue
        parent_idx = label_to_index.get(panel.below)
        if parent_idx is None:
            raise ValueError(
                f"below must reference an existing panel label: {panel.below!r}"
            )
        children[parent_idx].append(idx)

    states = [0] * len(panels)

    def validate_acyclic(panel_idx: int) -> None:
        if states[panel_idx] == 1:
            raise ValueError("Panel below relationships must not contain cycles")
        if states[panel_idx] == 2:
            return
        states[panel_idx] = 1
        for child_idx in children[panel_idx]:
            validate_acyclic(child_idx)
        states[panel_idx] = 2

    for idx in range(len(panels)):
        validate_acyclic(idx)

    subtree_sizes: list[tuple[float, float] | None] = [None] * len(panels)

    def get_subtree_size(panel_idx: int) -> tuple[float, float]:
        cached_size = subtree_sizes[panel_idx]
        if cached_size is not None:
            return cached_size
        panel = panels[panel_idx]
        subtree_width = panel.total_width
        subtree_height = panel.total_height
        for child_idx in children[panel_idx]:
            child_width, child_height = get_subtree_size(child_idx)
            subtree_width = max(subtree_width, child_width)
            subtree_height += child_height
        subtree_sizes[panel_idx] = (subtree_width, subtree_height)
        return subtree_width, subtree_height

    rows: list[list[int]] = []
    row_heights: list[float] = []
    current_row: list[int] = []
    current_row_width = 0.0
    current_row_height = 0.0

    root_indices = [idx for idx, panel in enumerate(panels) if panel.below is None]
    for panel_idx in root_indices:
        subtree_width, subtree_height = get_subtree_size(panel_idx)
        if current_row and current_row_width + subtree_width > max_width:
            rows.append(current_row)
            row_heights.append(current_row_height)
            current_row = [panel_idx]
            current_row_width = subtree_width
            current_row_height = subtree_height
        else:
            current_row.append(panel_idx)
            current_row_width += subtree_width
            current_row_height = max(current_row_height, subtree_height)

    if current_row:
        rows.append(current_row)
        row_heights.append(current_row_height)

    positions = [(0.0, 0.0)] * len(panels)

    def place_subtree(panel_idx: int, column_x: float, outer_y: float) -> float:
        panel = panels[panel_idx]
        positions[panel_idx] = (
            column_x + panel.margin_left + panel.left_reserve,
            outer_y + panel.margin_top + panel.top_reserve,
        )
        next_y = outer_y + panel.total_height
        for child_idx in children[panel_idx]:
            next_y = place_subtree(child_idx, column_x, next_y)
        return next_y

    row_y = title_height
    for row_idx, row in enumerate(rows):
        column_x = 0.0
        for panel_idx in row:
            place_subtree(panel_idx, column_x, row_y)
            column_x += get_subtree_size(panel_idx)[0]
        row_y += row_heights[row_idx]

    return _PanelLayout(
        rows=tuple(tuple(row) for row in rows),
        row_heights=tuple(row_heights),
        positions=tuple(positions),
    )


def _validate_title_loc(loc: str) -> str:
    """Validate figure title alignment."""
    if loc not in {"left", "center", "right"}:
        raise ValueError("loc must be one of: 'left', 'center', or 'right'")
    return loc


def _validate_title_fontweight(value: str | int) -> str | int:
    """Validate figure title font weight values."""
    if value is None or isinstance(value, bool) or not isinstance(value, (str, int)):
        raise TypeError("title_fontweight must be a string or integer")
    return value


class multipanel:
    """
    Create multi-panel figures with flexible panel sizes and margins.

    Each panel can have independent dimensions and margins. Panels flow
    left-to-right and wrap to new rows when they exceed max_width.

    Each panel consists of:

    - Padding (pad_left, pad_top): space for panel labels plus extra clearance
      around rendered axis decorations
    - Axes area (width, height): the plotting area
    - Margins (left, top, right, bottom): space around the entire panel

    Parameters
    ----------
    max_width : int, optional
        Maximum figure width in pixels (default: 540). Panels wrap to new
        rows when this width would be exceeded.
    title : str or None, optional
        Figure-level title shown above the panel grid (default: None).
    loc : {'left', 'center', 'right'}, optional
        Horizontal alignment for the figure title (default: 'center').
    title_fontweight : str or int, optional
        Font weight for the figure title (default: 'bold').

    Attributes
    ----------
    fig : matplotlib.figure.Figure
        The matplotlib figure object.
    axes : list
        List of matplotlib axes objects in order of creation.

    Examples
    --------
    >>> import cnsplots as cns
    >>> mp = cns.multipanel(max_width=540)
    >>> # Panel with label space and padding for ylabel
    >>> mp.panel(
    ...     "A",
    ...     width=100,
    ...     height=200,
    ...     pad_left=40,
    ...     pad_top=12,
    ...     margin_left=0,
    ...     margin_top=0,
    ...     margin_right=10,
    ...     margin_bottom=10,
    ... )
    >>> cns.boxplot(...)
    >>> cns.savefig("figure.pdf")

    Notes
    -----
    Panel layout structure::

        +------------------------------------------------+
        |                     margin_top                 |
        |   +-- label -------------------------------+   |
        |   |                 pad_top                |   |
        | m |   + ----------------------------------+| m |
        | a |   | +------------ title -------------+|| a |
        | r | p | |                                ||| r |
        | g | a | y                                ||| g |
        | i | d | l        axes content area       ||| i |
        | n | _ | a        (width x height)        ||| n |
        | _ | l | b                                ||| _ |
        | l | e | e                                ||| r |
        | e | f | l                                ||| i |
        | f | t | |                                ||| g |
        | t |   | +------------ xlabel ------------+|| t |
        |   |   + ----------------------------------+|   |
        |   +----------------------------------------+   |
        |                  margin_bottom                 |
        +------------------------------------------------+

    ``pad_left`` defines the extra horizontal gap between the panel label
    ("A", "B", etc.) and the leftmost visible left-side axis decoration. The
    multipanel layout measures the rendered y-axis decoration width on draw and
    reserves that width plus ``pad_left``.
    """

    def __init__(
        self,
        max_width: int | float | None = None,
        title: str | None = None,
        loc: str | None = None,
        title_fontweight: str | int = "bold",
    ) -> None:
        if max_width is None:
            max_width = settings.multipanel_max_width
        if loc is None:
            loc = settings.multipanel_title_loc
        self._max_width = _validate_positive_finite_dimension(
            "max_width",
            max_width,
        )
        self._title = title
        self._title_loc = _validate_title_loc(loc)
        self._title_fontweight = _validate_title_fontweight(title_fontweight)
        self._panels: list[_Panel] = []
        self.fig = None
        self.axes = []
        self._created_axes = {}
        self._label_texts = {}
        self._title_text: Text | None = None
        self._labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self._panel_index = 0

        # Track rows for flow layout
        # Each row is a list of panel indices
        self._rows = []
        self._row_heights = []  # Max total height in each row
        self._panel_positions: list[tuple[float, float]] = []
        self._draw_event_cid: int | None = None
        self._is_relayout_in_draw = False

    def _get_title_height_px(self) -> float:
        """Get the reserved height for the figure title band."""
        if self._title is None:
            return 0
        return max(
            settings.multipanel_title_height_min,
            settings.title_fontsize + settings.multipanel_title_height_pad,
        )

    def _get_left_decoration_width_px(
        self,
        panel: _Panel | dict[str, Any],
    ) -> float:
        """Get the cached rendered width of left-side axis decorations."""
        return float(panel.get("left_decoration_width_px", 0.0))

    def _get_label_width_px(self, panel: _Panel | dict[str, Any]) -> float:
        """Get the cached rendered width of the panel label."""
        return float(panel.get("label_width_px", 0.0))

    def _get_label_height_px(self, panel: _Panel | dict[str, Any]) -> float:
        """Get the cached rendered height of the panel label."""
        return float(panel.get("label_height_px", 0.0))

    def _get_top_decoration_height_px(
        self,
        panel: _Panel | dict[str, Any],
    ) -> float:
        """Get the cached rendered height of top-side axis decorations."""
        return float(panel.get("top_decoration_height_px", 0.0))

    def _get_layout_scale(self) -> float:
        """Get the display-to-layout pixel scale used by multipanel geometry."""
        dpi = self.fig.dpi if self.fig is not None else settings.figure_dpi
        return dpi / 72

    def _display_px_to_layout_px(self, value: float) -> float:
        """Convert rendered pixels into multipanel layout pixels."""
        return value / self._get_layout_scale()

    def _get_label_gap_px(self, panel: _Panel | dict[str, Any]) -> float:
        """Get the rendered-pixel gap between the label and left decorations."""
        return self._get_left_decoration_width_px(panel) + panel.get("pad_left", 0)

    def _get_left_reserve_px(self, panel: _Panel | dict[str, Any]) -> float:
        """Get total left reserve in layout pixels for panel geometry."""
        return self._display_px_to_layout_px(
            self._get_label_width_px(panel) + self._get_label_gap_px(panel)
        )

    def _get_top_label_offset_px(self, panel: _Panel | dict[str, Any]) -> float:
        """Get the rendered-pixel offset from axes top to label bottom."""
        return self._get_top_decoration_height_px(panel) + float(
            panel.get("pad_top", 0)
        )

    def _get_top_reserve_px(self, panel: _Panel | dict[str, Any]) -> float:
        """Get total top reserve in layout pixels for panel geometry."""
        return self._display_px_to_layout_px(
            self._get_label_height_px(panel) + self._get_top_label_offset_px(panel)
        )

    def _get_content_horizontal_bounds_px(self) -> tuple[float, float]:
        """Get the visible left/right bounds of the multipanel content."""
        left_bound = float(self._max_width)
        right_bound = 0.0
        found_panel = False

        for idx, panel in enumerate(self._panels):
            if panel.get("_is_spacer"):
                continue

            x, _ = self._get_panel_position(idx)
            left_bound = min(
                left_bound,
                x - self._get_left_reserve_px(panel),
            )
            right_bound = max(right_bound, x + panel["width"])
            found_panel = True

        if not found_panel:
            return 0.0, float(self._max_width)
        return left_bound, right_bound

    def _get_panel_total_size(
        self,
        panel: _Panel | dict[str, Any],
    ) -> tuple[float, float]:
        """Get the total width and height of a panel including margins."""
        total_width = (
            panel["margin_left"]
            + self._get_left_reserve_px(panel)
            + panel["width"]
            + panel["margin_right"]
        )
        total_height = (
            panel["margin_top"]
            + self._get_top_reserve_px(panel)
            + panel["height"]
            + panel["margin_bottom"]
        )
        return total_width, total_height

    def _get_label_transform(
        self,
        ax: Axes,
        label_left_offset: float,
        label_top_offset: float,
    ):
        """Build the padded axes-relative transform used for panel labels."""
        fig = ax.figure
        return ax.transAxes + mtransforms.ScaledTranslation(
            -label_left_offset / fig.dpi,
            label_top_offset / fig.dpi,
            fig.dpi_scale_trans,
        )

    def _get_live_label_text(self, label: str, ax: Axes) -> Text | None:
        """Return the current label artist when it still belongs to this axes."""
        label_text = self._label_texts.get(label)
        if label_text is None:
            return None
        if label_text.figure is not self.fig or label_text.axes is not ax:
            self._label_texts.pop(label, None)
            return None
        return label_text

    def _connect_draw_handler(self) -> None:
        """Connect a draw handler that can refine left reserves after rendering."""
        if self.fig is None or self._draw_event_cid is not None:
            return
        self._draw_event_cid = self.fig.canvas.mpl_connect("draw_event", self._on_draw)

    def _measure_left_decoration_width_px(
        self, ax: Axes, renderer: RendererBase
    ) -> float:
        """Measure the rendered width of left-side y-axis decorations."""
        tight_bbox = ax.yaxis.get_tightbbox(renderer)
        if tight_bbox is None:
            return 0.0
        axes_bbox = ax.get_window_extent(renderer=renderer)
        return max(0.0, float(axes_bbox.x0 - tight_bbox.x0))

    def _measure_label_width_px(
        self, label_text: Text, renderer: RendererBase
    ) -> float:
        """Measure the rendered width of a panel label."""
        return float(label_text.get_window_extent(renderer=renderer).width)

    def _measure_label_height_px(
        self, label_text: Text, renderer: RendererBase
    ) -> float:
        """Measure the rendered height of a panel label."""
        return float(label_text.get_window_extent(renderer=renderer).height)

    def _get_artist_bbox(self, artist: object, renderer: RendererBase) -> Bbox | None:
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

    def _iter_top_decoration_artists(self, ax: Axes, label_text: Text):
        """Yield artists that can contribute to top-side panel content."""
        yield ax.title
        yield ax.xaxis.label
        yield ax.xaxis.get_offset_text()
        yield from ax.get_xticklabels()

        legend = ax.get_legend()
        if legend is not None:
            yield legend

        for text in ax.texts:
            if text is not label_text:
                yield text

        for artist in (*ax.lines, *ax.collections, *ax.patches, *ax.artists):
            if not artist.get_clip_on():
                yield artist

    def _measure_top_decoration_height_px(
        self,
        ax: Axes,
        label_text: Text,
        renderer: RendererBase,
    ) -> float:
        """Measure the rendered height of top-side axis decorations."""
        axes_bbox = ax.get_window_extent(renderer=renderer)
        top_edge = float(axes_bbox.y1)
        topmost = top_edge

        for artist in self._iter_top_decoration_artists(ax, label_text):
            if not artist.get_visible():
                continue
            bbox = self._get_artist_bbox(artist, renderer)
            if bbox is None:
                continue
            if bbox.width <= 0 and bbox.height <= 0:
                continue
            if bbox.y1 > top_edge:
                topmost = max(topmost, float(bbox.y1))

        return max(0.0, topmost - top_edge)

    def _update_left_layout_metrics(self, renderer: RendererBase) -> bool:
        """Update cached left-layout measurements and report if layout changed."""
        changed = False
        for panel in self._panels:
            if panel.get("_is_spacer"):
                continue
            ax = self._created_axes.get(panel["label"])
            if ax is None:
                continue
            measured_left = self._measure_left_decoration_width_px(ax, renderer)
            current_left = self._get_left_decoration_width_px(panel)
            if abs(measured_left - current_left) > _LEFT_DECORATION_TOLERANCE_PX:
                panel["left_decoration_width_px"] = measured_left
                changed = True

            label_text = self._get_live_label_text(panel["label"], ax)
            if label_text is None:
                changed = True
                continue
            measured_label = self._measure_label_width_px(label_text, renderer)
            current_label = self._get_label_width_px(panel)
            if abs(measured_label - current_label) > _LEFT_DECORATION_TOLERANCE_PX:
                panel["label_width_px"] = measured_label
                changed = True

            measured_label_height = self._measure_label_height_px(label_text, renderer)
            current_label_height = self._get_label_height_px(panel)
            if (
                abs(measured_label_height - current_label_height)
                > _LEFT_DECORATION_TOLERANCE_PX
            ):
                panel["label_height_px"] = measured_label_height
                changed = True

            measured_top = self._measure_top_decoration_height_px(
                ax,
                label_text,
                renderer,
            )
            current_top = self._get_top_decoration_height_px(panel)
            if abs(measured_top - current_top) > _LEFT_DECORATION_TOLERANCE_PX:
                panel["top_decoration_height_px"] = measured_top
                changed = True
        return changed

    def _refresh_known_figure_axes_ids(self) -> None:
        """Update each panel's figure-axes snapshot for future helper capture."""
        if self.fig is None:
            return
        figure_axes_ids = {id(ax) for ax in self.fig.axes}
        for panel in self._panels:
            if panel.get("_is_spacer"):
                continue
            ax = self._created_axes.get(panel["label"])
            if ax is None or ax.figure is not self.fig:
                continue
            panel["known_figure_axes_ids"] = set(figure_axes_ids)

    def _iter_linked_helper_axes(
        self,
        ax: Axes,
        panel: _Panel | dict[str, Any],
    ):
        """Yield new helper axes that are directly linked to a host axes."""
        known_axes_ids = set(panel.get("known_figure_axes_ids", {id(ax)}))
        seen_ids = set()

        for artist in (*ax.collections, *ax.images):
            colorbar = getattr(artist, "colorbar", None)
            if colorbar is None:
                continue
            helper_ax = getattr(colorbar, "ax", None)
            if helper_ax is None or helper_ax is ax:
                continue
            if getattr(helper_ax, "figure", None) is not ax.figure:
                continue
            if id(helper_ax) in known_axes_ids or id(helper_ax) in seen_ids:
                continue

            colorbar_info = getattr(helper_ax, "_colorbar_info", None)
            if not isinstance(colorbar_info, dict):
                continue
            parents = colorbar_info.get("parents")
            if parents is None or ax not in parents:
                continue

            seen_ids.add(id(helper_ax))
            yield helper_ax

    def _capture_linked_helper_axes(self) -> bool:
        """Attach new directly linked helper axes to existing multipanel hosts."""
        if self.fig is None:
            return False

        captured = False
        for panel in self._panels:
            if panel.get("_is_spacer"):
                continue
            ax = self._created_axes.get(panel["label"])
            if ax is None or ax.figure is not self.fig:
                continue

            linked_axes = list(self._iter_linked_helper_axes(ax, panel))
            if not linked_axes:
                continue
            if utils._capture_detached_axes_layout(ax, detached_axes=linked_axes):
                captured = True

        if captured:
            self._refresh_known_figure_axes_ids()
        return captured

    def _get_canvas_renderer(self, canvas: object) -> RendererBase | None:
        """Return the canvas renderer when the backend exposes it."""
        get_renderer = getattr(canvas, "get_renderer", None)
        if not callable(get_renderer):
            return None
        return cast(Optional[RendererBase], get_renderer())

    def _on_draw(self, event: Event) -> None:
        """Relayout once after draw when left-side axis decorations change width."""
        if self.fig is None or self._is_relayout_in_draw:
            return
        if not isinstance(event, DrawEvent):
            return
        canvas = event.canvas
        if canvas is not self.fig.canvas:
            return
        renderer = event.renderer
        captured_linked_axes = self._capture_linked_helper_axes()
        if not (captured_linked_axes or self._update_left_layout_metrics(renderer)):
            return

        self._is_relayout_in_draw = True
        try:
            for _ in range(_RELAYOUT_MAX_PASSES):
                self._create_or_update_figure()
                canvas.draw()
                renderer = self._get_canvas_renderer(canvas)
                if renderer is None:
                    break
                captured_linked_axes = self._capture_linked_helper_axes()
                if not (
                    captured_linked_axes or self._update_left_layout_metrics(renderer)
                ):
                    break
        finally:
            self._is_relayout_in_draw = False

    def _get_panel_geometry(
        self,
        panel: _Panel | dict[str, Any],
    ) -> _PanelGeometry:
        """Create immutable layout input from mutable rendered panel state."""
        total_width, total_height = self._get_panel_total_size(panel)
        return _PanelGeometry(
            label=panel["label"],
            width=float(panel["width"]),
            height=float(panel["height"]),
            margin_left=float(panel.get("margin_left", 0)),
            margin_top=float(panel.get("margin_top", 0)),
            left_reserve=self._get_left_reserve_px(panel),
            top_reserve=self._get_top_reserve_px(panel),
            total_width=float(total_width),
            total_height=float(total_height),
            below=panel.get("_below"),
            is_spacer=bool(panel.get("_is_spacer")),
        )

    def _calculate_layout(self) -> None:
        """Calculate row assignments and positions for all panels."""
        for panel in self._panels:
            if panel.get("_is_spacer"):
                continue
            _validate_positive_finite_dimension("width", panel["width"])
            _validate_positive_finite_dimension("height", panel["height"])

        geometry = tuple(self._get_panel_geometry(panel) for panel in self._panels)
        layout = _layout_panels(
            geometry,
            float(self._max_width),
            float(self._get_title_height_px()),
        )
        self._rows = [list(row) for row in layout.rows]
        self._row_heights = list(layout.row_heights)
        self._panel_positions = list(layout.positions)

    def _get_panel_position(self, panel_idx: int) -> tuple[float, float]:
        """Get the x, y position (top-left of axes content area) for a panel."""
        if len(self._panel_positions) == len(self._panels):
            return self._panel_positions[panel_idx]
        return 0, 0

    def _create_or_update_figure(self) -> None:
        """Create or update the figure and all axes based on current layout."""
        self._calculate_layout()

        # Calculate total figure size
        title_height_px = self._get_title_height_px()
        fig_height_px = title_height_px + sum(self._row_heights)
        fig_width_px = self._max_width

        # Convert pixels to inches (72 dpi base)
        fig_width = fig_width_px / 72
        fig_height = fig_height_px / 72

        if self.fig is None:
            self.fig = plt.figure(
                figsize=(fig_width, fig_height), dpi=settings.figure_dpi
            )
        else:
            self.fig.set_size_inches(fig_width, fig_height)
        self._connect_draw_handler()

        if self._title is None:
            if self._title_text is not None:
                self._title_text.remove()
                self._title_text = None
        else:
            left_bound_px, right_bound_px = self._get_content_horizontal_bounds_px()
            center_bound_px = (left_bound_px + right_bound_px) / 2
            x_positions = {
                "left": left_bound_px / fig_width_px,
                "center": center_bound_px / fig_width_px,
                "right": right_bound_px / fig_width_px,
            }
            title_y_px = title_height_px / 2
            title_y_fig = (fig_height_px - title_y_px) / fig_height_px

            if self._title_text is None:
                self._title_text = self.fig.text(
                    x_positions[self._title_loc],
                    title_y_fig,
                    self._title,
                    fontsize=settings.title_fontsize,
                    fontweight=self._title_fontweight,
                    va="center",
                    ha=self._title_loc,
                )
            else:
                self._title_text.set_position(
                    (x_positions[self._title_loc], title_y_fig)
                )
                self._title_text.set_text(self._title)
                self._title_text.set_ha(self._title_loc)
                self._title_text.set_va("center")
                self._title_text.set_fontsize(settings.title_fontsize)
                self._title_text.set_fontweight(self._title_fontweight)

        # Create or update axes for all panels
        for idx, panel in enumerate(self._panels):
            # Skip spacer panels
            if panel.get("_is_spacer"):
                continue

            x, y = self._get_panel_position(idx)
            label = panel["label"]
            label_gap = self._get_label_gap_px(panel)
            top_label_offset = self._get_top_label_offset_px(panel)

            # Convert to figure coordinates (0-1 range)
            # Note: matplotlib uses bottom-left as origin, we use top-left
            left = x / fig_width_px
            bottom = (fig_height_px - y - panel["height"]) / fig_height_px
            ax_width = panel["width"] / fig_width_px
            ax_height = panel["height"] / fig_height_px

            ax = self._created_axes.get(label)
            if ax is None:
                # Create new axes
                ax = self.fig.add_axes((left, bottom, ax_width, ax_height))
                self.axes.append(ax)
                self._created_axes[label] = ax
            else:
                # Update existing axes position
                ax.set_position([left, bottom, ax_width, ax_height])
                sync_embedded_axes = getattr(ax, "_cnsplots_sync_embedded_axes", None)
                if callable(sync_embedded_axes):
                    sync_embedded_axes()

            label_text = self._get_live_label_text(label, ax)
            label_transform = self._get_label_transform(
                ax,
                label_gap,
                top_label_offset,
            )
            if label_text is None:
                label_text = ax.text(
                    0,
                    1,
                    label,
                    transform=label_transform,
                    fontsize=settings.title_fontsize,
                    fontweight=settings.panel_label_fontweight,
                    fontname=settings.panel_label_fontname,
                    ha="right",
                    va="bottom",
                )
                self._label_texts[label] = label_text
            else:
                label_text.set_position((0, 1))
                label_text.set_text(label)
                label_text.set_transform(label_transform)
                label_text.set_fontsize(settings.title_fontsize)
                label_text.set_fontweight(settings.panel_label_fontweight)
                label_text.set_fontname(settings.panel_label_fontname)
                label_text.set_ha("right")
                label_text.set_va("bottom")

        self._refresh_known_figure_axes_ids()

    def panel(
        self,
        label: str | None = None,
        height: int | float | None = None,
        width: int | float | None = None,
        pad_left: int | float | None = None,
        pad_top: int | float | None = None,
        *,
        margin_top: int | float | None = None,
        margin_bottom: int | float | None = None,
        margin_left: int | float | None = None,
        margin_right: int | float | None = None,
        color_cycle: str | list[str] | None = None,
        color_map: str | None = None,
        below: str | None = None,
    ) -> Axes:
        """
        Add a panel with specified dimensions, padding, and margins.

        Parameters
        ----------
        label : str or None, optional
            Panel label (e.g., "A", "B", "C"). If None, uses automatic
            sequential labeling (A, B, C, ...).
        height : int, optional
            Axes height in pixels. If None, uses cns.settings.panel_height.
        width : int, optional
            Axes width in pixels. If None, uses cns.settings.panel_width.
        pad_left : int, optional
            Extra horizontal gap in pixels between the panel label and the
            leftmost visible left-side axis decoration. The layout reserves the
            rendered width of y-axis decorations plus this gap. If no left-side
            decorations are visible, the panel label sits ``pad_left`` pixels to
            the left of the axes. If None, uses cns.settings.panel_pad_left.
        pad_top : int, optional
            Extra vertical gap in pixels between the panel label and the
            topmost visible top-side axis decoration, such as the axes title.
            The layout reserves the rendered height of those decorations plus
            this gap. If no top-side decorations are visible, the panel label's
            bottom edge sits ``pad_top`` pixels above the axes. If None, uses
            cns.settings.panel_pad_top.
        margin_top : int, optional
            Top margin in pixels. If None, uses cns.settings.panel_margin_top.
        margin_bottom : int, optional
            Bottom margin in pixels. If None, uses cns.settings.panel_margin_bottom.
        margin_left : int, optional
            Left margin in pixels. If None, uses cns.settings.panel_margin_left.
        margin_right : int, optional
            Right margin in pixels. If None, uses cns.settings.panel_margin_right.
        color_cycle : str or list of str, optional
            Color palette name or explicit color list for this panel. If None,
            uses cns.settings.palette_qual.
        color_map : str, optional
            Colormap name for this panel. If None, uses cns.settings.palette_seq.
        below : str, optional
            Label of another panel to stack this panel below (e.g., "D").
            The panel is positioned directly below the specified panel
            instead of flowing in the normal left-to-right layout.

        Returns
        -------
        ax : matplotlib.axes.Axes
            The matplotlib axes object for plotting.

        Examples
        --------
        >>> mp = cns.multipanel(max_width=400)
        >>> # Panel with ylabel - keep 45 px between label and left axis text
        >>> ax = mp.panel(
        ...     "A",
        ...     width=100,
        ...     height=150,
        ...     pad_left=45,
        ...     pad_top=12,
        ...     margin_left=0,
        ...     margin_top=0,
        ...     margin_right=10,
        ...     margin_bottom=20,
        ... )
        >>> cns.boxplot(data=df, x="group", y="value")
        >>> plt.ylabel("Values")
        >>>
        >>> # Panel without left-side decorations - less gap is enough
        >>> ax = mp.panel(
        ...     "B",
        ...     width=100,
        ...     height=150,
        ...     pad_left=15,
        ...     pad_top=12,
        ...     margin_left=0,
        ...     margin_top=0,
        ...     margin_right=10,
        ...     margin_bottom=20,
        ... )
        >>> cns.barplot(data=df, x="category", y="count")

        Notes
        -----
        Total panel dimensions are calculated as:

        - Total width = margin_left + label width + left decorations + pad_left
          + width + margin_right
        - Total height = margin_top + label height + top decorations + pad_top
          + height + margin_bottom

        Left decoration widths plus panel-label width/height and top decoration
        heights are refined after draw using the rendered artists, so
        multipanel may do one guarded relayout pass before display or save.
        """
        if color_cycle is None:
            color_cycle = settings.palette_qual
        if color_map is None:
            color_map = settings.palette_seq
        if height is None:
            height = settings.panel_height
        if width is None:
            width = settings.panel_width
        if pad_left is None:
            pad_left = settings.panel_pad_left
        if pad_top is None:
            pad_top = settings.panel_pad_top
        if margin_left is None:
            margin_left = settings.panel_margin_left
        if margin_top is None:
            margin_top = settings.panel_margin_top
        if margin_right is None:
            margin_right = settings.panel_margin_right
        if margin_bottom is None:
            margin_bottom = settings.panel_margin_bottom

        width = _validate_positive_finite_dimension("width", width)
        height = _validate_positive_finite_dimension("height", height)

        if label is None:
            if self._panel_index >= len(self._labels):
                raise ValueError(
                    "Automatic panel labels are limited to 26; "
                    "provide an explicit unique label"
                )
            label = self._labels[self._panel_index]
        if not isinstance(label, str):
            raise TypeError("label must be a string or None")
        if any(panel.get("label") == label for panel in self._panels):
            raise ValueError(f"Panel label {label!r} already exists")

        if below is not None:
            if not isinstance(below, str):
                raise TypeError("below must be a string or None")
            if not any(panel.get("label") == below for panel in self._panels):
                raise ValueError(
                    f"below must reference an existing panel label: {below!r}"
                )

        setup_matplotlib(color_cycle, color_map)

        self._capture_linked_helper_axes()

        panel_info = _Panel(
            label=label,
            width=width,
            height=height,
            pad_left=pad_left,
            pad_top=pad_top,
            margin_left=margin_left,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            _below=below,
        )
        self._panels.append(panel_info)

        # Create or update figure
        self._create_or_update_figure()

        self._panel_index += 1

        # Set this axes as current and return it
        ax = self._created_axes.get(label)
        if ax is None:
            msg = f"Panel '{label}' axes was not created"
            raise RuntimeError(msg)
        plt.sca(ax)
        return ax

    def get_axes(self, label: str) -> Axes | None:
        """
        Get a previously created axes by its label.

        Parameters
        ----------
        label : str
            The label of the panel to retrieve (e.g., "A", "B").

        Returns
        -------
        ax : matplotlib.axes.Axes or None
            The matplotlib axes object, or None if not found.
        """
        return self._created_axes.get(label)

    def newline(self) -> None:
        """
        Force the next panel to start on a new row.

        This is useful when you want to manually control row breaks
        instead of relying on the automatic wrapping behavior.

        Examples
        --------
        >>> mp = cns.multipanel(max_width=400)
        >>> mp.panel("A", width=100, height=100)
        >>> mp.newline()  # Force B to start on new row
        >>> mp.panel("B", width=100, height=100)
        """
        # Add a zero-width panel to force wrapping
        # We do this by adding a spacer panel that takes up remaining width
        if self._panels:
            self._calculate_layout()
            if self._rows:
                # Calculate remaining width in current row
                current_row = self._rows[-1]
                used_width = 0
                for idx in current_row:
                    p = self._panels[idx]
                    used_width += (
                        p["margin_left"]
                        + self._get_left_reserve_px(p)
                        + p["width"]
                        + p["margin_right"]
                    )
                remaining = self._max_width - used_width
                if remaining > 0:
                    # Add invisible spacer
                    self._panels.append(
                        _Panel(
                            label=f"_spacer_{len(self._panels)}",
                            width=0,
                            height=0,
                            pad_left=0,
                            pad_top=0,
                            margin_left=0,
                            margin_top=0,
                            margin_right=0,
                            margin_bottom=0,
                            _is_spacer=True,
                        )
                    )
