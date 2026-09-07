from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from lxml import etree  # ty: ignore[unresolved-import]
from matplotlib import font_manager as fm

import cnsplots as cns
from cnsplots import _setup


@pytest.mark.parametrize("format", ["png", "pdf", "svg"])
def test_portable_plot_exports_with_font_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, format: str
) -> None:
    # Exercise a real failed executable lookup even on hosts with mutool installed.
    monkeypatch.setenv("PATH", str(tmp_path))
    before_rc = mpl.rcParams.copy()
    before_settings = repr(cns.settings)
    with cns.settings.context(
        font_family="sans-serif",
        font_sans_serif=("Cnsplots Missing Smoke Font", "DejaVu Sans"),
        svg_fonttype="none",
        pdf_fonttype=42,
    ):
        fig = cns.figure(width=216, height=144)
        data = pd.DataFrame({"x": [0, 1, 2], "y": [0, 2, 1]})
        ax = cns.scatterplot(data=data, x="x", y="y")
        ax.plot(data["x"], data["y"], label="Series")
        ax.set_title("Portable export")
        ax.legend()
        assert ax.figure is fig
        np.testing.assert_array_equal(ax.collections[0].get_offsets(), data.values)
        for weight in ("normal", "bold"):
            resolved = fm.findfont(
                fm.FontProperties(family="sans-serif", weight=weight),
                fallback_to_default=False,
            )
            assert Path(resolved).is_file()
            assert fm.FontProperties(fname=resolved).get_name() == "DejaVu Sans"

        path = tmp_path / f"portable.{format}"
        if format == "svg":
            with pytest.warns(
                RuntimeWarning,
                match="mutool.*unavailable; saved a standard matplotlib SVG",
            ) as warnings:
                cns.savefig(path, fig=fig, dpi=96, bbox_inches=None)
            assert len(warnings) == 1
        else:
            cns.savefig(path, fig=fig, dpi=96, bbox_inches=None)

        if format == "png":
            pixels = plt.imread(path)
            assert pixels.shape == (192, 288, 4)
            assert np.any(pixels[:, :, 3] > 0)
            assert np.any(pixels[:, :, :3] < 0.5)
        elif format == "pdf":
            content = path.read_bytes()
            assert content.startswith(b"%PDF-")
            assert b"%%EOF" in content
            media_box = re.search(rb"/MediaBox\s*\[([^]]+)\]", content)
            assert media_box is not None
            assert [float(value) for value in media_box[1].split()] == [0, 0, 216, 144]
            assert b"/FontFile2" in content
        else:
            root = etree.parse(str(path)).getroot()
            assert root.tag == "{http://www.w3.org/2000/svg}svg"
            assert [float(value) for value in root.get("viewBox").split()] == [
                0,
                0,
                216,
                144,
            ]
            texts = root.xpath(
                "//svg:text", namespaces={"svg": "http://www.w3.org/2000/svg"}
            )
            labels = ["".join(text.itertext()) for text in texts]
            assert "Portable export" in labels
            assert "Series" in labels
            assert root.xpath(
                "//svg:path", namespaces={"svg": "http://www.w3.org/2000/svg"}
            )

    assert mpl.rcParams == before_rc
    assert repr(cns.settings) == before_settings


@pytest.mark.skipif(
    sys.platform != "darwin"
    or not Path("/System/Library/Fonts/Helvetica.ttc").is_file(),
    reason="Native macOS Helvetica collection is unavailable",
)
def test_native_macos_helvetica_extraction_uses_xdg_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache_home = tmp_path / "fresh-cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    manager = fm.FontManager()
    manager.ttflist = [
        font
        for font in manager.ttflist
        if not (font.name == "Helvetica" and int(font.weight) >= 700)
    ]
    monkeypatch.setattr(fm, "fontManager", manager)
    monkeypatch.setattr(_setup, "_HELVETICA_BOLD_REGISTERED", False)

    with cns.settings.context():
        cns.setup_matplotlib()
        cached_font = cache_home / "cnsplots" / "fonts" / "Helvetica-Bold.ttf"
        assert cached_font.is_file()
        resolved = manager.findfont(
            fm.FontProperties(family="Helvetica", weight="bold"),
            fallback_to_default=False,
        )
        assert Path(resolved).resolve() == cached_font.resolve()
        assert fm.FontProperties(fname=resolved).get_name() == "Helvetica"
        assert _setup._HELVETICA_BOLD_REGISTERED
