from __future__ import annotations

import logging
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Literal, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from lxml import etree  # ty: ignore[unresolved-import]
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox

import cnsplots as cns
from cnsplots import _svg


def test_figure_returns_new_current_figure_and_preserves_plotting(
    tmp_path: Path, numeric_df: pd.DataFrame
) -> None:
    previous = plt.figure()
    with cns.settings.context(figure_dpi=96), plt.rc_context():
        fig = cns.figure(width=216, height=144)
        assert isinstance(fig, Figure)
        assert fig is plt.gcf()
        assert fig is not previous
        assert fig.get_size_inches() == pytest.approx((3, 2))
        assert fig.dpi == 96

        ax = cns.scatterplot(data=numeric_df, x="x", y="y")
        assert ax.figure is fig
        assert len(np.asarray(ax.collections[0].get_offsets())) == len(numeric_df)
        path = tmp_path / "returned-figure.png"
        cns.savefig(path)
        assert path.is_file()
        assert plt.gcf() is fig
        assert fig.get_size_inches() == pytest.approx((3, 2))
        assert fig.dpi == 96


def _colored_figure(width: float, height: float, color: str) -> Figure:
    fig = plt.figure(figsize=(width, height), dpi=72, facecolor="yellow")
    fig.add_artist(
        Rectangle(
            (0.25, 0.25),
            0.5,
            0.5,
            transform=fig.transFigure,
            facecolor=color,
            edgecolor="none",
        )
    )
    return fig


def _assert_export(
    path: Path, size_inches: tuple[float, float], dpi: float, transparent: bool
) -> None:
    """Check the output dimensions and the red target, not the blue current figure."""
    if path.suffix == ".png":
        pixels = plt.imread(path)
        assert pixels.shape[1::-1] == pytest.approx(
            np.asarray(size_inches) * dpi, abs=1
        )
        assert np.any(np.all(pixels[:, :, :3] == (1, 0, 0), axis=-1))
        assert not np.any(np.all(pixels[:, :, :3] == (0, 0, 1), axis=-1))
        assert pixels[0, 0, 3] == (0 if transparent else 1)
    elif path.suffix == ".pdf":
        content = path.read_bytes()
        match = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)", content)
        assert match is not None
        size_points = tuple(float(value) for value in match.groups())
        assert size_points == pytest.approx(np.asarray(size_inches) * 72)
        assert b"1 0 0 rg" in content
        assert b"0 0 1 rg" not in content
        assert (b"1 1 0 rg" in content) is not transparent
    else:
        root = etree.parse(str(path)).getroot()
        view_box = [float(value) for value in root.get("viewBox").split()]
        assert view_box[2:] == pytest.approx(np.asarray(size_inches) * 72, abs=0.01)
        content = path.read_text(encoding="utf-8").lower()
        assert "#ff0000" in content
        assert "#0000ff" not in content
        assert ("#ffff00" in content) is not transparent


@pytest.mark.parametrize("format", ["png", "pdf", "svg", "svg-missing", "svg-failed"])
@pytest.mark.parametrize("bounds", ["tight", "full", "explicit"])
@pytest.mark.parametrize("transparent", [False, True])
def test_savefig_exports_explicit_figure_with_per_call_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    format: str,
    bounds: str,
    transparent: bool,
) -> None:
    if format == "svg" and shutil.which("mutool") is None:
        pytest.skip("MuPDF's mutool is required for optimized SVG export")

    def unavailable_mutool(*args: object, **kwargs: object) -> None:
        if format == "svg-missing":
            raise FileNotFoundError("mutool")
        raise subprocess.CalledProcessError(1, ["mutool"], stderr=b"conversion failed")

    if format.startswith("svg-"):
        monkeypatch.setattr(_svg.subprocess, "run", unavailable_mutool)

    bbox: Literal["tight"] | Bbox | None
    if bounds == "tight":
        bbox, size_inches = "tight", (1.2, 0.7)
    elif bounds == "full":
        bbox, size_inches = None, (2.0, 1.0)
    else:
        bbox, size_inches = Bbox.from_bounds(0, 0, 1.25, 0.75), (1.25, 0.75)

    with (
        cns.settings.context(
            savefig_dpi=144,
            savefig_bbox="tight",
            savefig_pad_inches=0.2,
            savefig_transparent=not transparent,
        ),
        plt.rc_context(
            {
                "savefig.dpi": 72,
                "savefig.bbox": "tight",
                "savefig.pad_inches": 0.3,
                "savefig.transparent": not transparent,
                "pdf.compression": 0,
            }
        ),
    ):
        target = _colored_figure(2, 1, "red")
        current = _colored_figure(5, 4, "blue")
        original_canvas = target.canvas
        assert isinstance(original_canvas, FigureCanvasAgg)
        original_canvas.draw()
        original_pixels = np.asarray(original_canvas.buffer_rgba()).copy()
        original_rc = dict(plt.rcParams)
        original_settings = repr(cns.settings)
        path = tmp_path / "nested" / f"target.{format.split('-')[0]}"

        def save() -> None:
            cns.savefig(
                path,
                fig=target,
                dpi=100,
                transparent=transparent,
                bbox_inches=bbox,
                pad_inches=0.1,
            )

        if format.startswith("svg-"):
            with pytest.warns(RuntimeWarning, match="mutool"):
                save()
        else:
            save()

        _assert_export(path, size_inches, dpi=100, transparent=transparent)
        assert plt.gcf() is current
        assert target.dpi == 72
        assert target.canvas is original_canvas
        np.testing.assert_array_equal(original_canvas.buffer_rgba(), original_pixels)
        assert target.patch.get_alpha() is None
        assert dict(plt.rcParams) == original_rc
        assert repr(cns.settings) == original_settings


@pytest.mark.parametrize("bbox_setting", ["tight", "standard"])
@pytest.mark.parametrize("transparent", [False, True])
def test_savefig_uses_current_settings_without_reapplying_style(
    tmp_path: Path, bbox_setting: str, transparent: bool
) -> None:
    with (
        cns.settings.context(
            savefig_dpi=100,
            savefig_bbox=bbox_setting,
            savefig_pad_inches=0.1,
            savefig_transparent=transparent,
        ),
        plt.rc_context(
            {
                "savefig.dpi": 200,
                "savefig.bbox": None if bbox_setting == "tight" else "tight",
                "savefig.pad_inches": 0.4,
                "savefig.transparent": not transparent,
            }
        ),
    ):
        target = _colored_figure(2, 1, "red")
        path = tmp_path / "defaults.png"
        original_rc = dict(plt.rcParams)
        cns.savefig(path, dpi=None, transparent=None, pad_inches=None)

        size_inches = (1.2, 0.7) if bbox_setting == "tight" else (2.0, 1.0)
        _assert_export(path, size_inches, dpi=100, transparent=transparent)
        assert plt.gcf() is target
        assert target.dpi == 72
        assert dict(plt.rcParams) == original_rc


@pytest.mark.parametrize("stage", ["draw", "bbox", "save"])
def test_savefig_restores_figure_and_style_after_export_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    target = _colored_figure(2, 1, "red")
    current = _colored_figure(5, 4, "blue")
    original_canvas = target.canvas
    original_rc = dict(plt.rcParams)
    original_settings = repr(cns.settings)
    logger = logging.getLogger("fontTools")
    original_level = logger.level
    calls = 0

    def fail_permanently(*args: object, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError(f"export interrupted at attempt {calls}")

    if stage == "draw":
        monkeypatch.setattr(original_canvas, "draw", fail_permanently)
    elif stage == "bbox":
        monkeypatch.setattr(target, "get_tightbbox", fail_permanently)
    else:
        monkeypatch.setattr(target, "savefig", fail_permanently)

    with pytest.raises(RuntimeError, match="export interrupted at attempt 1$"):
        cns.savefig(
            tmp_path / "failure.pdf",
            fig=target,
            dpi=144,
            transparent=True,
            bbox_inches="tight",
            pad_inches=0.1,
        )

    assert target.dpi == 72
    assert target.canvas is original_canvas
    assert target.patch.get_alpha() is None
    assert plt.gcf() is current
    assert dict(plt.rcParams) == original_rc
    assert repr(cns.settings) == original_settings
    assert logger.level == original_level


@pytest.mark.parametrize(
    "option,value,error",
    [
        ("dpi", 0, ValueError),
        ("dpi", -1, ValueError),
        ("dpi", float("inf"), ValueError),
        ("dpi", float("nan"), ValueError),
        ("dpi", "100", TypeError),
        ("dpi", True, TypeError),
        ("pad_inches", -1, ValueError),
        ("pad_inches", float("inf"), ValueError),
        ("pad_inches", float("nan"), ValueError),
        ("pad_inches", "0.1", TypeError),
        ("pad_inches", False, TypeError),
        ("transparent", 1, TypeError),
        ("bbox_inches", "standard", ValueError),
        ("bbox_inches", "invalid", ValueError),
    ],
)
def test_savefig_rejects_invalid_export_options(
    tmp_path: Path, option: str, value: object, error: type[Exception]
) -> None:
    target = _colored_figure(2, 1, "red")
    path = tmp_path / "invalid.png"
    save = cast(Callable[..., None], cns.savefig)
    with pytest.raises(error, match=option):
        save(path, fig=target, **{option: value})
    assert not path.exists()
    assert target.dpi == 72


@pytest.mark.parametrize("option", ["facecolor", "format", "metadata"])
def test_savefig_rejects_unsupported_options(tmp_path: Path, option: str) -> None:
    path = tmp_path / "unsupported.png"
    save = cast(Callable[..., None], cns.savefig)
    with pytest.raises(TypeError, match=option):
        save(path, **{option: "unsupported"})
    assert not path.exists()
