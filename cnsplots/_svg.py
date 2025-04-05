import os
import re
import shutil
import subprocess

import matplotlib.pyplot as plt
from lxml import etree


def _save_svg(filepath, root):
    tmp_pdf = f"/tmp/{os.path.basename(root)}.pdf"
    tmp_dir = "/tmp/mutool_output"
    os.makedirs(tmp_dir, exist_ok=True)
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
                os.path.join(tmp_dir, "%d.svg"),
                tmp_pdf,
            ],
            check=True,
        )
        tmp_svg = os.path.join(tmp_dir, "1.svg")
        _correct_svg(tmp_svg, filepath)
    except subprocess.CalledProcessError as e:
        print(f"Error during SVG conversion: {e}")
    finally:
        if os.path.exists(tmp_pdf):
            os.remove(tmp_pdf)
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)


def _correct_svg(input_file, output_file):
    """
    Process an SVG file to ungroup both text elements and clipped elements.

    Args:
        input_file (str): Path to the input SVG file
        output_file (str): Path to save the processed SVG file
    """
    # Read the SVG file
    with open(input_file, "r") as f:
        svg_content = f.read()

    # Step 1: First handle clip paths directly in the content
    # Remove clip-path attributes from g elements but preserve the g tags initially
    svg_content = re.sub(r'clip-path="[^"]+"', "", svg_content)

    # Remove all clipPath definitions
    svg_content = re.sub(
        r"<clipPath[^>]*>.*?</clipPath>", "", svg_content, flags=re.DOTALL
    )

    # Parse the modified SVG with lxml
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(svg_content.encode("utf-8"), parser)

    # Define SVG namespace
    ns = {"svg": "http://www.w3.org/2000/svg"}

    # Process text elements
    _process_text_elements_lxml(root, ns)

    # Flatten any remaining g elements
    _flatten_groups(root, ns)

    # Create an ElementTree from the root element
    tree = etree.ElementTree(root)

    # Write the modified SVG to output file
    tree.write(output_file, encoding="utf-8", xml_declaration=True, pretty_print=True)


def _process_text_elements_lxml(root, ns):
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


def _flatten_groups(root, ns):
    """Flatten all group elements by moving their children to parent."""
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

            # Get index of g in parent
            g_index = parent.index(g)

            # Move all children of g to parent
            children = list(g)
            for child in children:
                g.remove(child)
                parent.insert(g_index, child)
                g_index += 1

            # Remove empty g element
            parent.remove(g)
            flattened = True
            break  # Break after flattening one g to avoid modifying during iteration

        if not flattened:
            break  # Exit if no more g elements were flattened
