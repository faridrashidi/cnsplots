from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from matplotlib.figure import Figure

from collections.abc import Mapping
from collections.abc import Set as AbstractSet
import importlib
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

import cnsplots as cns


def _normalize_text_position(text: Any) -> None:
    """Coerce singleton array coordinates from upsetplot into scalar positions."""

    def _to_scalar(value: Any) -> Any:
        if isinstance(value, np.ndarray) and value.size == 1:
            return float(value.reshape(-1)[0])
        return value

    x, y = text.get_position()
    text.set_position((_to_scalar(x), _to_scalar(y)))


def _import_upsetplot_module() -> Any:
    """Import the third-party upsetplot package, avoiding local file shadowing."""

    def _path_contains_shadow_module(entry: str) -> bool:
        try:
            return (Path(entry or ".").resolve() / "upsetplot.py").is_file()
        except OSError:
            return False

    shadowed_module = sys.modules.get("upsetplot")
    shadowed_file = getattr(shadowed_module, "__file__", None)
    pruned_sys_path = [
        entry for entry in sys.path if not _path_contains_shadow_module(entry)
    ]
    removed_shadow_paths = len(pruned_sys_path) != len(sys.path)
    shadowed_local_module = bool(
        shadowed_file is not None
        and Path(str(shadowed_file)).name == "upsetplot.py"
        and not hasattr(shadowed_module, "from_memberships")
    )

    if not removed_shadow_paths and not shadowed_local_module:
        return importlib.import_module("upsetplot")

    original_sys_path = sys.path[:]
    try:
        sys.path[:] = pruned_sys_path
        if shadowed_local_module:
            sys.modules.pop("upsetplot", None)
        return importlib.import_module("upsetplot")
    finally:
        sys.path[:] = original_sys_path


def upsetplot(
    sets: Mapping[str, AbstractSet[Any] | list[Any]],
    *,
    fig: Figure | None = None,
    **kwargs: Any,
) -> dict:
    """
    Create an UpSet plot for visualizing set intersections.

    This function creates an UpSet plot, an advanced alternative to Venn diagrams
    for visualizing intersections among multiple sets.

    Parameters
    ----------
    sets : dict
        Dictionary mapping set names (str) to sets or array-like collections.
    fig : matplotlib.figure.Figure or None, optional
        Figure to draw the UpSet plot into. Defaults to a new figure.
    **kwargs
        Additional keyword arguments passed to `upsetplot.UpSet`.

    Returns
    -------
    dict
        Dictionary of matplotlib Axes objects from the UpSet plot.

    See Also
    --------
    vennplot : Create a Venn diagram for 2-3 sets.

    Examples
    --------
    >>> import cnsplots as cns
    >>> sets = {
    ...     "Set A": [1, 2, 3, 4, 5],
    ...     "Set B": [3, 4, 5, 6, 7],
    ...     "Set C": [5, 6, 7, 8, 9],
    ... }
    >>> axes = cns.upsetplot(sets)
    >>> axes["intersections"].set_ylabel("Intersection Size")

    >>> # Limit to larger intersections
    >>> axes = cns.upsetplot(sets, min_subset_size=10)
    """
    # Validate inputs
    if not isinstance(sets, dict):
        raise TypeError(
            f"[upsetplot] Parameter 'sets' must be a dictionary, got {type(sets).__name__}"
        )
    if not sets:
        raise ValueError("[upsetplot] Parameter 'sets' cannot be empty")

    usp = _import_upsetplot_module()

    normalized_sets: dict[str, set] = {
        k: (v if isinstance(v, set) else set(v)) for k, v in sets.items()
    }
    memberships = []
    all_items: set = set().union(*normalized_sets.values())
    for item in all_items:
        membership = [name for name, s in normalized_sets.items() if item in s]
        memberships.append(membership)
    data = usp.from_memberships(memberships)
    # Set defaults for compact, publication-style UpSet plots while allowing
    # callers to override them when a different layout is needed.
    kwargs.setdefault("subset_size", "count")
    kwargs.setdefault("element_size", 17)
    kwargs.setdefault("show_counts", "{:,}")
    upset = usp.UpSet(data, **kwargs)
    axes = upset.plot(fig=fig)
    plt.grid(False)
    for ax in axes.values():
        if ax is not None:
            ax.set_facecolor("none")
    plot_fig = next((ax.figure for ax in axes.values() if ax is not None), None)
    if plot_fig is not None and np.allclose(
        plot_fig.patch.get_facecolor(), (1.0, 1.0, 1.0, 1.0)
    ):
        plot_fig.patch.set_facecolor("none")
        plot_fig.patch.set_alpha(0)
    ax_tot = axes.get("totals")
    cns.setup_ax(axes["matrix"])
    cns.setup_ax(axes["shading"])
    axes["shading"].tick_params(axis="y", which="both", length=0, left=False)
    cns.setup_ax(axes["intersections"])
    axes["matrix"].tick_params(axis="both", which="both", length=0)
    for txt in axes["intersections"].texts:
        _normalize_text_position(txt)
        txt.set_size(cns.settings.fontsize_legend)
    if ax_tot is not None:
        cns.setup_ax(ax_tot)
        for txt in ax_tot.texts:
            _normalize_text_position(txt)
            txt.set_size(cns.settings.fontsize_legend)
        pos_mat = ax_tot.get_position()
        dx = 0.03
        new_pos = [pos_mat.x0 + dx, pos_mat.y0, pos_mat.width, pos_mat.height]
        ax_tot.set_position(new_pos)

    return axes


def vennplot(lists: list[set], labels: tuple[str, ...] | list[str]) -> Any:
    """
    Create a Venn diagram for 2 or 3 sets.

    This function generates a Venn diagram showing overlaps between 2 or 3 sets
    using colored, semi-transparent circles with intersection counts.

    Parameters
    ----------
    lists : list of set or array-like
        List of 2 or 3 sets or array-like collections to compare.
    labels : tuple or list of str
        Labels for each set, in the same order as lists.

    Returns
    -------
    matplotlib_venn.VennDiagram
        The Venn diagram object containing the plot elements.

    See Also
    --------
    upsetplot : Create an UpSet plot for multiple set intersections.

    Examples
    --------
    >>> import cnsplots as cns
    >>> set1 = {1, 2, 3, 4, 5}
    >>> set2 = {3, 4, 5, 6, 7}
    >>> set3 = {5, 6, 7, 8, 9}
    >>> venn = cns.vennplot([set1, set2], labels=["Group A", "Group B"])

    >>> # Three-way Venn diagram
    >>> venn = cns.vennplot(
    ...     [set1, set2, set3], labels=["Treatment A", "Treatment B", "Treatment C"]
    ... )
    """
    # Validate inputs
    if not isinstance(lists, list):
        raise TypeError(
            f"[vennplot] Parameter 'lists' must be a list, got {type(lists).__name__}"
        )
    if len(lists) not in [2, 3]:
        raise ValueError(
            f"[vennplot] Parameter 'lists' must contain 2 or 3 sets, got {len(lists)}"
        )
    if len(labels) != len(lists):
        raise ValueError(
            f"[vennplot] Length of 'labels' ({len(labels)}) must match length of 'lists' ({len(lists)})"
        )

    import matplotlib_venn as venn

    lists = [s if isinstance(s, AbstractSet) else set(s) for s in lists]
    func: Any
    if len(lists) == 2:
        areas = ["10", "01", "11"]
        func = venn.venn2
        names = ["A", "B"]
        colors = sns.color_palette(n_colors=2)
    else:
        areas = ["100", "010", "001", "110", "101", "011", "111"]
        func = venn.venn3
        names = ["A", "B", "C"]
        colors = sns.color_palette(n_colors=3)
    ax = func(lists, tuple(labels), set_colors=colors, alpha=0.8)  # type: ignore[arg-type]
    for area in areas:
        try:
            ax.get_label_by_id(area).set_fontsize(6)
            ax.get_patch_by_id(area).set_edgecolor("black")
            ax.get_patch_by_id(area).set_linewidth(0.5)
        except AttributeError:
            pass
    for area in names:
        ax.get_label_by_id(area).set_fontsize(7)

    return ax
