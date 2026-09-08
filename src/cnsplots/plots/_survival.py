from __future__ import annotations

import logging
import warnings
from collections.abc import Sequence
from typing import Any, Literal, cast

import matplotlib.pyplot as plt
import num2tex
import numpy as np
import pandas as pd
from matplotlib.axes import Axes

from cnsplots._validation import (
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
    validate_time_to_event_data,
)

logger = logging.getLogger(__name__)

CensorMarkPosition = Literal["line", "above", "below", "none"]
VisibleCensorMarkPosition = Literal["line", "above", "below"]
PValueLoc = Literal[
    "upper left",
    "upper center",
    "upper right",
    "center left",
    "center",
    "center right",
    "right",
    "lower left",
    "lower center",
    "lower right",
]
HorizontalAlignment = Literal["left", "center", "right"]
VerticalAlignment = Literal["top", "center", "bottom"]

_P_ADJUST_METHODS = ("bonferroni", "holm", "fdr_bh", "fdr_by")
_SURVIVAL_COLUMNS = (
    "kind",
    "test",
    "groups",
    "group1",
    "group2",
    "n",
    "events",
    "n1",
    "events1",
    "n2",
    "events2",
    "time",
    "estimate",
    "ci_lower",
    "ci_upper",
    "ci_level",
    "statistic",
    "pvalue_raw",
    "pvalue_adjusted",
    "p_adjust",
    "family_size",
    "status",
    "reason",
    "annotation",
)

_CIF_Y_LIMITS = (-0.05, 1.01)
_DEFAULT_CENSOR_MARK_LENGTH = 0.02
_CENSOR_MARK_POSITIONS = ("line", "above", "below", "none")
_PVALUE_LOCATIONS: dict[
    PValueLoc,
    tuple[float, float, HorizontalAlignment, VerticalAlignment],
] = {
    "upper left": (0.02, 0.98, "left", "top"),
    "upper center": (0.5, 0.98, "center", "top"),
    "upper right": (0.98, 0.98, "right", "top"),
    "center left": (0.02, 0.5, "left", "center"),
    "center": (0.5, 0.5, "center", "center"),
    "center right": (0.98, 0.5, "right", "center"),
    "right": (0.98, 0.5, "right", "center"),
    "lower left": (0.02, 0.02, "left", "bottom"),
    "lower center": (0.5, 0.02, "center", "bottom"),
    "lower right": (0.98, 0.02, "right", "bottom"),
}


def _unavailable_inference(function_name: str, label: str, reason: Exception) -> str:
    """Report failed optional inference without discarding descriptive estimates."""
    warnings.warn(
        f"[{function_name}] {label} unavailable: {reason}", UserWarning, stacklevel=3
    )
    return f"{label} unavailable"


def _format_inference_pvalue(pvalue: float) -> str:
    if not np.isfinite(pvalue) or not 0 <= pvalue <= 1:
        raise ValueError("the test did not return a finite p-value between 0 and 1")
    p = num2tex.num2tex(pvalue, precision=2)
    return rf"${p:.2g}$"


def _validate_comparison(data: pd.DataFrame, event: str, group: str) -> None:
    if data[group].nunique() < 2:
        raise ValueError("at least two groups are required")
    if not (data[event] == 1).any():
        raise ValueError("there are no events of interest (event code 1)")


def _validate_logrank_variance(
    data: pd.DataFrame, duration: str, event: str, group: str
) -> None:
    from lifelines.utils import group_survival_table_from_events

    _validate_comparison(data, event, group)
    _, removed, observed, _ = group_survival_table_from_events(
        data[group], data[duration], data[event]
    )
    at_risk = removed.sum().to_numpy() - removed.cumsum().shift(fill_value=0).to_numpy()
    total_at_risk = at_risk.sum(axis=1)
    events = observed.sum(axis=1).to_numpy()
    # Hypergeometric covariance of group event counts at each pooled event time.
    weight = events * (total_at_risk - events) / np.maximum(total_at_risk - 1, 1)
    proportions = at_risk / total_at_risk[:, None]
    weighted = weight[:, None] * proportions
    covariance = np.diag(weighted.sum(axis=0)) - proportions.T @ weighted
    if np.linalg.matrix_rank(covariance[:-1, :-1]) < at_risk.shape[1] - 1:
        raise ValueError("the log-rank comparison variance is zero or singular")


def _fit_cox_inference(data: pd.DataFrame, covariate: str) -> Any:
    import lifelines as ll

    _validate_comparison(data, "_event", covariate)
    if (
        data[covariate].nunique() == 2
        and (data.groupby(covariate, observed=True)["_event"].sum() == 0).any()
    ):
        raise ValueError("a comparison group has no observed events")
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        cph = ll.CoxPHFitter()
        cph.fit(data, duration_col="_duration", event_col="_event")
        summary = cph.summary.loc[covariate]
    estimates = summary[
        ["se(coef)", "exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%"]
    ].to_numpy(dtype=float)
    if not np.isfinite(estimates).all() or (estimates <= 0).any():
        raise ValueError("the Cox model did not return finite positive estimates")
    return cph


def _add_pvalue_annotation(
    ax: Axes,
    text: str,
    pvalue_loc: PValueLoc,
    *,
    data_position: tuple[float, float] | None = None,
) -> None:
    if data_position is not None:
        ax.text(
            *data_position,
            text,
            fontsize=plt.rcParams["legend.fontsize"],
            linespacing=1.25,
        )
        return

    if pvalue_loc not in _PVALUE_LOCATIONS:
        valid_locations = "', '".join(_PVALUE_LOCATIONS)
        raise ValueError(
            "[survival plots] Parameter 'pvalue_loc' must be one of "
            f"'{valid_locations}', got {pvalue_loc!r}"
        )
    x, y, horizontalalignment, verticalalignment = _PVALUE_LOCATIONS[pvalue_loc]
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha=horizontalalignment,
        va=verticalalignment,
        fontsize=plt.rcParams["legend.fontsize"],
        linespacing=1.25,
    )


def _format_valid_censor_mark_positions() -> str:
    return "', '".join(_CENSOR_MARK_POSITIONS)


def _validate_censor_mark_position(
    censor_mark_position: CensorMarkPosition | list[CensorMarkPosition],
    hue_order: Sequence[Any],
) -> None:
    valid_positions = _format_valid_censor_mark_positions()
    if isinstance(censor_mark_position, str):
        if censor_mark_position not in _CENSOR_MARK_POSITIONS:
            raise ValueError(
                "[cumulativeincidenceplot] Parameter 'censor_mark_position' must be one "
                f"of '{valid_positions}', got {censor_mark_position!r}"
            )
        return

    if not isinstance(censor_mark_position, list):
        raise TypeError(
            "[cumulativeincidenceplot] Parameter 'censor_mark_position' must be a "
            "string position or a list of positions"
        )

    if len(censor_mark_position) != len(hue_order):
        raise ValueError(
            "[cumulativeincidenceplot] Parameter 'censor_mark_position' must provide "
            "one position per hue_order group when passing a list, got "
            f"{len(censor_mark_position)} position(s) for {len(hue_order)} group(s)"
        )

    invalid_positions = {
        index: position
        for index, position in enumerate(censor_mark_position)
        if position not in _CENSOR_MARK_POSITIONS
    }
    if invalid_positions:
        raise ValueError(
            "[cumulativeincidenceplot] Parameter 'censor_mark_position' contains "
            f"invalid position(s) {invalid_positions!r}. Values must be one of "
            f"'{valid_positions}'"
        )


def _resolve_censor_mark_position(
    censor_mark_position: CensorMarkPosition | list[CensorMarkPosition],
    group_index: int,
) -> CensorMarkPosition:
    if isinstance(censor_mark_position, str):
        return censor_mark_position
    return censor_mark_position[group_index]


def _censor_mark_extents(
    censor_y: np.ndarray,
    position: VisibleCensorMarkPosition,
    length: float,
) -> tuple[np.ndarray, np.ndarray]:
    if position == "line":
        offset = length / 2
        ymin = censor_y - offset
        ymax = censor_y + offset
    elif position == "above":
        ymin = censor_y
        ymax = censor_y + length
    else:
        ymin = censor_y - length
        ymax = censor_y

    return (
        np.clip(ymin, _CIF_Y_LIMITS[0], _CIF_Y_LIMITS[1]),
        np.clip(ymax, _CIF_Y_LIMITS[0], _CIF_Y_LIMITS[1]),
    )


def get_survival_results(ax: Axes | None = None) -> pd.DataFrame:
    """Return the estimates and tests annotated by the latest survivalplot call.

    Parameters
    ----------
    ax : matplotlib.axes.Axes, optional
        Axes returned by survivalplot. Defaults to the current axes.

    Returns
    -------
    pandas.DataFrame
        A detached table in annotation order. ``kind`` identifies ``overall``,
        ``pairwise_cox``, ``median_survival``, ``landmark_survival``,
        ``landmark_test``, or ``rmst``. Only requested, enabled analyses appear.
        ``test`` names the inferential method; ``groups`` preserves its group
        order. For pairwise Cox rows, ``group1`` is the reference and ``group2``
        the comparison: ``estimate`` is the hazard ratio of group2 versus group1.
        Single-group estimates use ``group1``. ``n``/``events`` count contributing
        observations/events over full follow-up, even for landmark and RMST rows;
        ``n1``/``events1`` and ``n2``/``events2`` give group counts for non-overall
        rows. ``time`` is the landmark or RMST horizon.
        ``estimate`` holds the HR, median, survival probability, or RMST;
        ``ci_lower``, ``ci_upper``, and ``ci_level`` describe unadjusted 95% Cox
        intervals only. ``statistic`` is chi-square for log-rank, fixed-time, and
        Cox likelihood-ratio trend tests, or Wald z for Cox pairs. ``trend`` uses
        equally spaced scores in the order recorded in ``groups``.
        ``pvalue_raw`` and ``pvalue_adjusted`` agree without correction;
        ``p_adjust`` and ``family_size`` describe the requested Cox family only.
        ``status`` is ``available``, ``unavailable``, or ``not_reached``;
        ``reason`` explains missing inference or an infinite median. Inapplicable
        numeric fields and unavailable inference are NaN. ``annotation`` contains
        the row's displayed text. An empty table retains the same columns.

    Notes
    -----
    No models or tests are rerun. Each call returns a copy; each survivalplot call
    replaces the stored results. Clearing the axes or removing its annotation
    makes the results unavailable. DataFrame ``attrs`` record ``duration``,
    ``event``, ``hue``, ``time_label``, ``event_observed=1``, ``event_censored=0``,
    and ``common_follow_up`` (the minimum group maximum duration).

    Survival estimates include events at the landmark time. RMST integrates the
    Kaplan-Meier curve from zero through the requested horizon, in input time
    units. Unreached medians retain lifelines' positive infinity. Pairwise
    corrections exclude the overall and landmark tests and never adjust CIs.

    Examples
    --------
    >>> ax = cns.survivalplot(df, "time", "event", "group", p_adjust="holm")
    >>> results = cns.get_survival_results(ax)
    >>> results.to_csv("survival_results.csv", index=False)
    """
    if ax is None:
        ax = plt.gca()
    stored = getattr(ax, "_cnsplots_survival_results", None)
    if stored is None:
        return pd.DataFrame(columns=pd.Index(_SURVIVAL_COLUMNS))
    results, artists = stored
    if any(artist not in ax.texts for artist in artists):
        return pd.DataFrame(columns=pd.Index(_SURVIVAL_COLUMNS))
    return results.copy(deep=True)


def survivalplot(
    data: pd.DataFrame,
    duration: str,
    event: str,
    hue: str,
    hue_order: list[str] | None = None,
    time_label: str = "Time",
    *,
    ci_show: bool = False,
    show_risk_table: bool = False,
    risk_table_rows: tuple[str, ...] | None = ("At risk",),
    risk_table_ypos: float = -0.2,
    xticks: np.ndarray | Sequence[int | float] | None = None,
    show_median_survival: bool = False,
    landmark_time: float | None = None,
    rmst_time: float | None = None,
    overall_test: Literal["logrank", "trend"] = "logrank",
    pairs: list[tuple[str, str]] | None = None,
    p_adjust: Literal["bonferroni", "holm", "fdr_bh", "fdr_by"] | None = None,
    show_hazard_ratio: bool = True,
    descriptive_only: bool = False,
    pvalue_loc: PValueLoc = "lower left",
    ax: Axes | None = None,
) -> Axes:
    """
    Create a Kaplan-Meier survival plot with statistical comparisons.

    This function generates Kaplan-Meier survival curves comparing survival
    probabilities across groups, with an overall statistical test and optional
    pairwise Cox proportional hazards inference.

    Parameters
    ----------
    data : pd.DataFrame
        The input DataFrame containing survival data.
    duration : str
        Column name for finite, nonnegative time to event or right censoring.
        All times and analysis horizons use the same units; no rows are dropped.
    event : str
        Column name for the event indicator (1 = event occurred, 0 = censored).
    hue : str
        Column name for the grouping variable to compare survival curves.
    hue_order : list, optional
        Order of groups from hue to display and compare.
    time_label : str, default: "Time"
        Label for the time axis, including units when applicable.
    ci_show : bool, default: False
        Whether to display pointwise confidence bands for the Kaplan-Meier curves.
    show_risk_table : bool, default: False
        Whether to display a risk table below the plot.
    risk_table_rows : tuple of str or None, default: ('At risk',)
        Which rows to show in the risk table. Pass ``None`` to show at-risk,
        censored, and event counts.
    risk_table_ypos : float, default: -0.2
        Vertical position of the risk table relative to the plot.
    xticks : array-like, optional
        Specific x-axis tick positions. These positions are also used by the risk
        table when it is shown.
    show_median_survival : bool, default: False
        Whether to draw median-survival guides and include each group's median in
        the statistical annotation. Medians that are not observed are reported as
        ``not reached``.
    landmark_time : float, optional
        Time at which to mark and report each group's Kaplan-Meier survival
        probability, including events at that time. Must be finite, positive, and
        at most the minimum group maximum follow-up. For exactly two groups,
        also reports the two-sided fixed-time log-minus-log comparison p-value.
    rmst_time : float, optional
        Truncation time through which to compute and report each group's restricted
        mean survival time (RMST), integrating from zero in input time units. Must
        be finite, positive, and at most the minimum group maximum follow-up.
    overall_test : {'logrank', 'trend'}, default: 'logrank'
        Test used for the overall p-value. ``'logrank'`` performs a categorical
        omnibus log-rank test. ``'trend'`` performs a one-degree-of-freedom Cox
        trend test using equally spaced scores in ``hue_order`` and requires a
        complete, explicitly supplied ``hue_order``.
    pairs : list of tuple of str, optional
        Pairwise Cox contrasts written as ``(reference, comparison)``. Each
        contrast reports the hazard ratio for comparison versus reference, its
        95% confidence interval, and an unadjusted two-sided Cox Wald p-value.
        When omitted, the sole contrast is reported automatically for two groups;
        no contrast is inferred for three or more groups. Pass an empty list to
        suppress pairwise inference. Duplicate contrasts, including reversed
        duplicates, are rejected.
    p_adjust : {'bonferroni', 'holm', 'fdr_bh', 'fdr_by'} or None, default: None
        Adjust two-sided Cox Wald p-values across all requested pairwise contrasts
        in this call. Annotations show raw and adjusted values, the method and
        family size. Failed contrasts remain unavailable and count in the family
        using p=1 only during correction. Overall and landmark tests remain raw,
        and Cox confidence intervals remain unadjusted 95% intervals. Ignored
        when ``show_hazard_ratio=False`` or ``descriptive_only=True``.
    show_hazard_ratio : bool, default: True
        Whether to show pairwise hazard ratios, confidence intervals, and Cox
        p-values. If False, pairwise Cox inference is skipped and only the overall
        log-rank or trend p-value is shown. Any value passed to ``pairs`` is ignored.
    descriptive_only : bool, default: False
        Skip all statistical tests and Cox fitting, ignoring ``overall_test``,
        ``pairs``, and ``show_hazard_ratio``. Curves, confidence bands, risk tables,
        medians, landmark estimates, and RMST remain available, including for a
        single group or an all-censored cohort. Otherwise, unavailable inference
        emits a UserWarning with the reason and is annotated as ``unavailable``;
        valid curves and other estimates are retained.
    pvalue_loc : str, default: 'lower left'
        Axes-relative location for the p-value and hazard-ratio annotation. Accepts
        the fixed Matplotlib legend locations: ``'upper left'``, ``'upper center'``,
        ``'upper right'``, ``'center left'``, ``'center'``, ``'center right'``,
        ``'right'``, ``'lower left'``, ``'lower center'``, or ``'lower right'``.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. If None, uses the current axes. Any risk table is linked
        to this axes and created on the same figure.

    Returns
    -------
    matplotlib.axes.Axes
        The matplotlib Axes object containing the plot. Use
        ``get_survival_results(ax)`` to retrieve its estimates and test results.

    See Also
    --------
    cumulativeincidenceplot : Create a cumulative incidence plot for competing risks.
    forestplot : Create a forest plot from a Cox model.
    get_survival_results : Retrieve the estimates and tests used for annotations.

    Examples
    --------
    >>> import cnsplots as cns
    >>> ax = cns.survivalplot(
    ...     data=df,
    ...     duration="time_months",
    ...     event="death",
    ...     hue="treatment",
    ...     hue_order=["control", "drug_a", "drug_b"],
    ...     time_label="Time (months)",
    ...     pairs=[("control", "drug_b")],
    ...     ci_show=True,
    ...     show_risk_table=True,
    ...     show_median_survival=True,
    ...     landmark_time=12,
    ...     rmst_time=24,
    ... )
    >>> ax.set_title("Overall Survival by Treatment")
    """
    # Validate inputs
    validate_dataframe(data, "data", "survivalplot")
    validate_columns_exist(data, [duration, event, hue], "survivalplot")
    validate_dataframe_not_empty(data, "survivalplot")

    validate_time_to_event_data(
        data,
        duration,
        event,
        hue,
        "survivalplot",
    )

    import lifelines as ll
    from lifelines.plotting import add_at_risk_counts
    from lifelines.statistics import (
        multivariate_logrank_test,
        survival_difference_at_fixed_point_in_time_test,
    )
    from lifelines.utils import restricted_mean_survival_time

    data = data.copy()
    observed_groups = list(data[hue].unique())
    has_explicit_order = (
        hue_order is not None
        and len(hue_order) == len(observed_groups)
        and set(hue_order) == set(observed_groups)
    )
    if not descriptive_only and overall_test not in {"logrank", "trend"}:
        raise ValueError(
            "[survivalplot] Parameter 'overall_test' must be one of "
            "'logrank' or 'trend'."
        )
    if not descriptive_only and overall_test == "trend" and not has_explicit_order:
        raise ValueError(
            "[survivalplot] The trend test requires a complete explicit 'hue_order' "
            "because category order defines the trend scores."
        )
    if not has_explicit_order:
        hue_order = observed_groups
    assert hue_order is not None

    common_follow_up = float(data.groupby(hue, observed=True)[duration].max().min())
    for parameter_name, analysis_time in (
        ("landmark_time", landmark_time),
        ("rmst_time", rmst_time),
    ):
        if analysis_time is None:
            continue
        if (
            isinstance(analysis_time, bool)
            or not isinstance(analysis_time, (int, float, np.integer, np.floating))
            or not np.isfinite(analysis_time)
            or analysis_time <= 0
        ):
            raise ValueError(
                f"[survivalplot] Parameter '{parameter_name}' must be a finite "
                f"positive number, got {analysis_time!r}"
            )
        if analysis_time > common_follow_up:
            raise ValueError(
                f"[survivalplot] Parameter '{parameter_name}' must not exceed the "
                f"common follow-up time ({common_follow_up:g}), got {analysis_time!r}"
            )

    resolved_pairs: list[tuple[str, str]] = []
    if show_hazard_ratio and not descriptive_only:
        if p_adjust is not None and p_adjust not in _P_ADJUST_METHODS:
            raise ValueError(
                "[survivalplot] Parameter 'p_adjust' must be one of "
                f"{_P_ADJUST_METHODS} or None."
            )
        resolved_pairs = (
            [(hue_order[0], hue_order[1])]
            if pairs is None and len(hue_order) == 2
            else ([] if pairs is None else pairs)
        )
    seen_pairs: set[frozenset[str]] = set()
    for pair in resolved_pairs:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError(
                "[survivalplot] Each item in 'pairs' must contain exactly two groups "
                "as a (reference, comparison) tuple."
            )
        if pair[0] == pair[1]:
            raise ValueError(
                "[survivalplot] Pairwise contrasts must contain two distinct groups."
            )
        missing_groups = [group for group in pair if group not in observed_groups]
        if missing_groups:
            raise ValueError(
                "[survivalplot] Pairwise contrast contains group(s) not present in "
                f"'{hue}': {missing_groups}."
            )
        pair_key = frozenset(pair)
        if pair_key in seen_pairs:
            raise ValueError(
                "[survivalplot] Duplicate pairwise contrasts (including reversed "
                "pairs) are not allowed."
            )
        seen_pairs.add(pair_key)

    if ax is None:
        ax = plt.gca()
    data[hue] = pd.Categorical(data[hue], categories=hue_order, ordered=True)
    data = data.sort_values(hue)
    fitters: list[Any] = []
    curve_colors: list[Any] = []
    for group in hue_order:
        df = data[data[hue] == group]
        label = f"{group} (n={df.shape[0]})"
        if show_risk_table:
            label = group
        kmf = ll.KaplanMeierFitter()
        kmf.fit(df[duration], df[event], label=label)
        fitters.append(kmf)
        kmf.plot_survival_function(
            ax=ax,
            linewidth=1,
            ci_show=ci_show,
            show_censors=True,
            censor_styles={"ms": 3},
        )
        curve = next(line for line in ax.lines if line.get_label() == label)
        curve_colors.append(curve.get_color())
    ax.set_ylim(-0.05, 1.01)
    ax.set_xlabel(time_label)
    ax.set_ylabel("Survival probability")
    if xticks is not None:
        specified_xticks = np.asarray(list(xticks), dtype=float)
        if specified_xticks.size > 0:
            ax.set_xticks(specified_xticks)
            current_xlim = ax.get_xlim()
            ax.set_xlim(
                min(current_xlim[0], specified_xticks.min()),
                max(current_xlim[1], specified_xticks.max()),
            )

    result_rows: list[dict[str, Any]] = []

    def record_result(
        kind: str, groups: Sequence[str], **values: Any
    ) -> dict[str, Any]:
        subset = data[data[hue].isin(groups)]
        row: dict[str, Any] = dict.fromkeys(_SURVIVAL_COLUMNS, np.nan)
        row.update(
            kind=kind,
            test=None,
            groups=tuple(groups),
            group1=None,
            group2=None,
            n=len(subset),
            events=int(subset[event].sum()),
            p_adjust=None,
            status="available",
            reason=None,
            annotation="",
        )
        if kind != "overall":
            for index, group in enumerate(groups, start=1):
                group_data = subset[subset[hue] == group]
                row[f"group{index}"] = group
                row[f"n{index}"] = len(group_data)
                row[f"events{index}"] = int(group_data[event].sum())
        row.update(values)
        result_rows.append(row)
        return row

    annotation_lines = []
    if not descriptive_only and overall_test == "logrank":
        row = record_result("overall", hue_order, test="logrank")
        try:
            _validate_logrank_variance(data, duration, event, hue)
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                logrank_result = multivariate_logrank_test(
                    data[duration], data[hue], data[event]
                )
            row["annotation"] = "Log-rank P = " + _format_inference_pvalue(
                logrank_result.p_value
            )
            row.update(
                statistic=float(logrank_result.test_statistic),
                pvalue_raw=float(logrank_result.p_value),
                pvalue_adjusted=float(logrank_result.p_value),
            )
            logger.info("P-value was determined by two-sided omnibus log-rank test.")
        except (ValueError, RuntimeError, ArithmeticError, RuntimeWarning) as e:
            row.update(
                status="unavailable",
                reason=str(e),
                annotation=_unavailable_inference("survivalplot", "Log-rank", e),
            )
        annotation_lines.append(row["annotation"])
    elif not descriptive_only:
        row = record_result("overall", hue_order, test="trend")
        trend_data = pd.DataFrame(
            {
                "_duration": data[duration].to_numpy(),
                "_event": data[event].to_numpy(),
                "_group_score": data[hue].cat.codes.to_numpy(),
            }
        )
        try:
            cph = _fit_cox_inference(trend_data, "_group_score")
            trend_result = cph.log_likelihood_ratio_test()
            row["annotation"] = "Cox trend P = " + _format_inference_pvalue(
                trend_result.p_value
            )
            row.update(
                statistic=float(trend_result.test_statistic),
                pvalue_raw=float(trend_result.p_value),
                pvalue_adjusted=float(trend_result.p_value),
            )
            logger.info(
                "P-value was determined by a one-degree-of-freedom Cox proportional "
                "hazards trend test using hue_order scores."
            )
        except (ValueError, RuntimeError, ArithmeticError, RuntimeWarning) as e:
            row.update(
                status="unavailable",
                reason=str(e),
                annotation=_unavailable_inference("survivalplot", "Cox trend", e),
            )
        annotation_lines.append(row["annotation"])

    pair_rows = []
    for reference, comparison in resolved_pairs:
        row = record_result(
            "pairwise_cox",
            (reference, comparison),
            test="cox_wald",
            p_adjust=p_adjust,
            family_size=len(resolved_pairs),
        )
        pair_rows.append(row)
        pair_data = data[data[hue].isin([reference, comparison])]
        cox_data = pd.DataFrame(
            {
                "_duration": pair_data[duration].to_numpy(),
                "_event": pair_data[event].to_numpy(),
                "_comparison": (pair_data[hue] == comparison).astype(int).to_numpy(),
            }
        )
        try:
            cph = _fit_cox_inference(cox_data, "_comparison")
            summary = cph.summary.loc["_comparison"]
            hazard_ratio = summary["exp(coef)"]
            ci1 = summary["exp(coef) lower 95%"]
            ci2 = summary["exp(coef) upper 95%"]
            _format_inference_pvalue(summary["p"])
            row.update(
                estimate=float(hazard_ratio),
                ci_lower=float(ci1),
                ci_upper=float(ci2),
                ci_level=0.95,
                statistic=float(summary["z"]),
                pvalue_raw=float(summary["p"]),
                pvalue_adjusted=float(summary["p"]),
            )
        except (ValueError, RuntimeError, ArithmeticError, RuntimeWarning) as e:
            row.update(
                status="unavailable",
                reason=str(e),
                annotation=_unavailable_inference(
                    "survivalplot", f"Cox HR ({comparison} vs {reference})", e
                ),
            )

    if p_adjust is not None and pair_rows:
        from statsmodels.stats.multitest import multipletests

        # Keep the requested family intact when a contrast cannot be estimated.
        correction_input = [
            row["pvalue_raw"] if row["status"] == "available" else 1.0
            for row in pair_rows
        ]
        adjusted = multipletests(correction_input, method=p_adjust)[1]
        for row, pvalue in zip(pair_rows, adjusted, strict=True):
            if row["status"] == "available":
                row["pvalue_adjusted"] = float(pvalue)
        annotation_lines.append(
            f"Pairwise Cox ({p_adjust}-adjusted; {len(pair_rows)} contrasts)"
        )

    for row in pair_rows:
        if row["status"] == "unavailable":
            annotation_lines.append(row["annotation"])
            continue
        pair_lines = []
        if len(hue_order) > 2:
            pair_lines.append(f"{row['group2']} vs {row['group1']}")
        ci_label = "95% CI" if p_adjust is None else "95% CI (unadjusted)"
        pair_lines.extend(
            [
                f"HR = {row['estimate']:.2f}",
                f"{ci_label} {row['ci_lower']:.2f}-{row['ci_upper']:.2f}",
            ]
        )
        raw_p = _format_inference_pvalue(row["pvalue_raw"])
        if p_adjust is None:
            pair_lines.append("Cox P = " + raw_p)
        else:
            pair_lines.extend(
                [
                    "Cox raw P = " + raw_p,
                    f"Cox {p_adjust}-adjusted P = "
                    + _format_inference_pvalue(row["pvalue_adjusted"]),
                ]
            )
        row["annotation"] = "\n".join(pair_lines)
        annotation_lines.extend(pair_lines)
        logger.info(
            "Pairwise hazard ratios and unadjusted two-sided P-values were determined "
            "by Cox proportional hazards models."
        )

    if show_median_survival:
        annotation_lines.append("Median survival")
        for group, fitter, color in zip(hue_order, fitters, curve_colors, strict=True):
            median = float(fitter.median_survival_time_)
            row = record_result("median_survival", (group,), estimate=median)
            if np.isfinite(median):
                row["annotation"] = f"{group} = {median:g}"
                ax.hlines(
                    0.5,
                    0,
                    median,
                    colors=color,
                    linestyles=":",
                    linewidth=0.8,
                )
                ax.vlines(
                    median,
                    0,
                    0.5,
                    colors=color,
                    linestyles=":",
                    linewidth=0.8,
                )
            else:
                row.update(
                    status="not_reached",
                    reason="the Kaplan-Meier curve does not reach 0.5",
                    annotation=f"{group} = not reached",
                )
            annotation_lines.append(row["annotation"])

    analysis_guide_times = set()
    if landmark_time is not None:
        landmark_time = float(landmark_time)
        analysis_guide_times.add(landmark_time)
        landmark_estimates = [
            float(fitter.predict(landmark_time)) for fitter in fitters
        ]
        annotation_lines.append(f"Survival at {landmark_time:g}")
        for group, estimate, color in zip(
            hue_order, landmark_estimates, curve_colors, strict=True
        ):
            row = record_result(
                "landmark_survival",
                (group,),
                time=landmark_time,
                estimate=estimate,
                annotation=f"{group} = {estimate:.2f}",
            )
            annotation_lines.append(row["annotation"])
            ax.scatter(
                landmark_time,
                estimate,
                color=color,
                s=12,
                zorder=3,
            )
        if not descriptive_only and len(fitters) == 2:
            row = record_result(
                "landmark_test",
                hue_order,
                time=landmark_time,
                test="fixed_time_log_minus_log",
            )
            try:
                if not all(0 < estimate < 1 for estimate in landmark_estimates):
                    raise ValueError(
                        "survival estimates must be strictly between 0 and 1"
                    )
                with warnings.catch_warnings():
                    warnings.simplefilter("error", RuntimeWarning)
                    landmark_result = survival_difference_at_fixed_point_in_time_test(
                        landmark_time, fitters[0], fitters[1]
                    )
                row["annotation"] = "Landmark P = " + _format_inference_pvalue(
                    landmark_result.p_value
                )
                row.update(
                    statistic=float(landmark_result.test_statistic),
                    pvalue_raw=float(landmark_result.p_value),
                    pvalue_adjusted=float(landmark_result.p_value),
                )
                logger.info(
                    "Landmark P-value was determined by a two-sided fixed-time "
                    "log-minus-log test."
                )
            except (ValueError, RuntimeError, ArithmeticError, RuntimeWarning) as e:
                row.update(
                    status="unavailable",
                    reason=str(e),
                    annotation=_unavailable_inference(
                        "survivalplot", "Landmark test", e
                    ),
                )
            annotation_lines.append(row["annotation"])

    if rmst_time is not None:
        rmst_time = float(rmst_time)
        analysis_guide_times.add(rmst_time)
        annotation_lines.append(f"RMST to {rmst_time:g}")
        for group, fitter in zip(hue_order, fitters, strict=True):
            rmst = cast(float, restricted_mean_survival_time(fitter, t=rmst_time))
            row = record_result(
                "rmst",
                (group,),
                time=rmst_time,
                estimate=rmst,
                annotation=f"{group} = {rmst:.2f}",
            )
            annotation_lines.append(row["annotation"])

    for analysis_time in sorted(analysis_guide_times):
        ax.axvline(analysis_time, color="0.5", linestyle="--", linewidth=0.8)

    text_start = len(ax.texts)
    if annotation_lines:
        _add_pvalue_annotation(ax, "\n".join(annotation_lines), pvalue_loc)

    legend = ax.get_legend()
    if legend is not None:
        for handle in legend.legend_handles:
            set_linewidth = getattr(handle, "set_linewidth", None)
            if callable(set_linewidth):
                set_linewidth(1.7)

    if show_risk_table:
        rows = None if risk_table_rows is None else list(risk_table_rows)
        visible_xticks = np.asarray(ax.get_xticks())
        visible_xticks = visible_xticks[
            (visible_xticks >= ax.get_xlim()[0] - 1e-8)
            & (visible_xticks <= ax.get_xlim()[1] + 1e-8)
        ]
        add_at_risk_counts(
            *fitters,
            ax=ax,
            rows_to_show=rows,
            ypos=risk_table_ypos,
            xticks=visible_xticks.tolist(),
            fig=ax.figure,
        )

    results = pd.DataFrame(result_rows, columns=pd.Index(_SURVIVAL_COLUMNS))
    results.attrs.update(
        duration=duration,
        event=event,
        hue=hue,
        time_label=time_label,
        event_observed=1,
        event_censored=0,
        common_follow_up=common_follow_up,
    )
    setattr(ax, "_cnsplots_survival_results", (results, tuple(ax.texts)[text_start:]))
    return ax


def cumulativeincidenceplot(
    data: pd.DataFrame,
    duration: str,
    event: str,
    hue: str,
    hue_order: list[str] | None = None,
    pvalue_position: tuple[float, float] | None = None,
    show_risk_table: bool = False,
    risk_table_rows: tuple[str, ...] = ("At risk",),
    risk_table_ypos: float = -0.2,
    xticks: np.ndarray | Sequence[int | float] | None = None,
    censor_mark_position: CensorMarkPosition | list[CensorMarkPosition] = "line",
    censor_mark_length: float = _DEFAULT_CENSOR_MARK_LENGTH,
    time_label: str = "Time",
    seed: int | None = 0,
    *,
    descriptive_only: bool = False,
    pvalue_loc: PValueLoc = "center left",
    ax: Axes | None = None,
) -> Axes:
    """
    Create a cumulative incidence plot for competing risks analysis.

    This function generates cumulative incidence curves using the Aalen-Johansen
    estimator for competing risks data, with an automatic Gray's K-sample test and
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
    pvalue_position : tuple of float, optional
        Data coordinates for placing the Gray's test p-value annotation. When
        provided, this overrides ``pvalue_loc``.
    show_risk_table : bool, default: False
        Whether to display a risk table below the plot.
    risk_table_rows : tuple of str, default: ('At risk',)
        Which rows to show in the risk table.
    risk_table_ypos : float, default: -0.2
        Vertical position of the risk table relative to the plot.
    xticks : array-like, optional
        Specific x-axis tick positions.
    censor_mark_position : {'line', 'above', 'below', 'none'} or list, default: 'line'
        Where to draw censoring marks relative to each cumulative incidence curve.
        ``'line'`` draws short vertical marks crossing the curve, ``'above'`` draws
        marks from the curve upward, ``'below'`` draws marks up to the curve, and
        ``'none'`` hides censoring marks. Pass a list with one value per hue group
        to control groups separately, for example
        ``['above', 'none', 'below']`` for ``hue_order=['A', 'B', 'C']``.
    censor_mark_length : float, default: 0.02
        Length of each vertical censoring mark in cumulative-incidence probability
        units. The same length is used for all curves.
    time_label : str, default: "Time"
        Label for the time axis, including units when applicable.
    seed : int or None, default: 0
        Seed used by lifelines when tied event times require jittering. The default
        makes tied-data plots deterministic. The caller's NumPy random state is
        restored after fitting.
    descriptive_only : bool, default: False
        Skip Gray's test and its annotation. Single groups, all-censored groups,
        and groups without the event of interest have valid descriptive curves.
        Event code 0 always means censored, 1 is the event of interest, and all
        higher codes remain competing events, even when code 0 or 1 is absent.
        Otherwise, unavailable inference emits a UserWarning with the reason and
        is annotated as ``unavailable`` while preserving the curves.
    pvalue_loc : str, default: 'center left'
        Axes-relative location for the Gray's test p-value. Accepts the fixed
        Matplotlib legend locations: ``'upper left'``, ``'upper center'``,
        ``'upper right'``, ``'center left'``, ``'center'``, ``'center right'``,
        ``'right'``, ``'lower left'``, ``'lower center'``, or ``'lower right'``.
        Ignored when ``pvalue_position`` is provided.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. If None, uses the current axes. Any risk table is linked
        to this axes and created on the same figure.

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
    ...     time_label="Time (years)",
    ... )

    >>> # With custom tick positions
    >>> ax = cns.cumulativeincidenceplot(
    ...     data=df,
    ...     duration="months",
    ...     event="outcome",
    ...     hue="risk_group",
    ...     xticks=[0, 12, 24, 36, 48, 60],
    ...     time_label="Time (months)",
    ... )
    """
    # Validate inputs
    validate_dataframe(data, "data", "cumulativeincidenceplot")
    validate_columns_exist(data, [duration, event, hue], "cumulativeincidenceplot")
    validate_dataframe_not_empty(data, "cumulativeincidenceplot")

    validate_time_to_event_data(
        data,
        duration,
        event,
        hue,
        "cumulativeincidenceplot",
        competing_risks=True,
    )

    if censor_mark_length < 0:
        raise ValueError(
            "[cumulativeincidenceplot] Parameter 'censor_mark_length' must be "
            f"non-negative, got {censor_mark_length!r}"
        )

    import lifelines as ll
    from lifelines.plotting import add_at_risk_counts

    import cnsplots.helpers._cmprsk as helper_cmprsk

    data = data.copy()
    if ax is None:
        ax = plt.gca()
    if hue_order is None or set(data[hue].unique()) != set(hue_order):
        hue_order = list(data[hue].unique())
    _validate_censor_mark_position(censor_mark_position, hue_order)
    data[hue] = pd.Categorical(data[hue], categories=hue_order, ordered=True)
    data = data.sort_values(hue)
    fitters = []
    for i, group in enumerate(hue_order):
        df = data[data[hue] == group]
        label = f"{group} (n={df.shape[0]})"
        if show_risk_table:
            label = group
        fitter = ll.AalenJohansenFitter(seed=seed)
        random_state = np.random.get_state()
        try:
            fitter.fit(df[duration], df[event], label=label, event_of_interest=1)
        finally:
            np.random.set_state(random_state)
        fitters.append(fitter)
        df = df.astype({duration: float})
        df = pd.merge(
            fitter.cumulative_density_.reset_index(drop=False),
            df,
            how="outer",
            left_on="event_at",
            right_on=duration,
        )
        df = df.loc[df[event] == 0].copy()
        fitter.plot_cumulative_density(ax=ax, linewidth=1, ci_show=False)
        line_color = ax.get_lines()[-1].get_color()
        group_censor_mark_position = _resolve_censor_mark_position(
            censor_mark_position, i
        )
        if group_censor_mark_position != "none":
            censor_df = df[[duration, "CIF_1"]].dropna()
            if not censor_df.empty:
                censor_y = censor_df["CIF_1"].to_numpy(dtype=float)
                ymin, ymax = _censor_mark_extents(
                    censor_y,
                    group_censor_mark_position,
                    censor_mark_length,
                )
                ax.vlines(
                    censor_df[duration],
                    ymin,
                    ymax,
                    colors=line_color,
                    linewidth=1,
                )
    ax.set_ylim(_CIF_Y_LIMITS)
    ax.set_ylabel("Cumulative incidence probability")
    ax.set_xlabel(time_label)
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
    if not descriptive_only:
        try:
            _validate_comparison(data, event, hue)
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                pvalue = helper_cmprsk.cuminc(
                    data[duration], data[event], group=data[hue].cat.codes
                )
            annotation = "P = " + _format_inference_pvalue(pvalue)
            logger.info("P-value was determined by Gray's K-sample test.")
        except (ValueError, RuntimeError, ArithmeticError, RuntimeWarning) as e:
            annotation = _unavailable_inference(
                "cumulativeincidenceplot", "Gray's test", e
            )
        _add_pvalue_annotation(
            ax,
            annotation,
            pvalue_loc,
            data_position=pvalue_position,
        )

    if show_risk_table:
        rows = None if risk_table_rows is None else list(risk_table_rows)
        xticks = np.asarray(ax.get_xticks())
        xticks = xticks[
            (xticks >= ax.get_xlim()[0] - 1e-8) & (xticks <= ax.get_xlim()[1] + 1e-8)
        ]
        add_at_risk_counts(
            *fitters,
            ax=ax,
            rows_to_show=rows,
            ypos=risk_table_ypos,
            xticks=xticks.tolist(),
            fig=ax.figure,
        )
    return ax
