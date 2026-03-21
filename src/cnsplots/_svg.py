from __future__ import annotations

import re
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lxml.etree import _Element

import subprocess

import matplotlib.pyplot as plt
from lxml import etree
from matplotlib.text import Text

_PDF_SUBSET_FONT_PREFIX = re.compile(r"^[A-Z]{6}\+")


def _collect_bold_texts() -> set[str]:
    """Collect text strings that are bold in the current matplotlib figure."""
    bold_texts: set[str] = set()
    fig = plt.gcf()
    text_artists = list(fig.texts)
    for ax in fig.get_axes():
        for artist in ax.get_children():
            if isinstance(artist, Text):
                text_artists.append(artist)

    for artist in text_artists:
        txt = artist.get_text().strip()
        if not txt:
            continue
        weight = artist.get_fontweight()
        if weight in ("bold", "heavy", "extra bold", "semibold", "demibold") or (
            isinstance(weight, (int, float)) and weight >= 600
        ):
            bold_texts.add(txt)
            for line in txt.split("\n"):
                line = line.strip()
                if line:
                    bold_texts.add(line)
    return bold_texts


def _save_plain_svg(filepath: str, message: str) -> None:
    """Save a standard matplotlib SVG and surface why the optimized path was skipped."""
    warnings.warn(message, RuntimeWarning, stacklevel=2)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.savefig(filepath, format="svg")


def _save_svg(filepath: str, root: str) -> None:
    bold_texts = _collect_bold_texts()
    stem = Path(root).name or Path(filepath).stem or "cnsplots"

    with TemporaryDirectory(prefix=f"{stem}-svg-") as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        tmp_pdf = tmp_dir_path / f"{stem}.pdf"
        tmp_svg = tmp_dir_path / "1.svg"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.savefig(tmp_pdf)
        try:
            subprocess.run(
                [
                    "mutool",
                    "convert",
                    "-F",
                    "svg",
                    "-O",
                    "text=text",
                    "-o",
                    str(tmp_dir_path / "%d.svg"),
                    str(tmp_pdf),
                ],
                check=True,
                capture_output=True,
            )
            _correct_svg(str(tmp_svg), filepath, bold_texts)
        except FileNotFoundError:
            _save_plain_svg(
                filepath,
                "MuPDF's `mutool` is unavailable; saved a standard matplotlib SVG instead.",
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or b"").decode(errors="replace").strip()
            detail = f" ({stderr})" if stderr else ""
            _save_plain_svg(
                filepath,
                "MuPDF's `mutool` failed during SVG conversion"
                f"{detail}; saved a standard matplotlib SVG instead.",
            )


def _correct_svg(
    input_file: str, output_file: str, bold_texts: set[str] | None = None
) -> None:
    """
    Process an SVG file to ungroup both text elements and clipped elements.

    Args:
        input_file (str): Path to the input SVG file
        output_file (str): Path to save the processed SVG file
        bold_texts (set[str] | None): Text strings that should have font-weight bold
    """
    # Read the SVG file
    with open(input_file) as f:
        svg_content = f.read()

    # note clip-path attributes and clipPath definitions are intentionally
    # preserved so that axes clipping (e.g. from set_xlim / set_ylim) is
    # rendered correctly.  The _flatten_groups helper propagates clip-path
    # from parent <g> elements to their children when groups are dissolved.

    # Parse the modified SVG with lxml
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(svg_content.encode("utf-8"), parser)

    # Define SVG namespace
    ns = {"svg": "http://www.w3.org/2000/svg"}

    # Process text elements
    _process_text_elements_lxml(root, ns)

    # Restore bold font-weight lost during PDF→SVG conversion
    _restore_bold_fonts(root, ns, bold_texts or set())

    # Normalize PDF subset font names for better SVG editor compatibility
    _normalize_text_fonts(root, ns)

    # Flatten any remaining g elements
    _flatten_groups(root, ns)

    # Create an ElementTree from the root element
    tree = etree.ElementTree(root)

    # Write the modified SVG to output file
    tree.write(output_file, encoding="utf-8", xml_declaration=True, pretty_print=True)


def _process_text_elements_lxml(root: _Element, ns: dict[str, str]) -> None:
    """Process text elements to ungroup them using lxml."""
    # Find all text elements with tspan children
    text_elements = root.xpath(".//svg:text[svg:tspan]", namespaces=ns)

    for text in text_elements:
        # Find parent of text element
        parent = text.getparent()
        if parent is None:
            continue

        # Find all tspan elements within this text
        tspans = text.xpath("./svg:tspan", namespaces=ns)

        for tspan in tspans:
            # Create a new text element
            new_text = etree.Element("{http://www.w3.org/2000/svg}text")

            # Copy attributes from original text element
            for attr, value in text.attrib.items():
                new_text.set(attr, value)

            # Copy content and attributes from tspan
            new_text.text = tspan.text
            for attr, value in tspan.attrib.items():
                new_text.set(attr, value)

            # Add the new text element before the original
            parent.insert(parent.index(text), new_text)

        # Remove the original text element
        parent.remove(text)


def _restore_bold_fonts(
    root: _Element, ns: dict[str, str], bold_texts: set[str]
) -> None:
    """Restore font-weight="bold" on text elements whose content was bold in matplotlib.

    Mutool drops bold information during PDF→SVG conversion, so we match text
    content against the set collected from matplotlib before saving.
    """
    if not bold_texts:
        return

    for text_el in root.xpath(".//svg:text", namespaces=ns):
        content = (text_el.text or "").strip()
        if content in bold_texts:
            text_el.set("font-weight", "bold")


def _normalize_pdf_font_family(
    font_family: str,
) -> tuple[str, str | None, str | None]:
    """Convert PDF subset font names into SVG-friendly family/style attributes."""
    normalized_family = _PDF_SUBSET_FONT_PREFIX.sub("", font_family).strip()
    font_weight = None
    font_style = None

    for suffix, weight, style in (
        ("-BoldOblique", "bold", "italic"),
        ("-BoldItalic", "bold", "italic"),
        ("-Bold", "bold", None),
        ("-Oblique", None, "italic"),
        ("-Italic", None, "italic"),
    ):
        if normalized_family.endswith(suffix):
            normalized_family = normalized_family[: -len(suffix)] or normalized_family
            font_weight = weight
            font_style = style
            break

    return normalized_family, font_weight, font_style


def _normalize_text_fonts(root: _Element, ns: dict[str, str]) -> None:
    """Normalize subsetted PDF font names for broader SVG editor compatibility."""
    for text_el in root.xpath(".//svg:text", namespaces=ns):
        font_family = text_el.get("font-family")
        if not font_family:
            continue

        normalized_family, font_weight, font_style = _normalize_pdf_font_family(
            font_family
        )
        text_el.set("font-family", normalized_family)
        if font_weight is not None:
            text_el.set("font-weight", font_weight)
        if font_style is not None:
            text_el.set("font-style", font_style)


def _prepend_transform(
    parent_transform: str | None, child_transform: str | None
) -> str | None:
    """Compose SVG transforms so parent group transforms remain in effect."""
    parent_transform = (
        None if parent_transform is None else parent_transform.strip() or None
    )
    child_transform = (
        None if child_transform is None else child_transform.strip() or None
    )

    if parent_transform is None:
        return child_transform
    if child_transform is None:
        return parent_transform
    return f"{parent_transform} {child_transform}"


def _flatten_groups(root: _Element, ns: dict[str, str]) -> None:
    """Flatten all group elements by moving their children to parent.

    When a ``<g>`` carries a ``clip-path`` or ``transform`` attribute the
    attribute is propagated to each child element so that clipping and
    positioning remain preserved after the group is removed.
    """
    # Iteratively flatten groups until no more flattening occurs
    while True:
        # Find g elements
        g_elements = root.xpath("//svg:g", namespaces=ns)

        if not g_elements:
            break

        flattened = False
        for g in g_elements:
            parent = g.getparent()
            if parent is None:
                continue

            clip_path = g.get("clip-path")
            transform = g.get("transform")

            # Get index of g in parent
            g_index = parent.index(g)

            # Move all children of g to parent
            children = list(g)
            for child in children:
                # Propagate clip-path from the group to children that
                # don't already have their own clip-path.
                if clip_path is not None and child.get("clip-path") is None:
                    child.set("clip-path", clip_path)
                child_transform = _prepend_transform(transform, child.get("transform"))
                if child_transform is not None:
                    child.set("transform", child_transform)
                g.remove(child)
                parent.insert(g_index, child)
                g_index += 1

            # Remove empty g element
            parent.remove(g)
            flattened = True
            break  # Break after flattening one g to avoid modifying during iteration

        if not flattened:
            break  # Exit if no more g elements were flattened
