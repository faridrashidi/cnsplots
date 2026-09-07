"""Lightweight palette metadata and discovery with lazy color factories."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Literal, NamedTuple

if TYPE_CHECKING:
    from matplotlib.colors import Colormap
    from matplotlib.typing import ColorType

_PaletteKind = Literal["qualitative", "continuous"]
_RGBColor = tuple[float, float, float]


def _colorbrewer_palette(name: str, size: int) -> list[_RGBColor]:
    from palettable.colorbrewer.colorbrewer import get_map

    return get_map(name, "qualitative", size).mpl_colors


def _tableau_palette(name: str) -> list[_RGBColor]:
    from palettable.tableau.tableau import get_map

    return get_map(name).mpl_colors


def _cartocolor_palette(name: str) -> list[_RGBColor]:
    from palettable.cartocolors.qualitative import get_map

    return get_map(name).mpl_colors


def _qualitative_palette(colors: Sequence[ColorType]) -> list[_RGBColor]:
    import seaborn as sns

    return sns.color_palette(colors)


def _continuous_palette(name: str, colors: Sequence[Sequence[float]]) -> Colormap:
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list(name, colors)


class _PaletteSpec(NamedTuple):
    kind: _PaletteKind
    factory: Callable[[], list[_RGBColor] | Colormap]


_PALETTE_REGISTRY: dict[str, _PaletteSpec] = {
    "Set1": _PaletteSpec("qualitative", lambda: _colorbrewer_palette("Set1", 9)),
    "Set2": _PaletteSpec("qualitative", lambda: _colorbrewer_palette("Set2", 8)),
    "Set3": _PaletteSpec("qualitative", lambda: _colorbrewer_palette("Set3", 12)),
    "Pastel1": _PaletteSpec("qualitative", lambda: _colorbrewer_palette("Pastel1", 9)),
    "Pastel2": _PaletteSpec("qualitative", lambda: _colorbrewer_palette("Pastel2", 8)),
    "Paired": _PaletteSpec("qualitative", lambda: _colorbrewer_palette("Paired", 12)),
    "Dark2": _PaletteSpec("qualitative", lambda: _colorbrewer_palette("Dark2", 8)),
    "Accent": _PaletteSpec("qualitative", lambda: _colorbrewer_palette("Accent", 8)),
    "Tableau": _PaletteSpec("qualitative", lambda: _tableau_palette("Tableau_10")),
    "Bold": _PaletteSpec("qualitative", lambda: _cartocolor_palette("Bold_10")),
    "BlueRed": _PaletteSpec("qualitative", lambda: _tableau_palette("BlueRed_6")),
    "Cell": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#C84C3A",
                "#2F7E8F",
                "#E1A22E",
                "#4E5A8A",
                "#5F9862",
                "#D07A6A",
                "#8B6FA8",
                "#7B8C9E",
                "#B85F7A",
                "#6B6B6B",
            ]
        ),
    ),
    "Nature": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#E64B35",
                "#4DBBD5",
                "#00A087",
                "#3C5488",
                "#F39B7F",
                "#8491B4",
                "#91D1C2",
                "#DC0000",
                "#7E6148",
                "#B09C85",
            ]
        ),
    ),
    "Science": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#3B4992",
                "#EE0000",
                "#008B45",
                "#631879",
                "#008280",
                "#BB0021",
                "#5F559B",
                "#A20056",
                "#808180",
                "#1B1919",
            ]
        ),
    ),
    "Lancet": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#00468B",
                "#ED0000",
                "#42B540",
                "#0099B4",
                "#925E9F",
                "#FDAF91",
                "#AD002A",
                "#ADB6B6",
                "#1B1919",
            ]
        ),
    ),
    "NEJM": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#BC3C29",
                "#0072B5",
                "#E18727",
                "#20854E",
                "#7876B1",
                "#6F99AD",
                "#FFDC91",
                "#EE4C97",
            ]
        ),
    ),
    "JAMA": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#374E55",
                "#DF8F44",
                "#00A1D5",
                "#B24745",
                "#79AF97",
                "#6A6599",
                "#80796B",
            ]
        ),
    ),
    "JCO": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#0073C2",
                "#EFC000",
                "#868686",
                "#CD534C",
                "#7AA6DC",
                "#003C67",
                "#8F7700",
                "#3B3B3B",
                "#A73030",
                "#4A6990",
            ]
        ),
    ),
    "OkabeIto": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#E69F00",
                "#56B4E9",
                "#009E73",
                "#F0E442",
                "#0072B2",
                "#D55E00",
                "#CC79A7",
                "#000000",
            ]
        ),
    ),
    "TolBright": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#4477AA",
                "#EE6677",
                "#228833",
                "#CCBB44",
                "#66CCEE",
                "#AA3377",
                "#BBBBBB",
            ]
        ),
    ),
    "TolMuted": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#332288",
                "#88CCEE",
                "#44AA99",
                "#117733",
                "#999933",
                "#DDCC77",
                "#CC6677",
                "#882255",
                "#AA4499",
                "#DDDDDD",
            ]
        ),
    ),
    "ECharts": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#5470c6",
                "#91cc75",
                "#fac858",
                "#ee6666",
                "#9a60b4",
                "#73c0de",
                "#3ba272",
                "#fc8452",
                "#27727b",
                "#ea7ccc",
                "#d7504b",
                "#e87c25",
                "#b5c334",
                "#fe8463",
                "#26c0c0",
                "#f4e001",
            ]
        ),
    ),
    "Ecotyper1": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#D6372E",
                "#5189BB",
                "#70B460",
                "#985EA8",
                "#F08F35",
                "#FADD4B",
                "#A3A3A3",
                "#B7D3E5",
                "#E6D8C2",
            ]
        ),
    ),
    "Ecotyper2": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            ["#EB7D5B", "#FED23F", "#B5D33D", "#6CA2EA", "#442288"]
        ),
    ),
    "Ecotyper3": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#D13570",
                "#569AB4",
                "#70AC58",
                "#74509D",
                "#ED7E30",
                "#F5C945",
                "#9C5732",
                "#E787E5",
            ]
        ),
    ),
    "Ecotyper4": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#386cb0",
                "#fdb462",
                "#7fc97f",
                "#ef3b2c",
                "#662506",
                "#a6cee3",
                "#fb9a99",
                "#984ea3",
                "#ffff33",
            ]
        ),
    ),
    "Ecotyper5": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#E41A71",
                "#379DB8",
                "#5BAF4A",
                "#7B4EA3",
                "#FF7600",
                "#FFC800",
                "#A65328",
                "#F781EC",
                "#999999",
                "#A6DCE3",
                "#BBDF8A",
                "#FB9A99",
                "#FDB96F",
                "#BEB2D6",
                "#1B9E5E",
                "#D95802",
                "#707EB3",
                "#E729D3",
                "#E69F02",
                "#8DD3B9",
                "#FFFAB3",
                "#BABFDA",
                "#FB7F72",
                "#80C5D3",
                "#FDAE62",
                "#BEDE69",
                "#FCCDF7",
            ]
        ),
    ),
    "Ecotyper6": _PaletteSpec(
        "qualitative",
        lambda: _qualitative_palette(
            [
                "#FDC086",
                "#386CB0",
                "#F0027F",
                "#FFFF99",
                "#BF5B17",
                "#7FC97F",
                "lightblue",
                "#BEAED4",
                "#66C2A5",
                "#FC8D62",
                "#8DA0CB",
                "#E78AC3",
                "#A6D854",
                "#FFD92F",
                "#E5C494",
                "#B3B3B3",
                "#FBB4AE",
                "#B3CDE3",
                "#CCEBC5",
                "#DECBE4",
                "#FED9A6",
                "#FFFFCC",
                "#E5D8BD",
                "#FDDAEC",
            ]
        ),
    ),
    "BuRd_custom": _PaletteSpec(
        "continuous",
        lambda: _continuous_palette(
            "BuRd_custom",
            [
                [0.0588, 0.3412, 0.6157],
                [0.1220, 0.3940, 0.6610],
                [0.1843, 0.4471, 0.7059],
                [0.2650, 0.5000, 0.7450],
                [0.3451, 0.5529, 0.7843],
                [0.5412, 0.6902, 0.8667],
                [0.7294, 0.8275, 0.9333],
                [0.8863, 0.9255, 0.9765],
                [0.9500, 0.9700, 0.9900],
                [1.0000, 1.0000, 1.0000],
                [0.9900, 0.9500, 0.9400],
                [0.9882, 0.9020, 0.8863],
                [0.9650, 0.8200, 0.7900],
                [0.9412, 0.7412, 0.6980],
                [0.9080, 0.6330, 0.5840],
                [0.8745, 0.5255, 0.4706],
                [0.7961, 0.3137, 0.2784],
                [0.7137, 0.1216, 0.1686],
                [0.6196, 0.0588, 0.1373],
            ],
        ),
    ),
    "WhYlOrRd_custom": _PaletteSpec(
        "continuous",
        lambda: _continuous_palette(
            "WhYlOrRd_custom",
            [
                [1.0000, 1.0000, 1.0000],
                [1.0000, 1.0000, 0.8500],
                [1.0000, 0.9800, 0.7000],
                [1.0000, 0.9400, 0.5000],
                [1.0000, 0.8500, 0.3000],
                [0.9961, 0.7200, 0.2000],
                [0.9961, 0.5500, 0.1000],
                [0.9922, 0.4000, 0.0500],
                [0.9882, 0.2500, 0.0200],
                [0.9500, 0.1500, 0.0100],
                [0.9000, 0.0800, 0.0100],
                [0.8000, 0.0200, 0.0100],
                [0.6500, 0.0000, 0.0100],
                [0.5019, 0.0000, 0.0000],
                [0.4000, 0.0000, 0.0000],
            ],
        ),
    ),
    "OrBu_custom": _PaletteSpec(
        "continuous",
        lambda: _continuous_palette(
            "OrBu_custom",
            [
                [0.8500, 0.3800, 0.0500],
                [1.0000, 0.4980, 0.0549],
                [1.0000, 0.5841, 0.2169],
                [1.0000, 0.6702, 0.3790],
                [1.0000, 0.7563, 0.5410],
                [1.0000, 0.8424, 0.7031],
                [1.0000, 0.9284, 0.8651],
                [1.0000, 1.0000, 1.0000],
                [0.8608, 0.9235, 0.9745],
                [0.7216, 0.8471, 0.9490],
                [0.5824, 0.7706, 0.9235],
                [0.4431, 0.6941, 0.8980],
                [0.3039, 0.6176, 0.8725],
                [0.1647, 0.5412, 0.8471],
                [0.1216, 0.4667, 0.7059],
            ],
        ),
    ),
    "YlGnBu_custom": _PaletteSpec(
        "continuous",
        lambda: _continuous_palette(
            "YlGnBu_custom",
            [
                [1.00, 1.00, 0.80],
                [0.98, 0.99, 0.75],
                [0.95, 0.98, 0.70],
                [0.91, 0.97, 0.66],
                [0.87, 0.96, 0.62],
                [0.83, 0.95, 0.59],
                [0.77, 0.93, 0.58],
                [0.71, 0.91, 0.59],
                [0.64, 0.89, 0.62],
                [0.56, 0.87, 0.66],
                [0.48, 0.84, 0.69],
                [0.40, 0.81, 0.72],
                [0.32, 0.78, 0.74],
                [0.26, 0.74, 0.76],
                [0.21, 0.70, 0.77],
                [0.18, 0.65, 0.78],
                [0.15, 0.60, 0.78],
                [0.13, 0.55, 0.78],
                [0.12, 0.50, 0.76],
                [0.13, 0.44, 0.73],
                [0.13, 0.39, 0.70],
                [0.14, 0.33, 0.66],
                [0.14, 0.28, 0.62],
                [0.14, 0.22, 0.58],
                [0.05, 0.18, 0.52],
                [0.03, 0.15, 0.45],
            ],
        ),
    ),
    "parula": _PaletteSpec(
        "continuous",
        lambda: _continuous_palette(
            "parula",
            [
                [0.2081, 0.1663, 0.5292],
                [0.2116, 0.1898, 0.5777],
                [0.2123, 0.2138, 0.6270],
                [0.2081, 0.2386, 0.6771],
                [0.1959, 0.2645, 0.7279],
                [0.1707, 0.2919, 0.7792],
                [0.1253, 0.3242, 0.8303],
                [0.0591, 0.3598, 0.8683],
                [0.0117, 0.3875, 0.8820],
                [0.0060, 0.4086, 0.8828],
                [0.0165, 0.4266, 0.8786],
                [0.0329, 0.4430, 0.8720],
                [0.0498, 0.4586, 0.8641],
                [0.0629, 0.4737, 0.8554],
                [0.0723, 0.4887, 0.8467],
                [0.0779, 0.5040, 0.8384],
                [0.0793, 0.5200, 0.8312],
                [0.0749, 0.5375, 0.8263],
                [0.0641, 0.5570, 0.8240],
                [0.0488, 0.5772, 0.8228],
                [0.0343, 0.5966, 0.8199],
                [0.0265, 0.6137, 0.8135],
                [0.0239, 0.6287, 0.8038],
                [0.0231, 0.6418, 0.7913],
                [0.0228, 0.6535, 0.7768],
                [0.0267, 0.6642, 0.7607],
                [0.0384, 0.6743, 0.7436],
                [0.0590, 0.6838, 0.7254],
                [0.0843, 0.6928, 0.7062],
                [0.1133, 0.7015, 0.6859],
                [0.1453, 0.7098, 0.6646],
                [0.1801, 0.7177, 0.6424],
                [0.2178, 0.7250, 0.6193],
                [0.2586, 0.7317, 0.5954],
                [0.3022, 0.7376, 0.5712],
                [0.3482, 0.7424, 0.5473],
                [0.3953, 0.7459, 0.5244],
                [0.4420, 0.7481, 0.5033],
                [0.4871, 0.7491, 0.4840],
                [0.5300, 0.7491, 0.4661],
                [0.5709, 0.7485, 0.4494],
                [0.6099, 0.7473, 0.4337],
                [0.6473, 0.7456, 0.4188],
                [0.6834, 0.7435, 0.4044],
                [0.7184, 0.7411, 0.3905],
                [0.7525, 0.7384, 0.3768],
                [0.7858, 0.7356, 0.3633],
                [0.8185, 0.7327, 0.3498],
                [0.8507, 0.7299, 0.3360],
                [0.8824, 0.7274, 0.3217],
                [0.9139, 0.7258, 0.3063],
                [0.9450, 0.7261, 0.2886],
                [0.9739, 0.7314, 0.2666],
                [0.9938, 0.7455, 0.2403],
                [0.9990, 0.7653, 0.2164],
                [0.9955, 0.7861, 0.1967],
                [0.9880, 0.8066, 0.1794],
                [0.9789, 0.8271, 0.1633],
                [0.9697, 0.8481, 0.1475],
                [0.9626, 0.8705, 0.1309],
                [0.9589, 0.8949, 0.1132],
                [0.9598, 0.9218, 0.0948],
                [0.9661, 0.9514, 0.0755],
                [0.9763, 0.9831, 0.0538],
            ],
        ),
    ),
}


def available_palettes(kind: _PaletteKind | None = None) -> list[str]:
    """List built-in and registered palette names in registration order.

    Parameters
    ----------
    kind : {"qualitative", "continuous"}, optional
        Return only palettes of this kind. By default, return both kinds.

    Returns
    -------
    list of str
        A fresh list of palette names. Built-ins appear first, followed by
        user palettes in registration order. External Matplotlib names are
        not included, and no palette objects are created during discovery.

    Raises
    ------
    ValueError
        If ``kind`` is not ``None``, ``"qualitative"``, or ``"continuous"``.

    See Also
    --------
    palettes : Resolve a palette by name.
    register_palette : Register a custom qualitative palette.
    """
    if kind not in (None, "qualitative", "continuous"):
        raise ValueError("kind must be 'qualitative', 'continuous', or None.")
    return [
        name
        for name, spec in _PALETTE_REGISTRY.items()
        if kind is None or spec.kind == kind
    ]
