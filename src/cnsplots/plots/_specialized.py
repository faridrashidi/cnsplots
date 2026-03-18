from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anndata import AnnData
    from matplotlib.axes import Axes

import matplotlib.gridspec as grid_spec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Circle, FancyBboxPatch, Polygon
from sklearn.metrics import auc, roc_curve

import cnsplots.helpers._phylo as helper_phylo
import cnsplots.helpers._sankey as helper_sankey
from cnsplots._validation import (
    validate_anndata,
    validate_binary_column,
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
)


def placeholderplot(description: str) -> Axes:
    """
    Create a stylized placeholder panel for figure layout mockups.

    This helper clears the current axes, draws a rounded placeholder card with
    a mock image area, and places wrapped descriptive text in a centered
    caption area.

    Parameters
    ----------
    description : str
        Text to display in the center of the placeholder panel.

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
    >>> cns.figure(100, 200)
    >>> ax = cns.placeholderplot("A description to be centered in the panel")
    >>> ax.set_title("Placeholder")
    """
    if not isinstance(description, str):
        raise TypeError("[placeholderplot] 'description' must be a string.")

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


def sankeyplot(data: pd.DataFrame, x: str, y: str, label_rotation: float = 0) -> Axes:
    """
    Create a Sankey diagram showing flows between two categorical variables.

    This function generates a Sankey (alluvial) diagram visualizing the flow
    and connections between categories in two variables.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing the data to visualize.
    x : str
        Column name for the source (left-side) categorical variable.
    y : str
        Column name for the target (right-side) categorical variable.
    label_rotation : float, default: 0
        Rotation angle, in degrees, applied to both left and right Sankey
        labels.

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
    >>> ax = cns.sankeyplot(data=df, x="initial_diagnosis", y="final_diagnosis")
    >>> ax.set_title("Diagnosis Flow")

    >>> # Patient flow across treatment stages
    >>> ax = cns.sankeyplot(
    ...     data=df,
    ...     x="stage_1_response",
    ...     y="stage_2_response",
    ...     label_rotation=90,
    ... )
    """
    # Validate inputs
    validate_dataframe(data, "data", "sankeyplot")
    validate_columns_exist(data, [x, y], "sankeyplot")
    validate_dataframe_not_empty(data, "sankeyplot")

    ax = plt.gca()
    current_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    keys = np.union1d(data[x].unique(), data[y].unique())
    color_dict = dict(zip(keys, current_colors))
    helper_sankey.sankeyplot(
        data[x],
        data[y],
        fontsize=6,
        colorDict=color_dict,
        label_rotation=label_rotation,
        ax=ax,
    )
    return ax


def phyloplot(adata: AnnData) -> None:
    """
    Create a phylogenetic tree plot with associated heatmaps.

    Parameters
    ----------
    adata : AnnData
        Annotated data matrix containing tree structure and annotations.

    Returns
    -------
    None
        The plot is displayed directly; no Axes object is returned.

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

    helper_phylo.phyloplot(adata)


def forestplot(
    model: object, bar_width: float | None = None, add_pvalue: bool = True
) -> Axes:
    """
    Create a forest plot displaying effect sizes from a regression model.

    This function generates a forest plot showing hazard ratios (from Cox models)
    or AUC values (from logistic models) with confidence intervals.

    Parameters
    ----------
    model : CoxModel or LogisticModel
        Fitted regression model object containing results to plot.
    bar_width : float or None, optional
        Width of the bars in the p-value panel (Cox models only). If None,
        defaults to ``0.8 / n_hue_groups`` when there are multiple hue groups,
        or ``0.6`` otherwise.
    add_pvalue : bool, optional
        Whether to add the p-value bar panel alongside the forest plot
        (Cox models only). Default is True.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot (primary panel).

    See Also
    --------
    survivalplot : Create a Kaplan-Meier survival plot.
    rocplot : Create an ROC curve plot.
    boxplot : Create a box plot with statistical comparisons.

    Examples
    --------
    >>> import cnsplots as cns
    >>> from cnsplots import CoxModel
    >>>
    >>> # Fit Cox model
    >>> model = CoxModel(data=df, duration="time", event="death")
    >>> model.fit(predictors=["age", "stage", "treatment"])
    >>>
    >>> # Create forest plot
    >>> ax = cns.forestplot(model)
    >>> ax.set_title("Hazard Ratios")

    >>> # With grouping variable
    >>> model = CoxModel(data=df, duration="time", event="death", hue="cohort")
    >>> model.fit(predictors=["biomarker_a", "biomarker_b"])
    >>> ax = cns.forestplot(model)
    """
    # Validate model has required attributes
    if not hasattr(model, "results"):
        raise ValueError(
            "[forestplot] Model object must have a 'results' attribute containing fitted model results."
        )
    if not hasattr(model, "name"):
        raise ValueError(
            "[forestplot] Model object must have a 'name' attribute indicating model type."
        )

    # Validate results is a DataFrame
    results = getattr(model, "results")
    model_name = getattr(model, "name")
    model_hue = getattr(model, "hue", None)
    validate_dataframe(results, "model.results", "forestplot")
    if not isinstance(results, pd.DataFrame):
        raise TypeError(
            "[forestplot] Internal type validation failed for 'model.results'."
        )
    validate_dataframe_not_empty(results, "forestplot")

    # Validate required columns exist based on model type
    if model_name == "cox":
        required_cols = [
            "display_label",
            "exp(coef)",
            "log10_pvalue",
            "exp(coef) lower_err",
            "exp(coef) upper_err",
            "hue_group",
        ]
        validate_columns_exist(results, required_cols, "forestplot")
    else:
        required_cols = ["predictor", "auc", "lower_ci", "upper_ci", "hue_group"]
        validate_columns_exist(results, required_cols, "forestplot")

    data = results.copy()

    if model_name == "cox":
        y = "display_label"
        x1 = "exp(coef)"
        x2 = "log10_pvalue"
        x1err = ["exp(coef) lower_err", "exp(coef) upper_err"]
        x1label = "Hazard ratio (95% CI)"
        x2label = "\u2013log10(p-value)"
    else:
        y = "predictor"
        x1 = "auc"
        x2 = ""
        x1err = ["lower_ci", "upper_ci"]
        x1label = "AUC (95% CI)"
        x2label = ""
    fig = plt.gcf()

    if model_name == "cox" and add_pvalue:
        gs = grid_spec.GridSpec(1, 2, width_ratios=[5, 3])
    else:
        gs = grid_spec.GridSpec(1, 1)
    ax1 = fig.add_subplot(gs[0])

    unique_hue_groups = data["hue_group"].unique()
    colors = sns.color_palette(n_colors=len(unique_hue_groups))
    color_map = dict(zip(unique_hue_groups, colors))
    unique_labels = data[y].drop_duplicates().tolist()
    y_positions = {label: i for i, label in enumerate(reversed(unique_labels))}

    max_offset = 0.15
    n_hue_groups = len(unique_hue_groups)
    offsets = (
        np.linspace(-max_offset, max_offset, n_hue_groups) if n_hue_groups > 1 else [0]
    )
    hue_offset_map = dict(zip(unique_hue_groups, offsets))

    for hue_group in unique_hue_groups:
        hue_data = data[data["hue_group"] == hue_group]
        color = color_map[hue_group]
        y_coords = []
        x_coords = []
        x_errs_lower = []
        x_errs_upper = []
        for _, row in hue_data.iterrows():
            y_pos = y_positions[row[y]] + hue_offset_map[hue_group]
            y_coords.append(y_pos)
            x_coords.append(row[x1])
            x_errs_lower.append(row[x1err[0]])
            x_errs_upper.append(row[x1err[1]])

        ax1.errorbar(
            x_coords,
            y_coords,
            xerr=[x_errs_lower, x_errs_upper],
            fmt="s",
            color=color,
            markeredgewidth=0.8,
            elinewidth=0.8,
            capsize=2,
            markersize=3,
            label=hue_group,
        )
    ax1.set_yticks(list(y_positions.values()))
    ax1.set_yticklabels(list(y_positions.keys()))
    ax1.set_ylim(-0.5, len(unique_labels) - 0.5)
    ax1.set_xlabel(x1label)
    if len(unique_hue_groups) > 1:
        ax1.legend(title=model_hue, loc="lower right")
    if model_name == "cox":
        ax1.axvline(x=1, color="red", linestyle="--", linewidth=0.8)
        ax1.xaxis.set_major_locator(plt.MaxNLocator(nbins=5))
    else:
        ax1.axvline(x=0.5, color="red", linestyle="--", linewidth=0.8)

    if model_name == "cox" and add_pvalue:
        ax2 = fig.add_subplot(gs[1])
        if bar_width is None:
            bar_width = (
                0.8 / len(unique_hue_groups) if len(unique_hue_groups) > 1 else 0.6
            )
        for i, label in enumerate(reversed(unique_labels)):
            label_data = data[data[y] == label]
            for j, hue_group in enumerate(unique_hue_groups):
                hue_data = label_data[label_data["hue_group"] == hue_group]
                if len(hue_data) > 0:
                    color = color_map[hue_group]
                    if len(unique_hue_groups) > 1:
                        bar_pos = i + (j - (len(unique_hue_groups) - 1) / 2) * bar_width
                    else:
                        bar_pos = i
                    ax2.barh(
                        bar_pos,
                        hue_data[x2].iloc[0],
                        height=bar_width,
                        color=color,
                        edgecolor=None,
                    )

        ax2.set_yticks(list(range(len(unique_labels))))
        ax2.set_yticklabels([])
        ax2.set_xlabel(x2label)
        ax2.axvline(
            x=-np.log10(0.05), color="red", linestyle="--", linewidth=0.8, alpha=0.7
        )
        ax2.set_ylim(-0.5, len(unique_labels) - 0.5)
        ax2.xaxis.set_major_locator(plt.MaxNLocator(nbins=5))

    return ax1


def rocplot(
    data: pd.DataFrame, true_label_col: str, pred_prob_cols: str | list[str]
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
    validate_binary_column(data, true_label_col, "rocplot")

    for col in pred_prob_cols:
        fpr, tpr, _ = roc_curve(data[true_label_col], data[col])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, label=f"{col} (AUC={roc_auc:.2f})", linewidth=1)

    plt.plot(
        [0, 1], [0, 1], color="black", linestyle="--", linewidth=0.8, dashes=(8, 5)
    )
    plt.xlim([-0.02, 1.02])
    plt.ylim([-0.02, 1.02])
    plt.xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    ax = plt.gca()
    ax.legend(loc="lower right")

    legend = ax.get_legend()
    if legend is not None:
        for handle in legend.legend_handles:
            if hasattr(handle, "set_linewidth"):
                handle.set_linewidth(1.7)  # type: ignore[call-non-callable]

    return ax
