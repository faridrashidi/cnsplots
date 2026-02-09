from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes

import matplotlib as mpl

import cnsplots as cns


def setup_matplotlib(
    color_cycle: str | None = None,
    color_map: str | None = None,
    fontsize_title: int | float | None = None,
    fontsize_legend: int | float | None = None,
    linewidth_axes: float | None = None,
) -> None:
    """
    Configure matplotlib with publication-quality default styling.

    This function sets up matplotlib with custom styling optimized for
    scientific publications, including font settings, color palettes,
    axis styling, and export parameters.

    Parameters
    ----------
    color_cycle : str, default: None
        Name of the qualitative color palette for the default color cycle.
        If None, uses cns.settings.palette_qual.
        Options include: 'Set1', 'Set2', 'Dark2', 'Ecotyper1'-'Ecotyper6',
        'Tableau', 'Bold', 'ECharts', etc.
    color_map : str, default: None
        Name of the sequential colormap for continuous data.
        If None, uses cns.settings.palette_seq.
        Options include: 'gnuplot', 'parula', 'bwr', 'hot', 'BuRd_custom',
        'WhYlOrRd_custom', etc.
    fontsize_title : int, default: None
        Font size for titles, axis labels, and legend titles.
        If None, uses cns.settings.fontsize_title.
    fontsize_legend : int, default: None
        Font size for tick labels and legend text.
        If None, uses cns.settings.fontsize_legend.
    linewidth_axes : float, default: None
        Line width for axis spines.
        If None, uses cns.settings.linewidth_axes.

    Returns
    -------
    None
        This function modifies matplotlib's global rcParams.

    See Also
    --------
    figure : Initialize a new figure with custom size.
    setup_scanpy : Configure styling for scanpy plots.
    setup_ax : Apply styling to a specific axes.

    Notes
    -----
    The function configures:

    **Fonts:**
    - Family: Sans-serif (Helvetica)
    - Math text: Custom fontset
    - Sizes: title=8pt, legend=7pt (by default)

    **Axes:**
    - Spines: Bottom and left only (top and right hidden)
    - Line width: 0.5pt
    - Colors: Black
    - Margins: 5% on x and y axes
    - Grid: Disabled

    **Ticks:**
    - Size: 2pt length, 0.6pt width
    - Padding: 1pt
    - Colors: Black

    **Legend:**
    - Frame: Disabled
    - Marker scale: 0.5
    - Handle dimensions: 0.7 × 0.7

    **Export:**
    - DPI: 288 (72 × 4)
    - Format: Tight bounding box with 0.01" padding
    - Transparency: Enabled
    - SVG fonts: Embedded as text (fonttype='none')

    **Colormaps:**
    Registers all custom and predefined colormaps for easy access.

    This configuration follows journal guidelines for Cell, Nature, and Science.

    Examples
    --------
    >>> import cnsplots as cns
    >>> # Use default settings
    >>> cns.setup_matplotlib()

    >>> # Customize colors and sizes
    >>> cns.setup_matplotlib(
    ...     color_cycle="Set2", color_map="parula", fontsize_title=10, fontsize_legend=8
    ... )
    """
    # Use settings values if parameters are not provided
    if color_cycle is None:
        color_cycle = cns.settings.palette_qual
    if color_map is None:
        color_map = cns.settings.palette_seq
    if fontsize_title is None:
        fontsize_title = cns.settings.fontsize_title
    if fontsize_legend is None:
        fontsize_legend = cns.settings.fontsize_legend
    if linewidth_axes is None:
        linewidth_axes = cns.settings.linewidth_axes

    def config() -> dict[str, object]:
        """
        Generate matplotlib rcParams configuration dictionary.

        Returns
        -------
        dict
            Configuration dictionary for matplotlib.rcParams.update().
        """
        return {
            "mathtext.fontset": "custom",
            "font.family": "sans-serif",
            "font.sans-serif": "Helvetica",
            "font.size": fontsize_title,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.01,
            "savefig.dpi": 72 * 4,
            "savefig.transparent": True,
            "svg.fonttype": "none",
            "axes.titlesize": fontsize_title,
            "axes.labelsize": fontsize_title,
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": linewidth_axes,
            "axes.edgecolor": "black",
            "axes.labelcolor": "black",
            "axes.labelpad": 2,
            "axes.titlepad": 4,
            "axes.xmargin": 0.05,
            "axes.ymargin": 0.05,
            "axes.prop_cycle": mpl.cycler(color=cns.palettes(color_cycle)),
            "image.cmap": color_map,
            "legend.fontsize": fontsize_title,
            "legend.title_fontsize": fontsize_title,
            "legend.frameon": False,
            "legend.markerscale": 0.5,
            "legend.handlelength": 0.7,
            "legend.handleheight": 0.7,
            "legend.handletextpad": 0.3,
            "xtick.labelsize": fontsize_legend,
            "xtick.bottom": True,
            "xtick.color": "black",
            "xtick.major.size": 2,
            "xtick.major.width": 0.6,
            "xtick.major.pad": 1,
            "xtick.alignment": "center",
            "ytick.labelsize": fontsize_legend,
            "ytick.left": True,
            "ytick.color": "black",
            "ytick.major.size": 2,
            "ytick.major.width": 0.6,
            "ytick.major.pad": 1,
            "ytick.alignment": "center_baseline",
        }

    for categorical in [
        "Set1",
        "Set2",
        "Set3",
        "Pastel1",
        "Pastel2",
        "Paired",
        "Dark2",
        "Accent",
        "Tableau",
        "Bold",
        "BlueRed",
        "ECharts",
        "Ecotyper1",
        "Ecotyper2",
        "Ecotyper3",
        "Ecotyper4",
        "Ecotyper5",
        "Ecotyper6",
    ]:
        if categorical not in mpl.colormaps:
            mpl.colormaps.register(
                mpl.colors.ListedColormap(cns.palettes(categorical)), name=categorical
            )
    for continues in [
        "parula",
        "gnuplot",
        "hot",
        "WhYlOrRd_custom",
        "BuRd_custom",
        "OrBu_custom",
        "YlGnBu_custom",
    ]:
        if continues not in mpl.colormaps:
            mpl.colormaps.register(cns.palettes(continues), name=continues)

    mpl.rcParams.update(config())


def setup_scanpy() -> None:
    """
    Configure matplotlib and scanpy with consistent publication-quality styling.

    This function applies cnsplots styling to matplotlib and configures scanpy
    to use compatible figure parameters for single-cell analysis visualizations.

    Parameters
    ----------
    None

    Returns
    -------
    None
        This function modifies global matplotlib and scanpy settings.

    See Also
    --------
    setup_matplotlib : Configure matplotlib styling.
    figure : Initialize a new figure.

    Notes
    -----
    This function performs two configuration steps:

    1. Calls setup_matplotlib() to apply cnsplots styling
    2. Sets scanpy figure parameters:
       - scanpy=False: Disable scanpy's default styling
       - figsize=(2.5, 2.5): Default figure size in inches
       - facecolor='white': White background for figures

    This ensures consistency between cnsplots and scanpy visualizations in
    single-cell analysis workflows.

    Examples
    --------
    >>> import cnsplots as cns
    >>> import scanpy as sc
    >>> cns.setup_scanpy()
    >>> sc.pl.umap(adata, color="cell_type")
    """
    import scanpy

    setup_matplotlib()
    scanpy.set_figure_params(scanpy=False, figsize=(2.5, 2.5), facecolor="white")


def setup_ax(
    ax: Axes,
    fontsize_title: int | float | None = None,
    fontsize_legend: int | float | None = None,
    linewidth_axes: float | None = None,
    colorbar_label: str = "FDR q-val",
) -> None:
    """
    Apply publication-quality styling to a specific matplotlib axes.

    This function formats an existing axes object with consistent styling
    including fonts, spine visibility, tick parameters, and colorbar formatting.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes object to format.
    fontsize_title : int, default: None
        Font size for axis labels and title.
        If None, uses cns.settings.fontsize_title.
    fontsize_legend : int, default: None
        Font size for tick labels and colorbar labels.
        If None, uses cns.settings.fontsize_legend.
    linewidth_axes : float, default: None
        Line width for axis spines.
        If None, uses cns.settings.linewidth_axes.
    colorbar_label : str, default: 'FDR q-val'
        Label for the colorbar (if present). Set to empty string '' to
        remove colorbar label.

    Returns
    -------
    None
        This function modifies the axes in-place.

    See Also
    --------
    setup_matplotlib : Configure global matplotlib styling.
    figure : Initialize a new figure.

    Notes
    -----
    This function applies the following formatting:

    **Font settings:**
    - Family: Sans-serif (Helvetica)
    - Sizes: title=8pt, tick labels=7pt (by default)
    - Color: Black

    **Axis spines:**
    - Visible: Bottom and left only
    - Hidden: Top and right
    - Line width: 0.5pt (by default)
    - Color: Black

    **Ticks:**
    - Size: 2pt length, 0.6pt width
    - Padding: 1pt
    - Color: Black
    - Rotation: 0 degrees

    **Other:**
    - Grid: Disabled
    - Margins: 5% on x and y axes
    - Colorbar: Formatted with matching font settings

    Useful for formatting axes created by external libraries (e.g., seaborn,
    scanpy, gseapy) to match cnsplots styling.

    Examples
    --------
    >>> import cnsplots as cns
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> ax.scatter(x, y)
    >>> cns.setup_ax(ax)

    >>> # Format with custom sizes
    >>> cns.setup_ax(ax, fontsize_title=10, fontsize_legend=9)

    >>> # Format axes from external library
    >>> import seaborn as sns
    >>> ax = sns.heatmap(data)
    >>> cns.setup_ax(ax, colorbar_label="Expression")
    """
    # Use settings values if parameters are not provided
    if fontsize_title is None:
        fontsize_title = cns.settings.fontsize_title
    if fontsize_legend is None:
        fontsize_legend = cns.settings.fontsize_legend
    if linewidth_axes is None:
        linewidth_axes = cns.settings.linewidth_axes

    mpl.rcParams.update(
        {
            "mathtext.fontset": "custom",
            "font.family": "sans-serif",
            "font.sans-serif": "Helvetica",
        }
    )
    ax.set_title(ax.get_title(), fontsize=fontsize_title, pad=4)
    ax.set_xlabel(ax.get_xlabel(), fontsize=fontsize_title, color="black")
    ax.set_ylabel(ax.get_ylabel(), fontsize=fontsize_title, color="black")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_linewidth(linewidth_axes)
    ax.spines["left"].set_linewidth(linewidth_axes)
    ax.spines["bottom"].set_color("black")
    ax.spines["left"].set_color("black")
    ax.tick_params(
        axis="x",
        labelsize=fontsize_legend,
        colors="black",
        length=2,
        width=0.6,
        pad=1,
        labelrotation=0,
    )
    ax.tick_params(
        axis="y",
        labelsize=fontsize_legend,
        colors="black",
        length=2,
        width=0.6,
        pad=1,
        labelrotation=0,
    )
    ax.grid(False)
    ax.margins(x=0.05, y=0.05)
    cbar = ax.collections[0].colorbar if ax.collections else None
    if cbar is not None:
        cbar.ax.tick_params(labelsize=fontsize_legend)
        if colorbar_label:
            cbar.set_label(colorbar_label, fontsize=fontsize_title, color="black")


def setup_ggplot() -> str:
    """
    Generate R ggplot2 theme code matching cnsplots styling.

    This function returns an R code string defining a custom ggplot2 theme
    that matches the cnsplots matplotlib styling, enabling consistent
    visualization across Python and R workflows.

    Parameters
    ----------
    None

    Returns
    -------
    str
        R code string defining a custom ggplot2 theme (theme_custom).

    See Also
    --------
    setup_matplotlib : Configure matplotlib styling.
    setup_scanpy : Configure scanpy styling.

    Notes
    -----
    The returned R code defines a ggplot2 theme with:

    **Fonts:**
    - Size: 10pt for all text elements
    - Family: Sans-serif
    - Face: Plain (no bold or italic)
    - Color: Black

    **Grid:**
    - Major and minor grid lines: Disabled

    **Axes:**
    - Text size: 10pt
    - Title size: 10pt
    - Color: Black

    **Legend:**
    - Text size: 10pt
    - Title size: 10pt

    To use this theme in R:
    1. Copy the returned string to your R script
    2. Apply with: `plot + theme_custom`

    The theme follows the same minimalist design philosophy as cnsplots,
    with clean axes, no grid, and consistent typography.

    Examples
    --------
    >>> import cnsplots as cns
    >>> theme_code = cns.setup_ggplot()
    >>> print(theme_code)

    In R:
    >>> # Copy the theme code, then use:
    >>> p < -ggplot(data, aes(x=x, y=y)) + geom_point()
    >>> p + theme_custom
    """
    return """
    fontsize <- 10
    theme_custom <- theme(
      text = element_text(
        size = fontsize,
        color = 'black',
        family = "sans",
        face = "plain"
      ),
      panel.grid.major = element_blank(),
      panel.grid.minor = element_blank(),

      axis.text.x = element_text(
        size = fontsize,
        color = 'black'
      ),
      axis.text.y = element_text(
        size = fontsize,
        color = 'black'
      ),

      axis.title.x = element_text(
        size = fontsize,
        color = 'black'
      ),
      axis.title.y = element_text(
        size = fontsize,
        color = 'black'
      ),

      axis.title = element_text(
        size = fontsize,
        color = 'black',
        face = "plain"
      ),

      plot.title = element_text(
        size = fontsize,
        color = 'black',
        face = "plain"
      ),

      legend.text = element_text(size = fontsize),
      legend.title = element_text(size = fontsize)
    )
    """
