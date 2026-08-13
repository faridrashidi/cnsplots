from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import cnsplots as cns


def test_survivalplot_can_show_confidence_bands(
    survival_df: pd.DataFrame,
) -> None:
    default_ax = cns.survivalplot(survival_df, "time", "event", "group")
    assert len(default_ax.collections) == 0

    plt.figure()
    ci_ax = cns.survivalplot(
        survival_df,
        "time",
        "event",
        "group",
        ci_show=True,
    )
    assert len(ci_ax.collections) == 2


def test_survivalplot_risk_table_uses_supplied_axes_and_ticks(
    survival_df: pd.DataFrame,
) -> None:
    fig, (target_ax, current_ax) = plt.subplots(1, 2)
    plt.sca(current_ax)

    result = cns.survivalplot(
        survival_df,
        "time",
        "event",
        "group",
        show_risk_table=True,
        xticks=[0, 4, 8],
        ax=target_ax,
    )

    assert result is target_ax
    assert list(target_ax.get_xticks()) == [0, 4, 8]
    assert fig.axes[-1] is not current_ax
    risk_table_labels = [
        label.get_text().split() for label in fig.axes[-1].get_xticklabels()
    ]
    assert risk_table_labels == [
        ["At", "risk", "Control", "6", "Treatment", "6"],
        ["6", "5"],
        ["2", "2"],
    ]


def test_survivalplot_can_annotate_median_survival(
    survival_df: pd.DataFrame,
) -> None:
    data = survival_df.copy()
    treatment = data["group"] == "Treatment"
    data.loc[treatment, "event"] = 0
    data.loc[treatment & (data["time"] == 4), "event"] = 1

    ax = cns.survivalplot(
        data,
        "time",
        "event",
        "group",
        show_hazard_ratio=False,
        show_median_survival=True,
    )

    assert ax.texts[0].get_text().splitlines()[-3:] == [
        "Median survival",
        "Control = 8",
        "Treatment = not reached",
    ]
    assert len(ax.collections) == 2


def test_survivalplot_can_run_two_group_landmark_analysis(
    survival_df: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("INFO", logger="cnsplots"):
        ax = cns.survivalplot(
            survival_df,
            "time",
            "event",
            "group",
            landmark_time=6,
        )

    assert ax.texts[0].get_text().splitlines()[-4:] == [
        "Survival at 6",
        "Control = 0.67",
        "Treatment = 0.62",
        "Landmark P = $0.88$",
    ]
    assert "fixed-time log-minus-log test" in caplog.text
    assert len(ax.collections) == 2
    assert any(np.array_equal(line.get_xdata(), [6, 6]) for line in ax.lines)


def test_survivalplot_skips_landmark_test_at_survival_boundary(
    survival_df: pd.DataFrame,
) -> None:
    ax = cns.survivalplot(
        survival_df,
        "time",
        "event",
        "group",
        landmark_time=1,
    )

    assert ax.texts[0].get_text().splitlines()[-3:] == [
        "Survival at 1",
        "Control = 1.00",
        "Treatment = 1.00",
    ]


def test_survivalplot_can_report_rmst(survival_df: pd.DataFrame) -> None:
    ax = cns.survivalplot(
        survival_df,
        "time",
        "event",
        "group",
        rmst_time=8,
    )

    assert ax.texts[0].get_text().splitlines()[-3:] == [
        "RMST to 8",
        "Control = 7.17",
        "Treatment = 6.92",
    ]
    assert any(np.array_equal(line.get_xdata(), [8, 8]) for line in ax.lines)


@pytest.mark.parametrize("invalid_time", [True, "six", np.inf, 0])
def test_survivalplot_requires_positive_finite_analysis_times(
    survival_df: pd.DataFrame,
    invalid_time: Any,
) -> None:
    with pytest.raises(ValueError, match="finite positive number"):
        cns.survivalplot(
            survival_df,
            "time",
            "event",
            "group",
            landmark_time=invalid_time,
        )


def test_survivalplot_analysis_times_require_common_follow_up(
    survival_df: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="common follow-up time \\(11\\)"):
        cns.survivalplot(
            survival_df,
            "time",
            "event",
            "group",
            rmst_time=12,
        )
