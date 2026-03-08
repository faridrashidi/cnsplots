from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from PyComplexHeatmap import ClusterMapPlotter
from PyComplexHeatmap.clustermap import mm2inch

import cnsplots as cns


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
        legend_anchor: str = "auto",
        legend_gap: int = 7,
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
        self.legend_width = legend_width
        self.legend_hpad = legend_hpad
        self.legend_vpad = legend_vpad
        self.legend_anchor = legend_anchor
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
        if subplot_spec is None:
            # Constrain the GridSpec to the current axes' position so the
            # heatmap doesn't span the entire figure.
            pos = self.ax.get_position()
            wspace = (
                self.subplot_gap
                * mm2inch
                * self.ax.figure.dpi
                / (self.ax.get_window_extent().width / 3)
            )
            hspace = (
                self.subplot_gap
                * mm2inch
                * self.ax.figure.dpi
                / (self.ax.get_window_extent().height / 3)
            )

            self.gs = self.ax.figure.add_gridspec(
                3,
                3,
                width_ratios=self.widths,
                height_ratios=self.heights,
                wspace=0,
                hspace=0,
                left=pos.x0,
                right=pos.x1,
                top=pos.y1,
                bottom=pos.y0,
            )
            self.wspace = wspace
            self.hspace = hspace

            self.ax_heatmap = self.ax.figure.add_subplot(self.gs[1, 1])
            self.ax_top = self.ax.figure.add_subplot(
                self.gs[0, 1], sharex=self.ax_heatmap
            )
            self.ax_bottom = self.ax.figure.add_subplot(
                self.gs[2, 1], sharex=self.ax_heatmap
            )
            self.ax_left = self.ax.figure.add_subplot(
                self.gs[1, 0], sharey=self.ax_heatmap
            )
            self.ax_right = self.ax.figure.add_subplot(
                self.gs[1, 2], sharey=self.ax_heatmap
            )
            self.ax_heatmap.set_xlim((0, self.data2d.shape[1]))
            self.ax_heatmap.set_ylim((0, self.data2d.shape[0]))
            self.ax_heatmap.yaxis.set_visible(False)
            self.ax_heatmap.xaxis.set_visible(False)
            self.ax.tick_params(
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
            self.ax_heatmap.tick_params(
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
                self.ax.spines[side].set_visible(False)
            from matplotlib.figure import Figure

            fig = self.ax.figure
            if isinstance(fig, Figure):
                fig.set_layout_engine("none")
        else:
            super()._define_axes(subplot_spec)

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
            if len(self.legend_list) > 1:
                self.legend_list = sorted(self.legend_list, key=lambda x: x[3])
