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


def figure(height=150, width=150, color_cycle=None, color_map=None):
    """
    Initialize a new figure with custom size and styling.

    This function creates a new matplotlib figure with specified dimensions and
    applies the cnsplots style configuration including color palette and colormap.

    Parameters
    ----------
    height : int, default: 150
        Height of the figure in pixels.
    width : int, default: 150
        Width of the figure in pixels.
    color_cycle : str, default: None
        Name of the qualitative color palette to use for the color cycle.
        If None, uses cns.settings.palette_qual.
        Options include: 'Ecotyper1', 'Set1', 'Set2', 'Dark2', 'Tableau', etc.
    color_map : str, default: None
        Name of the sequential colormap to use for continuous data.
        If None, uses cns.settings.palette_seq.
        Options include: 'gnuplot', 'parula', 'bwr', 'hot', etc.

    Returns
    -------
    None
        This function creates a figure and returns nothing.

    See Also
    --------
    multipanel : Create multi-panel figures with automatic layout.
    savefig : Save the current figure to a file.
    setup_matplotlib : Configure matplotlib styling.

    Notes
    -----
    The function converts pixel dimensions to inches assuming 72 DPI base resolution
    and sets the actual DPI to 144 for high-quality output.

    The figure size formula: inches = pixels / 72, with DPI = 144

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.figure(height=200, width=300)
    >>> cns.boxplot(data=df, x="group", y="value")
    >>> cns.savefig("plot.pdf")

    >>> # With custom color scheme
    >>> cns.figure(height=150, width=150, color_cycle="Set2", color_map="parula")
    >>> cns.heatmapplot(adata)
    """
    if color_cycle is None:
        color_cycle = cns.settings.palette_qual
    if color_map is None:
        color_map = cns.settings.palette_seq
    cns.setup_matplotlib(color_cycle, color_map)
    plt.figure(figsize=(width / 72, height / 72), dpi=72 * 2)


def savefig(filepath):
    """
    Save the current figure to a file, creating directories if needed.

    This function saves the current matplotlib figure to the specified file path,
    automatically creating any missing parent directories.

    Parameters
    ----------
    filepath : str
        Path where the figure should be saved. Can include home directory shorthand
        (~). The file format is determined by the extension (e.g., .pdf, .png, .svg).

    Returns
    -------
    None
        This function saves the figure and returns nothing.

    See Also
    --------
    figure : Initialize a new figure with custom size and styling.
    multipanel : Create multi-panel figures.

    Notes
    -----
    The function automatically:
    - Expands user home directory (~) in the path
    - Creates all necessary parent directories if they don't exist
    - Determines the file format from the file extension

    Supported formats include: PDF, PNG, SVG, JPG, EPS, and more (any format
    supported by matplotlib.pyplot.savefig).

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.figure()
    >>> cns.boxplot(data=df, x="group", y="value")
    >>> cns.savefig("~/results/figures/boxplot.pdf")

    >>> # Save in multiple formats
    >>> cns.savefig("output/plot.png")
    >>> cns.savefig("output/plot.svg")
    """
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
    """
    Move the legend outside the plot area to the upper-left of the right margin.

    This function repositions the current axes legend to appear outside and to
    the right of the plot area, preventing overlap with the plotted data.

    Parameters
    ----------
    title : str, optional
        Title for the legend. If None, uses the existing legend title from
        the current axes.

    Returns
    -------
    None
        This function modifies the current legend and returns nothing.

    See Also
    --------
    figure : Initialize a new figure.
    multipanel : Create multi-panel figures with automatic layout.

    Notes
    -----
    The legend is positioned with:
    - bbox_to_anchor=(1, 1.02): Slight offset above the upper-right corner
    - loc='upper left': Legend's upper-left corner is anchored to that point

    This ensures the legend appears just to the right of the plot area without
    obscuring data points.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.figure()
    >>> cns.scatterplot(data=df, x="PC1", y="PC2", hue="cell_type")
    >>> cns.take_legend_out()

    >>> # With custom title
    >>> cns.barplot(data=df, x="treatment", y="response", hue="batch")
    >>> cns.take_legend_out(title="Batch")
    """
    ax = plt.gca()
    legend = ax.get_legend()
    handles = None
    labels = None
    if legend is not None:
        handles = legend.legend_handles
        labels = [t.get_text() for t in legend.texts]
        if title is None:
            title = legend.get_title().get_text()
    if title is None:
        title = ""
    plt.legend(
        handles=handles,
        labels=labels,
        bbox_to_anchor=(1, 1.02),
        loc="upper left",
        title=title,
        markerscale=1,
    )


def add_panel_label(name="A", offset_x=-0.25, offset_y=1.1):
    """
    Add a panel label (e.g., 'A', 'B', 'C') to the current axes.

    This function adds a bold text label to the current axes, typically used
    for labeling panels in multi-panel figures for publication.

    Parameters
    ----------
    name : str, default: 'A'
        The label text to display (typically a single letter).
    offset_x : float, default: -0.25
        Horizontal offset in axes coordinates. Negative values place the label
        to the left of the axes.
    offset_y : float, default: 1.1
        Vertical offset in axes coordinates. Values > 1.0 place the label above
        the axes.

    Returns
    -------
    None
        This function adds text to the axes and returns nothing.

    See Also
    --------
    multipanel : Create multi-panel figures with automatic labeling.
    figure : Initialize a new figure.

    Notes
    -----
    The label is positioned using axes coordinates where:
    - (0, 0) is the lower-left corner of the axes
    - (1, 1) is the upper-right corner of the axes
    - Values outside [0, 1] place the label outside the axes area

    The label uses Arial font (bold) at 8pt size (FONTSIZE_TITLE) for consistency
    with publication standards.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.figure()
    >>> cns.boxplot(data=df, x="group", y="value")
    >>> cns.add_panel_label("A")

    >>> # Custom positioning
    >>> cns.figure()
    >>> cns.barplot(data=df, x="treatment", y="response")
    >>> cns.add_panel_label("B", offset_x=-0.3, offset_y=1.15)
    """
    plt.text(
        offset_x,
        offset_y,
        name,
        transform=plt.gca().transAxes,
        fontsize=cns.settings.fontsize_title,
        fontname="Arial",
        fontweight="bold",
    )


def get_hexcolors_from_apalette(
    alist, palette=palettable.colorbrewer.qualitative.Set1_9.hex_colors
):
    """
    Extract specific colors from a palette by index.

    This function retrieves a subset of colors from a color palette based on
    the provided indices.

    Parameters
    ----------
    alist : list of int
        List of indices specifying which colors to extract from the palette.
        Indices are 0-based.
    palette : str or list, default: Set1_9.hex_colors
        Either a palette name (str) that can be resolved by the palettes() function,
        or a list of hex color codes.

    Returns
    -------
    list
        List of hex color codes corresponding to the requested indices.

    See Also
    --------
    palettes : Get a complete color palette by name.

    Notes
    -----
    When palette is a string, it is first resolved to a list of colors using
    the palettes() function, which supports many predefined palettes including:
    - ColorBrewer palettes: 'Set1', 'Set2', 'Set3', 'Dark2', 'Paired', etc.
    - Custom palettes: 'Ecotyper1'-'Ecotyper6', 'BlueRed', 'ECharts', etc.

    When palette is a list, colors are extracted directly by index.

    Examples
    --------
    >>> import cnsplots as cns
    >>> # Extract first two colors from Set1
    >>> colors = cns.get_hexcolors_from_apalette([0, 1], "Set1")
    >>> colors
    ['#E41A1C', '#377EB8']

    >>> # Extract specific colors from custom palette
    >>> custom = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    >>> selected = cns.get_hexcolors_from_apalette([0, 2], custom)
    >>> selected
    ['#FF0000', '#0000FF']
    """
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


def get_showcase_data():
    import numpy as np
    import pandas as pd
    import scanpy as sc
    import seaborn as sns

    np.random.seed(42)
    survival_data = []
    for grp, scale in [("Treatment", 36), ("Control", 24)]:
        times = np.random.exponential(scale=scale, size=50)
        events = np.random.binomial(1, 0.7, 50)
        for t, e in zip(times, events):
            survival_data.append({"time": t, "event": e, "group": grp})
    survival_df = pd.DataFrame(survival_data)
    survival_df["age"] = np.random.normal(60, 10, len(survival_df)).astype(int)
    survival_df["stage"] = np.random.choice(["I", "II", "III"], len(survival_df))

    iris_df = sns.load_dataset("iris")
    tips_df = sns.load_dataset("tips")
    blobs = sc.datasets.blobs()
    blobs.obs["TP53"] = np.random.random(blobs.shape[0])
    blobs.obs["KRAS"] = np.random.random(blobs.shape[0])
    blobs.var["Ensemble"] = [f"ens{x}" for x in np.random.randint(0, 3, blobs.shape[1])]
    blobs.obs["Selected"] = np.where(blobs.obs["TP53"] > 0.95, "o", None)
    blobs.obs["Cluster"] = pd.Categorical(
        [f"C{x}" for x in np.random.randint(0, 4, blobs.shape[0])]
    )
    blobs.X = blobs.X - blobs.X.mean()

    # Volcano plot data (synthetic DE results)
    n_genes = 500
    logfc = np.random.normal(0, 1.5, n_genes)
    pvals = 10 ** (-np.abs(logfc) * np.random.uniform(0.5, 3, n_genes))
    pvals = np.clip(pvals, 1e-50, 1)
    volcano_df = pd.DataFrame(
        {
            "log2FoldChange": logfc,
            "-log10(adjp)": -np.log10(pvals),
            "symbol": [f"Gene{i}" for i in range(n_genes)],
        }
    )

    # Venn plot data
    gene_sets = [
        set(f"Gene{i}" for i in np.random.choice(200, 80, replace=False)),
        set(f"Gene{i}" for i in np.random.choice(200, 90, replace=False)),
        set(f"Gene{i}" for i in np.random.choice(200, 70, replace=False)),
    ]

    # ROC data
    y_true = np.random.binomial(1, 0.4, 200)
    roc_df = pd.DataFrame(
        {
            "label": y_true,
            "Model A": y_true * 0.5
            + (1 - y_true) * 0.3
            + np.random.normal(0, 0.25, 200),
            "Model B": y_true * 0.6
            + (1 - y_true) * 0.2
            + np.random.normal(0, 0.2, 200),
        }
    )
    return iris_df, tips_df, survival_df, blobs.T, volcano_df, gene_sets, roc_df


def palettes(color):
    """
    Get a color palette by name.

    This function returns a predefined color palette as a list of colors in
    matplotlib-compatible format. Supports ColorBrewer palettes, custom scientific
    palettes, and specialized colormaps.

    Parameters
    ----------
    color : str or list
        Palette name or list of color values. If a list is provided, it is
        converted to a seaborn color palette.

        **Supported palette names:**

        **ColorBrewer Qualitative:**
        - 'Set1', 'Set2', 'Set3'
        - 'Pastel1', 'Pastel2'
        - 'Paired'
        - 'Dark2'
        - 'Accent'

        **Other Qualitative:**
        - 'Tableau': Tableau 10 colors
        - 'Bold': Cartographic bold colors
        - 'BlueRed': Tableau blue-red diverging palette
        - 'ECharts': ECharts library default colors
        - 'Ecotyper1'-'Ecotyper6': Custom palettes for cell type visualization

        **Sequential/Diverging (for use with colormaps):**
        - 'BuRd_custom': Custom blue-white-red diverging
        - 'WhYlOrRd_custom': White-yellow-orange-red sequential
        - 'OrBu_custom': Orange-white-blue diverging
        - 'YlGnBu_custom': Yellow-green-blue sequential
        - 'parula': MATLAB parula colormap

    Returns
    -------
    list or matplotlib.colors.LinearSegmentedColormap
        For qualitative palettes: list of RGB tuples or color objects
        For sequential/diverging palettes: LinearSegmentedColormap object

    See Also
    --------
    get_hexcolors_from_apalette : Extract specific colors from a palette by index.
    figure : Initialize a figure with custom color cycle.

    Notes
    -----
    Ecotyper palettes are custom color schemes designed for biological data
    visualization, particularly for distinguishing cell types and molecular
    subtypes in tumor microenvironment studies.

    The function returns:
    - Qualitative palettes as lists of matplotlib color objects (RGB tuples)
    - Sequential/diverging palettes as LinearSegmentedColormap objects

    Examples
    --------
    >>> import cnsplots as cns
    >>> # Get Set1 palette
    >>> colors = cns.palettes("Set1")
    >>> len(colors)
    9

    >>> # Get Ecotyper1 palette
    >>> eco_colors = cns.palettes("Ecotyper1")

    >>> # Use parula colormap
    >>> parula_cmap = cns.palettes("parula")

    >>> # Pass a custom list
    >>> custom = ["#FF0000", "#00FF00", "#0000FF"]
    >>> palette = cns.palettes(custom)
    """
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
