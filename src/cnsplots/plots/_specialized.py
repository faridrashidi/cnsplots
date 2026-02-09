import matplotlib.gridspec as grid_spec
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
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


def sankeyplot(data, x, y):
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
    >>> ax = cns.sankeyplot(data=df, x="stage_1_response", y="stage_2_response")
    """
    # Validate inputs
    validate_dataframe(data, "data", "sankeyplot")
    validate_columns_exist(data, [x, y], "sankeyplot")
    validate_dataframe_not_empty(data, "sankeyplot")

    ax = plt.gca()
    current_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    keys = np.union1d(data[x].unique(), data[y].unique())
    color_dict = dict(zip(keys, current_colors))
    helper_sankey.sankeyplot(data[x], data[y], fontsize=6, colorDict=color_dict, ax=ax)
    return ax


def phyloplot(adata):
    """
    Create a phylogenetic tree plot with associated heatmaps.

    Parameters
    ----------
    adata : AnnData
        Annotated data matrix containing tree structure and annotations.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    heatmapplot : Create a clustered heatmap.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.phyloplot(adata)
    """
    # Validate inputs
    validate_anndata(adata, "adata", "phyloplot")

    ax = helper_phylo.phyloplot(adata)
    return ax


def forestplot(model):
    """
    Create a forest plot displaying effect sizes from a regression model.

    This function generates a forest plot showing hazard ratios (from Cox models)
    or AUC values (from logistic models) with confidence intervals.

    Parameters
    ----------
    model : CoxModel or LogisticModel
        Fitted regression model object containing results to plot.

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
    validate_dataframe(model.results, "model.results", "forestplot")
    validate_dataframe_not_empty(model.results, "forestplot")

    # Validate required columns exist based on model type
    if model.name == "cox":
        required_cols = [
            "display_label",
            "exp(coef)",
            "log10_pvalue",
            "exp(coef) lower_err",
            "exp(coef) upper_err",
            "hue_group",
        ]
        validate_columns_exist(model.results, required_cols, "forestplot")
    else:
        required_cols = ["predictor", "auc", "lower_ci", "upper_ci", "hue_group"]
        validate_columns_exist(model.results, required_cols, "forestplot")

    data = model.results.copy()

    if model.name == "cox":
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

    if model.name == "cox":
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
        ax1.legend(title=model.hue, loc="lower right")
    if model.name == "cox":
        ax1.axvline(x=1, color="red", linestyle="--", linewidth=0.8)
        ax1.xaxis.set_major_locator(plt.MaxNLocator(nbins=5))
    else:
        ax1.axvline(x=0.5, color="red", linestyle="--", linewidth=0.8)

    if model.name == "cox":
        ax2 = fig.add_subplot(gs[1])
        bar_width = 0.8 / len(unique_hue_groups) if len(unique_hue_groups) > 1 else 0.6
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


def rocplot(data, true_label_col, pred_prob_cols):
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

    if ax.get_legend() is not None:
        for handle in ax.get_legend().legend_handles:
            if hasattr(handle, "set_linewidth"):
                handle.set_linewidth(1.7)

    return ax
