from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import numpy as np
import pytest
from matplotlib.typing import ColorType

import cnsplots as cns
from cnsplots import _utils


@pytest.mark.parametrize("indices", [[0], (2, 0, 2, -1), range(3), []])
@pytest.mark.parametrize(
    "palette",
    [None, "Set1", "Ecotyper2", ["red", (0, 1, 0), "#0000ff"]],
)
def test_palette_color_names_are_compatible(
    indices: Sequence[int], palette: str | Sequence[ColorType] | None
) -> None:
    expected = cns.get_palette_colors(indices=indices, palette=palette)

    assert cns.get_hexcolors_from_apalette(indices, palette) == expected
    assert cns.get_hexcolors_from_apalette(alist=indices, palette=palette) == expected


def test_palette_color_selection_preserves_colors_and_index_order() -> None:
    assert cns.get_palette_colors([0]) == ["#e41a1c"]
    assert cns.get_hexcolors_from_apalette(alist=[0]) == ["#e41a1c"]
    assert cns.get_palette_colors([2, 0, 2, -1], "Ecotyper2") == [
        "#b5d33d",
        "#eb7d5b",
        "#b5d33d",
        "#442288",
    ]
    assert cns.get_palette_colors([2, 0, 1], ["red", (0, 1, 0), (0, 0, 1, 0.5)]) == [
        "#0000ff",
        "#ff0000",
        "#00ff00",
    ]


def test_palette_color_selection_accepts_numpy_indices() -> None:
    indices = cast(Sequence[int], np.array([0, 1, -1]))
    expected = ["#e41a1c", "#377eb8", "#999999"]

    assert cns.get_palette_colors(indices) == expected
    assert cns.get_hexcolors_from_apalette(indices) == expected


@pytest.mark.parametrize("indices", [[3], [-4]])
def test_palette_color_selection_preserves_index_errors(indices: list[int]) -> None:
    for select in (cns.get_palette_colors, cns.get_hexcolors_from_apalette):
        with pytest.raises(IndexError):
            select(indices, ["red", "green", "blue"])


def test_palette_color_selection_preserves_unknown_name_error() -> None:
    for select in (cns.get_palette_colors, cns.get_hexcolors_from_apalette):
        with pytest.raises(RuntimeError, match="Wrong Choice!"):
            select([0], "not-a-palette")


def test_palette_color_default_resolves_on_each_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested: list[str] = []
    colors = ["red"]

    def resolve(name: str) -> list[str]:
        requested.append(name)
        return colors

    monkeypatch.setattr(_utils, "palettes", resolve)

    assert cns.get_palette_colors([0]) == ["#ff0000"]
    colors[0] = "blue"
    assert cns.get_hexcolors_from_apalette([0]) == ["#0000ff"]
    assert requested == ["Set1", "Set1"]


def test_palette_color_result_is_independent() -> None:
    selected = cns.get_palette_colors([0])
    selected[0] = "#000000"

    assert cns.get_palette_colors([0]) == ["#e41a1c"]
    assert cns.get_hexcolors_from_apalette([0]) == ["#e41a1c"]
