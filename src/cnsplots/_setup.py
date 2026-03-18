from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from matplotlib.axes import Axes

import matplotlib as mpl
from matplotlib import font_manager as fm

import cnsplots as cns

_HELVETICA_BOLD_REGISTERED = False
ColorCycle = Union[str, list[str]]


def _ensure_helvetica_bold() -> None:
    """
    Ensure matplotlib can resolve a true Helvetica bold face on macOS.
    """
    global _HELVETICA_BOLD_REGISTERED
    if _HELVETICA_BOLD_REGISTERED:
        return

    for font in fm.fontManager.ttflist:
        if font.name == "Helvetica" and int(font.weight) >= 700:
            _HELVETICA_BOLD_REGISTERED = True
            return

    if sys.platform != "darwin":
        return

    ttc_path = Path("/System/Library/Fonts/Helvetica.ttc")
    if not ttc_path.exists():
        return

    try:
        from fontTools.ttLib import TTCollection
    except Exception:
        return

    bold_ttf_path = Path.home() / ".cache" / "cnsplots" / "fonts" / "Helvetica-Bold.ttf"
    try:
        bold_ttf_path.parent.mkdir(parents=True, exist_ok=True)
        if not bold_ttf_path.exists():
            ttc = TTCollection(str(ttc_path))
            bold_face = None
            for face in ttc.fonts:
                family = (face["name"].getDebugName(1) or "").strip()
                subfamily = (face["name"].getDebugName(2) or "").strip().lower()
                if family == "Helvetica" and "bold" in subfamily:
                    bold_face = face
                    break
            if bold_face is None:
                return
            bold_face.save(str(bold_ttf_path))

        fm.fontManager.addfont(str(bold_ttf_path))
    except Exception:
        return

    for font in fm.fontManager.ttflist:
        if font.name == "Helvetica" and int(font.weight) >= 700:
            _HELVETICA_BOLD_REGISTERED = True
            return


def _validate_title_fontweight(value: str | int | None) -> str | int:
    """
    Validate font weight values against the public setup/settings contract.
    """
    if value is None or isinstance(value, bool) or not isinstance(value, (str, int)):
        raise TypeError("title_fontweight must be a string or integer")
    return value


def _font_rcparams() -> dict[str, object]:
    """Return the shared font-related matplotlib rcParams."""
    return {
        "mathtext.fontset": cns.settings.mathtext_fontset,
        "font.family": cns.settings.font_family,
        "font.sans-serif": list(cns.settings.font_sans_serif),
    }


def _resolve_legend_fontsizes(
    title_fontsize: int | float,
) -> tuple[int | float, int | float]:
    """Resolve legend font sizes while preserving title-font inheritance."""
    legend_fontsize = cns.settings.legend_fontsize
    if legend_fontsize is None:
        legend_fontsize = title_fontsize

    legend_title_fontsize = cns.settings.legend_title_fontsize
    if legend_title_fontsize is None:
        legend_title_fontsize = title_fontsize

    return legend_fontsize, legend_title_fontsize


def setup_matplotlib(
    color_cycle: ColorCycle | None = None,
    color_map: str | None = None,
    title_fontsize: int | float | None = None,
    title_fontweight: str | int | None = None,
    fontsize_legend: int | float | None = None,
    axes_linewidth: float | None = None,
) -> None:
    """
    Configure matplotlib with publication-quality default styling.

    This function sets up matplotlib with custom styling optimized for
    scientific publications, including font settings, color palettes,
    axis styling, and export parameters.

    Parameters
    ----------
    color_cycle : str or list of str, default: None
        Name of the qualitative color palette for the default color cycle, or
        an explicit list of colors. If None, uses cns.settings.palette_qual.
        Named options include: 'Set1', 'Set2', 'Dark2',
        'Ecotyper1'-'Ecotyper6', 'Tableau', 'Bold', 'ECharts', etc.
    color_map : str, default: None
        Name of the sequential colormap for continuous data.
        If None, uses cns.settings.palette_seq.
        Options include: 'gnuplot', 'parula', 'bwr', 'hot', 'BuRd_custom',
        'WhYlOrRd_custom', etc.
    title_fontsize : int, default: None
        Font size for titles, axis labels, and legend titles.
        If None, uses cns.settings.title_fontsize.
    title_fontweight : str | int, default: None
        Font weight for titles.
        If None, uses cns.settings.title_fontweight.
    fontsize_legend : int, default: None
        Font size for tick labels and legend text.
        If None, uses cns.settings.fontsize_legend.
    axes_linewidth : float, default: None
        Line width for axis spines.
        If None, uses cns.settings.axes_linewidth.

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
    - Title weight: bold (by default)

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
    ...     color_cycle="Set2",
    ...     color_map="parula",
    ...     title_fontsize=10,
    ...     title_fontweight="normal",
    ...     fontsize_legend=8,
    ... )
    """
    # Use settings values if parameters are not provided
    if color_cycle is None:
        color_cycle = cns.settings.palette_qual
    if color_map is None:
        color_map = cns.settings.palette_seq
    if title_fontsize is None:
        title_fontsize = cns.settings.title_fontsize
    if title_fontweight is None:
        title_fontweight = cns.settings.title_fontweight
    title_fontweight = _validate_title_fontweight(title_fontweight)
    if fontsize_legend is None:
        fontsize_legend = cns.settings.fontsize_legend
    if axes_linewidth is None:
        axes_linewidth = cns.settings.axes_linewidth

    _ensure_helvetica_bold()
    legend_fontsize, legend_title_fontsize = _resolve_legend_fontsizes(title_fontsize)

    def config() -> dict[str, object]:
        """
        Generate matplotlib rcParams configuration dictionary.

        Returns
        -------
        dict
            Configuration dictionary for matplotlib.rcParams.update().
        """
        return {
            **_font_rcparams(),
            "font.size": title_fontsize,
            "savefig.bbox": cns.settings.savefig_bbox,
            "savefig.pad_inches": cns.settings.savefig_pad_inches,
            "savefig.dpi": cns.settings.savefig_dpi,
            "savefig.transparent": cns.settings.savefig_transparent,
            "svg.fonttype": cns.settings.svg_fonttype,
            # Embed fonts as TrueType (Type 42) in the intermediate PDF so that
            # mutool can resolve every glyph back to a Unicode codepoint.  The
            # default Type 3 encoding has no Unicode map, causing math/symbol
            # glyphs (e.g. the minus sign in 10⁻⁹) to be converted to paths.
            "pdf.fonttype": cns.settings.pdf_fonttype,
            "axes.titlesize": title_fontsize,
            "axes.titleweight": title_fontweight,
            "axes.titlelocation": cns.settings.axes_titlelocation,
            "axes.labelsize": title_fontsize,
            "axes.grid": cns.settings.axes_grid,
            "axes.spines.top": cns.settings.axes_spines_top,
            "axes.spines.right": cns.settings.axes_spines_right,
            "axes.linewidth": axes_linewidth,
            "axes.edgecolor": cns.settings.axes_edgecolor,
            "axes.labelcolor": cns.settings.axes_labelcolor,
            "axes.labelpad": cns.settings.axes_labelpad,
            "axes.titlepad": cns.settings.axes_titlepad,
            "axes.xmargin": cns.settings.axes_xmargin,
            "axes.ymargin": cns.settings.axes_ymargin,
            "axes.prop_cycle": mpl.cycler(color=cns.palettes(color_cycle)),
            "image.cmap": color_map,
            "legend.fontsize": legend_fontsize,
            "legend.title_fontsize": legend_title_fontsize,
            "legend.frameon": cns.settings.legend_frameon,
            "legend.markerscale": cns.settings.legend_markerscale,
            "legend.handlelength": cns.settings.legend_handlelength,
            "legend.handleheight": cns.settings.legend_handleheight,
            "legend.handletextpad": cns.settings.legend_handletextpad,
            "xtick.labelsize": fontsize_legend,
            "xtick.bottom": cns.settings.xtick_bottom,
            "xtick.color": cns.settings.xtick_color,
            "xtick.major.size": cns.settings.xtick_major_size,
            "xtick.major.width": cns.settings.xtick_major_width,
            "xtick.major.pad": cns.settings.xtick_major_pad,
            "xtick.alignment": cns.settings.xtick_alignment,
            "ytick.labelsize": fontsize_legend,
            "ytick.left": cns.settings.ytick_left,
            "ytick.color": cns.settings.ytick_color,
            "ytick.major.size": cns.settings.ytick_major_size,
            "ytick.major.width": cns.settings.ytick_major_width,
            "ytick.major.pad": cns.settings.ytick_major_pad,
            "ytick.alignment": cns.settings.ytick_alignment,
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
        "NPG",
        "AAAS",
        "Lancet",
        "NEJM",
        "JAMA",
        "JCO",
        "OkabeIto",
        "TolBright",
        "TolMuted",
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
    scanpy.set_figure_params(
        scanpy=cns.settings.scanpy_use_default_style,
        figsize=cns.settings.scanpy_figsize,
        facecolor=cns.settings.scanpy_facecolor,
    )


def setup_ax(
    ax: Axes,
    title_fontsize: int | float | None = None,
    title_fontweight: str | int | None = None,
    fontsize_legend: int | float | None = None,
    axes_linewidth: float | None = None,
    colorbar_label: str | None = None,
) -> None:
    """
    Apply publication-quality styling to a specific matplotlib axes.

    This function formats an existing axes object with consistent styling
    including fonts, spine visibility, tick parameters, and colorbar formatting.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes object to format.
    title_fontsize : int, default: None
        Font size for axis labels and title.
        If None, uses cns.settings.title_fontsize.
    title_fontweight : str | int, default: None
        Font weight for the title.
        If None, uses cns.settings.title_fontweight.
    fontsize_legend : int, default: None
        Font size for tick labels and colorbar labels.
        If None, uses cns.settings.fontsize_legend.
    axes_linewidth : float, default: None
        Line width for axis spines.
        If None, uses cns.settings.axes_linewidth.
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
    - Title weight: bold (by default)
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

    >>> # Format with custom sizes and title weight
    >>> cns.setup_ax(
    ...     ax, title_fontsize=10, title_fontweight="normal", fontsize_legend=9
    ... )

    >>> # Format axes from external library
    >>> import seaborn as sns
    >>> ax = sns.heatmap(data)
    >>> cns.setup_ax(ax, colorbar_label="Expression")
    """
    # Use settings values if parameters are not provided
    if title_fontsize is None:
        title_fontsize = cns.settings.title_fontsize
    if title_fontweight is None:
        title_fontweight = cns.settings.title_fontweight
    title_fontweight = _validate_title_fontweight(title_fontweight)
    if fontsize_legend is None:
        fontsize_legend = cns.settings.fontsize_legend
    if axes_linewidth is None:
        axes_linewidth = cns.settings.axes_linewidth
    if colorbar_label is None:
        colorbar_label = cns.settings.setup_ax_colorbar_label

    _ensure_helvetica_bold()

    mpl.rcParams.update(_font_rcparams())
    title_props = ax.title.get_fontproperties().copy()
    title_props.set_size(title_fontsize)
    title_props.set_weight(title_fontweight)
    ax.set_title(
        ax.get_title(),
        fontproperties=title_props,
        loc=cns.settings.axes_titlelocation,
        pad=cns.settings.axes_titlepad,
    )
    ax.set_xlabel(
        ax.get_xlabel(),
        fontsize=title_fontsize,
        color=cns.settings.axes_labelcolor,
        labelpad=cns.settings.axes_labelpad,
    )
    ax.set_ylabel(
        ax.get_ylabel(),
        fontsize=title_fontsize,
        color=cns.settings.axes_labelcolor,
        labelpad=cns.settings.axes_labelpad,
    )
    ax.spines["top"].set_visible(cns.settings.axes_spines_top)
    ax.spines["right"].set_visible(cns.settings.axes_spines_right)
    for spine_name in ("top", "right", "bottom", "left"):
        ax.spines[spine_name].set_linewidth(axes_linewidth)
        ax.spines[spine_name].set_color(cns.settings.axes_edgecolor)
    ax.tick_params(
        axis="x",
        labelsize=fontsize_legend,
        colors=cns.settings.xtick_color,
        length=cns.settings.xtick_major_size,
        width=cns.settings.xtick_major_width,
        pad=cns.settings.xtick_major_pad,
        labelrotation=cns.settings.xtick_labelrotation,
        bottom=cns.settings.xtick_bottom,
    )
    ax.tick_params(
        axis="y",
        labelsize=fontsize_legend,
        colors=cns.settings.ytick_color,
        length=cns.settings.ytick_major_size,
        width=cns.settings.ytick_major_width,
        pad=cns.settings.ytick_major_pad,
        labelrotation=cns.settings.ytick_labelrotation,
        left=cns.settings.ytick_left,
    )
    for tick_label in ax.get_xticklabels():
        tick_label.set_horizontalalignment(cns.settings.xtick_alignment)
    for tick_label in ax.get_yticklabels():
        tick_label.set_verticalalignment(cns.settings.ytick_alignment)
    ax.grid(cns.settings.axes_grid)
    ax.margins(x=cns.settings.axes_xmargin, y=cns.settings.axes_ymargin)
    cbar = ax.collections[0].colorbar if ax.collections else None
    if cbar is not None:
        cbar.ax.tick_params(labelsize=fontsize_legend, colors=cns.settings.ytick_color)
        if colorbar_label:
            cbar.set_label(
                colorbar_label,
                fontsize=title_fontsize,
                color=cns.settings.axes_labelcolor,
            )


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
    fontsize = cns.settings.ggplot_fontsize
    font_family = json.dumps(cns.settings.ggplot_font_family)
    font_face = json.dumps(cns.settings.ggplot_font_face)
    text_color = json.dumps(cns.settings.ggplot_text_color)

    return f"""
    fontsize <- {fontsize}
    theme_custom <- theme(
      text = element_text(
        size = fontsize,
        color = {text_color},
        family = {font_family},
        face = {font_face}
      ),
      panel.grid.major = element_blank(),
      panel.grid.minor = element_blank(),

      axis.text.x = element_text(
        size = fontsize,
        color = {text_color}
      ),
      axis.text.y = element_text(
        size = fontsize,
        color = {text_color}
      ),

      axis.title.x = element_text(
        size = fontsize,
        color = {text_color}
      ),
      axis.title.y = element_text(
        size = fontsize,
        color = {text_color}
      ),

      axis.title = element_text(
        size = fontsize,
        color = {text_color},
        face = {font_face}
      ),

      plot.title = element_text(
        size = fontsize,
        color = {text_color},
        face = {font_face}
      ),

      legend.text = element_text(size = fontsize),
      legend.title = element_text(size = fontsize)
    )
    """
