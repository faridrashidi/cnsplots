"""Static checks for the public typing contract."""

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from importlib.resources.abc import Traversable
    else:
        from importlib.abc import Traversable

    import pandas as pd
    from anndata import AnnData
    from matplotlib.axes import Axes
    from matplotlib.colors import Colormap
    from typing_extensions import assert_type

    import cnsplots as cns
    from cnsplots._settings import CNSSettings

    def _check_public_types(data: pd.DataFrame, ax: Axes) -> None:
        assert_type(cns.settings, CNSSettings)
        assert_type(cns.settings.palette_qual, str)
        assert_type(cns.settings.title_fontsize, int | float)
        assert_type(cns.settings.legend_fontsize, int | float | None)
        assert_type(cns.settings.savefig_transparent, bool)
        assert_type(cns.settings.font_sans_serif, tuple[str, ...])

        assert_type(cns.figure(width=120, height=80), None)
        assert_type(cns.savefig("figure.svg"), None)
        assert_type(cns.add_panel_label("A"), None)
        assert_type(cns.apply_unicode_font(ax), None)
        assert_type(cns.take_legend_out("Group"), None)
        assert_type(cns.get_hexcolors_from_apalette([0], "Set1"), list[str])
        assert_type(cns.palettes("Set1"), list[tuple[float, float, float]])
        assert_type(cns.palettes("parula"), Colormap)
        assert_type(cns.boxplot(data, x="group", y="value"), Axes)
        assert_type(cns.histplot(data, x="x", ax=ax), Axes)
        assert_type(cns.lineplot(data, x="x", y="y", ax=ax), Axes)
        assert_type(cns.regplot(data, x="x", y="y", color=(0.1, 0.2, 0.3)), Axes)
        assert_type(cns.sankeyplot(data, x=["source", "target"], ax=ax), Axes)
        assert_type(cns.sankeyplot(data, x=["baseline", "week_4", "week_12"]), Axes)
        assert_type(
            cns.dumbbellplot(data, x="value", y="group", hue="condition", ax=ax),
            Axes,
        )

        panels = cns.multipanel()
        assert_type(panels.panel("A", color_cycle=("red", "blue")), Axes)

        showcase = cns.datasets.get_showcase_data()
        assert_type(showcase[0], pd.DataFrame)
        assert_type(showcase[3], AnnData)
        showcase_with_images = cns.datasets.get_showcase_data(
            include_showcase_images=True
        )
        assert_type(showcase_with_images[-1], Traversable)
