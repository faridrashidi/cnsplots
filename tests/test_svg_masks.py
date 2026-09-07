from pathlib import Path

from lxml import etree  # ty: ignore[unresolved-import]

from cnsplots import _svg


def test_svg_cleanup_preserves_nested_group_masks(tmp_path: Path) -> None:
    source = tmp_path / "source.svg"
    output = tmp_path / "output.svg"
    source.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<defs><mask id="outer"><rect width="100" height="100" fill="white"/>'
        '</mask><mask id="inner"><circle r="10" fill="white"/></mask></defs>'
        '<g transform="translate(10 20)"><g mask="url(#outer)">'
        '<rect width="20" height="20"/>'
        '<g mask="url(#inner)"><g transform="scale(2)">'
        '<image width="10" height="10"/>'
        "</g></g></g></g></svg>",
        encoding="utf-8",
    )

    _svg._correct_svg(str(source), str(output))

    root = etree.parse(str(output))
    ns = {"svg": "http://www.w3.org/2000/svg"}
    outer, inner = root.xpath("//svg:g", namespaces=ns)
    assert outer.get("mask") == "url(#outer)"
    assert outer.get("transform") == "translate(10 20)"
    assert inner.get("mask") == "url(#inner)"
    assert inner.getparent() is outer
    assert len(outer) == 2  # The outer mask still covers both siblings together.
    image = inner.find("svg:image", namespaces=ns)
    assert image is not None
    assert image.get("transform") == "scale(2)"
