from __future__ import annotations

import shutil
import subprocess
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pytest
from lxml import etree  # ty: ignore[unresolved-import]

import cnsplots as cns
from cnsplots import _svg


@pytest.mark.parametrize("converter", ["mutool", "missing", "failed"])
def test_svg_export_preserves_repeated_label_styles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, converter: str
) -> None:
    if converter == "mutool" and shutil.which("mutool") is None:
        pytest.skip("MuPDF's mutool is required for the conversion regression")

    def unavailable_mutool(*args: object, **kwargs: object) -> None:
        if converter == "missing":
            raise FileNotFoundError("mutool")
        raise subprocess.CalledProcessError(1, ["mutool"], stderr=b"conversion failed")

    if converter != "mutool":
        monkeypatch.setattr(_svg.subprocess, "run", unavailable_mutool)

    styles = [
        ("normal", "normal"),
        ("bold", "normal"),
        ("normal", "italic"),
        ("bold", "italic"),
    ]
    with plt.rc_context(
        {"font.family": "DejaVu Sans", "pdf.fonttype": 42, "svg.fonttype": "none"}
    ):
        fig, axes = plt.subplots(2, 2, figsize=(8, 6))
        for ax, (weight, style) in zip(axes.flat, styles):
            properties = {"weight": weight, "style": style}
            position = ax.get_position()
            fig.text(position.x0, position.y0, "Panel", fontdict=properties)
            ax.set_title("Title", **properties)
            ax.set_xlabel("Axis", **properties)
            ax.set_ylabel("Axis", **properties)
            ax.set_xticks([0.5], ["Tick"], **properties)
            ax.set_yticks([])
            ax.text(0.2, 0.3, "SAME\nLINE", **properties)
            ax.plot([0, 1], [0, 1], label="Legend")
            ax.legend(prop=properties)

        path = tmp_path / "weights.svg"
        if converter == "mutool":
            cns.savefig(path)
        else:
            with pytest.warns(RuntimeWarning, match="mutool"):
                cns.savefig(path)

    root = etree.parse(str(path))
    ns = {"svg": "http://www.w3.org/2000/svg"}
    texts = root.xpath("//svg:text", namespaces=ns)
    for label in ("Panel", "Title", "Axis", "Tick", "Legend", "SAME", "LINE"):
        actual = []
        for text in texts:
            if "".join(text.itertext()) != label:
                continue
            attributes = dict(text.attrib)
            for declaration in text.get("style", "").split(";"):
                if ":" in declaration:
                    name, value = declaration.split(":", 1)
                    attributes[name.strip()] = value.strip()
            weight = attributes.get("font-weight", "normal")
            actual.append(
                (
                    "bold" if weight in ("bold", "700") else weight,
                    attributes.get("font-style", "normal"),
                )
            )
        assert Counter(actual) == Counter(styles * (2 if label == "Axis" else 1)), label


def test_svg_normalizes_each_repeated_labels_pdf_font(tmp_path: Path) -> None:
    source = tmp_path / "source.svg"
    destination = tmp_path / "normalized.svg"
    source.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<text font-family="ABCDEF+Helvetica"><tspan>SAME</tspan></text>'
        '<text font-family="ABCDEF+Helvetica-Bold"><tspan>SAME</tspan></text>'
        '<text font-family="ABCDEF+Helvetica-Oblique"><tspan>SAME</tspan></text>'
        '<text font-family="ABCDEF+Helvetica-BoldOblique"><tspan>SAME</tspan></text>'
        "</svg>",
        encoding="utf-8",
    )

    _svg._correct_svg(str(source), str(destination))

    texts = etree.parse(str(destination)).xpath(
        "//svg:text", namespaces={"svg": "http://www.w3.org/2000/svg"}
    )
    assert [text.text for text in texts] == ["SAME"] * 4
    assert [text.get("font-family") for text in texts] == ["Helvetica"] * 4
    assert [
        (text.get("font-weight", "normal"), text.get("font-style", "normal"))
        for text in texts
    ] == [
        ("normal", "normal"),
        ("bold", "normal"),
        ("normal", "italic"),
        ("bold", "italic"),
    ]
