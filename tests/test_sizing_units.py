"""Regression tests for physical sizing units and the legacy point defaults."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

import cnsplots as cns


def _render(fig: Figure) -> np.ndarray:
    canvas = cast(FigureCanvasAgg, fig.canvas)
    canvas.draw()
    return np.asarray(canvas.buffer_rgba()).copy()


@pytest.mark.parametrize(
    "unit,width,height", [("pt", 144, 108), ("in", 2, 1.5), ("mm", 50.8, 38.1)]
)
def test_figure_units_define_the_same_physical_size(
    unit: Literal["pt", "in", "mm"], width: float, height: float
) -> None:
    with cns.settings.context(figure_dpi=144):
        fig = cns.figure(width, height, unit=unit)
    assert fig.get_size_inches() == pytest.approx((2, 1.5))
    assert fig.canvas.get_width_height() == (288, 216)


@pytest.mark.parametrize("scalar_type", [np.int64, np.float32, np.float64])
def test_numpy_real_scalars_preserve_legacy_sizes_and_unit_conversion(
    scalar_type: Any,
) -> None:
    legacy = cns.figure(scalar_type(100), scalar_type(150))
    assert legacy.get_size_inches() == pytest.approx((100 / 72, 150 / 72))
    dimensions: list[tuple[Literal["pt", "in", "mm"], int, float]] = [
        ("pt", 144, 1 / 72),
        ("in", 2, 1),
        ("mm", 50, 1 / 25.4),
    ]
    for unit, width, inches_per_unit in dimensions:
        expected = (width * inches_per_unit, width / 2 * inches_per_unit)
        fig = cns.figure(scalar_type(width), scalar_type(width / 2), unit=unit)
        assert fig.get_size_inches() == pytest.approx(expected)
        mp = cns.multipanel(max_width=scalar_type(width * 3), unit=unit)
        ax = mp.panel(width=scalar_type(width), height=scalar_type(width / 2))
        assert mp.fig is not None
        mp.fig.canvas.draw()
        assert mp.fig.get_size_inches()[0] == pytest.approx(expected[0] * 3)
        bbox = ax.get_window_extent()
        assert np.asarray((bbox.width, bbox.height)) / mp.fig.dpi == (
            pytest.approx(expected)
        )


def test_legacy_point_dimensions_and_export_dpi(tmp_path: Path) -> None:
    with cns.settings.context(figure_dpi=144):
        fig = cns.figure(100, 150)
    ax = fig.add_axes((0.2, 0.2, 0.6, 0.6))
    ax.plot([0, 1], [0, 1])
    ax.set_axis_off()
    assert fig.get_size_inches() == pytest.approx((100 / 72, 150 / 72))
    assert fig.canvas.get_width_height() == (200, 300)

    full_path = tmp_path / "full.png"
    cns.savefig(full_path, fig=fig, dpi=288, bbox_inches=None)
    assert plt.imread(full_path).shape[1::-1] == (400, 600)
    tight_path = tmp_path / "tight.png"
    cns.savefig(tight_path, fig=fig, dpi=288, bbox_inches="tight", pad_inches=0)
    assert plt.imread(tight_path).shape[1::-1] != (400, 600)
    assert fig.dpi == 144
    assert fig.get_size_inches() == pytest.approx((100 / 72, 150 / 72))


def test_explicit_points_preserve_legacy_figure_rendering() -> None:
    with cns.settings.context(figure_dpi=144):
        legacy = cns.figure(144, 108, "Set2", "parula")
        explicit = cns.figure(144, 108, "Set2", "parula", unit="pt")
    for fig in (legacy, explicit):
        ax = fig.add_subplot()
        ax.plot([0, 1, 2], [1, 0, 2])
        ax.set_title("Physical size")
    np.testing.assert_array_equal(_render(legacy), _render(explicit))


def _sized_multipanel(unit: Literal["pt", "in", "mm"] | None) -> cns.multipanel:
    points_per_unit = {None: 1, "pt": 1, "in": 72, "mm": 72 / 25.4}[unit]
    unit_kwargs: dict[str, Any] = {} if unit is None else {"unit": unit}
    mp = cns.multipanel(324 / points_per_unit, "Sizing", "left", **unit_kwargs)
    for label in "ABC":
        ax = mp.panel(
            label,
            width=72 / points_per_unit,
            height=54 / points_per_unit,
            pad_left=13,
            pad_top=9,
            margin_left=7,
            margin_right=11,
            margin_top=5,
            margin_bottom=8,
        )
        ax.plot([0, 1, 2], [1, 0, 2])
        ax.set_title("Panel")
    assert mp.fig is not None
    mp.fig.canvas.draw()
    return mp


@pytest.mark.parametrize("unit", ["pt", "in", "mm"])
def test_multipanel_units_preserve_axes_wrapping_margins_and_pixel_padding(
    unit: Literal["pt", "in", "mm"],
) -> None:
    with cns.settings.context(figure_dpi=144):
        legacy = _sized_multipanel(None)
        converted = _sized_multipanel(unit)
    assert legacy.fig is not None
    assert converted.fig is not None
    assert converted._rows == legacy._rows == [[0, 1], [2]]
    assert converted.fig.get_size_inches() == pytest.approx(
        legacy.fig.get_size_inches()
    )
    renderer = cast(FigureCanvasAgg, converted.fig.canvas).get_renderer()
    for actual, expected, panel in zip(
        converted.axes, legacy.axes, converted._panels, strict=True
    ):
        assert actual.get_position().bounds == pytest.approx(
            expected.get_position().bounds
        )
        bbox = actual.get_window_extent(renderer=renderer)
        assert np.asarray((bbox.width, bbox.height)) / converted.fig.dpi == (
            pytest.approx((1, 0.75))
        )
        assert (panel.margin_left, panel.margin_right) == (7, 11)
        assert (panel.margin_top, panel.margin_bottom) == (5, 8)
        label_bbox = converted._label_texts[panel.label].get_window_extent(renderer)
        yaxis_bbox = actual.yaxis.get_tightbbox(renderer)
        assert yaxis_bbox is not None
        assert yaxis_bbox.x0 - label_bbox.x1 == pytest.approx(13, abs=0.8)
        assert label_bbox.y0 - actual.title.get_window_extent(renderer).y1 == (
            pytest.approx(9, abs=0.8)
        )
    if unit == "pt":
        np.testing.assert_array_equal(_render(legacy.fig), _render(converted.fig))


@pytest.mark.parametrize("unit,two_inches", [("in", 2), ("mm", 50.8)])
def test_omitted_dimensions_keep_settings_in_points(
    unit: Literal["in", "mm"], two_inches: float
) -> None:
    with cns.settings.context(
        figure_width=216,
        figure_height=108,
        multipanel_max_width=360,
        panel_width=72,
        panel_height=54,
        figure_dpi=144,
    ):
        assert cns.figure(unit=unit).get_size_inches() == pytest.approx((3, 1.5))
        assert cns.figure(width=two_inches, unit=unit).get_size_inches() == (
            pytest.approx((2, 1.5))
        )
        assert cns.figure(height=two_inches, unit=unit).get_size_inches() == (
            pytest.approx((3, 2))
        )
        mp = cns.multipanel(unit=unit)
        mp.panel("A")
        mp.panel("B", width=two_inches)
        mp.panel("C", height=two_inches, unit=None)
        assert mp.fig is not None
        mp.fig.canvas.draw()
        assert mp.fig.get_size_inches()[0] == pytest.approx(5)
        for ax, expected in zip(mp.axes, [(1, 0.75), (2, 0.75), (1, 2)], strict=True):
            bbox = ax.get_window_extent()
            assert np.asarray((bbox.width, bbox.height)) / mp.fig.dpi == (
                pytest.approx(expected)
            )


def test_panel_unit_override_does_not_change_inherited_units() -> None:
    mp = cns.multipanel(max_width=8, unit="in")
    mp.panel("A", width=25.4, height=12.7, unit="mm")
    mp.panel("B", width=72, height=36, unit="pt")
    mp.panel("C", width=1, height=0.5)
    mp.panel("D", width=1, height=0.5, unit=None)
    assert mp.fig is not None
    mp.fig.canvas.draw()
    for ax in mp.axes:
        bbox = ax.get_window_extent()
        assert np.asarray((bbox.width, bbox.height)) / mp.fig.dpi == (
            pytest.approx((1, 0.5))
        )


@pytest.mark.parametrize("unit", ["px", "inch", "PT", "", 1, ["pt"]])
def test_invalid_units_leave_figures_and_panel_state_unchanged(unit: Any) -> None:
    mp = cns.multipanel()
    ax = mp.panel("A", width=72, height=54)
    assert mp.fig is not None
    before_pixels = _render(mp.fig)
    before_rc = dict(plt.rcParams)
    before_figures = plt.get_fignums()
    before_panel = vars(mp._panels[0]).copy()
    for make in (cns.figure, cns.multipanel, mp.panel):
        with pytest.raises(ValueError, match="unit"):
            cast(Any, make)(unit=unit)
        assert plt.get_fignums() == before_figures
        assert plt.gcf() is mp.fig
        assert dict(plt.rcParams) == before_rc
        assert mp.axes == [ax]
        assert mp._panel_index == 1
        assert len(mp._panels) == 1
        assert vars(mp._panels[0]) == before_panel
        np.testing.assert_array_equal(_render(mp.fig), before_pixels)
    empty = cns.multipanel()
    with pytest.raises(ValueError, match="unit"):
        cast(Any, empty.panel)(unit=unit)
    assert empty.fig is None
    assert empty._panels == []


def test_none_unit_is_only_valid_for_panel_inheritance() -> None:
    before = plt.get_fignums()
    for make in (cns.figure, cns.multipanel):
        with pytest.raises(ValueError, match="unit"):
            cast(Any, make)(unit=None)
    assert plt.get_fignums() == before


@pytest.mark.parametrize("dimension", ["width", "height"])
@pytest.mark.parametrize(
    "value,error",
    [
        (True, TypeError),
        ("2", TypeError),
        (1j, TypeError),
        (0, ValueError),
        (-1, ValueError),
        (np.nan, ValueError),
        (np.inf, ValueError),
        (-np.inf, ValueError),
    ],
)
def test_invalid_dimensions_leave_existing_state_unchanged(
    dimension: str, value: Any, error: type[Exception]
) -> None:
    mp = cns.multipanel(unit="in")
    ax = mp.panel("A", width=1, height=0.75)
    assert mp.fig is not None
    before_pixels = _render(mp.fig)
    before_rc = dict(plt.rcParams)
    before_figures = plt.get_fignums()
    for make in (cns.figure, mp.panel):
        with pytest.raises(error, match=dimension):
            cast(Any, make)(**{dimension: value}, unit="mm")
        assert plt.get_fignums() == before_figures
        assert plt.gcf() is mp.fig
        assert dict(plt.rcParams) == before_rc
        assert mp.axes == [ax]
        assert len(mp._panels) == mp._panel_index == 1
        np.testing.assert_array_equal(_render(mp.fig), before_pixels)
    with pytest.raises(error, match="max_width"):
        cns.multipanel(max_width=value, unit="in")
    assert plt.get_fignums() == before_figures
