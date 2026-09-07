"""Round-trip checks of final exports, independent of platform-specific hashes."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pytest
from lxml import etree  # ty: ignore[unresolved-import]
from matplotlib.cm import ScalarMappable
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from mpl_toolkits.axes_grid1 import make_axes_locatable
from PIL import Image

import cnsplots as cns
from cnsplots import _svg


@pytest.fixture
def mutool(mode: str) -> str:
    executable = shutil.which("mutool")
    if executable is None and mode in {"pdf", "svg"}:
        pytest.skip("MuPDF's mutool is required to round-trip PDF/SVG exports")
    return executable or "mutool"


def _chrome() -> str:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chrome"):
        executable = shutil.which(name)
        if executable is not None:
            return executable
    locations = [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")]
    locations.extend(
        Path(os.environ[root]) / "Google/Chrome/Application/chrome.exe"
        for root in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")
        if root in os.environ
    )
    for location in locations:
        if location.is_file():
            return str(location)
    pytest.skip("Chrome/Chromium is required to round-trip SVG clipping and masks")


@contextmanager
def _artifacts(directory: Path, name: str) -> Iterator[None]:
    """Keep the final source, reference, rendering and difference on failures."""
    try:
        yield
    except (
        AssertionError,
        OSError,
        subprocess.SubprocessError,
        pytest.fail.Exception,
    ) as exc:
        reference = directory / "reference.png"
        rendered = directory / "rendered.png"
        if reference.exists() and rendered.exists():
            with Image.open(reference) as first, Image.open(rendered) as second:
                size = (
                    max(first.width, second.width),
                    max(first.height, second.height),
                )
                left = Image.new("RGBA", size)
                right = Image.new("RGBA", size)
                left.paste(first)
                right.paste(second)
                delta = np.abs(
                    np.asarray(left, dtype=int) - np.asarray(right, dtype=int)
                )
                difference = np.clip(delta.max(axis=2) * 4, 0, 255).astype("uint8")
                Image.fromarray(difference).save(directory / "difference.png")
        destination = Path("mpl-results/export-pipeline") / name
        shutil.copytree(
            directory,
            destination,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("chrome-profile"),
        )
        raise AssertionError(
            f"{exc}\nExport comparison artifacts: {destination}"
        ) from exc


def _export_and_render(
    fig: Figure,
    directory: Path,
    mode: str,
    mutool: str,
    monkeypatch: pytest.MonkeyPatch,
    *,
    bbox: Literal["tight"] | None = None,
    transparent: bool = False,
) -> np.ndarray:
    chrome = None if mode == "pdf" else _chrome()
    # Agg is an independent reference; it bypasses cns.savefig's PDF/SVG pipeline.
    fig.savefig(
        directory / "reference.png",
        dpi=100,
        bbox_inches=bbox,
        pad_inches=0.1,
        transparent=transparent,
    )
    suffix = "pdf" if mode == "pdf" else "svg"
    final = directory / f"final.{suffix}"

    def unavailable_converter(*args: object, **kwargs: object) -> None:
        if mode == "svg-missing":
            raise FileNotFoundError("mutool")
        raise subprocess.CalledProcessError(1, ["mutool"], stderr=b"conversion failed")

    # Restore subprocess.run before invoking the renderer, including fallback cases.
    with monkeypatch.context() as patch:
        if mode in {"svg-missing", "svg-failed"}:
            patch.setattr(_svg.subprocess, "run", unavailable_converter)
        current = plt.figure()

        def save() -> None:
            cns.savefig(
                final,
                fig=fig,
                dpi=100,
                bbox_inches=bbox,
                pad_inches=0.1,
                transparent=transparent,
            )

        if mode in {"svg-missing", "svg-failed"}:
            with pytest.warns(RuntimeWarning, match="mutool"):
                save()
        else:
            save()
        assert plt.gcf() is current

    rendered = directory / "rendered.png"
    size = None
    if chrome is None:
        command = [
            mutool,
            "draw",
            "-q",
            "-r",
            "100",
            "-c",
            "rgba",
            "-o",
            str(rendered),
            str(final),
        ]
    else:
        # MuPDF's SVG renderer ignores clipping; use a browser for final SVGs.
        root = etree.parse(str(final)).getroot()
        _, _, width, height = map(float, root.get("viewBox").split())
        size = (math.ceil(width * 100 / 72), math.ceil(height * 100 / 72))
        page = directory / "render.html"
        page.write_text(
            "<!doctype html><style>html,body{margin:0}img{display:block}</style>"
            f'<img src="{final.name}" style="width:{width * 100 / 72}px;'
            f'height:{height * 100 / 72}px">',
            encoding="utf-8",
        )
        command = [
            chrome,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--force-device-scale-factor=1",
            "--default-background-color=00000000",
            f"--user-data-dir={directory / 'chrome-profile'}",
            f"--window-size={max(size[0], 800)},{max(size[1], 600)}",
            f"--screenshot={rendered}",
            page.as_uri(),
        ]
    with (directory / "renderer.log").open("wb") as log:
        if chrome is None:
            subprocess.run(
                command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=30
            )
        else:
            # Some Chrome builds stay alive after --screenshot completes. Reap this
            # isolated browser as soon as a complete PNG is available.
            with subprocess.Popen(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=os.name == "posix",
            ) as process:
                deadline = time.monotonic() + 30
                try:
                    while time.monotonic() < deadline:
                        if rendered.exists():
                            try:
                                with Image.open(rendered) as image:
                                    image.verify()
                                break
                            except (OSError, SyntaxError):
                                pass
                        assert process.poll() is None, (
                            "Chrome exited without a screenshot"
                        )
                        time.sleep(0.1)
                    else:
                        raise AssertionError(
                            "Chrome did not produce a screenshot within 30s"
                        )
                finally:
                    if process.poll() is None:
                        if os.name == "posix":
                            with suppress(ProcessLookupError):
                                os.killpg(process.pid, signal.SIGKILL)
                        else:
                            subprocess.run(
                                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                stdout=log,
                                stderr=subprocess.STDOUT,
                                check=False,
                                timeout=10,
                            )
                    process.wait()
    with Image.open(rendered) as image:
        pixels = image.convert("RGBA")
        if size is not None:
            # Chromium has a minimum viewport; retain just the SVG's point bounds.
            pixels = pixels.crop((0, 0, *size))
        pixels.save(rendered)
        return np.asarray(pixels)


def _assert_region(actual: np.ndarray, expected: np.ndarray) -> None:
    """Allow antialiasing differences but detect missing, shifted or clipped shapes."""
    assert actual.any(), "Export lost a colored region"
    assert expected.any(), "Reference must contain the checked region"
    actual_y, actual_x = np.nonzero(actual)
    expected_y, expected_x = np.nonzero(expected)
    actual_bounds = (actual_x.min(), actual_y.min(), actual_x.max(), actual_y.max())
    expected_bounds = (
        expected_x.min(),
        expected_y.min(),
        expected_x.max(),
        expected_y.max(),
    )
    assert actual_bounds == pytest.approx(expected_bounds, abs=2)
    # A one-pixel antialiased border can cover >8% of a narrow colorbar.
    perimeter = 2 * (
        expected_x.max() - expected_x.min() + expected_y.max() - expected_y.min()
    )
    assert actual.sum() == pytest.approx(expected.sum(), abs=perimeter)


@pytest.mark.parametrize("mode", ["pdf", "svg", "svg-missing", "svg-failed"])
@pytest.mark.parametrize("tight_transparent", [False, True])
def test_exported_bounds_clipping_transparency_and_raster_layers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutool: str,
    mode: str,
    tight_transparent: bool,
) -> None:
    with (
        plt.rc_context({"savefig.bbox": None}),
        _artifacts(tmp_path, f"geometry-{mode}-{tight_transparent}"),
    ):
        fig = plt.figure(figsize=(3, 2), dpi=100)
        ax = fig.add_axes((0.2, 0.2, 0.6, 0.6))
        ax.set(xlim=(0, 1), ylim=(0, 1))
        ax.set_axis_off()
        ax.add_patch(Rectangle((-0.5, 0.1), 2, 0.3, color="red", alpha=0.5, lw=0))
        ax.scatter(
            [0.25, 0.75],
            [0.75, 0.75],
            s=225,
            marker="s",
            color="blue",
            linewidth=0,
            rasterized=True,
        )
        actual = _export_and_render(
            fig,
            tmp_path,
            mode,
            mutool,
            monkeypatch,
            bbox="tight" if tight_transparent else None,
            transparent=tight_transparent,
        )
        with Image.open(tmp_path / "reference.png") as image:
            expected = np.asarray(image.convert("RGBA"))

        # The tight bbox is the 1.8 x 1.2 inch axes plus 0.1 inch padding per side.
        expected_size = (200, 140) if tight_transparent else (300, 200)
        assert actual.shape[1::-1] == pytest.approx(expected_size, abs=1)
        assert actual[0, 0, 3] == (0 if tight_transparent else 255)
        if tight_transparent:
            # The rasterized collection's gap must retain its transparency mask.
            assert actual[40, 100, 3] == 0

        for channel in (0, 2):

            def colored(pixels: np.ndarray) -> np.ndarray:
                rgb = pixels[:, :, :3].astype(int)
                others = np.delete(rgb, channel, axis=2).max(axis=2)
                return (rgb[:, :, channel] - others > 80) & (pixels[:, :, 3] > 90)

            actual_mask, expected_mask = colored(actual), colored(expected)
            _assert_region(actual_mask, expected_mask)
            expected_alpha = 128 if channel == 0 and tight_transparent else 255
            assert np.median(actual[:, :, 3][actual_mask]) == pytest.approx(
                expected_alpha, abs=2
            )

        final = tmp_path / ("final.pdf" if mode == "pdf" else "final.svg")
        content = final.read_bytes()
        assert (b"/Subtype /Image" if mode == "pdf" else b"<image") in content


@pytest.mark.parametrize("mode", ["pdf", "svg", "svg-missing", "svg-failed"])
def test_exported_multipanel_helper_axes_keep_their_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutool: str,
    mode: str,
) -> None:
    with (
        plt.rc_context(),
        cns.settings.context(figure_dpi=100, font_sans_serif=("DejaVu Sans",)),
        _artifacts(tmp_path, f"multipanel-{mode}"),
    ):
        mp = cns.multipanel(max_width=360)
        ax = mp.panel("A", width=100, height=80, margin_right=30)
        assert mp.fig is not None
        ax.imshow([[0, 1], [0, 1]], cmap=ListedColormap(["red", "blue"]), aspect="auto")
        ax.set(xticks=[], yticks=[])
        cax = make_axes_locatable(ax).append_axes("right", size="12%", pad=0.05)
        mp.fig.colorbar(
            ScalarMappable(cmap=ListedColormap(["lime", "magenta"])), cax=cax
        )
        cax.set_yticks([])
        inset = ax.inset_axes((0.15, 0.2, 0.25, 0.3))
        inset.set(xticks=[], yticks=[])
        inset.set_facecolor("cyan")
        second = mp.panel("B", width=90, height=80)
        second.set(xticks=[], yticks=[])
        second.set_facecolor("orange")
        mp.fig.canvas.draw()
        mp.fig.canvas.draw()

        actual = _export_and_render(
            mp.fig, tmp_path, mode, mutool, monkeypatch, bbox="tight"
        )
        with Image.open(tmp_path / "reference.png") as image:
            expected = np.asarray(image.convert("RGBA"))
        assert actual.shape[:2] == pytest.approx(expected.shape[:2], abs=1)
        for color in (
            (255, 0, 0),
            (0, 0, 255),
            (0, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
            (255, 165, 0),
        ):
            actual_mask = (
                np.max(np.abs(actual[:, :, :3].astype(int) - color), axis=2) < 25
            )
            expected_mask = (
                np.max(np.abs(expected[:, :, :3].astype(int) - color), axis=2) < 25
            )
            _assert_region(actual_mask, expected_mask)


@pytest.mark.parametrize("mode", ["pdf", "svg", "svg-missing", "svg-failed"])
def test_exported_repeated_text_keeps_distinct_font_weights(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutool: str,
    mode: str,
) -> None:
    with (
        plt.rc_context(
            {"pdf.fonttype": 42, "svg.fonttype": "none", "savefig.bbox": None}
        ),
        _artifacts(tmp_path, f"text-{mode}"),
    ):
        fig = plt.figure(figsize=(2.5, 2), dpi=100)
        for index, (family, weight) in enumerate(
            [
                (family, weight)
                for family in ("DejaVu Sans", "DejaVu Serif")
                for weight in ("normal", "bold")
            ]
        ):
            fig.text(
                0.1,
                0.875 - index * 0.25,
                "SAME",
                va="center",
                fontsize=18,
                family=family,
                weight=weight,
            )
        actual = _export_and_render(fig, tmp_path, mode, mutool, monkeypatch)
        # Integrate ink rather than comparing glyph pixels across font renderers.
        ink = (255 - actual[:, :, :3].mean(axis=2)) / 255
        row_ink = [region.sum() for region in np.array_split(ink, 4)]
        assert all(amount > 100 for amount in row_ink)
        assert row_ink[1] > row_ink[0] * 1.1
        assert row_ink[3] > row_ink[2] * 1.1
