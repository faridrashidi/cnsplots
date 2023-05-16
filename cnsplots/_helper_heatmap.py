from PyComplexHeatmap import *

import cnsplots as cns


def _is_qualitative_cmap(cmap_name):
    if isinstance(cmap_name, list) or isinstance(cmap_name, dict):
        return True
    else:
        cmap = plt.get_cmap(cmap_name)
        return cmap.N < 33


class ClusterMapPlotterNew(ClusterMapPlotter):
    def __init__(
        self,
        data,
        z_score=None,
        standard_scale=None,
        top_annotation=None,
        bottom_annotation=None,
        left_annotation=None,
        right_annotation=None,
        row_cluster=True,
        col_cluster=True,
        row_cluster_method="average",
        row_cluster_metric="correlation",
        col_cluster_method="average",
        col_cluster_metric="correlation",
        show_rownames=False,
        show_colnames=False,
        row_names_side="right",
        col_names_side="bottom",
        row_dendrogram=False,
        col_dendrogram=False,
        row_dendrogram_size=10,
        col_dendrogram_size=10,
        row_split=None,
        col_split=None,
        dendrogram_kws=None,
        tree_kws=None,
        row_split_order=None,
        col_split_order=None,
        row_split_gap=0.5,
        col_split_gap=0.2,
        mask=None,
        subplot_gap=1,
        legend=True,
        legend_kws=None,
        plot=True,
        plot_legend=True,
        legend_anchor="auto",
        legend_gap=7,
        legend_width=4.5,
        legend_hpad=2,
        legend_vpad=5,
        legend_side="right",
        cmap="jet",
        label=None,
        xticklabels_kws=None,
        yticklabels_kws=None,
        rasterized=False,
        legend_delta_x=None,
        verbose=1,
        **kwargs
    ):
        self.data = data
        self.kwargs = kwargs if not kwargs is None else {}
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
        self.dendrogram_kws = dendrogram_kws
        self.tree_kws = {} if tree_kws is None else tree_kws
        self.row_split = row_split
        self.col_split = col_split
        self.row_split_gap = row_split_gap
        self.col_split_gap = col_split_gap
        self.row_split_order = row_split_order
        self.col_split_order = col_split_order
        self.rasterized = rasterized
        self.legend = legend
        self.legend_kws = legend_kws if not legend_kws is None else {}
        self.legend_side = legend_side
        self.cmap = cmap
        self.label = label if not label is None else "heatmap"
        self.legend_gap = legend_gap
        self.legend_width = legend_width
        self.legend_hpad = legend_hpad
        self.legend_vpad = legend_vpad
        self.legend_anchor = legend_anchor
        self.legend_delta_x = legend_delta_x
        if plot:
            self.plot()
            if plot_legend:
                if legend_anchor == "auto":
                    if (
                        not self.right_annotation is None
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

    def collect_legends(self):
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
            if not annotation is None:
                annotation.collect_legends()
                if annotation.plot_legend and len(annotation.legend_list) > 0:
                    self.legend_list.extend(annotation.legend_list)
                # print(annotation.label_max_width,self.label_max_width)
                if annotation.label_max_width > self.label_max_width:
                    self.label_max_width = annotation.label_max_width
        if self.legend:
            if _is_qualitative_cmap(self.cmap):
                if isinstance(self.data, pd.DataFrame):
                    unique_values = sorted(np.unique(self.data.values.astype(str)))
                else:
                    unique_values = sorted(np.unique(self.data.astype(str)))
                if isinstance(self.cmap, list):
                    cmap = self.cmap
                    cmap = {v: k for v, k in zip(unique_values, cmap)}
                elif isinstance(self.cmap, dict):
                    cmap = self.cmap  # TODO: bug
                else:
                    cmap = cns._utils._get_hex_colors_from_colorbar(
                        self.cmap, len(unique_values)
                    )
                    cmap = {v: k for v, k in zip(unique_values, cmap)}  # TODO: bug
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
