import itertools
import operator
import os

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import num2tex
import palettable
import pandas as pd
import scipy.stats as stats
import seaborn as sns
from statannotations.Annotator import Annotator
from statannotations.PValueFormat import PValueFormat
from statannotations.utils import DEFAULT

import cnsplots as cns

PALETTE_QUAL = "Ecotyper1"
PALETTE_SEQ = "gnuplot"
FONTSIZE_TITLE = 8
FONTSIZE_LEGEND = 7
LINEWIDTH_AXES = 0.5
RED = "#D6372E"
BLUE = "#5189BB"
GREEN = "#70B460"
PURPLE = "#985EA8"
ORANGE = "#F08F35"
YELLOW = "#FADD4B"
BROWN = "#9C5732"
PINK = "#E787E5"
GRAY = "#A3A3A3"
VIOLET = "#442288"
CHOCOLATE = "#662506"


def figure(height=150, width=150, color_cycle=PALETTE_QUAL, color_map=PALETTE_SEQ):
    cns.setup_matplotlib(color_cycle, color_map)
    plt.figure(figsize=(width / 72, height / 72), dpi=72 * 2)


def savefig(filepath):
    filepath = os.path.expanduser(filepath)
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    # root, ext = os.path.splitext(filepath)
    # if ext.lower() == ".svg":
    # _save_svg(filepath, root)
    # else:
    plt.savefig(filepath)


def take_legend_out(title=None):
    if title is None:
        ax = plt.gca()
        title = ax.get_legend().get_title().get_text()
    plt.legend(
        bbox_to_anchor=(1, 1.02),
        loc="upper left",
        title=title,
    )


def add_panel_name(name="A", offset_x=-0.25, offset_y=1.1):
    plt.text(
        offset_x,
        offset_y,
        name,
        transform=plt.gca().transAxes,
        fontsize=FONTSIZE_TITLE,
        fontname="Arial",
        fontweight="bold",
    )


class multipanel:
    """
    Create multi-panel figures in Cell, Nature, Science journal style.

    This class provides a simple API for creating publication-quality
    multi-panel figures with automatic subplot labeling (A, B, C, ...).

    The figure size is calculated from individual panel sizes:
    - Row heights: maximum height of panels in each row
    - Column widths: maximum width of panels in each column
    - Total width: sum of column widths + gaps (capped at max_width)
    - Total height: sum of row heights + gaps

    Parameters
    ----------
    layout : tuple or list
        Grid layout as (rows, cols) or a list of lists for custom layouts.
        For example: (2, 3) creates a 2x3 grid.
        For custom layouts, use a list like [[1, 1, 2], [3, 4, 4]] where
        numbers represent subplot indices (1-based).
    max_width : int, optional
        Maximum figure width in pixels (default: 540). If panel widths + gaps
        are less than this, blank space remains on the right.
    hgap : int, optional
        Horizontal gap between panels in pixels (default: 40).
    vgap : int, optional
        Vertical gap between panels in pixels (default: 40).
    color_cycle : str, optional
        Color palette name (default: PALETTE_QUAL).
    color_map : str, optional
        Colormap name (default: PALETTE_SEQ).

    Attributes
    ----------
    fig : matplotlib.figure.Figure
        The matplotlib figure object.
    axes : list
        List of matplotlib axes objects.

    Examples
    --------
    >>> import cnsplots as cns
    >>> mp = cns.multipanel((2, 2), max_width=540)
    >>> mp.panel("A", 100, 150)  # height=100, width=150
    >>> cns.boxplot(...)
    >>> mp.panel("B", 100, 150)
    >>> cns.barplot(...)
    """

    def __init__(
        self,
        layout,
        max_width=540,
        hgap=40,
        vgap=40,
        color_cycle=PALETTE_QUAL,
        color_map=PALETTE_SEQ,
    ):
        cns.setup_matplotlib(color_cycle, color_map)

        # Store layout info
        if isinstance(layout, tuple):
            self._rows, self._cols = layout
            self._layout_type = "grid"
            self._n_panels = self._rows * self._cols
        else:
            self._rows = len(layout)
            self._cols = max(len(row) for row in layout)
            self._layout_type = "mosaic"
            self._mosaic = layout
            self._n_panels = max(max(row) for row in layout)

        self._hgap = hgap
        self._vgap = vgap
        self._max_width = max_width

        # Track panel sizes for each row and column
        self._row_heights = [0] * self._rows
        self._col_widths = [0] * self._cols
        self._panel_info = []  # Store (label, height, width) for each panel

        self.fig = None
        self._gs = None
        self.axes = []
        self._panel_index = 0
        self._labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self._created_axes = {}
        self._label_texts = {}
        self._label_offsets_x = {}
        self._label_offsets_y = {}

    def _get_panel_position(self, panel_idx):
        """Get the row and column spans for a panel."""
        if self._layout_type == "grid":
            row = panel_idx // self._cols
            col = panel_idx % self._cols
            return [row], [col]
        else:
            panel_num = panel_idx + 1
            rows_span = []
            cols_span = []
            for r, rowlist in enumerate(self._mosaic):
                for c, val in enumerate(rowlist):
                    if val == panel_num:
                        rows_span.append(r)
                        cols_span.append(c)
            return rows_span, cols_span

    def _create_figure(self):
        """Create the figure with calculated dimensions based on panel sizes."""
        # Calculate total content size
        content_height = sum(self._row_heights) + (self._rows - 1) * self._vgap

        # Figure width is max_width, height is based on content
        fig_width_px = self._max_width
        fig_height_px = content_height

        # Convert pixels to inches (matplotlib uses 72 dpi base)
        fig_width = fig_width_px / 72
        fig_height = fig_height_px / 72

        self.fig = plt.figure(figsize=(fig_width, fig_height), dpi=72 * 2)

        # Calculate positions manually for precise control
        # We'll place axes using figure coordinates (0-1 range)

        # Calculate the left margin to position content at the left
        # Content starts at x=0 (left-aligned within the figure)
        x_positions = [0]
        for i in range(self._cols - 1):
            x_positions.append(x_positions[-1] + self._col_widths[i] + self._hgap)

        y_positions = [fig_height_px - self._row_heights[0]]  # Start from top
        for i in range(self._rows - 1):
            y_positions.append(y_positions[-1] - self._row_heights[i + 1] - self._vgap)

        # Create all axes at their precise positions
        for idx, (label, height, width) in enumerate(self._panel_info):
            rows_span, cols_span = self._get_panel_position(idx)

            if not rows_span:
                raise ValueError(f"Panel {idx + 1} not found in layout")

            row = min(rows_span)
            col = min(cols_span)

            # Calculate axes position in figure coordinates (0-1)
            left = x_positions[col] / fig_width_px
            bottom = y_positions[row] / fig_height_px
            ax_width = width / fig_width_px
            ax_height = height / fig_height_px

            ax = self.fig.add_axes([left, bottom, ax_width, ax_height])

            self.axes.append(ax)
            self._created_axes[label] = ax

            # Add panel label - bold, 8pt, positioned above and to the left
            # Use Arial explicitly for reliable bold rendering across systems
            label_text = ax.text(
                self._label_offsets_x[label],
                self._label_offsets_y[label],
                label,
                transform=ax.transAxes,
                fontsize=FONTSIZE_TITLE,
                fontweight="bold",
                fontname="Arial",
                va="bottom",
                ha="right",
            )
            self._label_texts[label] = label_text

    def panel(self, label=None, height=150, width=150, offset_x=-0.25, offset_y=1.1):
        """
        Define a panel with its size and get the axes for plotting.

        Parameters
        ----------
        label : str or None, optional
            Label for the panel (e.g., "A", "B", "C").
            If None, uses automatic sequential labeling.
        height : int, optional
            Height of this panel in pixels (default: 150).
        width : int, optional
            Width of this panel in pixels (default: 150).

        Returns
        -------
        ax : matplotlib.axes.Axes
            The matplotlib axes object for the panel.
        """
        if label is None:
            label = self._labels[self._panel_index]

        self._label_offsets_x[label] = offset_x
        self._label_offsets_y[label] = offset_y

        # Get panel position
        rows_span, cols_span = self._get_panel_position(self._panel_index)

        if not rows_span:
            raise ValueError(f"Panel {self._panel_index + 1} not found in layout")

        # Update row heights and column widths (take max for each row/col)
        for r in rows_span:
            self._row_heights[r] = max(self._row_heights[r], height)
        for c in cols_span:
            self._col_widths[c] = max(self._col_widths[c], width)

        # Store panel info
        self._panel_info.append((label, height, width))
        self._panel_index += 1

        # Check if all panels have been defined
        if self._panel_index == self._n_panels:
            self._create_figure()

        # Return the axes if figure is created
        if self.fig is not None:
            ax = self._created_axes.get(label)
            if ax is not None:
                plt.sca(ax)
            return ax
        return None

    def get_axes(self, label):
        """
        Get a previously created axes by its label.

        Parameters
        ----------
        label : str
            The label of the panel to retrieve.

        Returns
        -------
        ax : matplotlib.axes.Axes
            The matplotlib axes object.
        """
        return self._created_axes.get(label)


def get_hexcolors_from_apalette(
    alist, palette=palettable.colorbrewer.qualitative.Set1_9.hex_colors
):
    if isinstance(palette, str):
        colors = palettes(palette)
        return list(operator.itemgetter(*alist)(colors))
    else:
        return list(operator.itemgetter(*alist)(palette))


def _is_qualitative_cmap(cmap_name):
    if isinstance(cmap_name, list) or isinstance(cmap_name, dict):
        return True
    else:
        cmap = plt.get_cmap(cmap_name)
        return cmap.N < 33


def _get_hex_colors_from_colorbar(cmap_name, n_colors):
    cmap = plt.cm.get_cmap(cmap_name)
    if _is_qualitative_cmap(cmap_name):
        colors = [mcolors.to_hex(cmap(i)) for i in range(0, n_colors)]
    else:
        colors = [mcolors.to_hex(cmap(i)) for i in range(0, cmap.N, cmap.N // n_colors)]
    return colors


def _remove_edge_from_legend_items(ax):
    handles, labels = ax.get_legend_handles_labels()
    for handle in handles:
        if hasattr(handle, "set_edgecolor"):
            handle.set_edgecolor("none")
    ax.legend(handles, labels)


def _addcount_helper(data, attr, ax):
    xtick_labels = ax.get_xticklabels()
    tick_positions = ax.get_xticks()
    new_xtick_labels = []
    for label in xtick_labels:
        n = len(data[data[attr] == label.get_text()])
        new_xtick_labels.append(f"{label.get_text()}\n(n={n})")
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(new_xtick_labels)


def _p_value_helper(test, data, ax, plotting, pairs, contingency=None, format="star"):
    # format {star, full}
    class PValueFormatNew(PValueFormat):
        def __init__(self):
            super(PValueFormat, self).__init__()
            self._pvalue_format_string = "{:.3e}"
            self._simple_format_string = "{:.2f}"
            self._text_format = "star"
            self.fontsize = "small"
            self._default_pvalue_thresholds = True
            self._pvalue_thresholds = self._get_pvalue_thresholds(DEFAULT)
            self._correction_format = "{star} ({suffix})"
            self.show_test_name = True

        if format == "full":

            def format_data(self, result):
                text = f"{result.test_short_name} " if self.show_test_name else ""
                if result.pvalue > 0.05:
                    return "ns"
                return r"${}P = {}{}$".format(
                    "{}", self.pvalue_format_string, "{}"
                ).format(
                    text, num2tex.num2tex(result.pvalue), result.significance_suffix
                )

    x_is_numeric = pd.api.types.is_numeric_dtype(data[plotting["x"]])
    if x_is_numeric:
        plotting["orient"] = "h"
        primary_col = plotting["y"]
    else:
        primary_col = plotting["x"]

    primary_levels = list(pd.unique(data[primary_col].dropna()))
    order = plotting.get("order")
    if order is not None:
        primary_levels = [level for level in order if level in primary_levels]

    if pairs == "all":
        pairs = list(itertools.combinations(primary_levels, 2))
    elif pairs == "hue":
        hue_col = plotting.get("hue")
        if hue_col is None:
            raise ValueError(
                "`pairs='hue'` requires a hue column in the plotting data."
            )
        hue_levels = list(pd.unique(data[hue_col].dropna()))
        hue_order = plotting.get("hue_order")
        if hue_order is not None:
            hue_levels = [level for level in hue_order if level in hue_levels]
        hue_pairs = []
        for category in primary_levels:
            subset = data[data[primary_col] == category]
            present_hues = [
                level
                for level in hue_levels
                if level in pd.unique(subset[hue_col].dropna())
            ]
            hue_pairs.extend(
                ((category, first), (category, second))
                for first, second in itertools.combinations(present_hues, 2)
            )
        pairs = hue_pairs

    annotator = Annotator(ax, pairs, **plotting)
    annotator._pvalue_format = PValueFormatNew()
    annotator.configure(
        test=test if contingency is None else None,
        text_format=format,
        loc="inside",
        line_width=0.5,
        line_offset=0,
        line_offset_to_group=0,
        text_offset=0,
        color="black",
        show_test_name=False,
        pvalue_format_string="{:.1e}",
        use_fixed_offset=True,
        verbose=0,
    )

    pvalues = []
    if test == "fisher-exact":
        for pair in pairs:
            pvalues.append(stats.fisher_exact(contingency.loc[list(pair)].values)[1])
    if test == "chi-squared":
        for pair in pairs:
            pvalues.append(
                stats.chi2_contingency(contingency.loc[list(pair)].values)[1]
            )

    if contingency is None:
        annotator.apply_and_annotate()
    else:
        annotator.set_pvalues(pvalues=pvalues)
        annotator.annotate()

    if test == "Mann-Whitney":
        print("   ---> P-values were determined by two-sided Mann-Whitney U test.")
    if test == "t-test_welch":
        print("   ---> P-values were determined by two-sided Welch's t-test.")
    if test == "fisher-exact":
        print("   ---> P-values were determined by two-sided Fisher's exact test.")
    if test == "chi-squared":
        print("   ---> P-values were determined by two-sided Chi-squared test.")


def palettes(color):
    if isinstance(color, list):
        return sns.color_palette(color)
    else:
        if color == "Set1":
            return palettable.colorbrewer.qualitative.Set1_9.mpl_colors
        elif color == "Set2":
            return palettable.colorbrewer.qualitative.Set2_8.mpl_colors
        elif color == "Set3":
            return palettable.colorbrewer.qualitative.Set3_12.mpl_colors
        elif color == "Pastel1":
            return palettable.colorbrewer.qualitative.Pastel1_9.mpl_colors
        elif color == "Pastel2":
            return palettable.colorbrewer.qualitative.Pastel2_8.mpl_colors
        elif color == "Paired":
            return palettable.colorbrewer.qualitative.Paired_12.mpl_colors
        elif color == "Dark2":
            return palettable.colorbrewer.qualitative.Dark2_8.mpl_colors
        elif color == "Accent":
            return palettable.colorbrewer.qualitative.Accent_8.mpl_colors
        elif color == "Tableau":
            return palettable.tableau.Tableau_10.mpl_colors
        elif color == "Bold":
            return palettable.cartocolors.qualitative.Bold_10.mpl_colors
        elif color == "BlueRed":
            return palettable.tableau.BlueRed_6.mpl_colors
        elif color == "ECharts":
            colors = [
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
            return sns.color_palette(colors)
        elif color == "Ecotyper1":
            colors = [
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
            return sns.color_palette(colors)
        elif color == "Ecotyper2":
            colors = ["#EB7D5B", "#FED23F", "#B5D33D", "#6CA2EA", "#442288"]
            return sns.color_palette(colors)
        elif color == "Ecotyper3":
            colors = [
                "#D13570",
                "#569AB4",
                "#70AC58",
                "#74509D",
                "#ED7E30",
                "#F5C945",
                "#9C5732",
                "#E787E5",
            ]
            return sns.color_palette(colors)
        elif color == "Ecotyper4":
            colors = [
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
            return sns.color_palette(colors)
        elif color == "Ecotyper5":
            colors = [
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
            return sns.color_palette(colors)
        elif color == "Ecotyper6":
            colors = [
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
            return sns.color_palette(colors)
        elif color == "BuRd_custom":
            cm_data = [
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
            ]
            return mpl.colors.LinearSegmentedColormap.from_list("BuRd_custom", cm_data)
        elif color == "WhYlOrRd_custom":
            cm_data = [
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
            ]
            return mpl.colors.LinearSegmentedColormap.from_list(
                "WhYlOrRd_custom", cm_data
            )
        elif color == "OrBu_custom":
            cm_data = [
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
            ]
            return mpl.colors.LinearSegmentedColormap.from_list("OrBu_custom", cm_data)
        elif color == "YlGnBu_custom":
            cm_data = [
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
            ]
            return mpl.colors.LinearSegmentedColormap.from_list(
                "YlGnBu_custom", cm_data
            )
        elif color == "parula":
            cm_data = [
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
            ]
            return mpl.colors.LinearSegmentedColormap.from_list("parula", cm_data)
        else:
            return RuntimeError("Wrong Choice!")
