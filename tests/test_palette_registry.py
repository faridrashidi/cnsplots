from __future__ import annotations

from collections.abc import Sequence
import hashlib
import subprocess
import sys
from typing import Any, cast, get_args

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pytest
import seaborn as sns
from matplotlib.colors import Colormap, LinearSegmentedColormap
from matplotlib.typing import ColorType

import cnsplots as cns
from cnsplots import _palettes, _utils


# Captured from main before replacing palette dispatch with the registry.
_QUALITATIVE_COLORS = {
    "Set1": "#e41a1c #377eb8 #4daf4a #984ea3 #ff7f00 #ffff33 #a65628 #f781bf #999999",
    "Set2": "#66c2a5 #fc8d62 #8da0cb #e78ac3 #a6d854 #ffd92f #e5c494 #b3b3b3",
    "Set3": "#8dd3c7 #ffffb3 #bebada #fb8072 #80b1d3 #fdb462 #b3de69 #fccde5 #d9d9d9 #bc80bd #ccebc5 #ffed6f",
    "Pastel1": "#fbb4ae #b3cde3 #ccebc5 #decbe4 #fed9a6 #ffffcc #e5d8bd #fddaec #f2f2f2",
    "Pastel2": "#b3e2cd #fdcdac #cbd5e8 #f4cae4 #e6f5c9 #fff2ae #f1e2cc #cccccc",
    "Paired": "#a6cee3 #1f78b4 #b2df8a #33a02c #fb9a99 #e31a1c #fdbf6f #ff7f00 #cab2d6 #6a3d9a #ffff99 #b15928",
    "Dark2": "#1b9e77 #d95f02 #7570b3 #e7298a #66a61e #e6ab02 #a6761d #666666",
    "Accent": "#7fc97f #beaed4 #fdc086 #ffff99 #386cb0 #f0027f #bf5b17 #666666",
    "Tableau": "#1f77b4 #ff7f0e #2ca02c #d62728 #9467bd #8c564b #e377c2 #7f7f7f #bcbd22 #17becf",
    "Bold": "#7f3c8d #11a579 #3969ac #f2b701 #e73f74 #80ba5a #e68310 #008695 #cf1c90 #f97b72",
    "BlueRed": "#2c69b0 #f02720 #ac613c #6ba3d6 #ea6b73 #e9c39b",
    "Cell": "#c84c3a #2f7e8f #e1a22e #4e5a8a #5f9862 #d07a6a #8b6fa8 #7b8c9e #b85f7a #6b6b6b",
    "Nature": "#e64b35 #4dbbd5 #00a087 #3c5488 #f39b7f #8491b4 #91d1c2 #dc0000 #7e6148 #b09c85",
    "Science": "#3b4992 #ee0000 #008b45 #631879 #008280 #bb0021 #5f559b #a20056 #808180 #1b1919",
    "Lancet": "#00468b #ed0000 #42b540 #0099b4 #925e9f #fdaf91 #ad002a #adb6b6 #1b1919",
    "NEJM": "#bc3c29 #0072b5 #e18727 #20854e #7876b1 #6f99ad #ffdc91 #ee4c97",
    "JAMA": "#374e55 #df8f44 #00a1d5 #b24745 #79af97 #6a6599 #80796b",
    "JCO": "#0073c2 #efc000 #868686 #cd534c #7aa6dc #003c67 #8f7700 #3b3b3b #a73030 #4a6990",
    "OkabeIto": "#e69f00 #56b4e9 #009e73 #f0e442 #0072b2 #d55e00 #cc79a7 #000000",
    "TolBright": "#4477aa #ee6677 #228833 #ccbb44 #66ccee #aa3377 #bbbbbb",
    "TolMuted": "#332288 #88ccee #44aa99 #117733 #999933 #ddcc77 #cc6677 #882255 #aa4499 #dddddd",
    "ECharts": "#5470c6 #91cc75 #fac858 #ee6666 #9a60b4 #73c0de #3ba272 #fc8452 #27727b #ea7ccc #d7504b #e87c25 #b5c334 #fe8463 #26c0c0 #f4e001",
    "Ecotyper1": "#d6372e #5189bb #70b460 #985ea8 #f08f35 #fadd4b #a3a3a3 #b7d3e5 #e6d8c2",
    "Ecotyper2": "#eb7d5b #fed23f #b5d33d #6ca2ea #442288",
    "Ecotyper3": "#d13570 #569ab4 #70ac58 #74509d #ed7e30 #f5c945 #9c5732 #e787e5",
    "Ecotyper4": "#386cb0 #fdb462 #7fc97f #ef3b2c #662506 #a6cee3 #fb9a99 #984ea3 #ffff33",
    "Ecotyper5": "#e41a71 #379db8 #5baf4a #7b4ea3 #ff7600 #ffc800 #a65328 #f781ec #999999 #a6dce3 #bbdf8a #fb9a99 #fdb96f #beb2d6 #1b9e5e #d95802 #707eb3 #e729d3 #e69f02 #8dd3b9 #fffab3 #babfda #fb7f72 #80c5d3 #fdae62 #bede69 #fccdf7",
    "Ecotyper6": "#fdc086 #386cb0 #f0027f #ffff99 #bf5b17 #7fc97f #add8e6 #beaed4 #66c2a5 #fc8d62 #8da0cb #e78ac3 #a6d854 #ffd92f #e5c494 #b3b3b3 #fbb4ae #b3cde3 #ccebc5 #decbe4 #fed9a6 #ffffcc #e5d8bd #fddaec",
}

# Digests cover every color in the full 256-entry LUT and its under/over/bad colors.
# Quantization ignores platform-level interpolation roundoff below 12 decimals.
_CONTINUOUS_DIGESTS = {
    "BuRd_custom": "4587995577590c256dfbcfb541675b616f3060bec4288a7997b68d3738182f53",
    "WhYlOrRd_custom": "5ff215821beb27b6c5ae0e98e8d3fdfe16d77852745d069380f2f675dc831ae0",
    "OrBu_custom": "be1c869700b3277bb8710aa0d5a5dc0110f4936d9bdd4bfe11ffd64b1f5c6891",
    "YlGnBu_custom": "1331c9e6250663679fbe167cba07a3886e2c79d55714e0dd0d9744844e17b4a3",
    "parula": "c92bd1f664a80f2b686330ba97985de329f1cb5152e29ba511b55d8f023ed575",
}


@pytest.fixture(autouse=True)
def _isolated_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        _palettes, "_PALETTE_REGISTRY", _palettes._PALETTE_REGISTRY.copy()
    )


@pytest.mark.parametrize("name", _QUALITATIVE_COLORS)
def test_builtin_qualitative_palette_preserves_all_colors_and_type(name: str) -> None:
    palette = cns.palettes(name)
    expected = [mcolors.to_rgb(color) for color in _QUALITATIVE_COLORS[name].split()]

    expected_type = (
        list if name in list(_QUALITATIVE_COLORS)[:11] else sns.palettes._ColorPalette
    )
    assert type(palette) is expected_type
    assert palette == expected


@pytest.mark.parametrize("name", _CONTINUOUS_DIGESTS)
def test_builtin_continuous_palette_preserves_full_lookup_table(name: str) -> None:
    palette = cns.palettes(name)

    assert type(palette) is LinearSegmentedColormap
    assert palette.name == name
    assert palette.N == 256
    lut = np.vstack((palette(np.arange(-1, palette.N + 1)), palette(np.nan)))
    digest = hashlib.sha256(np.rint(lut * 10**12).astype("<i8").tobytes()).hexdigest()
    assert digest == _CONTINUOUS_DIGESTS[name]


def test_palette_discovery_matches_builtin_types_and_order() -> None:
    qualitative = list(_QUALITATIVE_COLORS)
    continuous = list(_CONTINUOUS_DIGESTS)

    assert cns.available_palettes() == qualitative + continuous
    assert cns.available_palettes("qualitative") == qualitative
    assert cns.available_palettes("continuous") == continuous
    assert get_args(_utils._QualitativePaletteName) == tuple(qualitative)
    assert get_args(_utils._ContinuousPaletteName) == tuple(continuous)
    assert "viridis" not in cns.available_palettes()


@pytest.mark.parametrize("kind", ["sequential", "", "Qualitative", 1, []])
def test_palette_discovery_rejects_invalid_kind(kind: object) -> None:
    with pytest.raises(ValueError, match="kind.*qualitative.*continuous"):
        cns.available_palettes(cast(Any, kind))


def test_palette_discovery_does_not_construct_palettes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_factory() -> None:
        pytest.fail("Palette discovery must not resolve a palette")

    for name, spec in _palettes._PALETTE_REGISTRY.items():
        monkeypatch.setitem(
            _palettes._PALETTE_REGISTRY,
            name,
            _palettes._PaletteSpec(spec.kind, cast(Any, unexpected_factory)),
        )

    assert cns.available_palettes() == list(_QUALITATIVE_COLORS) + list(
        _CONTINUOUS_DIGESTS
    )
    assert cns.available_palettes("qualitative") == list(_QUALITATIVE_COLORS)
    assert cns.available_palettes("continuous") == list(_CONTINUOUS_DIGESTS)


def test_palette_discovery_does_not_import_plotting_dependencies() -> None:
    script = """
import sys
import cnsplots as cns

assert cns.available_palettes()
assert cns.available_palettes("qualitative")
assert cns.available_palettes("continuous")
assert "cnsplots._utils" not in sys.modules
heavy_modules = {
    "Bio", "PyComplexHeatmap", "gseapy", "lifelines", "matplotlib", "numpy",
    "palettable", "pandas", "scanpy", "scipy", "seaborn", "sklearn", "statsmodels",
}
assert not ({name.split(".")[0] for name in sys.modules} & heavy_modules)
"""
    subprocess.run([sys.executable, "-c", script], check=True)


@pytest.mark.parametrize("name", ["NPG", "AAAS", "viridis", "missing", "set1"])
def test_unknown_palette_name_preserves_error(name: str) -> None:
    with pytest.raises(RuntimeError, match="^Wrong Choice!$"):
        cns.palettes(name)


@pytest.mark.parametrize("colors", [["red", "#00ff00"], ((0, 0, 1), "black"), []])
def test_explicit_color_sequences_preserve_seaborn_conversion(
    colors: Sequence[ColorType],
) -> None:
    palette = cns.palettes(colors)

    assert type(palette) is sns.palettes._ColorPalette
    assert palette == sns.color_palette(colors)


def test_register_palette_resolves_and_extends_qualitative_discovery() -> None:
    initial_names = cns.available_palettes()
    initial_qualitative = cns.available_palettes("qualitative")
    initial_continuous = cns.available_palettes("continuous")
    colors: list[ColorType] = ["red", "#00ff00", (0, 0, 1, 0.5)]

    assert cns.register_palette("Study palette", colors) is None
    cns.register_palette("Second study", ("white", "black"))

    assert cns.palettes("Study palette") == [mcolors.to_rgb(color) for color in colors]
    expected_subset = ["#0000ff", "#ff0000", "#0000ff"]
    assert cns.get_palette_colors([2, 0, 2], "Study palette") == expected_subset
    assert (
        cns.get_hexcolors_from_apalette([2, 0, 2], "Study palette") == expected_subset
    )
    assert cns.palettes("Second study") == [(1, 1, 1), (0, 0, 0)]
    assert cns.available_palettes() == initial_names + ["Study palette", "Second study"]
    assert cns.available_palettes("qualitative") == initial_qualitative + [
        "Study palette",
        "Second study",
    ]
    assert cns.available_palettes("continuous") == initial_continuous
    assert "Study palette" not in mpl.colormaps


def test_registered_palette_works_as_figure_color_cycle() -> None:
    colors = ["#112233", "#445566", "#778899"]
    cns.register_palette("Figure study", colors)

    with mpl.rc_context():
        cns.figure(color_cycle="Figure study")
        ax = plt.gca()
        lines = [ax.plot([0, 1], [index, index + 1])[0] for index in range(4)]

    assert [mcolors.to_hex(line.get_color()) for line in lines] == colors + colors[:1]
    assert cns.palettes("Figure study") == [mcolors.to_rgb(color) for color in colors]


def test_registration_defensively_copies_mutable_inputs_and_outputs() -> None:
    colors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    cns.register_palette("Mutable study", cast(Sequence[ColorType], colors))

    colors[0][0] = 0.0
    colors[1] = [0.0, 0.0, 1.0]
    colors.append([0.5, 0.5, 0.5])
    first = cns.palettes("Mutable study")
    assert isinstance(first, list)
    first[0] = (0.0, 0.0, 0.0)
    first.append((1.0, 1.0, 1.0))

    assert cns.palettes("Mutable study") == [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    discovered = cns.available_palettes()
    discovered.clear()
    assert "Mutable study" in cns.available_palettes()


@pytest.mark.parametrize("name", _QUALITATIVE_COLORS)
def test_builtin_palette_results_are_independent(name: str) -> None:
    palette = cns.palettes(name)
    assert isinstance(palette, list)
    palette[0] = (0.0, 0.0, 0.0)
    palette.clear()

    assert cns.palettes(name) == [
        mcolors.to_rgb(color) for color in _QUALITATIVE_COLORS[name].split()
    ]


@pytest.mark.parametrize("name", _CONTINUOUS_DIGESTS)
def test_builtin_colormap_results_are_independent(name: str) -> None:
    palette = cns.palettes(name)
    assert isinstance(palette, Colormap)
    palette.name = "Modified palette"

    fresh = cns.palettes(name)
    assert isinstance(fresh, Colormap)
    assert fresh is not palette
    assert fresh.name == name
    assert fresh(np.nan) == (0.0, 0.0, 0.0, 0.0)


@pytest.mark.parametrize("name", [None, 1, b"study"])
def test_register_palette_rejects_nonstring_names(name: object) -> None:
    with pytest.raises(TypeError, match="name.*string"):
        cns.register_palette(cast(str, name), ["red"])


@pytest.mark.parametrize("name", ["", " ", "\t\n"])
def test_register_palette_rejects_blank_names(name: str) -> None:
    with pytest.raises(ValueError, match="name.*(empty|blank|nonempty|non-empty)"):
        cns.register_palette(name, ["red"])


@pytest.mark.parametrize("name", ["Set1", "Nature", "parula", "viridis", "tab10"])
def test_register_palette_rejects_builtin_and_matplotlib_collisions(name: str) -> None:
    before = cns.available_palettes()
    existing_cmap = mpl.colormaps[name] if name in mpl.colormaps else None

    with pytest.raises(ValueError, match="already|exist|registered|reserved"):
        cns.register_palette(name, ["red"])

    assert cns.available_palettes() == before
    if existing_cmap is not None:
        np.testing.assert_array_equal(
            mpl.colormaps[name](np.linspace(0, 1, 5)),
            existing_cmap(np.linspace(0, 1, 5)),
        )


def test_register_palette_rejects_duplicate_custom_names() -> None:
    cns.register_palette("Duplicate study", ["red"])

    with pytest.raises(ValueError, match="already|exist|registered|reserved"):
        cns.register_palette("Duplicate study", ["blue"])

    assert cns.palettes("Duplicate study") == [(1.0, 0.0, 0.0)]
    assert cns.available_palettes().count("Duplicate study") == 1


@pytest.mark.parametrize("colors", [None, 1, "red", b"red", {"red"}, {"a": "red"}])
def test_register_palette_requires_color_sequence(colors: object) -> None:
    before = cns.available_palettes()
    with pytest.raises(TypeError, match="colors.*sequence"):
        cns.register_palette("Invalid study", cast(Sequence[ColorType], colors))
    assert cns.available_palettes() == before


@pytest.mark.parametrize("colors", [[], ()])
def test_register_palette_rejects_empty_sequences(colors: Sequence[ColorType]) -> None:
    with pytest.raises(ValueError, match="(empty|at least one)"):
        cns.register_palette("Empty study", colors)
    assert "Empty study" not in cns.available_palettes()


@pytest.mark.parametrize(
    "color", ["not-a-color", (1.1, 0.0, 0.0), (float("nan"), 0, 0), (0, 1), object()]
)
def test_register_palette_rejects_invalid_colors_without_partial_registration(
    color: object,
) -> None:
    with pytest.raises(ValueError, match="(invalid|Invalid|color)"):
        cns.register_palette("Invalid color study", ["red", cast(ColorType, color)])
    assert "Invalid color study" not in cns.available_palettes()

    cns.register_palette("Invalid color study", ["blue"])
    assert cns.palettes("Invalid color study") == [(0.0, 0.0, 1.0)]
