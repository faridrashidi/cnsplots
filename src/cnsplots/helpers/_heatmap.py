from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import matplotlib.legend as mlegend
import numpy as np
import pandas as pd
from PyComplexHeatmap import ClusterMapPlotter, DotClustermapPlotter
from PyComplexHeatmap.clustermap import mm2inch

import cnsplots as cns


def _define_axes_within_current_bounds(
    plotter: ClusterMapPlotter,
    subplot_spec: Any = None,
) -> bool:
    """Constrain embedded heatmap-like plotters to the active host axes."""
    if subplot_spec is not None:
        return False

    def _sync_embedded_axes() -> None:
        pos = plotter.ax.get_position()
        plotter.gs.update(
            left=pos.x0,
            right=pos.x1,
            top=pos.y1,
            bottom=pos.y0,
        )
        _sync_detached_legend_axes(plotter)

    pos = plotter.ax.get_position()
    wspace = (
        plotter.subplot_gap
        * mm2inch
        * plotter.ax.figure.dpi
        / (plotter.ax.get_window_extent().width / 3)
    )
    hspace = (
        plotter.subplot_gap
        * mm2inch
        * plotter.ax.figure.dpi
        / (plotter.ax.get_window_extent().height / 3)
    )

    plotter.gs = plotter.ax.figure.add_gridspec(
        3,
        3,
        width_ratios=plotter.widths,
        height_ratios=plotter.heights,
        wspace=0,
        hspace=0,
        left=pos.x0,
        right=pos.x1,
        top=pos.y1,
        bottom=pos.y0,
    )
    plotter.wspace = wspace
    plotter.hspace = hspace

    plotter.ax_heatmap = plotter.ax.figure.add_subplot(plotter.gs[1, 1])
    plotter.ax_top = plotter.ax.figure.add_subplot(
        plotter.gs[0, 1], sharex=plotter.ax_heatmap
    )
    plotter.ax_bottom = plotter.ax.figure.add_subplot(
        plotter.gs[2, 1], sharex=plotter.ax_heatmap
    )
    plotter.ax_left = plotter.ax.figure.add_subplot(
        plotter.gs[1, 0], sharey=plotter.ax_heatmap
    )
    plotter.ax_right = plotter.ax.figure.add_subplot(
        plotter.gs[1, 2], sharey=plotter.ax_heatmap
    )
    plotter.ax_heatmap.set_xlim((0, plotter.data2d.shape[1]))
    plotter.ax_heatmap.set_ylim((0, plotter.data2d.shape[0]))
    plotter.ax_heatmap.yaxis.set_visible(False)
    plotter.ax_heatmap.xaxis.set_visible(False)
    plotter.ax.tick_params(
        axis="both",
        which="both",
        left=False,
        right=False,
        labelleft=False,
        labelright=False,
        top=False,
        bottom=False,
        labeltop=False,
        labelbottom=False,
    )
    plotter.ax_heatmap.tick_params(
        axis="both",
        which="both",
        left=False,
        right=False,
        top=False,
        bottom=False,
        labeltop=False,
        labelbottom=False,
        labelleft=False,
        labelright=False,
    )
    for side in ["left", "right", "top", "bottom"]:
        plotter.ax.spines[side].set_visible(False)
    setattr(plotter.ax, "_cnsplots_sync_embedded_axes", _sync_embedded_axes)
    setattr(
        plotter.ax,
        "_cnsplots_sync_detached_legends",
        lambda: _sync_detached_legend_axes(plotter),
    )

    from matplotlib.figure import Figure

    fig = plotter.ax.figure
    if isinstance(fig, Figure):
        fig.set_layout_engine("none")
    return True


def _stabilize_detached_legends(cbars: Sequence[Any]) -> None:
    """Keep PyComplexHeatmap legends anchored to their helper axes on resize."""
    for cbar in cbars:
        if not isinstance(cbar, mlegend.Legend):
            continue
        ax = cbar.axes
        if ax is None:
            continue
        renderer = ax.figure.canvas.get_renderer()
        if renderer is None:
            continue
        legend_bbox = cbar.get_window_extent(renderer=renderer)
        ax_bbox = ax.get_window_extent(renderer=renderer)
        if ax_bbox.width > 0 and ax_bbox.height > 0:
            cbar.set_bbox_to_anchor(
                (
                    0,
                    min(max((legend_bbox.y1 - ax_bbox.y0) / ax_bbox.height, 0), 1),
                ),
                transform=ax.transAxes,
            )


def _sync_detached_legend_axes(plotter: ClusterMapPlotter) -> None:
    """Re-anchor detached legend columns to the current legend anchor axes."""
    anchor_ax = getattr(plotter, "_legend_anchor_ax", None)
    legend_axes = list(getattr(plotter, "legend_axes", []) or [])
    if anchor_ax is None or not legend_axes:
        return

    renderer = anchor_ax.figure.canvas.get_renderer()
    if renderer is None:
        return

    fig_bbox = anchor_ax.figure.bbox.frozen()
    anchor_bbox = anchor_ax.get_window_extent(renderer=renderer)
    if (
        fig_bbox.width <= 0
        or fig_bbox.height <= 0
        or anchor_bbox.width <= 0
        or anchor_bbox.height <= 0
    ):
        return

    legend_bboxes = [
        legend_ax.get_window_extent(renderer=renderer).frozen()
        for legend_ax in legend_axes
    ]

    first_legend_x0 = float(legend_bboxes[0].x0)
    legend_delta_x = getattr(plotter, "legend_delta_x", None)
    if legend_delta_x is None:
        space = 0.0
        if plotter.legend_side == "right" and plotter.right_annotation is not None:
            space = float(plotter.label_max_width)
        elif (
            plotter.legend_side == "right"
            and plotter.show_rownames
            and plotter.row_names_side == "right"
        ):
            space = float(plotter.label_max_width)
        base_x0 = (
            float(anchor_bbox.x1)
            + space
            + float(plotter.legend_hpad) * mm2inch * anchor_ax.figure.dpi
            + anchor_ax.yaxis.labelpad * 1.2 * anchor_ax.figure.dpi / 72
        )
    else:
        base_x0 = (anchor_ax.get_position().x1 + float(legend_delta_x)) * float(
            fig_bbox.width
        )

    for legend_ax, legend_bbox in zip(legend_axes, legend_bboxes):
        x0_px = base_x0 + float(legend_bbox.x0 - first_legend_x0)
        legend_ax.set_position(
            [
                x0_px / float(fig_bbox.width),
                float(anchor_bbox.y0) / float(fig_bbox.height),
                float(legend_bbox.width) / float(fig_bbox.width),
                float(anchor_bbox.height) / float(fig_bbox.height),
            ]
        )

    _stabilize_detached_legends(getattr(plotter, "cbars", []))


class ClusterMapPlotterNew(ClusterMapPlotter):
    def __init__(
        self,
        data: pd.DataFrame,
        z_score: int | None = None,
        standard_scale: int | None = None,
        top_annotation: Any = None,
        bottom_annotation: Any = None,
        left_annotation: Any = None,
        right_annotation: Any = None,
        row_cluster: bool = True,
        col_cluster: bool = True,
        row_cluster_method: str = "average",
        row_cluster_metric: str = "correlation",
        col_cluster_method: str = "average",
        col_cluster_metric: str = "correlation",
        show_rownames: bool = False,
        show_colnames: bool = False,
        row_names_side: str = "right",
        col_names_side: str = "bottom",
        row_dendrogram: bool = False,
        col_dendrogram: bool = False,
        row_dendrogram_size: int = 10,
        col_dendrogram_size: int = 10,
        row_split: Any = None,
        col_split: Any = None,
        row_dendrogram_kws: dict[str, Any] | None = None,
        col_dendrogram_kws: dict[str, Any] | None = None,
        bezier: bool = False,
        dotsize: int = 1,
        tree_kws: dict[str, Any] | None = None,
        row_split_order: list[str] | None = None,
        col_split_order: list[str] | None = None,
        row_split_gap: float = 0.5,
        col_split_gap: float = 0.2,
        mask: Any = None,
        subplot_gap: int = 1,
        legend: bool = True,
        legend_kws: dict[str, Any] | None = None,
        plot: bool = True,
        plot_legend: bool = True,
        legend_order: bool | str | Sequence[str] = "auto",
        legend_anchor: str = "auto",
        legend_gap: int = 7,
        legend_vgap: int | None = None,
        legend_hgap: int | None = None,
        legend_width: float = 4.5,
        legend_hpad: int = 2,
        legend_vpad: int = 5,
        legend_side: str = "right",
        cmap: str | list[Any] | dict[str, Any] = "jet",
        label: str | None = None,
        xticklabels_kws: dict[str, Any] | None = None,
        yticklabels_kws: dict[str, Any] | None = None,
        rasterized: bool = False,
        xlabel: str | None = None,
        ylabel: str | None = None,
        xlabel_kws: dict[str, Any] | None = None,
        ylabel_kws: dict[str, Any] | None = None,
        xlabel_side: str = "bottom",
        ylabel_side: str = "left",
        xlabel_bbox_kws: dict[str, Any] | None = None,
        ylabel_bbox_kws: dict[str, Any] | None = None,
        legend_delta_x: float | None = None,
        verbose: int = 1,
        **kwargs: Any,
    ) -> None:
        self.data = data
        self.kwargs = kwargs if kwargs is not None else {}
        self.rasterized = rasterized
        self.data2d = self.format_data(data, mask, z_score, standard_scale)
        self.verbose = verbose
        self._define_kws(xticklabels_kws, yticklabels_kws)
        self.top_annotation = top_annotation
        self.bottom_annotation = bottom_annotation
        self.left_annotation = left_annotation
        self.right_annotation = right_annotation
        self.row_dendrogram_size = row_dendrogram_size
        self.col_dendrogram_size = col_dendrogram_size
        self.row_cluster = row_cluster
        self.col_cluster = col_cluster
        self.row_cluster_method = row_cluster_method
        self.row_cluster_metric = row_cluster_metric
        self.col_cluster_method = col_cluster_method
        self.col_cluster_metric = col_cluster_metric
        self.show_rownames = show_rownames
        self.show_colnames = show_colnames
        self.row_names_side = row_names_side
        self.col_names_side = col_names_side
        self.row_dendrogram = row_dendrogram
        self.col_dendrogram = col_dendrogram
        self.subplot_gap = subplot_gap
        self.row_dendrogram_kws = (
            {} if row_dendrogram_kws is None else row_dendrogram_kws
        )
        self.col_dendrogram_kws = (
            {} if col_dendrogram_kws is None else col_dendrogram_kws
        )
        self.bezier = bezier
        self.dotsize = dotsize
        self.tree_kws = {} if tree_kws is None else tree_kws
        self.row_split = row_split
        self.col_split = col_split
        self.row_split_gap = row_split_gap
        self.col_split_gap = col_split_gap
        self.row_split_order = row_split_order
        self.col_split_order = col_split_order
        self.legend = legend
        self.legend_kws = legend_kws if legend_kws is not None else {}
        self.legend_side = legend_side
        self.cmap = cmap
        self.label = label if label is not None else "heatmap"
        self.legend_gap = legend_gap
        self.legend_vgap = legend_gap if legend_vgap is None else legend_vgap
        self.legend_hgap = legend_gap if legend_hgap is None else legend_hgap
        self.legend_width = legend_width
        self.legend_hpad = legend_hpad
        self.legend_vpad = legend_vpad
        self.legend_anchor = legend_anchor
        self.legend_order = legend_order
        self.legend_delta_x = legend_delta_x
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.xlabel_kws = xlabel_kws if xlabel_kws is not None else {}
        self.ylabel_kws = ylabel_kws if ylabel_kws is not None else {}
        self.xlabel_side = xlabel_side
        self.ylabel_side = ylabel_side
        self.xlabel_bbox_kws = xlabel_bbox_kws
        self.ylabel_bbox_kws = ylabel_bbox_kws
        if plot:
            self.plot()
            if plot_legend:
                if legend_anchor == "auto":
                    if (
                        self.right_annotation is not None
                        and self.legend_side == "right"
                    ):
                        legend_anchor = "ax"
                    else:
                        legend_anchor = "ax_heatmap"
                if legend_anchor == "ax_heatmap":
                    self.plot_legends(ax=self.ax_heatmap)
                else:
                    self.plot_legends(ax=self.ax)

        self.post_processing()

    def _define_axes(self, subplot_spec: Any = None) -> None:
        if not _define_axes_within_current_bounds(self, subplot_spec):
            super()._define_axes(subplot_spec)

    def plot_legends(self, ax: Any = None) -> None:
        super().plot_legends(ax=ax)
        self._legend_anchor_ax = self.ax if ax is None else ax
        _sync_detached_legend_axes(self)

    def collect_legends(self) -> None:
        if self.verbose >= 1:
            print("Collecting legends..")
        self.legend_list = []
        self.label_max_width = 0
        for annotation in [
            self.top_annotation,
            self.bottom_annotation,
            self.left_annotation,
            self.right_annotation,
        ]:
            if annotation is not None:
                annotation.collect_legends()
                if annotation.plot_legend and len(annotation.legend_list) > 0:
                    self.legend_list.extend(annotation.legend_list)
                # print(annotation.label_max_width,self.label_max_width)
                if annotation.label_max_width > self.label_max_width:
                    self.label_max_width = annotation.label_max_width
        if self.legend:
            if cns._utils._is_qualitative_cmap(self.cmap):
                if isinstance(self.data, pd.DataFrame):
                    unique_values = sorted(np.unique(self.data.values.astype(str)))
                else:
                    unique_values = sorted(np.unique(self.data.astype(str)))
                if isinstance(self.cmap, list):
                    cmap = self.cmap
                    cmap = {k: v for k, v in zip(unique_values, cmap)}
                elif isinstance(self.cmap, dict):
                    cmap = {k: v for k, v in self.cmap.items() if k in unique_values}
                else:
                    cmap = cns._utils._get_hex_colors_from_colorbar(
                        self.cmap, len(unique_values)
                    )
                    cmap = {k: v for k, v in zip(unique_values, cmap)}
                self.legend_kws.setdefault("frameon", False)
                self.legend_kws.setdefault("labelspacing", 0.2)
                self.legend_kws.setdefault("handletextpad", 0.4)
                self.legend_kws.setdefault("color_text", False)
                self.legend_list.append(
                    [cmap, self.label, self.legend_kws, 4, "color_dict"]
                )
            else:
                vmax = self.kwargs.get(
                    "vmax", np.nanmax(self.data2d[self.data2d != np.inf])
                )
                vmin = self.kwargs.get(
                    "vmin", np.nanmin(self.data2d[self.data2d != -np.inf])
                )
                self.legend_kws.setdefault("vmin", round(vmin, 2))
                self.legend_kws.setdefault("vmax", round(vmax, 2))
                self.legend_list.append(
                    [self.cmap, self.label, self.legend_kws, 4, "cmap"]
                )
            heatmap_label_max_width = (
                max(label.get_window_extent().width for label in self.yticklabels)
                if len(self.yticklabels) > 0
                else 0
            )
            if (
                heatmap_label_max_width >= self.label_max_width
                or self.legend_anchor == "ax_heatmap"
            ):
                self.label_max_width = heatmap_label_max_width * 1.1
            if isinstance(self.legend_order, (list, tuple)):
                ordered_titles = set()
                legend_by_title = {item[1]: item for item in self.legend_list}
                ordered_legends = []
                for title in self.legend_order:
                    legend = legend_by_title.get(title)
                    if legend is None:
                        continue
                    ordered_legends.append(legend)
                    ordered_titles.add(title)
                ordered_legends.extend(
                    item for item in self.legend_list if item[1] not in ordered_titles
                )
                self.legend_list = ordered_legends
            elif len(self.legend_list) > 1 and self.legend_order in [True, "auto"]:
                self.legend_list = sorted(self.legend_list, key=lambda x: x[3])


class DotClustermapPlotterNew(DotClustermapPlotter):
    def _define_axes(self, subplot_spec: Any = None) -> None:
        if not _define_axes_within_current_bounds(self, subplot_spec):
            super()._define_axes(subplot_spec)

    def plot_legends(self, ax: Any = None) -> None:
        super().plot_legends(ax=ax)
        self._legend_anchor_ax = self.ax if ax is None else ax
        _sync_detached_legend_axes(self)
