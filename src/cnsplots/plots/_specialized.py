from __future__ import annotations

from itertools import combinations
from typing import Any, Literal

import matplotlib.pyplot as plt
import num2tex
import numpy as np
import pandas as pd
import seaborn as sns
from anndata import AnnData
from matplotlib.axes import Axes
from matplotlib.patches import Circle, FancyBboxPatch, Polygon
from mpl_toolkits.axes_grid1 import make_axes_locatable
from sklearn.metrics import auc, roc_curve
from statsmodels.stats.multitest import multipletests

import cnsplots.helpers._roc as helper_roc
import cnsplots.helpers._sankey as helper_sankey
from cnsplots._utils import _legend_fontsize
from cnsplots._validation import (
    validate_anndata,
    validate_binary_column,
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
    validate_no_nulls,
)


_FOREST_LABEL = "_forest_label"
_FOREST_ESTIMATE = "_forest_estimate"
_FOREST_LOWER = "_forest_lower"
_FOREST_UPPER = "_forest_upper"
_FOREST_PVALUE = "_forest_pvalue"
_FOREST_GROUP = "_forest_group"
_FOREST_HUE = "_forest_hue"
_FOREST_ALL = "__forest_all__"
_P_ADJUST_METHODS = ("bonferroni", "holm", "fdr_bh", "fdr_by")


def placeholderplot(description: str, *, ax: Axes | None = None) -> Axes:
    """
    Create a stylized placeholder panel for figure layout mockups.

    This helper clears the current axes, draws a rounded placeholder card with
    a mock image area, and places wrapped descriptive text in a centered
    caption area.

    Parameters
    ----------
    description : str
        Text to display in the center of the placeholder panel.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. If None, uses the current axes.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the placeholder panel.

    See Also
    --------
    figure : Initialize a new figure with custom size and styling.
    multipanel : Create multi-panel figures with automatic layout.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.figure(200, 100)
    >>> ax = cns.placeholderplot("A description to be centered in the panel")
    >>> ax.set_title("Placeholder")
    """
    if not isinstance(description, str):
        raise TypeError("[placeholderplot] 'description' must be a string.")

    if ax is None:
        ax = plt.gca()
    ax.cla()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.add_patch(
        FancyBboxPatch(
            (0.02, 0.02),
            0.96,
            0.96,
            transform=ax.transAxes,
            boxstyle="round,pad=0.02,rounding_size=0.01",
            facecolor="#EEF1F4",
            edgecolor="#B8C0CC",
            linewidth=0.9,
            clip_on=False,
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (0.08, 0.34),
            0.84,
            0.44,
            transform=ax.transAxes,
            boxstyle="round,pad=0.015,rounding_size=0.01",
            facecolor="#E0E5EB",
            edgecolor="#C5CCD6",
            linewidth=0.8,
        )
    )
    ax.add_patch(
        Circle(
            (0.77, 0.68),
            0.045,
            transform=ax.transAxes,
            facecolor="#C7D0DB",
            edgecolor="none",
        )
    )
    ax.add_patch(
        Polygon(
            [(0.15, 0.38), (0.34, 0.60), (0.52, 0.38)],
            closed=True,
            transform=ax.transAxes,
            facecolor="#B7C2D0",
            edgecolor="none",
        )
    )
    ax.add_patch(
        Polygon(
            [(0.36, 0.38), (0.58, 0.55), (0.82, 0.38)],
            closed=True,
            transform=ax.transAxes,
            facecolor="#A8B5C5",
            edgecolor="none",
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (0.13, 0.10),
            0.74,
            0.14,
            transform=ax.transAxes,
            boxstyle="round,pad=0.015,rounding_size=0.01",
            facecolor="#F8F9FB",
            edgecolor="none",
        )
    )
    ax.text(
        0.5,
        0.17,
        description,
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontfamily=plt.rcParams["font.family"],
        fontsize=plt.rcParams["axes.labelsize"],
        fontweight=plt.rcParams["axes.titleweight"],
        color="#59616B",
        wrap=True,
    )
    ax.set_axis_off()
    return ax


def sankeyplot(
    data: pd.DataFrame,
    x: list[str],
    label_rotation: float = 0,
    *,
    ax: Axes | None = None,
) -> Axes:
    """
    Create a Sankey diagram showing flows across categorical variables.

    This function generates a Sankey (alluvial) diagram visualizing the flow
    and connections between categories in two or more ordered stages.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to visualize.
    x : list of str
        Ordered list of two or more stage columns.
    label_rotation : float, default: 0
        Rotation angle, in degrees, applied to all Sankey category labels.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. If None, uses the current axes.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    stackplot : Create a stacked bar plot for categorical distributions.
    vennplot : Create a Venn diagram for set overlaps.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.sankeyplot(data=df, x=["initial_diagnosis", "final_diagnosis"])
    >>> ax.set_title("Diagnosis Flow")

    >>> # Patient flow across treatment stages
    >>> ax = cns.sankeyplot(
    ...     data=df,
    ...     x=["baseline_response", "week_4_response", "week_12_response"],
    ...     label_rotation=90,
    ... )
    """
    # Validate inputs
    validate_dataframe(data, "data", "sankeyplot")
    validate_dataframe_not_empty(data, "sankeyplot")

    if not isinstance(x, list):
        raise TypeError("[sankeyplot] 'x' must be a list of column names.")
    if len(x) < 2:
        raise ValueError("[sankeyplot] 'x' must contain at least two stage columns.")
    if not all(isinstance(column, str) for column in x):
        raise TypeError("[sankeyplot] Every stage column in 'x' must be a string.")

    validate_columns_exist(data, x, "sankeyplot")

    if ax is None:
        ax = plt.gca()
    if len(x) == 2:
        keys = np.union1d(data[x[0]].unique(), data[x[1]].unique())
    else:
        validate_no_nulls(data, x, "sankeyplot")
        keys = pd.unique(pd.concat([data[column] for column in x], ignore_index=True))
    colors = sns.color_palette(n_colors=len(keys))
    color_dict = dict(zip(keys, colors))
    if len(x) == 2:
        helper_sankey.sankeyplot(
            data[x[0]],
            data[x[1]],
            fontsize=_legend_fontsize(),
            colorDict=color_dict,
            label_rotation=label_rotation,
            ax=ax,
        )
    else:
        helper_sankey.multistage_sankeyplot(
            data,
            x,
            fontsize=_legend_fontsize(),
            colorDict=color_dict,
            label_rotation=label_rotation,
            ax=ax,
        )
    return ax


def phyloplot(adata: AnnData, *, ax: Axes | None = None) -> Axes:
    """
    Create a phylogenetic tree plot with associated heatmaps.

    Parameters
    ----------
    adata : AnnData
        Annotated data matrix containing tree structure and annotations.
    ax : matplotlib.axes.Axes, optional
        Host axes for the phylogenetic heatmap. If None, uses the current axes.

    Returns
    -------
    matplotlib.axes.Axes
        The host Axes containing the mutation heatmap.

    See Also
    --------
    heatmapplot : Create a clustered heatmap.

    Examples
    --------
    >>> import cnsplots as cns
    >>> cns.phyloplot(adata)
    """
    # Validate inputs
    validate_anndata(adata, "adata", "phyloplot")

    import cnsplots.helpers._phylo as helper_phylo

    if ax is None:
        ax = plt.gca()
    return helper_phylo.phyloplot(adata, ax=ax)


def _complete_forest_order(
    observed: list[Any], requested: list[Any] | None, parameter: str
) -> list[Any]:
    """Return a complete explicit order or preserve first appearance."""
    if requested is None:
        return observed
    if not isinstance(requested, list):
        raise TypeError(f"[forestplot] '{parameter}' must be a list or None.")
    if (
        len(requested) != len(observed)
        or len(set(requested)) != len(requested)
        or set(requested) != set(observed)
    ):
        raise ValueError(
            f"[forestplot] '{parameter}' must contain every observed value exactly "
            f"once. Observed values: {observed}"
        )
    return list(requested)


def _validate_normalized_forest_data(data: pd.DataFrame, *, has_pvalue: bool) -> None:
    """Validate normalized forest-plot values."""
    columns = [
        _FOREST_LABEL,
        _FOREST_ESTIMATE,
        _FOREST_LOWER,
        _FOREST_UPPER,
        _FOREST_GROUP,
        _FOREST_HUE,
    ]
    if has_pvalue:
        columns.append(_FOREST_PVALUE)
    validate_no_nulls(data, columns, "forestplot")

    numeric_columns = [_FOREST_ESTIMATE, _FOREST_LOWER, _FOREST_UPPER]
    if has_pvalue:
        numeric_columns.append(_FOREST_PVALUE)
    for column in numeric_columns:
        values = data[column]
        if (
            not pd.api.types.is_numeric_dtype(values.dtype)
            or pd.api.types.is_bool_dtype(values.dtype)
            or np.iscomplexobj(values.to_numpy())
        ):
            raise ValueError(
                f"[forestplot] Column '{column}' must contain real numeric values."
            )
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(
                f"[forestplot] Column '{column}' must contain only finite values."
            )

    invalid_bounds = (data[_FOREST_LOWER] > data[_FOREST_ESTIMATE]) | (
        data[_FOREST_ESTIMATE] > data[_FOREST_UPPER]
    )
    if invalid_bounds.any():
        raise ValueError(
            "[forestplot] Confidence intervals must satisfy "
            "lower <= estimate <= upper for every row."
        )
    if has_pvalue and ((data[_FOREST_PVALUE] <= 0) | (data[_FOREST_PVALUE] > 1)).any():
        raise ValueError(
            "[forestplot] P-values must be greater than 0 and less than or equal to 1."
        )
    if data.duplicated([_FOREST_GROUP, _FOREST_LABEL, _FOREST_HUE]).any():
        raise ValueError(
            "[forestplot] Each group, label, and hue combination must identify "
            "exactly one row."
        )


def _normalize_forest_table(
    data: pd.DataFrame,
    *,
    label: str | None,
    estimate: str | None,
    lower: str | None,
    upper: str | None,
    pvalue: str | None,
    group: str | None,
    hue: str | None,
) -> tuple[pd.DataFrame, bool, bool, bool]:
    """Map a caller-supplied results table to the forest renderer schema."""
    validate_dataframe(data, "data", "forestplot")
    validate_dataframe_not_empty(data, "forestplot")
    mappings = {
        "label": label,
        "estimate": estimate,
        "lower": lower,
        "upper": upper,
    }
    missing_mappings = [name for name, column in mappings.items() if column is None]
    if missing_mappings:
        raise ValueError(
            "[forestplot] DataFrame input requires column mappings for "
            f"{missing_mappings}."
        )
    assert label is not None
    assert estimate is not None
    assert lower is not None
    assert upper is not None

    selected_columns = [label, estimate, lower, upper]
    selected_columns.extend(
        column for column in [pvalue, group, hue] if column is not None
    )
    validate_columns_exist(data, selected_columns, "forestplot")

    normalized = pd.DataFrame(
        {
            _FOREST_LABEL: data[label],
            _FOREST_ESTIMATE: data[estimate],
            _FOREST_LOWER: data[lower],
            _FOREST_UPPER: data[upper],
            _FOREST_GROUP: data[group] if group is not None else _FOREST_ALL,
            _FOREST_HUE: data[hue] if hue is not None else _FOREST_ALL,
        }
    )
    if pvalue is not None:
        normalized[_FOREST_PVALUE] = data[pvalue]
    normalized = normalized.reset_index(drop=True)
    _validate_normalized_forest_data(normalized, has_pvalue=pvalue is not None)
    return normalized, group is not None, hue is not None, pvalue is not None


def _normalize_forest_model(
    model: object,
) -> tuple[pd.DataFrame, bool, bool, bool, float, str, str | None]:
    """Map a supported fitted model to the forest renderer schema."""
    if not hasattr(model, "results"):
        raise ValueError(
            "[forestplot] Model object must have a 'results' attribute containing "
            "fitted model results."
        )
    if not hasattr(model, "name"):
        raise ValueError(
            "[forestplot] Model object must have a 'name' attribute indicating "
            "model type."
        )

    results = getattr(model, "results")
    model_name = getattr(model, "name")
    validate_dataframe(results, "model.results", "forestplot")
    if not isinstance(results, pd.DataFrame):
        raise TypeError(
            "[forestplot] Internal type validation failed for 'model.results'."
        )
    validate_dataframe_not_empty(results, "forestplot")

    if model_name == "cox":
        validate_columns_exist(
            results,
            ["display_label", "exp(coef)", "hue_group"],
            "forestplot",
        )
        absolute_bounds = {
            "exp(coef) lower 95%",
            "exp(coef) upper 95%",
        }
        if absolute_bounds <= set(results.columns):
            lower_values = results["exp(coef) lower 95%"]
            upper_values = results["exp(coef) upper 95%"]
        else:
            validate_columns_exist(
                results,
                ["exp(coef) lower_err", "exp(coef) upper_err"],
                "forestplot",
            )
            lower_values = results["exp(coef)"] - results["exp(coef) lower_err"]
            upper_values = results["exp(coef)"] + results["exp(coef) upper_err"]
        if "p" in results:
            pvalues = results["p"]
        else:
            validate_columns_exist(results, ["log10_pvalue"], "forestplot")
            pvalues = np.power(10.0, -results["log10_pvalue"])
        normalized = pd.DataFrame(
            {
                _FOREST_LABEL: results["display_label"],
                _FOREST_ESTIMATE: results["exp(coef)"],
                _FOREST_LOWER: lower_values,
                _FOREST_UPPER: upper_values,
                _FOREST_PVALUE: pvalues,
                _FOREST_GROUP: _FOREST_ALL,
                _FOREST_HUE: results["hue_group"],
            }
        )
        reference = 1.0
        x_label = "Hazard ratio (95% CI)"
    elif model_name == "logistic":
        validate_columns_exist(
            results,
            ["predictor", "auc", "lower_ci", "upper_ci", "hue_group"],
            "forestplot",
        )
        normalized = pd.DataFrame(
            {
                _FOREST_LABEL: results["predictor"],
                _FOREST_ESTIMATE: results["auc"],
                _FOREST_LOWER: results["auc"] - results["lower_ci"],
                _FOREST_UPPER: results["auc"] + results["upper_ci"],
                _FOREST_GROUP: _FOREST_ALL,
                _FOREST_HUE: results["hue_group"],
            }
        )
        reference = 0.5
        x_label = "AUC (95% CI)"
    else:
        raise ValueError(
            f"[forestplot] Unsupported fitted model type {model_name!r}. Pass a "
            "results DataFrame with explicit column mappings instead."
        )

    normalized = normalized.reset_index(drop=True)
    has_pvalue = model_name == "cox"
    _validate_normalized_forest_data(normalized, has_pvalue=has_pvalue)
    hue_title = getattr(model, "hue", None)
    has_hue = hue_title is not None or normalized[_FOREST_HUE].nunique() > 1
    return normalized, False, has_hue, has_pvalue, reference, x_label, hue_title


def _draw_forestplot(
    data: pd.DataFrame,
    *,
    has_group: bool,
    has_hue: bool,
    has_pvalue: bool,
    group_order: list[Any] | None,
    order: list[Any] | None,
    hue_order: list[Any] | None,
    reference: float | None,
    xlabel: str,
    hue_title: str | None,
    bar_width: float | None,
    add_pvalue: bool,
    ax: Axes,
) -> Axes:
    """Draw normalized effect estimates and optional p-values."""
    if not has_group and group_order is not None:
        raise ValueError("[forestplot] 'group_order' requires a 'group' column.")
    if not has_hue and hue_order is not None:
        raise ValueError("[forestplot] 'hue_order' requires a 'hue' column.")

    observed_groups = data[_FOREST_GROUP].drop_duplicates().tolist()
    observed_labels = data[_FOREST_LABEL].drop_duplicates().tolist()
    observed_hues = data[_FOREST_HUE].drop_duplicates().tolist()
    groups = _complete_forest_order(observed_groups, group_order, "group_order")
    labels = (
        None
        if order is None
        else _complete_forest_order(observed_labels, order, "order")
    )
    hues = _complete_forest_order(observed_hues, hue_order, "hue_order")

    row_specs: list[tuple[str, Any, Any | None]] = []
    for group_value in groups:
        group_data = data[data[_FOREST_GROUP] == group_value]
        if has_group:
            row_specs.append(("group", group_value, None))
        group_labels = (
            group_data[_FOREST_LABEL].drop_duplicates().tolist()
            if labels is None
            else labels
        )
        for label_value in group_labels:
            if (group_data[_FOREST_LABEL] == label_value).any():
                row_specs.append(("label", group_value, label_value))

    tick_positions = list(reversed(range(len(row_specs))))
    label_positions = {
        (group_value, label_value): position
        for (kind, group_value, label_value), position in zip(row_specs, tick_positions)
        if kind == "label"
    }
    tick_labels = [
        str(group_value) if kind == "group" else f"  {label_value}"
        for kind, group_value, label_value in row_specs
    ]
    if not has_group:
        tick_labels = [label.lstrip() for label in tick_labels]

    colors = sns.color_palette(n_colors=len(hues))
    color_map = dict(zip(hues, colors))
    offsets = np.linspace(-0.15, 0.15, len(hues)) if len(hues) > 1 else [0.0]
    hue_offset_map = dict(zip(hues, offsets))

    for hue_value in hues:
        hue_data = data[data[_FOREST_HUE] == hue_value]
        y_coords = [
            label_positions[(row[_FOREST_GROUP], row[_FOREST_LABEL])]
            + hue_offset_map[hue_value]
            for _, row in hue_data.iterrows()
        ]
        estimates = hue_data[_FOREST_ESTIMATE].to_numpy(dtype=float)
        lower_errors = estimates - hue_data[_FOREST_LOWER].to_numpy(dtype=float)
        upper_errors = hue_data[_FOREST_UPPER].to_numpy(dtype=float) - estimates
        ax.errorbar(
            estimates,
            y_coords,
            xerr=[lower_errors, upper_errors],
            fmt="s",
            color=color_map[hue_value],
            markeredgewidth=0.8,
            elinewidth=0.8,
            capsize=2,
            markersize=3,
            label=hue_value,
        )

    ax.set_yticks(tick_positions)
    ax.set_yticklabels(tick_labels)
    for tick_label, (kind, _, _) in zip(ax.get_yticklabels(), row_specs):
        if kind == "group":
            tick_label.set_fontweight("bold")
    ax.set_ylim(-0.5, len(row_specs) - 0.5)
    ax.set_xlabel(xlabel)
    ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=5))
    if len(hues) > 1:
        ax.legend(title=hue_title, loc="lower right")
    if reference is not None:
        ax.axvline(x=reference, color="red", linestyle="--", linewidth=0.8)

    if has_pvalue and add_pvalue:
        divider = make_axes_locatable(ax)
        pvalue_ax = divider.append_axes("right", size="60%", pad=0.1)
        resolved_bar_width = bar_width
        if resolved_bar_width is None:
            resolved_bar_width = 0.8 / len(hues) if len(hues) > 1 else 0.6
        for _, row in data.iterrows():
            hue_index = hues.index(row[_FOREST_HUE])
            bar_position = label_positions[(row[_FOREST_GROUP], row[_FOREST_LABEL])]
            if len(hues) > 1:
                bar_position += (hue_index - (len(hues) - 1) / 2) * resolved_bar_width
            pvalue_ax.barh(
                bar_position,
                -np.log10(row[_FOREST_PVALUE]),
                height=resolved_bar_width,
                color=color_map[row[_FOREST_HUE]],
                edgecolor=None,
            )
        pvalue_ax.set_yticks(tick_positions)
        pvalue_ax.set_yticklabels([])
        pvalue_ax.set_xlabel("\u2013log10(p-value)")
        pvalue_ax.axvline(
            x=-np.log10(0.05),
            color="red",
            linestyle="--",
            linewidth=0.8,
            alpha=0.7,
        )
        pvalue_ax.set_ylim(-0.5, len(row_specs) - 0.5)
        pvalue_ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=5))

    return ax


def forestplot(
    model: object | pd.DataFrame | None = None,
    bar_width: float | None = None,
    add_pvalue: bool = True,
    *,
    data: pd.DataFrame | None = None,
    label: str | None = None,
    estimate: str | None = None,
    lower: str | None = None,
    upper: str | None = None,
    pvalue: str | None = None,
    group: str | None = None,
    hue: str | None = None,
    order: list[Any] | None = None,
    group_order: list[Any] | None = None,
    hue_order: list[Any] | None = None,
    reference: float | None = None,
    xlabel: str | None = None,
    ax: Axes | None = None,
) -> Axes:
    """
    Create a forest plot from a results table or fitted model.

    DataFrame input supports any effect measure with explicit columns for its
    estimate and confidence interval. CoxModel and LogisticModel inputs retain
    the model-specific labels and reference lines used by earlier releases.

    Parameters
    ----------
    model : CoxModel, LogisticModel, or pandas.DataFrame, optional
        Fitted model to adapt, or a results DataFrame passed positionally. Use
        either ``model`` or ``data``, not both.
    bar_width : float or None, optional
        Width of bars in the p-value panel. If None, uses ``0.8 / n_hue_groups``
        for multiple hue groups and ``0.6`` otherwise.
    add_pvalue : bool, default: True
        Add a ``-log10(p)`` bar panel when p-values are available.
    data : pandas.DataFrame, optional
        Results table. Table input requires ``label``, ``estimate``, ``lower``,
        and ``upper`` column mappings.
    label : str, optional
        Column containing row labels.
    estimate : str, optional
        Column containing effect estimates.
    lower, upper : str, optional
        Columns containing absolute lower and upper confidence bounds.
    pvalue : str, optional
        Column containing raw p-values greater than 0 and at most 1.
    group : str, optional
        Column defining labeled row sections.
    hue : str, optional
        Column defining offset, color-coded estimates within each row.
    order, group_order, hue_order : list, optional
        Complete display orders for labels, groups, and hue levels. Each list
        must contain every observed value exactly once.
    reference : float, optional
        Position of the vertical reference line. Table input draws no reference
        line by default. Cox and logistic models default to 1 and 0.5.
    xlabel : str, optional
        Label for the estimate axis. Defaults to the estimate column name for
        table input and the model-specific effect label for fitted models.
    ax : matplotlib.axes.Axes, optional
        Axes for the primary forest panel. The p-value panel is appended to it.

    Returns
    -------
    matplotlib.axes.Axes
        The primary forest-plot Axes.

    See Also
    --------
    survivalplot : Create a Kaplan-Meier survival plot.
    rocplot : Create an ROC curve plot.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.forestplot(
    ...     data=results,
    ...     label="term",
    ...     estimate="effect",
    ...     lower="ci_low",
    ...     upper="ci_high",
    ...     pvalue="p",
    ...     group="analysis",
    ...     reference=1,
    ...     xlabel="Risk ratio (95% CI)",
    ... )

    >>> model.fit()
    >>> ax = cns.forestplot(model)
    """
    if model is None and data is None:
        raise ValueError("[forestplot] Pass exactly one of 'model' or 'data'.")
    if model is not None and data is not None:
        raise ValueError("[forestplot] Pass exactly one of 'model' or 'data'.")
    if bar_width is not None and (
        isinstance(bar_width, bool)
        or not isinstance(bar_width, (int, float, np.number))
        or not np.isfinite(bar_width)
        or bar_width <= 0
    ):
        raise ValueError("[forestplot] 'bar_width' must be a positive finite number.")
    if reference is not None and (
        isinstance(reference, bool)
        or not isinstance(reference, (int, float, np.number))
        or not np.isfinite(reference)
    ):
        raise ValueError("[forestplot] 'reference' must be a finite number or None.")
    if xlabel is not None and not isinstance(xlabel, str):
        raise TypeError("[forestplot] 'xlabel' must be a string or None.")

    source = data if data is not None else model
    if data is not None and not isinstance(data, pd.DataFrame):
        raise TypeError("[forestplot] 'data' must be a pandas DataFrame.")

    if isinstance(source, pd.DataFrame):
        normalized, has_group, has_hue, has_pvalue = _normalize_forest_table(
            source,
            label=label,
            estimate=estimate,
            lower=lower,
            upper=upper,
            pvalue=pvalue,
            group=group,
            hue=hue,
        )
        resolved_reference = reference
        resolved_xlabel = estimate if xlabel is None else xlabel
        assert resolved_xlabel is not None
        hue_title = hue
    else:
        table_parameters = {
            "label": label,
            "estimate": estimate,
            "lower": lower,
            "upper": upper,
            "pvalue": pvalue,
            "group": group,
            "hue": hue,
        }
        supplied_table_parameters = [
            name for name, value in table_parameters.items() if value is not None
        ]
        if supplied_table_parameters:
            raise TypeError(
                "[forestplot] Table column mappings are only valid with DataFrame "
                f"input: {supplied_table_parameters}"
            )
        assert source is not None
        (
            normalized,
            has_group,
            has_hue,
            has_pvalue,
            model_reference,
            model_xlabel,
            hue_title,
        ) = _normalize_forest_model(source)
        resolved_reference = model_reference if reference is None else reference
        resolved_xlabel = model_xlabel if xlabel is None else xlabel

    if ax is None:
        ax = plt.gca()
    return _draw_forestplot(
        normalized,
        has_group=has_group,
        has_hue=has_hue,
        has_pvalue=has_pvalue,
        group_order=group_order,
        order=order,
        hue_order=hue_order,
        reference=resolved_reference,
        xlabel=resolved_xlabel,
        hue_title=hue_title,
        bar_width=bar_width,
        add_pvalue=add_pvalue,
        ax=ax,
    )


def _resolve_roc_pairs(
    pred_prob_cols: list[str],
    pairs: Literal["all"] | list[tuple[str, str]] | None,
) -> list[tuple[str, str]]:
    """Validate and resolve requested ROC comparisons."""
    if pairs is None:
        return []
    if len(set(pred_prob_cols)) != len(pred_prob_cols):
        raise ValueError(
            "[rocplot] Prediction columns must be unique when requesting comparisons."
        )
    if pairs == "all":
        if len(pred_prob_cols) < 2:
            raise ValueError(
                "[rocplot] pairs='all' requires at least two prediction columns."
            )
        return list(combinations(pred_prob_cols, 2))
    if not isinstance(pairs, list):
        raise ValueError(
            "[rocplot] 'pairs' must be a list of tuples, \"all\", or None."
        )

    resolved_pairs: list[tuple[str, str]] = []
    seen_pairs: set[frozenset[str]] = set()
    for pair in pairs:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError(
                "[rocplot] Each item in 'pairs' must contain exactly two prediction "
                "columns as a tuple."
            )
        first, second = pair
        if first == second:
            raise ValueError(
                "[rocplot] Comparison pairs must contain two distinct prediction "
                "columns."
            )
        missing = [column for column in pair if column not in pred_prob_cols]
        if missing:
            raise ValueError(
                "[rocplot] Comparison pair contains prediction column(s) not plotted: "
                f"{missing}."
            )
        pair_key = frozenset(pair)
        if pair_key in seen_pairs:
            raise ValueError(
                "[rocplot] Comparison pairs must be unique regardless of order."
            )
        seen_pairs.add(pair_key)
        resolved_pairs.append(pair)
    return resolved_pairs


def _validate_roc_scores(data: pd.DataFrame, columns: list[str]) -> None:
    """Require complete, finite, real-valued ROC scores."""
    validate_no_nulls(data, columns, "rocplot")
    for column in columns:
        values = data[column]
        if (
            not pd.api.types.is_numeric_dtype(values.dtype)
            or pd.api.types.is_bool_dtype(values.dtype)
            or np.iscomplexobj(values.to_numpy())
        ):
            raise ValueError(
                f"[rocplot] Column '{column}' must contain real numeric scores."
            )
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(
                f"[rocplot] Column '{column}' must contain only finite scores."
            )


def rocplot(
    data: pd.DataFrame,
    true_label_col: str,
    pred_prob_cols: str | list[str],
    *,
    ci_show: bool = False,
    pairs: Literal["all"] | list[tuple[str, str]] | None = None,
    p_adjust: Literal["bonferroni", "holm", "fdr_bh", "fdr_by"] | None = None,
    ax: Axes | None = None,
) -> Axes:
    """
    Create a receiver operating characteristic (ROC) curve plot.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing true labels and predicted probabilities.
    true_label_col : str
        Column name for the true binary labels (0 or 1).
    pred_prob_cols : str or list of str
        Column name(s) for predicted probabilities.
    ci_show : bool, default: False
        Whether to display deterministic pointwise 95% bootstrap confidence bands.
    pairs : list of tuple of str or {'all'}, optional
        Prediction-column pairs to compare with paired, two-sided DeLong tests. Use
        ``'all'`` to compare every plotted pair. No comparisons are run by default.
    p_adjust : {'bonferroni', 'holm', 'fdr_bh', 'fdr_by'}, optional
        Multiple-comparison correction applied across the resolved DeLong tests.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. If None, uses the current axes.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    confusionplot : Create a confusion matrix heatmap.
    forestplot : Create a forest plot from a logistic model.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.rocplot(
    ...     data=df, true_label_col="disease", pred_prob_cols="model_probability"
    ... )
    >>> ax.set_title("ROC Curve")

    >>> # Compare multiple models
    >>> ax = cns.rocplot(
    ...     data=df,
    ...     true_label_col="outcome",
    ...     pred_prob_cols=["model_a_prob", "model_b_prob", "model_c_prob"],
    ...     ci_show=True,
    ...     pairs="all",
    ...     p_adjust="holm",
    ... )
    """
    # Validate inputs
    validate_dataframe(data, "data", "rocplot")
    validate_dataframe_not_empty(data, "rocplot")

    if isinstance(pred_prob_cols, str):
        pred_prob_cols = [pred_prob_cols]

    # Validate columns
    columns_to_check = [true_label_col] + pred_prob_cols
    validate_columns_exist(data, columns_to_check, "rocplot")

    # Validate binary labels
    validate_no_nulls(data, true_label_col, "rocplot")
    validate_binary_column(data, true_label_col, "rocplot")
    _validate_roc_scores(data, pred_prob_cols)
    resolved_pairs = _resolve_roc_pairs(pred_prob_cols, pairs)
    if p_adjust is not None and p_adjust not in _P_ADJUST_METHODS:
        choices = ", ".join(repr(value) for value in _P_ADJUST_METHODS)
        raise ValueError(f"[rocplot] 'p_adjust' must be one of: {choices}, or None.")
    if resolved_pairs:
        class_counts = data[true_label_col].value_counts()
        if (class_counts < 2).any():
            raise ValueError(
                "[rocplot] DeLong comparisons require at least two positive and two "
                "negative observations."
            )

    if ax is None:
        ax = plt.gca()
    for col in pred_prob_cols:
        fpr, tpr, _ = roc_curve(data[true_label_col], data[col])
        roc_auc = auc(fpr, tpr)
        (curve,) = ax.plot(
            fpr,
            tpr,
            label=f"{col} (AUC={roc_auc:.2f})",
            linewidth=1,
        )
        if ci_show:
            ci_fpr, ci_lower, ci_upper = helper_roc._bootstrap_roc_confidence_band(
                data[true_label_col].to_numpy(),
                data[col].to_numpy(),
            )
            ax.fill_between(
                ci_fpr,
                ci_lower,
                ci_upper,
                color=curve.get_color(),
                alpha=0.2,
                linewidth=0,
                zorder=curve.get_zorder() - 1,
            )

    ax.plot([0, 1], [0, 1], color="black", linestyle="--", linewidth=0.8, dashes=(8, 5))
    ax.set_xlim((-0.02, 1.02))
    ax.set_ylim((-0.02, 1.02))
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend(loc="lower right")

    legend = ax.get_legend()
    if legend is not None:
        for handle in legend.legend_handles:
            set_linewidth = getattr(handle, "set_linewidth", None)
            if callable(set_linewidth):
                set_linewidth(1.7)

    if resolved_pairs:
        raw_pvalues = [
            helper_roc._delong_roc_test(
                data[true_label_col].to_numpy(),
                data[first].to_numpy(),
                data[second].to_numpy(),
            )
            for first, second in resolved_pairs
        ]
        displayed_pvalues = raw_pvalues
        annotation_header = "DeLong test"
        if p_adjust is not None:
            displayed_pvalues = multipletests(raw_pvalues, method=p_adjust)[1].tolist()
            annotation_header += f" ({p_adjust}-adjusted)"
        annotation_lines = [annotation_header]
        annotation_lines.extend(
            f"{first} vs {second}: P = "
            + rf"${num2tex.num2tex(pvalue, precision=2):.2g}$"
            for (first, second), pvalue in zip(
                resolved_pairs, displayed_pvalues, strict=True
            )
        )
        ax.text(
            0.02,
            0.02,
            "\n".join(annotation_lines),
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=_legend_fontsize(),
            linespacing=1.25,
        )

    return ax
