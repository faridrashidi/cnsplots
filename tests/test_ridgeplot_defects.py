from __future__ import annotations

import pandas as pd
import pytest
import scipy.stats

import cnsplots as cns


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (
            pd.DataFrame(
                {"value": [1.0, None, 2.0, 3.0], "group": ["A", "A", "B", "B"]}
            ),
            "Null values",
        ),
        (
            pd.DataFrame({"value": [2.0, 3.0, 1.0], "group": ["B", "B", "A"]}),
            "at least two observations",
        ),
        (
            pd.DataFrame(
                {"value": [2.0, 3.0, 1.0, 1.0], "group": ["B", "B", "A", "A"]}
            ),
            "constant",
        ),
    ],
)
def test_ridgeplot_rejects_invalid_groups_before_kde(
    monkeypatch: pytest.MonkeyPatch,
    data: pd.DataFrame,
    message: str,
) -> None:
    def unexpected_kde(*args: object, **kwargs: object) -> None:
        raise AssertionError("gaussian_kde should not be called")

    monkeypatch.setattr(scipy.stats, "gaussian_kde", unexpected_kde)

    with pytest.raises(ValueError, match=message):
        cns.ridgeplot(data, x="value", y="group")


def test_ridgeplot_rejects_null_group_labels() -> None:
    data = pd.DataFrame({"value": [1.0, 2.0, 3.0, 4.0], "group": ["A", "A", None, "B"]})

    with pytest.raises(ValueError, match="Null values"):
        cns.ridgeplot(data, x="value", y="group")
