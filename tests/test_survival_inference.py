from __future__ import annotations

from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import cnsplots as cns


def _annotation(ax: plt.Axes) -> str:
    return ax.texts[0].get_text()


def test_survivalplot_omnibus_test_is_category_order_invariant(
    survival_three_group_df: pd.DataFrame,
) -> None:
    annotations = []
    for order in (["Low", "Mid", "High"], ["Low", "High", "Mid"]):
        plt.figure()
        ax = cns.survivalplot(
            survival_three_group_df,
            "time",
            "event",
            "group",
            hue_order=order,
        )
        annotations.append(_annotation(ax))

    assert annotations == ["Log-rank P = $0.36$"] * 2


def test_survivalplot_trend_test_is_explicitly_ordered(
    survival_three_group_df: pd.DataFrame,
) -> None:
    annotations = []
    for order in (["Low", "Mid", "High"], ["Low", "High", "Mid"]):
        plt.figure()
        ax = cns.survivalplot(
            survival_three_group_df,
            "time",
            "event",
            "group",
            hue_order=order,
            overall_test="trend",
        )
        annotations.append(_annotation(ax))

    assert annotations == ["Cox trend P = $0.16$", "Cox trend P = $0.57$"]


@pytest.mark.parametrize("hue_order", [None, ["Low", "High"]])
def test_survivalplot_trend_requires_complete_explicit_order(
    survival_three_group_df: pd.DataFrame,
    hue_order: list[str] | None,
) -> None:
    with pytest.raises(ValueError, match="complete explicit 'hue_order'"):
        cns.survivalplot(
            survival_three_group_df,
            "time",
            "event",
            "group",
            hue_order=hue_order,
            overall_test="trend",
        )


@pytest.mark.parametrize(
    ("pair", "expected"),
    [
        (
            ("Low", "High"),
            [
                "High vs Low",
                "HR = 0.38",
                "95% CI 0.08–1.75",
                "Cox P = $0.21$",
            ],
        ),
        (
            ("High", "Low"),
            [
                "Low vs High",
                "HR = 2.66",
                "95% CI 0.57–12.43",
                "Cox P = $0.21$",
            ],
        ),
    ],
)
def test_survivalplot_reports_named_directional_pairwise_inference(
    survival_three_group_df: pd.DataFrame,
    pair: tuple[str, str],
    expected: list[str],
) -> None:
    annotations = []
    for order in (["Low", "Mid", "High"], ["Low", "High", "Mid"]):
        plt.figure()
        ax = cns.survivalplot(
            survival_three_group_df,
            "time",
            "event",
            "group",
            hue_order=order,
            pairs=[pair],
        )
        annotations.append(_annotation(ax).splitlines())

    assert annotations == [
        ["Log-rank P = $0.36$", *expected],
        ["Log-rank P = $0.36$", *expected],
    ]


def test_survivalplot_can_hide_hazard_ratio_results(
    survival_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import lifelines

    class UnexpectedCoxModel:
        def __init__(self) -> None:
            raise AssertionError("Pairwise Cox inference should be skipped")

    monkeypatch.setattr(lifelines, "CoxPHFitter", UnexpectedCoxModel)

    ax = cns.survivalplot(
        survival_df,
        "time",
        "event",
        "group",
        pairs=[("Control", "Treatment")],
        show_hazard_ratio=False,
    )

    assert _annotation(ax) == "Log-rank P = $0.6$"


def test_survivalplot_uses_lower_left_default_location(
    survival_three_group_df: pd.DataFrame,
) -> None:
    ax = cns.survivalplot(
        survival_three_group_df,
        "time",
        "event",
        "group",
        hue_order=["Low", "Mid", "High"],
        pairs=[("Low", "High")],
    )

    annotation = ax.texts[0]

    assert annotation.get_position() == (0.02, 0.02)
    assert annotation.get_transform() is ax.transAxes
    assert annotation.get_horizontalalignment() == "left"
    assert annotation.get_verticalalignment() == "bottom"
    assert annotation.get_bbox_patch() is None
    assert annotation.get_text().splitlines() == [
        "Log-rank P = $0.36$",
        "High vs Low",
        "HR = 0.38",
        "95% CI 0.08–1.75",
        "Cox P = $0.21$",
    ]


@pytest.mark.parametrize(
    ("pvalue_loc", "position", "horizontalalignment", "verticalalignment"),
    [
        ("upper left", (0.02, 0.98), "left", "top"),
        ("upper right", (0.98, 0.98), "right", "top"),
        ("lower center", (0.5, 0.02), "center", "bottom"),
    ],
)
def test_survivalplot_supports_legend_style_pvalue_locations(
    survival_three_group_df: pd.DataFrame,
    pvalue_loc: str,
    position: tuple[float, float],
    horizontalalignment: str,
    verticalalignment: str,
) -> None:
    ax = cns.survivalplot(
        survival_three_group_df,
        "time",
        "event",
        "group",
        pvalue_loc=cast(Any, pvalue_loc),
    )

    annotation = ax.texts[0]

    assert annotation.get_position() == position
    assert annotation.get_horizontalalignment() == horizontalalignment
    assert annotation.get_verticalalignment() == verticalalignment


def test_survivalplot_rejects_unknown_pvalue_location(
    survival_three_group_df: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="'pvalue_loc' must be one of"):
        cns.survivalplot(
            survival_three_group_df,
            "time",
            "event",
            "group",
            pvalue_loc=cast(Any, "outside"),
        )


@pytest.mark.parametrize(
    ("pairs", "message"),
    [
        (["Low"], "exactly two groups"),
        ([("Low", "Low")], "two distinct groups"),
        ([("Low", "missing")], "not present in 'group'"),
    ],
)
def test_survivalplot_validates_pairwise_contrasts(
    survival_three_group_df: pd.DataFrame,
    pairs: list[object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        cns.survivalplot(
            survival_three_group_df,
            "time",
            "event",
            "group",
            pairs=cast(Any, pairs),
        )


def test_survivalplot_rejects_unknown_overall_test(
    survival_three_group_df: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="'overall_test' must be one of"):
        cns.survivalplot(
            survival_three_group_df,
            "time",
            "event",
            "group",
            overall_test=cast(Any, "score"),
        )
