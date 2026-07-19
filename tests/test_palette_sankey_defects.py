from __future__ import annotations

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import pytest
from cycler import cycler

from cnsplots import _utils
from cnsplots.plots import _specialized


def test_get_hexcolors_from_apalette_preserves_singleton_color() -> None:
    assert _utils.get_hexcolors_from_apalette([0], "Set1") == ["#e41a1c"]


def test_get_hexcolors_from_apalette_normalizes_custom_colors() -> None:
    assert _utils.get_hexcolors_from_apalette([0, 1], ["red", (0, 1, 0)]) == [
        "#ff0000",
        "#00ff00",
    ]


@pytest.mark.parametrize("n_colors", [3, 300])
def test_get_hex_colors_from_colorbar_returns_requested_count(n_colors: int) -> None:
    colors = _utils._get_hex_colors_from_colorbar("viridis", n_colors)

    assert len(colors) == n_colors
    assert colors[0] == mcolors.to_hex(mpl.colormaps["viridis"](0))
    assert colors[-1] == mcolors.to_hex(mpl.colormaps["viridis"](1.0))


def test_sankeyplot_assigns_color_to_every_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = pd.DataFrame(
        {
            "source": ["source_a", "source_b", "source_c"],
            "target": ["target", "target", "target"],
        }
    )
    captured_colors: dict[str, object] = {}

    def capture_colors(
        *args: object, colorDict: dict[str, object], **kwargs: object
    ) -> None:
        captured_colors.update(colorDict)

    monkeypatch.setattr(_specialized.helper_sankey, "sankeyplot", capture_colors)

    with plt.rc_context({"axes.prop_cycle": cycler(color=["#111111", "#eeeeee"])}):
        _specialized.sankeyplot(data, x="source", y="target")

    assert set(captured_colors) == {
        "source_a",
        "source_b",
        "source_c",
        "target",
    }
    assert len(captured_colors) == 4
