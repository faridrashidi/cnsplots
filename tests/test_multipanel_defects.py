"""Regression tests for multipanel validation and stacked layout."""

from __future__ import annotations

import string
from dataclasses import FrozenInstanceError, replace
from typing import Any, cast

import numpy as np
import pytest

import cnsplots as cns
from cnsplots import _multipanels as multipanel_mod


@pytest.mark.parametrize("max_width", [0, -1, np.nan, np.inf, -np.inf])
def test_multipanel_rejects_non_positive_or_non_finite_max_width(
    max_width: float,
) -> None:
    with pytest.raises(ValueError, match="max_width must be a positive finite number"):
        cns.multipanel(max_width=max_width)


@pytest.mark.parametrize("max_width", [True, "100"])
def test_multipanel_rejects_non_numeric_max_width(max_width: Any) -> None:
    with pytest.raises(TypeError, match="max_width must be a number"):
        cns.multipanel(max_width=max_width)


@pytest.mark.parametrize("dimension", ["width", "height"])
@pytest.mark.parametrize("value", [0, -1, np.nan, np.inf, -np.inf])
def test_multipanel_rejects_non_positive_or_non_finite_panel_dimensions(
    dimension: str,
    value: float,
) -> None:
    mp = cns.multipanel()

    with pytest.raises(
        ValueError,
        match=rf"{dimension} must be a positive finite number",
    ):
        cast(Any, mp.panel)(**{dimension: value})

    assert mp._panels == []
    assert mp.fig is None


@pytest.mark.parametrize("dimension", ["width", "height"])
@pytest.mark.parametrize("value", [True, "100"])
def test_multipanel_rejects_non_numeric_panel_dimensions(
    dimension: str,
    value: Any,
) -> None:
    mp = cns.multipanel()

    with pytest.raises(TypeError, match=rf"{dimension} must be a number"):
        cast(Any, mp.panel)(**{dimension: value})

    assert mp._panels == []
    assert mp.fig is None


def test_multipanel_rejects_duplicate_labels_without_mutating_layout() -> None:
    mp = cns.multipanel(max_width=100)
    original_ax = mp.panel("A", width=20, height=20)

    with pytest.raises(ValueError, match="Panel label 'A' already exists"):
        mp.panel("A", width=20, height=20)

    assert len(mp._panels) == 1
    assert mp.axes == [original_ax]
    assert mp.get_axes("A") is original_ax


def test_multipanel_rejects_automatic_label_collision() -> None:
    mp = cns.multipanel(max_width=100)
    mp.panel("B", width=20, height=20)

    with pytest.raises(ValueError, match="Panel label 'B' already exists"):
        mp.panel(width=20, height=20)


def test_multipanel_rejects_missing_below_parent_without_mutating_layout() -> None:
    mp = cns.multipanel(max_width=100)

    with pytest.raises(
        ValueError,
        match="below must reference an existing panel label: 'missing'",
    ):
        mp.panel("A", width=20, height=20, below="missing")

    assert mp._panels == []
    assert mp.fig is None


def test_multipanel_rejects_non_string_labels_and_parents() -> None:
    mp = cns.multipanel(max_width=100)
    legacy_panel = cast(Any, mp.panel)

    with pytest.raises(TypeError, match="label must be a string or None"):
        legacy_panel(1, width=20, height=20)

    mp.panel("A", width=20, height=20)
    with pytest.raises(TypeError, match="below must be a string or None"):
        legacy_panel("B", width=20, height=20, below=1)


def test_multipanel_layout_rejects_below_cycles() -> None:
    mp = cns.multipanel(max_width=100)
    mp.panel("A", width=20, height=20)
    mp.panel("B", width=20, height=20, below="A")
    mp._panels[0]["_below"] = "B"

    with pytest.raises(ValueError, match="below relationships must not contain cycles"):
        mp._calculate_layout()


def test_pure_multipanel_layout_validates_duplicate_and_missing_labels() -> None:
    mp = cns.multipanel(max_width=100)
    mp.panel("A", width=20, height=20)
    mp.panel("B", width=20, height=20)
    geometry = tuple(mp._get_panel_geometry(panel) for panel in mp._panels)

    duplicate_geometry = (geometry[0], replace(geometry[1], label="A"))
    with pytest.raises(ValueError, match="Panel label 'A' already exists"):
        multipanel_mod._layout_panels(duplicate_geometry, 100, 0)

    missing_parent_geometry = (
        geometry[0],
        replace(geometry[1], below="missing"),
    )
    with pytest.raises(
        ValueError,
        match="below must reference an existing panel label: 'missing'",
    ):
        multipanel_mod._layout_panels(missing_parent_geometry, 100, 0)


def test_multipanel_reports_exhausted_automatic_labels() -> None:
    mp = cns.multipanel(max_width=100)

    for expected_label in string.ascii_uppercase:
        mp.panel(
            width=1,
            height=1,
            pad_left=0,
            pad_top=0,
            margin_left=0,
            margin_top=0,
            margin_right=0,
            margin_bottom=0,
        )
        assert mp._panels[-1]["label"] == expected_label

    with pytest.raises(ValueError, match="Automatic panel labels are limited to 26"):
        mp.panel(width=1, height=1)


def test_multipanel_stacks_multiple_children_without_overlap() -> None:
    mp = cns.multipanel(max_width=100)
    panel_kwargs = {
        "width": 20,
        "pad_left": 0,
        "pad_top": 0,
        "margin_left": 0,
        "margin_top": 0,
        "margin_right": 0,
        "margin_bottom": 0,
    }

    mp.panel("A", height=20, **panel_kwargs)
    mp.panel("B", height=10, below="A", **panel_kwargs)
    mp.panel("C", height=15, below="A", **panel_kwargs)

    assert mp._get_panel_position(0) == pytest.approx((0, 0))
    assert mp._get_panel_position(1) == pytest.approx((0, 20))
    assert mp._get_panel_position(2) == pytest.approx((0, 30))
    assert mp._row_heights == pytest.approx([45])


def test_multipanel_stacks_nested_children_before_later_siblings() -> None:
    mp = cns.multipanel(max_width=100)
    panel_kwargs = {
        "width": 20,
        "pad_left": 0,
        "pad_top": 0,
        "margin_left": 0,
        "margin_top": 0,
        "margin_right": 0,
        "margin_bottom": 0,
    }

    mp.panel("A", height=20, **panel_kwargs)
    mp.panel("B", height=10, below="A", **panel_kwargs)
    mp.panel("C", height=15, below="A", **panel_kwargs)
    mp.panel("D", height=5, below="B", **panel_kwargs)

    assert mp._get_panel_position(0) == pytest.approx((0, 0))
    assert mp._get_panel_position(1) == pytest.approx((0, 20))
    assert mp._get_panel_position(3) == pytest.approx((0, 30))
    assert mp._get_panel_position(2) == pytest.approx((0, 35))
    assert mp._row_heights == pytest.approx([50])


def test_multipanel_uses_descendant_width_for_row_wrapping() -> None:
    mp = cns.multipanel(max_width=70)
    panel_kwargs = {
        "height": 10,
        "pad_left": 0,
        "pad_top": 0,
        "margin_left": 0,
        "margin_top": 0,
        "margin_right": 0,
        "margin_bottom": 0,
    }

    mp.panel("A", width=20, **panel_kwargs)
    mp.panel("B", width=60, below="A", **panel_kwargs)
    mp.panel("C", width=20, **panel_kwargs)

    assert mp._rows == [[0], [2]]
    assert mp._get_panel_position(2)[1] == pytest.approx(20)


def test_multipanel_uses_typed_panels_and_pure_immutable_layout() -> None:
    mp = cns.multipanel(max_width=100)
    panel_kwargs = {
        "width": 20,
        "pad_left": 0,
        "pad_top": 0,
        "margin_left": 0,
        "margin_top": 0,
        "margin_right": 0,
        "margin_bottom": 0,
    }
    mp.panel("A", height=20, **panel_kwargs)
    mp.panel("B", height=10, below="A", **panel_kwargs)

    panel = mp._panels[0]
    assert isinstance(panel, multipanel_mod._Panel)
    assert panel.width == panel["width"] == 20

    panel.pop("known_figure_axes_ids", None)
    fallback_axes_ids = {123}
    assert panel.get("known_figure_axes_ids", fallback_axes_ids) is fallback_axes_ids
    assert "known_figure_axes_ids" not in panel
    assert panel.pop("known_figure_axes_ids", fallback_axes_ids) is fallback_axes_ids
    assert panel.pop("width", "not removable") == "not removable"
    assert panel.width == 20

    geometry = tuple(mp._get_panel_geometry(item) for item in mp._panels)
    panel_state = tuple(vars(item).copy() for item in mp._panels)
    figure = mp.fig
    axes = tuple(mp.axes)

    first_layout = multipanel_mod._layout_panels(geometry, 100, 0)
    second_layout = multipanel_mod._layout_panels(geometry, 100, 0)

    assert first_layout == second_layout
    assert first_layout.rows == ((0,),)
    assert first_layout.row_heights == pytest.approx((30,))
    assert np.asarray(first_layout.positions) == pytest.approx(
        np.asarray(((0, 0), (0, 20)))
    )
    assert tuple(vars(item).copy() for item in mp._panels) == panel_state
    assert mp.fig is figure
    assert tuple(mp.axes) == axes
    with pytest.raises(FrozenInstanceError):
        setattr(first_layout, "rows", ())
