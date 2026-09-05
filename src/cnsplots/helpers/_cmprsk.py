from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import Series

import numpy as np
import pandas as pd

from cnsplots._validation import (
    validate_categorical_has_levels,
    validate_column_type,
    validate_dataframe_not_empty,
    validate_length_match,
    validate_no_nulls,
)


def cuminc(
    durations: Series,
    events: Series,
    group: Series,
    event_of_interest: int = 1,
) -> float:
    """
    Calculate Gray's K-sample test p-value for cumulative incidence functions.

    Parameters:
    - durations: Sequence of time-to-event.
    - events: Sequence of event codes (0=censored; all other codes are events).
    - group: Sequence of group labels.
    - event_of_interest: The code for the primary event (default 1).

    Returns:
    - p_value: The p-value testing the null hypothesis that CIFs are identical.
    """

    validate_length_match(durations, events, "durations", "events", "cuminc")
    validate_length_match(durations, group, "durations", "group", "cuminc")

    # 1. Create a working dataframe
    df = pd.DataFrame({"T": durations, "E": events, "group": group})
    validate_dataframe_not_empty(df, "cuminc")
    validate_no_nulls(df, ["T", "E", "group"], "cuminc")
    validate_column_type(df, "T", ["numeric"], "cuminc")
    validate_column_type(df, "E", ["numeric"], "cuminc")
    validate_categorical_has_levels(df, "group", min_levels=2, function_name="cuminc")

    from comprisk import gray_test

    result = gray_test(
        time=df["T"],
        event=df["E"],
        group=df["group"],
        cause=event_of_interest,
        rho=0.0,
    )

    if (
        not np.isfinite(result.var).all()
        or np.linalg.matrix_rank(result.var) < result.df
    ):
        raise ValueError("Gray's test comparison variance is zero or singular")
    return float(result.pvalue)
