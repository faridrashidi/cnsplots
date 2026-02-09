from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    import numpy as np
    import pandas as pd

import matplotlib.pyplot as plt
import num2tex
import numpy as np
import pandas as pd

import cnsplots.helpers._cmprsk as helper_cmprsk
from cnsplots._validation import (
    validate_binary_column,
    validate_column_type,
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
    validate_no_nulls,
    validate_sufficient_data,
)


def survivalplot(
    data: pd.DataFrame,
    duration: str,
    event: str,
    hue: str,
    hue_order: list[str] | None = None,
) -> Axes:
    """
    Create a Kaplan-Meier survival plot with statistical comparisons.

    This function generates Kaplan-Meier survival curves comparing survival
    probabilities across groups, with automatic statistical testing and
    hazard ratio calculation.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing survival data.
    duration : str
        Column name for the time-to-event or time-to-censoring variable.
    event : str
        Column name for the event indicator (1 = event occurred, 0 = censored).
    hue : str
        Column name for the grouping variable to compare survival curves.
    hue_order : list, optional
        Order of groups from hue to display and compare.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    cumulativeincidenceplot : Create a cumulative incidence plot for competing risks.
    forestplot : Create a forest plot from a Cox model.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.survivalplot(
    ...     data=df,
    ...     duration="time_months",
    ...     event="death",
    ...     hue="treatment",
    ...     hue_order=["control", "drug_a", "drug_b"],
    ... )
    >>> ax.set_title("Overall Survival by Treatment")
    """
    # Validate inputs
    validate_dataframe(data, "data", "survivalplot")
    validate_columns_exist(data, [duration, event, hue], "survivalplot")
    validate_dataframe_not_empty(data, "survivalplot")

    # Validate data types
    validate_column_type(data, duration, ["numeric"], "survivalplot")
    validate_binary_column(data, event, "survivalplot")

    # Validate no nulls in critical columns
    validate_no_nulls(data, [duration, event, hue], "survivalplot")

    # Validate sufficient data
    validate_sufficient_data(data, duration, 2, "survivalplot")

    import lifelines as ll

    ax = None
    if hue_order is None or set(data[hue].unique()) != set(hue_order):
        hue_order = list(data[hue].unique())
    data[hue] = pd.Categorical(data[hue], categories=hue_order, ordered=True)
    data = data.sort_values(hue)
    kmf = ll.KaplanMeierFitter()
    for i, group in enumerate(hue_order):
        df = data[data[hue] == group]
        label = f"{group} (n={df.shape[0]})"
        kmf.fit(df[duration], df[event], label=label)
        if i != 0:
            ax = kmf.plot_survival_function(
                linewidth=1, ci_show=False, show_censors=True, censor_styles={"ms": 3}
            )
        else:
            ax = kmf.plot_survival_function(
                ax=ax,
                linewidth=1,
                ci_show=False,
                show_censors=True,
                censor_styles={"ms": 3},
            )
    plt.ylim(-0.05, 1.01)
    if ax.get_xlim()[1] > 120:
        ax.xaxis.set_major_locator(plt.MultipleLocator(24))
        plt.xlabel("Time (Months)")
    elif ax.get_xlim()[1] > 12:
        ax.xaxis.set_major_locator(plt.MultipleLocator(12))
        plt.xlabel("Time (Months)")
    else:
        ax.xaxis.set_major_locator(plt.MultipleLocator(1))
        plt.xlabel("Time (Years)")
    plt.ylabel("Overall survival probability")

    df = data[[duration, hue, event]].copy()
    df[hue] = df[hue].cat.codes

    if len(hue_order) == 2:
        try:
            logrank_test = ll.statistics.multivariate_logrank_test(
                df[duration], df[hue], df[event]
            )
            p = num2tex.num2tex(logrank_test.p_value, precision=2)
            print(
                "   ---> P-value was determined by two-sided multivariate log-rank test."
            )
        except Exception as e:
            raise RuntimeError(
                "[survivalplot] Log-rank test failed. This may indicate insufficient data "
                f"or invalid event/duration values. Details: {e}"
            ) from e
    else:
        try:
            cph = ll.CoxPHFitter()
            cph.fit(df, duration_col=duration, event_col=event)
            trend_test = cph.log_likelihood_ratio_test()
            p = num2tex.num2tex(trend_test.p_value, precision=2)
            print(
                "   ---> P-value was determined by two-sided multivariate log-rank test for trend."
            )
        except Exception as e:
            raise RuntimeError(
                "[survivalplot] Cox proportional hazards model failed. This may indicate "
                f"insufficient data or model convergence issues. Details: {e}"
            ) from e

    df = data[[duration, hue, event]].copy()
    df = df[df[hue].isin([hue_order[0], hue_order[-1]])]
    df[hue] = pd.Categorical(
        df[hue], categories=[hue_order[0], hue_order[-1]], ordered=True
    )
    df[hue] = df[hue].cat.codes
    try:
        cph = ll.CoxPHFitter()
        cph.fit(df, duration_col=duration, event_col=event)
        hazard_ratio = cph.hazard_ratios_.iloc[0]
        ci1 = cph.summary["exp(coef) lower 95%"].iloc[0]
        ci2 = cph.summary["exp(coef) upper 95%"].iloc[0]
    except Exception as e:
        raise RuntimeError(
            "[survivalplot] Could not compute hazard ratios. This may indicate "
            f"insufficient data or model convergence issues. Details: {e}"
        ) from e
    ax.text(
        0, 0, f"HR = {hazard_ratio:.2f} ({ci1:.2f}-{ci2:.2f})\nP = " + rf"${p:.2g}$"
    )

    if ax.get_legend() is not None:
        for handle in ax.get_legend().legend_handles:
            if hasattr(handle, "set_linewidth"):
                handle.set_linewidth(1.7)

    return ax


def cumulativeincidenceplot(
    data: pd.DataFrame,
    duration: str,
    event: str,
    hue: str,
    hue_order: list[str] | None = None,
    pvalue_position: tuple[float, float] = (0, 0.5),
    show_risk_table: bool = False,
    risk_table_rows: tuple[str, ...] = ("At risk",),
    risk_table_ypos: float = -0.2,
    xticks: np.ndarray | list[float] | None = None,
) -> Axes:
    """
    Create a cumulative incidence plot for competing risks analysis.

    This function generates cumulative incidence curves using the Aalen-Johansen
    estimator for competing risks data, with automatic statistical testing and
    optional at-risk table.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing time-to-event data with competing risks.
    duration : str
        Column name for the time-to-event or time-to-censoring variable.
    event : str
        Column name for the event indicator (0 = censored, 1 = event of interest,
        2+ = competing events).
    hue : str
        Column name for the grouping variable to compare cumulative incidence curves.
    hue_order : list, optional
        Order of groups from hue to display and compare.
    pvalue_position : tuple of float, default: (0, 0.5)
        (x, y) coordinates for placing the p-value text annotation.
    show_risk_table : bool, default: False
        Whether to display a risk table below the plot.
    risk_table_rows : tuple of str, default: ('At risk',)
        Which rows to show in the risk table.
    risk_table_ypos : float, default: -0.2
        Vertical position of the risk table relative to the plot.
    xticks : array-like, optional
        Specific x-axis tick positions.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot.

    See Also
    --------
    survivalplot : Create a Kaplan-Meier survival plot.
    forestplot : Create a forest plot from a Cox model.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.cumulativeincidenceplot(
    ...     data=df,
    ...     duration="time_years",
    ...     event="event_type",
    ...     hue="treatment",
    ...     hue_order=["placebo", "drug"],
    ...     show_risk_table=True,
    ... )

    >>> # With custom tick positions
    >>> ax = cns.cumulativeincidenceplot(
    ...     data=df,
    ...     duration="months",
    ...     event="outcome",
    ...     hue="risk_group",
    ...     xticks=[0, 12, 24, 36, 48, 60],
    ... )
    """
    # Validate inputs
    validate_dataframe(data, "data", "cumulativeincidenceplot")
    validate_columns_exist(data, [duration, event, hue], "cumulativeincidenceplot")
    validate_dataframe_not_empty(data, "cumulativeincidenceplot")

    # Validate data types
    validate_column_type(data, duration, ["numeric"], "cumulativeincidenceplot")

    # Validate no nulls in critical columns
    validate_no_nulls(data, [duration, event, hue], "cumulativeincidenceplot")

    # Validate sufficient data
    validate_sufficient_data(data, duration, 2, "cumulativeincidenceplot")

    import lifelines as ll

    ax = None
    if hue_order is None or set(data[hue].unique()) != set(hue_order):
        hue_order = list(data[hue].unique())
    data[hue] = pd.Categorical(data[hue], categories=hue_order, ordered=True)
    data = data.sort_values(hue)
    fitters = []
    for i, group in enumerate(hue_order):
        df = data[data[hue] == group]
        label = f"{group} (n={df.shape[0]})"
        if show_risk_table:
            label = group
        fitter = ll.AalenJohansenFitter()
        fitter.fit(df[duration], df[event], label=label, event_of_interest=1)
        fitters.append(fitter)
        df = pd.merge(
            fitter.cumulative_density_.reset_index(drop=False),
            df,
            how="outer",
            left_on="event_at",
            right_on=duration,
        )
        df = df.loc[df[event] == 0].copy()
        if i == 0:
            ax = fitter.plot(linewidth=1, ci_show=False)
        else:
            ax = fitter.plot(ax=ax, linewidth=1, ci_show=False)
        line_color = ax.get_lines()[-1].get_color()
        ax.plot(df[duration], df["CIF_1"], "+", markersize=3, color=line_color)
    ax.set_ylim(-0.05, 1.01)
    ax.set_ylabel("Cumulative incidence probability")
    ax.set_xlabel("Time (Years)")
    specified_xticks = None
    if xticks is not None:
        specified_xticks = np.asarray(list(xticks), dtype=float)
        if specified_xticks.size > 0:
            ax.set_xticks(specified_xticks)
            current_xlim = ax.get_xlim()
            new_xlim = (
                min(current_xlim[0], specified_xticks.min()),
                max(current_xlim[1], specified_xticks.max()),
            )
            ax.set_xlim(new_xlim)
    if data[hue].nunique() > 1:
        pvalue = helper_cmprsk.cuminc(
            data[duration], data[event], group=data[hue].cat.codes
        )
        p = num2tex.num2tex(pvalue, precision=2)
        print("   ---> P-value was determined by two-sided Gray's test.")
        ax.text(pvalue_position[0], pvalue_position[1], "P = " + rf"${p:.2g}$")

    if show_risk_table:
        rows = None if risk_table_rows is None else list(risk_table_rows)
        xticks = np.asarray(ax.get_xticks())
        xticks = xticks[
            (xticks >= ax.get_xlim()[0] - 1e-8) & (xticks <= ax.get_xlim()[1] + 1e-8)
        ]
        ll.plotting.add_at_risk_counts(
            *fitters,
            ax=ax,
            rows_to_show=rows,
            ypos=risk_table_ypos,
            xticks=xticks.tolist(),
        )
    return ax
