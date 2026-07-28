from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd
    from anndata import AnnData
    from matplotlib.axes import Axes

import matplotlib.axes
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from mpl_toolkits.axes_grid1 import make_axes_locatable

from cnsplots._validation import (
    validate_adata_layer,
    validate_adata_obs_columns,
    validate_adata_uns_keys,
    validate_anndata,
)


def phyloplot(adata: AnnData, *, ax: Axes | None = None) -> Axes:
    import io

    import Bio.Phylo

    validate_anndata(adata, "adata", "phyloplot")
    validate_adata_layer(adata, "trisicell_output", "phyloplot")
    validate_adata_obs_columns(adata, "group", "phyloplot")
    validate_adata_uns_keys(adata, "tree", "phyloplot")

    tree = Bio.Phylo.read(io.StringIO(adata.uns["tree"]), "newick")
    cell_ids: list[str] = [
        cast(str, terminal.name) for terminal in tree.get_terminals()
    ]
    adata = cast(Any, adata)[cell_ids].copy()

    if ax is None:
        ax = plt.gca()
    heatmap_ax = ax
    divider = make_axes_locatable(heatmap_ax)
    tree_ax = divider.append_axes("left", size="33.333%", pad=0.01, sharey=ax)
    group_ax_1 = divider.append_axes("right", size="8.333%", pad=0.01, sharey=ax)
    group_ax_2 = divider.append_axes("right", size="8.333%", pad=0.01, sharey=ax)
    legend_ax = divider.append_axes("right", size="16.667%", pad=0.01)
    axes = [tree_ax, heatmap_ax, group_ax_1, group_ax_2, legend_ax]
    for ax in axes:
        ax.set_axis_off()
    with plt.rc_context({"lines.linewidth": 0.5}):
        Bio.Phylo.draw(tree, label_func=lambda _: "", axes=tree_ax, do_show=False)
    ax = sns.heatmap(
        adata.layers["trisicell_output"],
        ax=heatmap_ax,
        rasterized=True,
        # cbar_kws={"aspect": 0.5},
        cbar_ax=legend_ax,
        cmap="parula",
    )
    cbar = ax.collections[0].colorbar
    cbar.locator = plt.MaxNLocator(nbins=2)
    cbar.ax.set_rasterized(True)
    cbar.ax.set_aspect(0.5)
    obs_group = adata.obs[["group"]]
    _heatmap(
        obs_group,
        ax=group_ax_1,
        leg_ax=legend_ax,
        rasterized=True,
        palette="Set1",
    )
    _heatmap(
        obs_group,
        ax=group_ax_2,
        leg_ax=legend_ax,
        rasterized=True,
        palette="Set2",
    )
    return heatmap_ax


def _heatmap(
    data: pd.DataFrame | pd.Series | np.ndarray,
    cmap: dict[str, Any] | None = None,
    palette: str = "Set1",
    ax: Axes | None = None,
    legend: bool = True,
    leg_pos: str = "right",
    leg_ax: Axes | None = None,
    leg_kws: dict[str, Any] | None = None,
    **sns_kws: Any,
) -> tuple[Axes, dict[str, Any]]:
    """Class to plot categorical heatmap using seaborn.

    https://github.com/schlegelp/catheat
    https://github.com/mwaskom/seaborn/issues/1031
    Parameters
    ----------
    data :      rectangular dataset
                2D dataset that can be coerced into an ndarray. If a Pandas
                DataFrame is provided, the index/column information will be
                used to label the columns and rows.
    cmap :      dict, optional
                Colors for each category in the dataset. Missing colors will
                be added from the palette.
    palette :   matplotlib/seaborn color palette name or object, optional
                Palette to be used for heatmap.
    ax :        matplotlib ax, optional
    legend :    bool, optional
                If True, plot legend.
    leg_ax :    matplotlib axis, optional
                By default, will add legend to same ax as heatmap. Use this
                argument to explicitly set legend ax.
    leg_pos :   {'right', 'top'}
                Position of legend. Only relevant if legend ax is not
                explicitly provided via `leg_ax`.
    leg_kws :   dict, optional
                Keyword arguments passed to plt.legend()
    **sns_kws
                Keyword arguments passed through to `seaborn.heatmap()`
    Returns
    -------
    matplotlib axis
                    Heatmap axis as returned by seaborn.heatmap().
    colormap :      dict
                    Colormap mapping categorical values to RGB colours.
    """

    if cmap is None:
        cmap = {}
    if leg_kws is None:
        leg_kws = {}

    if not isinstance(data, (pd.DataFrame, pd.Series, np.ndarray)):
        raise TypeError(f'Unable to work with data of type "{type(data)}"')

    # If not provided, get ax
    if ax is None:
        ax = plt.gca()

    # Get unique values in dataset
    if isinstance(data, (pd.DataFrame, pd.Series)):
        unique_values = sorted(np.unique(data.values.astype(str)))
    else:
        unique_values = sorted(np.unique(data.astype(str)))

    n_unique = len(unique_values)

    # Prepare colors
    if not cmap:
        # Generate colors -> for the heatmap
        colors = _gen_colors(palette, n_unique)

        # We have colours, let's generate a cmap -> for the legend
        cmap = {v: colors[i] for i, v in enumerate(unique_values)}
    elif isinstance(cmap, dict):
        # Check for missing entries
        missing_entries = [v for v in unique_values if v not in cmap]

        # Generate missing colors
        colors = _gen_colors(palette, len(missing_entries))

        # Update colormap
        cmap.update({v: colors[i] for i, v in enumerate(missing_entries)})

        # Generate colours in order -> for legend
        colors = [cmap[cat] for cat in unique_values]
    else:
        raise TypeError(f'Unable to interpret colormap of type "{type(cmap)}"')

    # Turn data into numeric values
    vmap = {c: i for i, c in enumerate(unique_values)}

    def mapper(t):
        return vmap[str(t)]

    vfunc = np.vectorize(mapper)

    if isinstance(data, pd.DataFrame):
        numerical_data = data.applymap(mapper)
    elif isinstance(data, pd.Series):
        numerical_data = data.map(mapper).to_frame()
    elif isinstance(data, np.ndarray):
        numerical_data = vfunc(data)

    # Plot heatmap
    cmap_object = mcolors.LinearSegmentedColormap.from_list(
        "custom", colors, N=len(colors)
    )
    sns_ax = sns.heatmap(numerical_data, ax=ax, cmap=cmap_object, cbar=False, **sns_kws)

    # Add legend
    if legend:
        if not leg_ax:
            # Use the heatmap's ax if none provided
            leg_ax = sns_ax

            # Make heatmap a bit less wide
            box = sns_ax.get_position()
            sns_ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])

            # Add some default specific to using the heatmap for legend
            if leg_pos.lower() == "top":
                leg_kws["bbox_to_anchor"] = (0.0, 1.02, 1.0, 0.102)
                leg_kws["ncol"] = n_unique
            elif leg_pos.lower() == "right":
                leg_kws["bbox_to_anchor"] = (1.02, 0.0, 0.102, 1.0)
                leg_kws["ncol"] = 1
            leg_kws["labelspacing"] = 0.2

        elif not isinstance(leg_ax, matplotlib.axes.Axes):
            raise TypeError(f'leg_ax must be matplotlib axes, not "{type(leg_ax)}"')

        patches = [mpatches.Patch(facecolor=cmap[v]) for v in unique_values]

        _ = leg_ax.legend(patches, unique_values, **leg_kws)

    return sns_ax, cmap


def _is_categorical(
    x: pd.DataFrame | pd.Series | np.ndarray | str,
) -> bool | list[bool]:
    """Return True if data is categorical (i.e. not numerical)."""
    if isinstance(x, pd.DataFrame):
        num_cols = x.mean(axis=0).index.tolist()
        return [col not in num_cols for col in x.columns]
    elif isinstance(x, pd.Series):
        try:
            x.mean()
            return True
        except BaseException:
            return False
    elif isinstance(x, np.ndarray):
        arr = np.asarray(x)
        if arr.ndim > 2:
            raise ValueError("Can only process 1d or 2d arrays.")
        elif arr.ndim == 2:
            cat_cols: list[bool] = []
            for i in range(arr.shape[1]):
                try:
                    arr[:, i].astype(int)
                    cat_cols.append(False)
                except BaseException:
                    cat_cols.append(True)
            return cat_cols
        elif arr.ndim == 1:
            try:
                arr.astype(int)
                return False
            except BaseException:
                return True
    return False


def _gen_colors(
    pal: str | list[Any] | np.ndarray | mcolors.Colormap, n: int
) -> list[Any]:
    """Generate colours from provided palette."""
    colors: list

    # If string
    if isinstance(pal, str):
        # First, check if seaborn palette
        try:
            colors = sns.color_palette(pal, n)
        # If not, try getting the matplotlib palette
        except BaseException:
            cmap = plt.get_cmap(pal)
            colors = [cmap(i) for i in np.linspace(0, 1, n)]
    # If palette provided
    elif isinstance(pal, mcolors.Colormap):
        colors = [pal(i) for i in np.linspace(0, 1, n)]
    # If list of colors
    elif isinstance(pal, (list, np.ndarray)):
        if len(pal) < n:
            raise ValueError(
                f"Must provide at least as many colors as there are unique entries: {n}"
            )
        else:
            colors = list(pal)
    else:
        raise TypeError(f'Unable to generate colors from palette of type "{type(pal)}"')

    return colors
