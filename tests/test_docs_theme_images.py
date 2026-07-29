import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sphinx_gallery.scrapers import ImagePathIterator

sys.path.insert(0, str(Path(__file__).parents[1] / "docs" / "_ext"))

from theme_aware_matplotlib import (  # noqa: E402  # ty: ignore[unresolved-import]
    _dark_figure,
    _dark_path,
    _mark_theme,
    theme_aware_matplotlib_scraper,
)


def test_dark_figure_changes_only_neutral_foreground():
    fig, ax = plt.subplots()
    black_line = ax.plot([0, 1], color="black")[0]
    color_line = ax.plot([1, 0], color="#d62728")[0]
    ax.set_title("Example")
    image = ax.imshow(np.array([[[0.0, 0.2, 0.8]]]))

    title_color = ax.title.get_color()
    black_line_color = black_line.get_color()
    canvas_color = ax.patch.get_facecolor()
    image_array = image.get_array()
    assert image_array is not None
    image_data = image_array.copy()

    with _dark_figure(fig):
        assert ax.title.get_color() != title_color
        assert black_line.get_color() != black_line_color
        assert color_line.get_color() == "#d62728"
        assert ax.patch.get_facecolor() == canvas_color
        np.testing.assert_array_equal(image.get_array(), image_data)

    assert ax.title.get_color() == title_color
    assert black_line.get_color() == black_line_color
    assert color_line.get_color() == "#d62728"
    assert ax.patch.get_facecolor() == canvas_color


def test_dark_path_preserves_srcset_suffix():
    light_path = Path("sphx_glr_example_001_2_00x.png")

    assert _dark_path(light_path) == Path("sphx_glr_example_001_2_00x_dark.png")


def test_mark_theme_wraps_single_images_and_horizontal_lists():
    single_image = ":class: sphx-glr-single-img\n"
    horizontal_list = ".. rst-class:: sphx-glr-horizontal\n"

    assert _mark_theme(single_image, "dark") == (
        "\n.. container:: only-dark\n\n   :class: sphx-glr-single-img\n"
    )
    assert _mark_theme(horizontal_list, "light") == (
        "\n.. container:: only-light\n\n   .. rst-class:: sphx-glr-horizontal\n"
    )


def test_scraper_generates_theme_specific_images_and_markup(tmp_path):
    plt.figure()
    plt.plot([0, 1], color="black")
    plt.title("Theme test")
    image_paths = ImagePathIterator(str(tmp_path / "sphx_glr_test_{0:03}.png"))

    rst = theme_aware_matplotlib_scraper(
        None,
        {
            "image_path_iterator": image_paths,
            "example_globals": {},
            "multi_image": None,
            "file_conf": {},
        },
        {
            "image_srcset": [2.0],
            "matplotlib_animations": (False, None),
            "compress_images": (),
            "compress_images_args": (),
            "src_dir": str(tmp_path),
        },
    )

    expected_images = {
        "sphx_glr_test_001.png",
        "sphx_glr_test_001_2_00x.png",
        "sphx_glr_test_001_dark.png",
        "sphx_glr_test_001_2_00x_dark.png",
    }
    assert {path.name for path in tmp_path.glob("*.png")} == expected_images
    assert ".. container:: only-light" in rst
    assert ".. container:: only-dark" in rst
    assert "/sphx_glr_test_001_dark.png" in rst
    assert "/sphx_glr_test_001_2_00x_dark.png 2.00x" in rst
