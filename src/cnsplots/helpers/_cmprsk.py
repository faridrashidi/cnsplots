from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import Series

import pandas as pd
from lifelines.statistics import multivariate_logrank_test


def cuminc(
    durations: Series,
    events: Series,
    group: Series,
    event_of_interest: int = 1,
    competing_event: int = 2,
) -> float:
    """
    Approximates Gray's Test (cmprsk::cuminc) using a Subdistribution Hazard
    Log-Rank Test in pure Python.

    Method:
    1. Identifies the Competing Events.
    2. "Immortalizes" them: In the subdistribution framework, subjects who
       experience a competing event remain in the risk set for the event of interest
       (effectively censored at infinity).
    3. Runs a standard Log-Rank test on this modified risk set.

    Parameters:
    - durations: Sequence of time-to-event.
    - events: Sequence of event codes (0=censored, 1=interest, 2=competing).
    - group: Sequence of group labels.
    - event_of_interest: The code for the primary event (default 1).
    - competing_event: The code for the competing event (default 2).

    Returns:
    - p_value: The p-value testing the null hypothesis that CIFs are identical.
    """

    # 1. Create a working dataframe
    df = pd.DataFrame({"T": durations, "E": events, "group": group})

    # 2. Pre-process for Subdistribution Hazard (Fine-Gray approach)
    # The trick: Subjects with the *competing* event are treated as if
    # they are still in the risk set (censored at a time later than the max time).

    # Find the maximum time in the dataset to shift competing events beyond it
    max_time = df["T"].max() + 1.0

    # Create mask for competing events
    mask_competing = df["E"] == competing_event

    # Create mask for the event of interest
    mask_interest = df["E"] == event_of_interest

    # Apply the transformation:
    # - Event of Interest: Stays as Event (1) at Time T
    # - Censored: Stays as Censored (0) at Time T
    # - Competing Event: Becomes Censored (0) at Time "Infinity" (max_time)

    df["T_mod"] = df["T"]
    df["E_mod"] = 0  # Default to censored

    # Set event of interest
    df.loc[mask_interest, "E_mod"] = 1

    # For competing events, shift time to 'infinity' so they stay in risk set
    df.loc[mask_competing, "T_mod"] = max_time

    # 3. Run Multivariate Log-Rank Test on the modified data
    # This compares the subdistribution hazards across groups
    result = multivariate_logrank_test(
        event_durations=df["T_mod"], event_observed=df["E_mod"], groups=df["group"]
    )

    return result.p_value
