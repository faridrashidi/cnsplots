"""Generate light and dark variants of Sphinx-Gallery Matplotlib figures."""

from __future__ import annotations

import copy
from contextlib import contextmanager
from pathlib import Path
from textwrap import indent
from typing import Iterator

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from docutils import nodes
from matplotlib.collections import Collection
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text
from sphinx_gallery.scrapers import matplotlib_scraper
from sphinx_gallery.utils import scale_image

_DARK_FOREGROUND = mcolors.to_rgba("#e6e6e6")[:3]
_DARK_BACKGROUND = mcolors.to_rgba("#202124")[:3]


def _map_neutral_color(value, *, light_background: bool = False):
    """Map neutral colors for a dark canvas without changing data colors."""
    if isinstance(value, np.ndarray) and value.ndim > 1:
        mapped = value.copy()
        changed = False
        for index, color in enumerate(value):
            mapped_color, color_changed = _map_neutral_color(
                color, light_background=light_background
            )
            if color_changed:
                mapped[index] = mapped_color
                changed = True
        return mapped, changed

    try:
        red, green, blue, alpha = mcolors.to_rgba(value)
    except (TypeError, ValueError):
        return value, False

    if alpha == 0 or max(red, green, blue) - min(red, green, blue) > 0.03:
        return value, False

    if light_background and min(red, green, blue) >= 0.85:
        return (*_DARK_BACKGROUND, alpha), True
    if max(red, green, blue) <= 0.3:
        return (*_DARK_FOREGROUND, alpha), True
    return value, False


def _replace_color(changes, artist, getter_name, setter_name, **kwargs) -> None:
    """Replace one artist color and record enough state to restore it."""
    getter = getattr(artist, getter_name)
    setter = getattr(artist, setter_name)
    old_value = copy.deepcopy(getter())
    new_value, changed = _map_neutral_color(old_value, **kwargs)
    if changed:
        setter(new_value)
        changes.append((setter, old_value))


@contextmanager
def _dark_figure(fig: Figure) -> Iterator[None]:
    """Temporarily adapt a figure's neutral foreground for a dark page."""
    changes = []
    canvas_patches = {fig.patch, *(ax.patch for ax in fig.axes)}
    text_bbox_patches = {
        bbox
        for artist in fig.findobj(match=Text)
        if (bbox := artist.get_bbox_patch()) is not None
    }

    for artist in fig.findobj():
        if isinstance(artist, Text):
            _replace_color(changes, artist, "get_color", "set_color")
            bbox = artist.get_bbox_patch()
            if bbox is not None:
                _replace_color(
                    changes,
                    bbox,
                    "get_facecolor",
                    "set_facecolor",
                    light_background=True,
                )
        elif isinstance(artist, Line2D):
            _replace_color(changes, artist, "get_color", "set_color")
            _replace_color(
                changes, artist, "get_markerfacecolor", "set_markerfacecolor"
            )
            _replace_color(
                changes, artist, "get_markeredgecolor", "set_markeredgecolor"
            )
        elif isinstance(artist, Patch):
            if artist not in canvas_patches and artist not in text_bbox_patches:
                _replace_color(changes, artist, "get_facecolor", "set_facecolor")
            _replace_color(changes, artist, "get_edgecolor", "set_edgecolor")
        elif isinstance(artist, Collection):
            _replace_color(changes, artist, "get_facecolor", "set_facecolor")
            _replace_color(changes, artist, "get_edgecolor", "set_edgecolor")

    try:
        yield
    finally:
        for setter, old_value in reversed(changes):
            setter(old_value)


def _dark_path(light_path: Path) -> Path:
    """Return the dark companion path for a gallery image."""
    return light_path.with_name(f"{light_path.stem}_dark{light_path.suffix}")


def _savefig_kwargs(fig: Figure) -> dict[str, object]:
    """Mirror Sphinx-Gallery's handling of explicit figure colors."""
    kwargs: dict[str, object] = {}
    for attribute in ("facecolor", "edgecolor"):
        figure_color = getattr(fig, f"get_{attribute}")()
        default_color = mpl.rcParams[f"figure.{attribute}"]
        if mcolors.to_rgba(figure_color) != mcolors.to_rgba(default_color):
            kwargs[attribute] = figure_color
    return kwargs


def _save_dark_companions(
    figures: list[Figure], light_paths: list[Path], srcset: list[float]
) -> dict[str, str]:
    """Save dark figures and return light-to-dark filename replacements."""
    replacements: dict[str, str] = {}

    for fig, light_path in zip(figures, light_paths, strict=True):
        kwargs = _savefig_kwargs(fig)
        dpi = kwargs.get("dpi", mpl.rcParams["savefig.dpi"])
        if dpi == "figure":
            dpi = fig.dpi

        with _dark_figure(fig):
            dark_path = _dark_path(light_path)
            fig.savefig(dark_path, **kwargs)
            replacements[light_path.name] = dark_path.name

            for multiplier in srcset:
                suffix = f"{multiplier:.2f}".replace(".", "_")
                light_srcset = light_path.with_name(
                    f"{light_path.stem}_{suffix}x{light_path.suffix}"
                )
                dark_srcset = _dark_path(light_srcset)
                fig.savefig(dark_srcset, dpi=multiplier * dpi, **kwargs)
                replacements[light_srcset.name] = dark_srcset.name

    return replacements


def _mark_theme(rst: str, theme: str) -> str:
    """Wrap gallery markup in a container recognized by Furo's theme switcher."""
    return f"\n.. container:: only-{theme}\n\n{indent(rst, '   ')}"


def _prepare_dark_gallery_thumbnails(
    gallery_dir: Path, thumbnail_size: tuple[int, int]
) -> None:
    """Create dark companions for generated gallery thumbnails."""
    image_dir = gallery_dir / "images"
    thumbnail_dir = image_dir / "thumb"
    if not thumbnail_dir.exists():
        return

    for light_thumbnail in thumbnail_dir.glob("sphx_glr_*_thumb.png"):
        example_name = light_thumbnail.stem.removeprefix("sphx_glr_").removesuffix(
            "_thumb"
        )
        dark_source = image_dir / f"sphx_glr_{example_name}_001_dark.png"
        if not dark_source.exists():
            continue

        dark_thumbnail = _dark_path(light_thumbnail)
        scale_image(
            str(dark_source),
            str(dark_thumbnail),
            *thumbnail_size,
        )


def prepare_dark_gallery_thumbnails(app, env, docnames) -> None:
    """Prepare dark thumbnails after Sphinx-Gallery generates sources."""
    del env, docnames

    gallery_dir = Path(app.srcdir) / "examples"
    thumbnail_size = tuple(app.config.sphinx_gallery_conf["thumbnail_size"])
    _prepare_dark_gallery_thumbnails(gallery_dir, thumbnail_size)


def theme_gallery_thumbnail_nodes(app, doctree) -> None:
    """Add theme-aware variants to gallery and API minigallery thumbnails."""
    for image in list(doctree.findall(nodes.image)):
        light_uri = Path(image["uri"])
        if not (
            light_uri.name.startswith("sphx_glr_")
            and light_uri.name.endswith("_thumb.png")
        ):
            continue

        dark_uri = _dark_path(light_uri)
        dark_source = Path(app.srcdir) / str(dark_uri).lstrip("/")
        if not dark_source.exists():
            continue

        light_container = nodes.container(classes=["only-light"])
        light_container += image.deepcopy()
        dark_image = image.deepcopy()
        dark_image["uri"] = dark_uri.as_posix()
        dark_container = nodes.container(classes=["only-dark"])
        dark_container += dark_image
        image.replace_self([light_container, dark_container])


def theme_aware_matplotlib_scraper(block, block_vars, gallery_conf) -> str:
    """Render transparent Matplotlib figures for both documentation themes."""
    image_paths = block_vars["image_path_iterator"]
    previous_count = len(image_paths)
    figures = [plt.figure(number) for number in plt.get_fignums()]

    light_rst = matplotlib_scraper(block, block_vars, gallery_conf)
    new_paths = [Path(path) for path in image_paths.paths[previous_count:]]
    if not light_rst or len(figures) != len(new_paths):
        return light_rst

    replacements = _save_dark_companions(
        figures, new_paths, gallery_conf["image_srcset"]
    )
    dark_rst = light_rst
    for light_name, dark_name in replacements.items():
        dark_rst = dark_rst.replace(light_name, dark_name)

    return _mark_theme(light_rst, "light") + _mark_theme(dark_rst, "dark")
