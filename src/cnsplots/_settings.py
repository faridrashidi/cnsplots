"""Global settings for cnsplots.

This module provides a centralized configuration system for cnsplots,
allowing users to set global defaults for setup, styling, and helper
behavior across plotting functions.

Examples
--------
>>> import cnsplots as cns

>>> # View current settings
>>> cns.settings.palette_qual
'Ecotyper1'

>>> # Change settings
>>> cns.settings.palette_qual = "Set2"
>>> cns.settings.title_fontsize = 10
>>> cns.settings.figure_width = 180

>>> # Suppress print statements
>>> cns.settings.verbosity = 0

>>> # Reset to defaults
>>> cns.settings.reset()

>>> # Temporarily override settings using a context manager
>>> with cns.settings.context(title_fontsize=12, palette_qual="Set2"):
...     cns.boxplot(...)  # Uses temporary settings
>>> cns.settings.title_fontsize  # Restored to previous value
8
"""

from __future__ import annotations

from collections.abc import Generator, Sequence
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable

_TITLE_LOCS = ("left", "center", "right")
_LEGEND_LOCS = (
    "best",
    "upper right",
    "upper left",
    "lower left",
    "lower right",
    "right",
    "center left",
    "center right",
    "lower center",
    "upper center",
    "center",
)


@dataclass(frozen=True)
class _SettingSpec:
    """Definition of a single public setting."""

    default: Any
    validator: Callable[[Any], Any]
    doc: str


def _validate_string(name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    return value


def _validate_string_choice(name: str, value: Any, choices: Sequence[str]) -> str:
    value = _validate_string(name, value)
    if value not in choices:
        quoted = ", ".join(repr(choice) for choice in choices)
        raise ValueError(f"{name} must be one of: {quoted}")
    return value


def _validate_number(
    name: str,
    value: Any,
    *,
    positive: bool = False,
    non_negative: bool = False,
    allow_none: bool = False,
) -> int | float | None:
    if value is None:
        if allow_none:
            return None
        raise TypeError(f"{name} must be a number")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    if non_negative and value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _validate_integer(
    name: str,
    value: Any,
    *,
    positive: bool = False,
    non_negative: bool = False,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    if non_negative and value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _validate_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")
    return value


def _validate_fontweight(name: str, value: Any) -> str | int:
    if value is None:
        raise TypeError(f"{name} must be a string or integer")
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise TypeError(f"{name} must be a string or integer")
    return value


def _validate_string_sequence(name: str, value: Any) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence of strings")
    result = tuple(value)
    if any(not isinstance(item, str) for item in result):
        raise TypeError(f"{name} must be a sequence of strings")
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _validate_numeric_tuple(
    name: str,
    value: Any,
    *,
    length: int,
    positive: bool = False,
    non_negative: bool = False,
) -> tuple[int | float, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence of {length} numbers")
    result = tuple(value)
    if len(result) != length:
        raise ValueError(f"{name} must contain exactly {length} numbers")
    validated: list[int | float] = []
    for item in result:
        validated_value = _validate_number(
            name,
            item,
            positive=positive,
            non_negative=non_negative,
        )
        assert validated_value is not None
        validated.append(validated_value)
    return tuple(validated)


def _validate_optional_number(name: str, value: Any) -> int | float | None:
    return _validate_number(name, value, positive=True, allow_none=True)


def _spec(default: Any, validator: Callable[[Any], Any], doc: str) -> _SettingSpec:
    return _SettingSpec(default=default, validator=validator, doc=doc)


_SETTING_SPECS: dict[str, _SettingSpec] = {
    "palette_qual": _spec(
        "Ecotyper1",
        lambda value: _validate_string("palette_qual", value),
        "Default qualitative color palette for categorical data.",
    ),
    "palette_seq": _spec(
        "gnuplot",
        lambda value: _validate_string("palette_seq", value),
        "Default sequential colormap for continuous data.",
    ),
    "title_fontsize": _spec(
        8,
        lambda value: _validate_number("title_fontsize", value, positive=True),
        "Font size for titles and axis labels.",
    ),
    "title_fontweight": _spec(
        "bold",
        lambda value: _validate_fontweight("title_fontweight", value),
        "Font weight for titles.",
    ),
    "fontsize_legend": _spec(
        7,
        lambda value: _validate_number("fontsize_legend", value, positive=True),
        "Font size for tick labels and legend-adjacent helper text.",
    ),
    "axes_linewidth": _spec(
        0.5,
        lambda value: _validate_number("axes_linewidth", value, positive=True),
        "Line width for axis spines.",
    ),
    "verbosity": _spec(
        1,
        lambda value: _validate_integer("verbosity", value, non_negative=True),
        "Verbosity level. 0 = silent, 1 = normal.",
    ),
    "mathtext_fontset": _spec(
        "custom",
        lambda value: _validate_string("mathtext_fontset", value),
        "Default matplotlib mathtext fontset.",
    ),
    "font_family": _spec(
        "sans-serif",
        lambda value: _validate_string("font_family", value),
        "Default matplotlib font family.",
    ),
    "font_sans_serif": _spec(
        (
            "Helvetica",
            "Helvetica Neue",
            "Arial",
            "DejaVu Sans",
            "Liberation Sans",
        ),
        lambda value: _validate_string_sequence("font_sans_serif", value),
        "Preferred sans-serif font family fallbacks.",
    ),
    "savefig_bbox": _spec(
        "tight",
        lambda value: _validate_string("savefig_bbox", value),
        "Default savefig bounding box mode.",
    ),
    "savefig_pad_inches": _spec(
        0.01,
        lambda value: _validate_number("savefig_pad_inches", value, positive=True),
        "Default savefig padding in inches.",
    ),
    "savefig_dpi": _spec(
        72 * 4,
        lambda value: _validate_number("savefig_dpi", value, positive=True),
        "Default savefig DPI.",
    ),
    "savefig_transparent": _spec(
        True,
        lambda value: _validate_bool("savefig_transparent", value),
        "Whether saved figures are transparent by default.",
    ),
    "svg_fonttype": _spec(
        "none",
        lambda value: _validate_string("svg_fonttype", value),
        "SVG font embedding mode.",
    ),
    "pdf_fonttype": _spec(
        42,
        lambda value: _validate_integer("pdf_fonttype", value, positive=True),
        "PDF font embedding type.",
    ),
    "axes_titlelocation": _spec(
        "center",
        lambda value: _validate_string_choice("axes_titlelocation", value, _TITLE_LOCS),
        "Default axes title alignment.",
    ),
    "axes_grid": _spec(
        False,
        lambda value: _validate_bool("axes_grid", value),
        "Whether axes grid lines are shown by default.",
    ),
    "axes_spines_top": _spec(
        False,
        lambda value: _validate_bool("axes_spines_top", value),
        "Whether the top axis spine is visible by default.",
    ),
    "axes_spines_right": _spec(
        False,
        lambda value: _validate_bool("axes_spines_right", value),
        "Whether the right axis spine is visible by default.",
    ),
    "axes_edgecolor": _spec(
        "black",
        lambda value: _validate_string("axes_edgecolor", value),
        "Default axes spine color.",
    ),
    "axes_labelcolor": _spec(
        "black",
        lambda value: _validate_string("axes_labelcolor", value),
        "Default axes label color.",
    ),
    "axes_labelpad": _spec(
        2,
        lambda value: _validate_number("axes_labelpad", value),
        "Default axis label padding.",
    ),
    "axes_titlepad": _spec(
        4,
        lambda value: _validate_number("axes_titlepad", value),
        "Default axis title padding.",
    ),
    "axes_xmargin": _spec(
        0.05,
        lambda value: _validate_number("axes_xmargin", value),
        "Default x-axis margin.",
    ),
    "axes_ymargin": _spec(
        0.05,
        lambda value: _validate_number("axes_ymargin", value),
        "Default y-axis margin.",
    ),
    "legend_fontsize": _spec(
        None,
        lambda value: _validate_optional_number("legend_fontsize", value),
        "Default legend text size. Use None to inherit title_fontsize.",
    ),
    "legend_title_fontsize": _spec(
        None,
        lambda value: _validate_optional_number("legend_title_fontsize", value),
        "Default legend title size. Use None to inherit title_fontsize.",
    ),
    "legend_frameon": _spec(
        False,
        lambda value: _validate_bool("legend_frameon", value),
        "Whether legends draw a frame by default.",
    ),
    "legend_markerscale": _spec(
        0.5,
        lambda value: _validate_number("legend_markerscale", value, non_negative=True),
        "Default legend marker scale.",
    ),
    "legend_handlelength": _spec(
        0.7,
        lambda value: _validate_number("legend_handlelength", value, non_negative=True),
        "Default legend handle length.",
    ),
    "legend_handleheight": _spec(
        0.7,
        lambda value: _validate_number("legend_handleheight", value, non_negative=True),
        "Default legend handle height.",
    ),
    "legend_handletextpad": _spec(
        0.3,
        lambda value: _validate_number(
            "legend_handletextpad", value, non_negative=True
        ),
        "Default legend handle-text padding.",
    ),
    "xtick_bottom": _spec(
        True,
        lambda value: _validate_bool("xtick_bottom", value),
        "Whether bottom x-axis ticks are shown by default.",
    ),
    "xtick_color": _spec(
        "black",
        lambda value: _validate_string("xtick_color", value),
        "Default x-axis tick color.",
    ),
    "xtick_major_size": _spec(
        2,
        lambda value: _validate_number("xtick_major_size", value, non_negative=True),
        "Default x-axis major tick length.",
    ),
    "xtick_major_width": _spec(
        0.6,
        lambda value: _validate_number("xtick_major_width", value, non_negative=True),
        "Default x-axis major tick width.",
    ),
    "xtick_major_pad": _spec(
        1,
        lambda value: _validate_number("xtick_major_pad", value),
        "Default x-axis major tick padding.",
    ),
    "xtick_alignment": _spec(
        "center",
        lambda value: _validate_string("xtick_alignment", value),
        "Default x-axis tick label alignment.",
    ),
    "xtick_labelrotation": _spec(
        0,
        lambda value: _validate_number("xtick_labelrotation", value),
        "Default x-axis tick label rotation for setup_ax.",
    ),
    "ytick_left": _spec(
        True,
        lambda value: _validate_bool("ytick_left", value),
        "Whether left y-axis ticks are shown by default.",
    ),
    "ytick_color": _spec(
        "black",
        lambda value: _validate_string("ytick_color", value),
        "Default y-axis tick color.",
    ),
    "ytick_major_size": _spec(
        2,
        lambda value: _validate_number("ytick_major_size", value, non_negative=True),
        "Default y-axis major tick length.",
    ),
    "ytick_major_width": _spec(
        0.6,
        lambda value: _validate_number("ytick_major_width", value, non_negative=True),
        "Default y-axis major tick width.",
    ),
    "ytick_major_pad": _spec(
        1,
        lambda value: _validate_number("ytick_major_pad", value),
        "Default y-axis major tick padding.",
    ),
    "ytick_alignment": _spec(
        "center_baseline",
        lambda value: _validate_string("ytick_alignment", value),
        "Default y-axis tick label alignment.",
    ),
    "ytick_labelrotation": _spec(
        0,
        lambda value: _validate_number("ytick_labelrotation", value),
        "Default y-axis tick label rotation for setup_ax.",
    ),
    "setup_ax_colorbar_label": _spec(
        "FDR q-val",
        lambda value: _validate_string("setup_ax_colorbar_label", value),
        "Default colorbar label for setup_ax.",
    ),
    "scanpy_use_default_style": _spec(
        False,
        lambda value: _validate_bool("scanpy_use_default_style", value),
        "Whether scanpy keeps its own default styling.",
    ),
    "scanpy_figsize": _spec(
        (2.5, 2.5),
        lambda value: _validate_numeric_tuple(
            "scanpy_figsize", value, length=2, positive=True
        ),
        "Default scanpy figure size in inches.",
    ),
    "scanpy_facecolor": _spec(
        "white",
        lambda value: _validate_string("scanpy_facecolor", value),
        "Default scanpy figure background color.",
    ),
    "ggplot_fontsize": _spec(
        10,
        lambda value: _validate_number("ggplot_fontsize", value, positive=True),
        "Font size used by setup_ggplot.",
    ),
    "ggplot_font_family": _spec(
        "sans",
        lambda value: _validate_string("ggplot_font_family", value),
        "Font family used by setup_ggplot.",
    ),
    "ggplot_font_face": _spec(
        "plain",
        lambda value: _validate_string("ggplot_font_face", value),
        "Font face used by setup_ggplot.",
    ),
    "ggplot_text_color": _spec(
        "black",
        lambda value: _validate_string("ggplot_text_color", value),
        "Text color used by setup_ggplot.",
    ),
    "figure_width": _spec(
        150,
        lambda value: _validate_number("figure_width", value, positive=True),
        "Default figure width in pixels for figure().",
    ),
    "figure_height": _spec(
        150,
        lambda value: _validate_number("figure_height", value, positive=True),
        "Default figure height in pixels for figure().",
    ),
    "figure_dpi": _spec(
        72 * 2,
        lambda value: _validate_number("figure_dpi", value, positive=True),
        "Default figure DPI for figure helpers.",
    ),
    "multipanel_max_width": _spec(
        540,
        lambda value: _validate_number("multipanel_max_width", value, positive=True),
        "Default maximum width in pixels for multipanel figures.",
    ),
    "multipanel_title_loc": _spec(
        "center",
        lambda value: _validate_string_choice(
            "multipanel_title_loc", value, _TITLE_LOCS
        ),
        "Default multipanel figure title alignment.",
    ),
    "multipanel_title_height_min": _spec(
        12,
        lambda value: _validate_number(
            "multipanel_title_height_min", value, non_negative=True
        ),
        "Minimum reserved title-band height for multipanel figures.",
    ),
    "multipanel_title_height_pad": _spec(
        4,
        lambda value: _validate_number(
            "multipanel_title_height_pad", value, non_negative=True
        ),
        "Extra title-band padding added to title_fontsize in multipanel figures.",
    ),
    "panel_width": _spec(
        150,
        lambda value: _validate_number("panel_width", value, positive=True),
        "Default panel width in pixels for multipanel.panel().",
    ),
    "panel_height": _spec(
        150,
        lambda value: _validate_number("panel_height", value, positive=True),
        "Default panel height in pixels for multipanel.panel().",
    ),
    "panel_label_left": _spec(
        10,
        lambda value: _validate_number("panel_label_left", value, non_negative=True),
        "Default left label reservation in pixels for multipanel.panel().",
    ),
    "panel_label_top": _spec(
        12,
        lambda value: _validate_number("panel_label_top", value, non_negative=True),
        "Default top label reservation in pixels for multipanel.panel().",
    ),
    "panel_pad_left": _spec(
        20,
        lambda value: _validate_number("panel_pad_left", value, non_negative=True),
        "Default left padding in pixels for multipanel.panel().",
    ),
    "panel_pad_top": _spec(
        0,
        lambda value: _validate_number("panel_pad_top", value, non_negative=True),
        "Default top padding in pixels for multipanel.panel().",
    ),
    "panel_margin_top": _spec(
        0,
        lambda value: _validate_number("panel_margin_top", value, non_negative=True),
        "Default top margin in pixels for multipanel.panel().",
    ),
    "panel_margin_bottom": _spec(
        20,
        lambda value: _validate_number("panel_margin_bottom", value, non_negative=True),
        "Default bottom margin in pixels for multipanel.panel().",
    ),
    "panel_margin_left": _spec(
        10,
        lambda value: _validate_number("panel_margin_left", value, non_negative=True),
        "Default left margin in pixels for multipanel.panel().",
    ),
    "panel_margin_right": _spec(
        0,
        lambda value: _validate_number("panel_margin_right", value, non_negative=True),
        "Default right margin in pixels for multipanel.panel().",
    ),
    "panel_label_fontname": _spec(
        "Arial",
        lambda value: _validate_string("panel_label_fontname", value),
        "Font name used for panel labels.",
    ),
    "panel_label_fontweight": _spec(
        "bold",
        lambda value: _validate_fontweight("panel_label_fontweight", value),
        "Font weight used for panel labels.",
    ),
    "panel_label_offset_x": _spec(
        -0.25,
        lambda value: _validate_number("panel_label_offset_x", value),
        "Default x offset for add_panel_label(), in axes coordinates.",
    ),
    "panel_label_offset_y": _spec(
        1.1,
        lambda value: _validate_number("panel_label_offset_y", value),
        "Default y offset for add_panel_label(), in axes coordinates.",
    ),
    "legend_out_bbox_to_anchor": _spec(
        (1, 1.02),
        lambda value: _validate_numeric_tuple(
            "legend_out_bbox_to_anchor", value, length=2
        ),
        "Default bbox_to_anchor for take_legend_out().",
    ),
    "legend_out_loc": _spec(
        "upper left",
        lambda value: _validate_string_choice("legend_out_loc", value, _LEGEND_LOCS),
        "Default legend location for take_legend_out().",
    ),
    "legend_out_markerscale": _spec(
        1,
        lambda value: _validate_number(
            "legend_out_markerscale", value, non_negative=True
        ),
        "Default marker scale for take_legend_out().",
    ),
}


def _make_setting_property(name: str, doc: str) -> property:
    def getter(self: CNSSettings) -> Any:
        return object.__getattribute__(self, f"_{name}")

    def setter(self: CNSSettings, value: Any) -> None:
        validated = type(self)._setting_specs[name].validator(value)
        object.__setattr__(self, f"_{name}", validated)

    return property(getter, setter, doc=doc)


class CNSSettings:
    """Global settings for cnsplots."""

    _setting_specs = _SETTING_SPECS
    _defaults = {name: spec.default for name, spec in _SETTING_SPECS.items()}

    def _invalid_setting_message(self, name: str) -> str:
        """Return a consistent error message for unknown setting names."""
        valid_settings = ", ".join(sorted(type(self)._defaults))
        return f"'{name}' is not a valid setting. Valid settings: {valid_settings}"

    def __setattr__(self, name: str, value: Any) -> None:
        """Reject unknown public attributes so removed settings fail loudly."""
        if not name.startswith("_") and name not in type(self)._defaults:
            raise AttributeError(self._invalid_setting_message(name))
        super().__setattr__(name, value)

    def __getattr__(self, name: str) -> Any:
        """Raise a helpful error for missing public setting names."""
        if not name.startswith("_"):
            raise AttributeError(self._invalid_setting_message(name))
        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {name!r}"
        )

    def __init__(self) -> None:
        """Initialize settings with default values."""
        self.reset()

    def reset(self) -> None:
        """Reset all settings to their default values."""
        for name, spec in type(self)._setting_specs.items():
            setattr(self, name, deepcopy(spec.default))

    @contextmanager
    def context(self, **kwargs: Any) -> Generator[CNSSettings, None, None]:
        """Temporarily override settings within a context manager."""
        for key in kwargs:
            if key not in self._defaults:
                raise AttributeError(self._invalid_setting_message(key))

        old_values = {key: deepcopy(getattr(self, key)) for key in kwargs}

        try:
            for key, value in kwargs.items():
                setattr(self, key, value)
            yield self
        finally:
            for key, value in old_values.items():
                setattr(self, key, value)

    def __repr__(self) -> str:
        """Return a string representation of current settings."""
        lines = ["CNSSettings("]
        for name in type(self)._defaults:
            lines.append(f"    {name}={getattr(self, name)!r},")
        lines[-1] = lines[-1].rstrip(",")
        lines.append(")")
        return "\n".join(lines)


for _setting_name, _setting_spec in CNSSettings._setting_specs.items():
    setattr(
        CNSSettings,
        _setting_name,
        _make_setting_property(_setting_name, _setting_spec.doc),
    )


# Global settings instance
settings = CNSSettings()
