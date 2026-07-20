from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import cnsplots as cns


def test_survivalplot_requires_zero_one_event_semantics(
    survival_df: pd.DataFrame,
) -> None:
    invalid = survival_df.copy()
    invalid["event"] += 1

    with pytest.raises(ValueError, match="specifically 0 and 1"):
        cns.survivalplot(invalid, "time", "event", "group")


@pytest.mark.parametrize(
    ("invalid_duration", "message"),
    [(np.inf, "finite durations"), (-1.0, "non-negative durations")],
)
def test_survivalplot_requires_valid_durations(
    survival_df: pd.DataFrame,
    invalid_duration: float,
    message: str,
) -> None:
    invalid = survival_df.copy()
    invalid.loc[0, "time"] = invalid_duration

    with pytest.raises(ValueError, match=message):
        cns.survivalplot(invalid, "time", "event", "group")


@pytest.mark.parametrize("duration_kind", ["complex", "boolean"])
def test_survivalplot_requires_real_numeric_durations(
    survival_df: pd.DataFrame,
    duration_kind: str,
) -> None:
    invalid = survival_df.copy()
    if duration_kind == "complex":
        invalid["time"] = invalid["time"].astype(complex) + 1j
    else:
        invalid["time"] = invalid["time"] > invalid["time"].median()

    with pytest.raises(ValueError, match="real-valued numeric durations"):
        cns.survivalplot(invalid, "time", "event", "group")


@pytest.mark.parametrize("invalid_code", [-1.0, 1.5, np.inf])
def test_cumulativeincidenceplot_requires_valid_event_codes(
    competing_risk_df: pd.DataFrame,
    invalid_code: float,
) -> None:
    invalid = competing_risk_df.copy()
    invalid.loc[0, "event"] = invalid_code

    with pytest.raises(ValueError, match="non-negative integer event codes"):
        cns.cumulativeincidenceplot(invalid, "time", "event", "group")


def test_cumulativeincidenceplot_rejects_complex_event_codes(
    competing_risk_df: pd.DataFrame,
) -> None:
    invalid = competing_risk_df.copy()
    invalid["event"] = invalid["event"].astype(complex) + 1j

    with pytest.raises(ValueError, match="non-negative integer event codes"):
        cns.cumulativeincidenceplot(invalid, "time", "event", "group")


def test_cumulativeincidenceplot_requires_numeric_event_codes(
    competing_risk_df: pd.DataFrame,
) -> None:
    invalid = competing_risk_df.assign(event=lambda frame: frame["event"].astype(str))

    with pytest.raises(ValueError, match="must be numeric"):
        cns.cumulativeincidenceplot(invalid, "time", "event", "group")


def test_survivalplot_requires_two_groups(survival_df: pd.DataFrame) -> None:
    invalid = survival_df.assign(group="only")

    with pytest.raises(ValueError, match="at least 2 groups"):
        cns.survivalplot(invalid, "time", "event", "group")


def test_survivalplot_requires_two_observations_per_group(
    survival_df: pd.DataFrame,
) -> None:
    invalid = pd.concat(
        [
            survival_df[survival_df["group"] == "Control"],
            survival_df[survival_df["group"] == "Treatment"].iloc[[0]],
        ],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="at least 2 observations"):
        cns.survivalplot(invalid, "time", "event", "group")


def test_survivalplot_requires_an_event_per_group(
    survival_df: pd.DataFrame,
) -> None:
    invalid = survival_df.copy()
    invalid.loc[invalid["group"] == "Treatment", "event"] = 0

    with pytest.raises(ValueError, match="at least one event of interest"):
        cns.survivalplot(invalid, "time", "event", "group")


def test_survival_time_labels_are_explicit_and_endpoint_neutral(
    survival_df: pd.DataFrame,
    competing_risk_df: pd.DataFrame,
) -> None:
    ax = cns.survivalplot(
        survival_df,
        "time",
        "event",
        "group",
        time_label="Follow-up (months)",
    )
    assert ax.get_xlabel() == "Follow-up (months)"
    assert ax.get_ylabel() == "Survival probability"

    plt.figure()
    cif_ax = cns.cumulativeincidenceplot(
        competing_risk_df,
        "time",
        "event",
        "group",
        time_label="Follow-up (years)",
    )
    assert cif_ax.get_xlabel() == "Follow-up (years)"


def test_cumulativeincidenceplot_accepts_multiple_competing_event_codes(
    competing_risk_df: pd.DataFrame,
) -> None:
    data = competing_risk_df.copy()
    data.loc[data["event"] == 2, "event"] = 3

    ax = cns.cumulativeincidenceplot(data, "time", "event", "group")

    assert ax.get_xlabel() == "Time"
    assert ax.texts[0].get_text() == "P = $0.88$"


def test_cumulativeincidenceplot_ties_are_deterministic_without_rng_side_effects() -> (
    None
):
    tied = pd.DataFrame(
        {
            "time": [1, 1, 2, 3, 1, 1, 2, 3],
            "event": [1, 2, 0, 1, 1, 2, 0, 1],
            "group": ["A"] * 4 + ["B"] * 4,
        }
    )

    np.random.seed(123)
    expected_random_values = np.random.random(5)
    np.random.seed(123)
    with pytest.warns(Warning, match="Tied event times"):
        first_ax = cns.cumulativeincidenceplot(tied, "time", "event", "group", seed=17)
    actual_random_values = np.random.random(5)
    first_coordinates = [
        (
            np.asarray(line.get_xdata()).copy(),
            np.asarray(line.get_ydata()).copy(),
        )
        for line in first_ax.lines
    ]

    plt.figure()
    with pytest.warns(Warning, match="Tied event times"):
        second_ax = cns.cumulativeincidenceplot(tied, "time", "event", "group", seed=17)

    np.testing.assert_array_equal(actual_random_values, expected_random_values)
    assert len(first_coordinates) == len(second_ax.lines)
    for (first_x, first_y), second_line in zip(
        first_coordinates, second_ax.lines, strict=True
    ):
        np.testing.assert_array_equal(first_x, second_line.get_xdata())
        np.testing.assert_array_equal(first_y, second_line.get_ydata())
