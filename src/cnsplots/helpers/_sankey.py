from __future__ import annotations

# https://github.com/Pierre-Sassoulas/pySankey
import warnings
from collections import defaultdict
from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from numpy import float64, ndarray
from pandas.core.frame import DataFrame
from pandas.core.series import Series


def check_data_matches_labels(
    labels: list[str] | set[str], data: Series | list[str] | set[str], side: str
) -> None:
    """Check whether data matches labels.

    Raise a LabelMismatch Exception if not."""
    if len(labels) > 0:
        data_set: set[str]
        if isinstance(data, list):
            data_set = set(cast("list[str]", data))
        elif isinstance(data, pd.Series):
            data_set = set(cast("list[str]", data.unique().tolist()))
        else:
            data_set = data
        label_set: set[str] = set(labels) if isinstance(labels, list) else labels
        if label_set != data_set:
            msg = "\n"
            if len(label_set) <= 20:
                msg = "Labels: " + ",".join(label_set) + "\n"
            if len(data_set) < 20:
                msg += "Data: " + ",".join(data_set)
            raise ValueError(f"{side} labels and data do not match.{msg}")


def sankeyplot(
    left: list | ndarray | Series,
    right: ndarray | Series,
    leftWeight: ndarray | None = None,
    rightWeight: ndarray | None = None,
    colorDict: dict[str, str] | None = None,
    leftLabels: list[str] | None = None,
    rightLabels: list[str] | None = None,
    aspect: int = 4,
    rightColor: bool = False,
    fontsize: int | float = 14,
    label_rotation: float = 0,
    figureName: str | None = None,
    closePlot: bool = False,
    figSize: tuple[int, int] | None = None,
    ax: Any = None,
) -> Any:
    """
    Make Sankey Diagram showing flow from left-->right

    Inputs:
        left = NumPy array of object labels on the left of the diagram
        right = NumPy array of corresponding labels on the right of the diagram
            len(right) == len(left)
        leftWeight = NumPy array of weights for each strip starting from the
            left of the diagram, if not specified 1 is assigned
        rightWeight = NumPy array of weights for each strip starting from the
            right of the diagram, if not specified the corresponding leftWeight
            is assigned
        colorDict = Dictionary of colors to use for each label
            {'label':'color'}
        leftLabels = order of the left labels in the diagram
        rightLabels = order of the right labels in the diagram
        aspect = vertical extent of the diagram in units of horizontal extent
        rightColor = If true, each strip in the diagram will be be colored
                    according to its left label
        label_rotation = rotation angle in degrees for left and right labels
        figSize = tuple setting the width and height of the sankey diagram.
            Defaults to current figure size
        ax = optional, matplotlib axes to plot on, otherwise uses current axes.
    Output:
        ax : matplotlib Axes
    """
    ax, leftLabels, leftWeight, rightLabels, rightWeight = init_values(
        ax,
        closePlot,
        figSize,
        figureName,
        left,
        leftLabels,
        leftWeight,
        rightLabels,
        rightWeight,
    )
    data_frame = _create_dataframe(left, leftWeight, right, rightWeight)
    # Identify all labels that appear 'left' or 'right'
    all_labels = pd.Series(
        np.r_[data_frame.left.unique(), data_frame.right.unique()]
    ).unique()
    leftLabels, rightLabels = identify_labels(data_frame, leftLabels, rightLabels)
    colorDict = create_colors(all_labels, colorDict)  # type: ignore
    ns_l, ns_r = determine_widths(data_frame, leftLabels, rightLabels)
    # Determine positions of left label patches and total widths
    leftWidths, topEdge = _get_positions_and_total_widths(
        data_frame, leftLabels, "left"
    )
    # Determine positions of right label patches and total widths
    rightWidths, topEdge = _get_positions_and_total_widths(
        data_frame, rightLabels, "right"
    )
    # Total vertical extent of diagram
    xMax = topEdge / aspect
    draw_vertical_bars(
        ax,
        colorDict,  # type: ignore
        fontsize,
        leftLabels,
        leftWidths,
        rightLabels,
        rightWidths,
        xMax,
        label_rotation,
    )
    plot_strips(
        ax,
        colorDict,  # type: ignore
        data_frame,
        leftLabels,
        leftWidths,
        ns_l,
        ns_r,
        rightColor,
        rightLabels,
        rightWidths,
        xMax,
    )
    if figSize is not None:
        plt.gcf().set_size_inches(figSize)
    if closePlot:
        plt.close()
    return ax


def identify_labels(
    dataFrame: DataFrame,
    leftLabels: list[str],
    rightLabels: list[str],
) -> tuple[list[str], list[str]]:
    # Identify left labels
    if len(leftLabels) == 0:
        leftLabels = pd.Series(dataFrame.left.unique()).unique().tolist()
    else:
        check_data_matches_labels(leftLabels, dataFrame["left"], "left")
    # Identify right labels
    if len(rightLabels) == 0:
        rightLabels = pd.Series(dataFrame.right.unique()).unique().tolist()
    else:
        check_data_matches_labels(rightLabels, dataFrame["right"], "right")
    return leftLabels, rightLabels


def init_values(
    ax: Any,
    closePlot: bool,
    figSize: tuple[int, int] | None,
    figureName: str | None,
    left: list | ndarray | Series,
    leftLabels: list[str] | None,
    leftWeight: ndarray | None,
    rightLabels: list[str] | None,
    rightWeight: ndarray | None,
) -> tuple[Any, list[str], ndarray, list[str], ndarray]:
    deprecation_warnings(closePlot, figSize, figureName)
    if ax is None:
        ax = plt.gca()
    if leftWeight is None:
        leftWeight = np.array([])
    if rightWeight is None:
        rightWeight = np.array([])
    if leftLabels is None:
        leftLabels = []
    if rightLabels is None:
        rightLabels = []
    # Check weights
    if len(leftWeight) == 0:
        leftWeight = np.ones(len(left))
    if len(rightWeight) == 0:
        rightWeight = leftWeight
    return ax, leftLabels, leftWeight, rightLabels, rightWeight


def deprecation_warnings(
    closePlot: bool, figSize: tuple[int, int] | None, figureName: str | None
) -> None:
    if figureName is not None:
        msg = "use of figureName in sankey() is deprecated"
        warnings.warn(msg, DeprecationWarning, stacklevel=2)
    if closePlot is not False:
        msg = "use of closePlot in sankey() is deprecated"
        warnings.warn(msg, DeprecationWarning, stacklevel=2)
    if figSize is not None:
        msg = "use of figSize in sankey() is deprecated"
        warnings.warn(msg, DeprecationWarning, stacklevel=2)


def determine_widths(
    dataFrame: DataFrame,
    leftLabels: list[str],
    rightLabels: list[str],
) -> tuple[dict, dict]:
    # Determine widths of individual strips
    ns_l: dict = defaultdict()
    ns_r: dict = defaultdict()
    for leftLabel in leftLabels:
        left_dict = {}
        right_dict = {}
        for rightLabel in rightLabels:
            left_dict[rightLabel] = dataFrame[
                (dataFrame.left == leftLabel) & (dataFrame.right == rightLabel)
            ].leftWeight.sum()
            right_dict[rightLabel] = dataFrame[
                (dataFrame.left == leftLabel) & (dataFrame.right == rightLabel)
            ].rightWeight.sum()
        ns_l[leftLabel] = left_dict
        ns_r[leftLabel] = right_dict
    return ns_l, ns_r


def draw_vertical_bars(
    ax: Any,
    colorDict: dict[str, tuple[float, float, float]] | dict[str, str],
    fontsize: int | float,
    leftLabels: list[str],
    leftWidths: dict,
    rightLabels: list[str],
    rightWidths: dict,
    xMax: float64,
    label_rotation: float = 0,
) -> None:
    # Draw vertical bars on left and right of each  label's section & print label
    rotation_padding = fontsize * abs(np.sin(np.deg2rad(label_rotation)))
    for leftLabel in leftLabels:
        ax.fill_between(
            [-0.02 * xMax, 0],
            2 * [leftWidths[leftLabel]["bottom"]],
            2 * [leftWidths[leftLabel]["bottom"] + leftWidths[leftLabel]["left"]],
            color=colorDict[leftLabel],
            alpha=1,
        )
        ax.annotate(
            leftLabel,
            xy=(
                -0.05 * xMax,
                leftWidths[leftLabel]["bottom"] + 0.5 * leftWidths[leftLabel]["left"],
            ),
            xytext=(-rotation_padding, 0),
            textcoords="offset points",
            ha="right",
            va="center",
            fontsize=fontsize,
            rotation=label_rotation,
            rotation_mode="anchor",
        )
    for rightLabel in rightLabels:
        ax.fill_between(
            [xMax, 1.02 * xMax],
            2 * [rightWidths[rightLabel]["bottom"]],
            2 * [rightWidths[rightLabel]["bottom"] + rightWidths[rightLabel]["right"]],
            color=colorDict[rightLabel],
            alpha=1,
        )
        ax.annotate(
            rightLabel,
            xy=(
                1.05 * xMax,
                rightWidths[rightLabel]["bottom"]
                + 0.5 * rightWidths[rightLabel]["right"],
            ),
            xytext=(rotation_padding, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=fontsize,
            rotation=label_rotation,
            rotation_mode="anchor",
        )


def create_colors(
    allLabels: ndarray, colorDict: dict[str, str] | None
) -> dict[str, tuple[float, float, float]] | dict[str, str]:
    # If no colorDict given, make one
    if colorDict is None:
        colorDict = {}
        palette = "hls"
        colorPalette = sns.color_palette(palette, len(allLabels))
        for i, label in enumerate(allLabels):
            colorDict[label] = colorPalette[i]
    else:
        missing = [label for label in allLabels if label not in colorDict.keys()]
        if missing:
            raise ValueError(
                "The colorDict parameter is missing values for the following labels : "
                + ", ".join(missing)
            )
    return colorDict


def _create_dataframe(
    left: list | ndarray | Series,
    leftWeight: ndarray | Series,
    right: ndarray | Series,
    rightWeight: ndarray | Series,
) -> DataFrame:
    # Create Dataframe
    if isinstance(left, pd.Series):
        left = left.reset_index(drop=True)
    if isinstance(right, pd.Series):
        right = right.reset_index(drop=True)
    if isinstance(leftWeight, pd.Series):
        leftWeight = leftWeight.reset_index(drop=True)
    if isinstance(rightWeight, pd.Series):
        rightWeight = rightWeight.reset_index(drop=True)
    data_frame = pd.DataFrame(
        {
            "left": left,
            "right": right,
            "leftWeight": leftWeight,
            "rightWeight": rightWeight,
        },
        index=range(len(left)),
    )
    if len(data_frame[(data_frame.left.isnull()) | (data_frame.right.isnull())]):
        raise ValueError("Sankey graph does not support null values.")
    return data_frame


def plot_strips(
    ax: Any,
    colorDict: dict[str, tuple[float, float, float]] | dict[str, str],
    dataFrame: DataFrame,
    leftLabels: list[str],
    leftWidths: dict,
    ns_l: dict,
    ns_r: dict,
    rightColor: bool,
    rightLabels: list[str],
    rightWidths: dict,
    xMax: float64,
) -> None:
    # Plot strips
    for leftLabel in leftLabels:
        for rightLabel in rightLabels:
            label_color = leftLabel
            if rightColor:
                label_color = rightLabel
            if (
                len(
                    dataFrame[
                        (dataFrame.left == leftLabel) & (dataFrame.right == rightLabel)
                    ]
                )
                > 0
            ):
                # Create array of y values for each strip, half at left value,
                # half at right, convolve
                ys_d = np.array(
                    50 * [leftWidths[leftLabel]["bottom"]]
                    + 50 * [rightWidths[rightLabel]["bottom"]]
                )
                ys_d = np.convolve(ys_d, 0.05 * np.ones(20), mode="valid")
                ys_d = np.convolve(ys_d, 0.05 * np.ones(20), mode="valid")
                ys_u = np.array(
                    50 * [leftWidths[leftLabel]["bottom"] + ns_l[leftLabel][rightLabel]]
                    + 50
                    * [rightWidths[rightLabel]["bottom"] + ns_r[leftLabel][rightLabel]]
                )
                ys_u = np.convolve(ys_u, 0.05 * np.ones(20), mode="valid")
                ys_u = np.convolve(ys_u, 0.05 * np.ones(20), mode="valid")

                # Update bottom edges at each label so next strip starts at the
                # right place
                leftWidths[leftLabel]["bottom"] += ns_l[leftLabel][rightLabel]
                rightWidths[rightLabel]["bottom"] += ns_r[leftLabel][rightLabel]
                ax.fill_between(
                    np.linspace(0, xMax, len(ys_d)),
                    ys_d,
                    ys_u,
                    alpha=0.65,
                    color=colorDict[label_color],
                )
    ax.axis("off")


def _get_positions_and_total_widths(
    df: DataFrame, labels: list[str], side: str
) -> tuple[dict, float64]:
    """Determine positions of label patches and total widths"""
    widths: dict = defaultdict()
    for i, label in enumerate(labels):
        label_widths = {}
        label_widths[side] = df[df[side] == label][side + "Weight"].sum()
        if i == 0:
            label_widths["bottom"] = 0
            label_widths["top"] = label_widths[side]
        else:
            bottom_width = widths[labels[i - 1]]["top"]
            weighted_sum = 0.02 * df[side + "Weight"].sum()
            label_widths["bottom"] = bottom_width + weighted_sum
            label_widths["top"] = label_widths["bottom"] + label_widths[side]
            topEdge = label_widths["top"]
        widths[label] = label_widths

    return widths, topEdge
