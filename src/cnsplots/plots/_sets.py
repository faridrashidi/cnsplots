from collections.abc import Set as AbstractSet

import matplotlib.pyplot as plt
import seaborn as sns

import cnsplots as cns


def upsetplot(sets, **kwargs):
    """
    Create an UpSet plot for visualizing set intersections.

    This function creates an UpSet plot, an advanced alternative to Venn diagrams
    for visualizing intersections among multiple sets.

    Parameters
    ----------
    sets : dict
        Dictionary mapping set names (str) to sets or array-like collections.
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

    import upsetplot as usp

    sets = {k: (v if isinstance(v, set) else set(v)) for k, v in sets.items()}
    memberships = []
    for item in set.union(*sets.values()):
        membership = [name for name, s in sets.items() if item in s]
        memberships.append(membership)
    data = usp.from_memberships(memberships)
    # Set default subset_size to "count" to handle non-unique groups
    kwargs.setdefault("subset_size", "count")
    upset = usp.UpSet(data, element_size=17, show_counts="{:,}", **kwargs)
    axes = upset.plot()
    plt.grid(False)
    ax_tot = axes.get("totals")
    cns.setup_ax(axes["matrix"])
    cns.setup_ax(axes["shading"])
    cns.setup_ax(axes["intersections"])
    axes["matrix"].tick_params(axis="both", which="both", length=0)
    for txt in axes["intersections"].texts:
        txt.set_size(cns.settings.fontsize_legend)
    if ax_tot is not None:
        cns.setup_ax(ax_tot)
        for txt in ax_tot.texts:
            txt.set_size(cns.settings.fontsize_legend)
        pos_mat = ax_tot.get_position()
        dx = 0.03
        new_pos = [pos_mat.x0 + dx, pos_mat.y0, pos_mat.width, pos_mat.height]
        ax_tot.set_position(new_pos)

    return axes


def vennplot(lists, labels):
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
    ax = func(lists, labels, set_colors=colors, alpha=0.8)
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
