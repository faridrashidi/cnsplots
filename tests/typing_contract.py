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
    from matplotlib.figure import Figure
    from matplotlib.transforms import Bbox
    from typing_extensions import assert_type

    import cnsplots as cns
    from cnsplots._settings import CNSSettings

    def _check_comparison_types(data: pd.DataFrame) -> None:
        string_pairs: list[tuple[str, str]] = [("A", "B")]
        numeric_pairs: list[tuple[int, float]] = [(0, 1.5)]
        hue_pairs: list[tuple[tuple[int, str], tuple[int, str]]] = [
            ((0, "control"), (0, "treated"))
        ]
        for plotter in (
            cns.boxplot,
            cns.violinplot,
            cns.barplot,
            cns.lollipopplot,
        ):
            assert_type(plotter(data, x="group", y="value", pairs="all"), Axes)
            assert_type(
                plotter(data, x="group", y="value", hue="condition", pairs="hue"),
                Axes,
            )
            assert_type(plotter(data, x="group", y="value", pairs=string_pairs), Axes)
            assert_type(plotter(data, x="group", y="value", pairs=numeric_pairs), Axes)
            assert_type(
                plotter(data, x="group", y="value", hue="condition", pairs=hue_pairs),
                Axes,
            )
            assert_type(plotter(data, x="group", y="value", pairs=(("A", "B"),)), Axes)
        assert_type(cns.stackplot(data, x="group", stack="outcome", pairs="all"), Axes)
        assert_type(
            cns.stackplot(data, x="group", stack="outcome", pairs=string_pairs), Axes
        )
        assert_type(
            cns.stackplot(data, y="group", stack="outcome", pairs=numeric_pairs), Axes
        )

    def _check_public_types(data: pd.DataFrame, ax: Axes, include_images: bool) -> None:
        assert_type(cns.settings, CNSSettings)
        assert_type(cns.settings.palette_qual, str)
        assert_type(cns.settings.title_fontsize, int | float)
        assert_type(cns.settings.legend_fontsize, int | float | None)
        assert_type(cns.settings.savefig_transparent, bool)
        assert_type(cns.settings.font_sans_serif, tuple[str, ...])
        assert_type(cns.settings.panel_label_fontname, str | None)

        fig = cns.figure(width=120, height=80)
        assert_type(fig, Figure)
        assert_type(cns.figure(2, 1.5, unit="in"), Figure)
        assert_type(cns.figure(50.8, 38.1, unit="mm"), Figure)
        assert_type(cns.figure(144, 108, unit="pt"), Figure)
        assert_type(cns.savefig("figure.svg"), None)
        assert_type(
            cns.savefig(
                "figure.png",
                fig=fig,
                dpi=300,
                transparent=False,
                bbox_inches="tight",
                pad_inches=0.1,
            ),
            None,
        )
        assert_type(cns.savefig("figure.pdf", fig=fig, bbox_inches=None), None)
        assert_type(
            cns.savefig(
                "figure.svg", fig=fig, bbox_inches=Bbox.from_bounds(0, 0, 2, 1)
            ),
            None,
        )
        assert_type(cns.add_panel_label("A"), None)
        assert_type(cns.apply_unicode_font(ax), None)
        assert_type(cns.take_legend_out("Group"), None)
        assert_type(cns.get_hexcolors_from_apalette([0], "Set1"), list[str])
        assert_type(
            cns.get_hexcolors_from_apalette(alist=[0], palette="Set1"), list[str]
        )
        assert_type(cns.get_palette_colors([0]), list[str])
        assert_type(cns.get_palette_colors([0], palette=None), list[str])
        assert_type(cns.get_palette_colors(indices=(0, 2), palette="Set1"), list[str])
        assert_type(cns.get_palette_colors([1], ["red", (0.1, 0.2, 0.3)]), list[str])
        assert_type(cns.available_palettes(), list[str])
        assert_type(cns.available_palettes(kind="qualitative"), list[str])
        assert_type(cns.available_palettes(kind="continuous"), list[str])
        assert_type(cns.register_palette("MyLab", ["red", (0.1, 0.2, 0.3)]), None)
        assert_type(cns.palettes("Set1"), list[tuple[float, float, float]])
        assert_type(cns.palettes("parula"), Colormap)
        assert_type(cns.boxplot(data, x="group", y="value"), Axes)
        assert_type(cns.get_comparison_results(ax), pd.DataFrame)
        assert_type(cns.get_comparison_results(), pd.DataFrame)
        assert_type(
            cns.survivalplot(
                data,
                duration="time",
                event="event",
                hue="group",
                pairs=[("A", "B"), ("A", "C")],
                p_adjust="holm",
                ax=ax,
            ),
            Axes,
        )
        assert_type(cns.get_survival_results(ax), pd.DataFrame)
        assert_type(cns.get_survival_results(), pd.DataFrame)
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
        sized_panels = cns.multipanel(max_width=7, unit="in")
        assert_type(sized_panels, cns.multipanel)
        assert_type(sized_panels.panel("A", width=2, height=1.5), Axes)
        assert_type(sized_panels.panel("B", width=50.8, unit="mm"), Axes)
        assert_type(sized_panels.panel("C", width=144, unit="pt"), Axes)
        assert_type(sized_panels.panel("D", width=2, unit=None), Axes)

        assert_type(cns.datasets.get_dataset_names(), list[str])
        showcase = cns.datasets.get_showcase_data()
        assert_type(showcase, cns.datasets.ShowcaseData)
        assert_type(
            cns.datasets.get_showcase_data(include_showcase_images=False),
            cns.datasets.ShowcaseData,
        )
        assert_type(showcase[0], pd.DataFrame)
        assert_type(showcase[3], AnnData)
        assert_type(showcase.iris_df, pd.DataFrame)
        assert_type(showcase.tips_df, pd.DataFrame)
        assert_type(showcase.survival_df, pd.DataFrame)
        assert_type(showcase.blobs, AnnData)
        assert_type(showcase.volcano_df, pd.DataFrame)
        assert_type(showcase.gene_sets, list[set[str]])
        assert_type(showcase.roc_df, pd.DataFrame)
        assert_type(showcase.slope_df, pd.DataFrame)
        assert_type(showcase.confusion_df, pd.DataFrame)
        assert_type(showcase.line_df, pd.DataFrame)
        assert_type(showcase.cumulative_incidence_df, pd.DataFrame)
        assert_type(showcase.forest_df, pd.DataFrame)
        assert_type(showcase.upset_sets, dict[str, set[str]])
        showcase_with_images = cns.datasets.get_showcase_data(
            include_showcase_images=True
        )
        assert_type(showcase_with_images, cns.datasets.ShowcaseDataWithImages)
        assert_type(showcase_with_images[-1], Traversable)
        assert_type(showcase_with_images.showcase_images, Traversable)
        optional_images = cns.datasets.get_showcase_data(
            include_showcase_images=include_images
        )
        assert_type(
            optional_images,
            cns.datasets.ShowcaseData | cns.datasets.ShowcaseDataWithImages,
        )
        assert_type(optional_images.iris_df, pd.DataFrame)
        assert_type(optional_images.tips_df, pd.DataFrame)
        assert_type(optional_images.survival_df, pd.DataFrame)
        assert_type(optional_images.blobs, AnnData)
        assert_type(optional_images.volcano_df, pd.DataFrame)
        assert_type(optional_images.gene_sets, list[set[str]])
        assert_type(optional_images.roc_df, pd.DataFrame)
        assert_type(optional_images.slope_df, pd.DataFrame)
        assert_type(optional_images.confusion_df, pd.DataFrame)
        assert_type(optional_images.line_df, pd.DataFrame)
        assert_type(optional_images.cumulative_incidence_df, pd.DataFrame)
        assert_type(optional_images.forest_df, pd.DataFrame)
        assert_type(optional_images.upset_sets, dict[str, set[str]])
