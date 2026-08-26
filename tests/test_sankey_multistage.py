from __future__ import annotations

import inspect
from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import cnsplots as cns
from cnsplots.plots import _specialized


@pytest.fixture
def multistage_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "baseline": ["A", "A", "B", "B"],
            "week_4": ["C", "D", "C", "D"],
            "week_12": ["E", "E", "F", "F"],
        }
    )


def test_sankeyplot_delegates_ordered_stages(
    multistage_data: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def capture_multistage(*args: Any, **kwargs: Any) -> None:
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(
        _specialized.helper_sankey, "multistage_sankeyplot", capture_multistage
    )
    _, ax = plt.subplots()

    with cns.settings.context(legend_fontsize=13):
        result = cns.sankeyplot(
            multistage_data,
            x=["baseline", "week_4", "week_12"],
            label_rotation=30,
            ax=ax,
        )

    assert result is ax
    args = captured["args"]
    assert args[0] is multistage_data
    assert args[1] == ["baseline", "week_4", "week_12"]
    kwargs = captured["kwargs"]
    assert kwargs["ax"] is ax
    assert kwargs["fontsize"] == 13
    assert kwargs["label_rotation"] == 30
    assert set(kwargs["colorDict"]) == {"A", "B", "C", "D", "E", "F"}


def test_sankeyplot_two_stage_list_uses_legacy_renderer(
    multistage_data: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def capture_legacy(*args: Any, **kwargs: Any) -> None:
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(_specialized.helper_sankey, "sankeyplot", capture_legacy)
    monkeypatch.setattr(
        _specialized.helper_sankey,
        "multistage_sankeyplot",
        lambda *args, **kwargs: pytest.fail("unexpected multistage renderer"),
    )

    cns.sankeyplot(multistage_data, x=["baseline", "week_4"])

    left, right = captured["args"]
    pd.testing.assert_series_equal(left, multistage_data["baseline"])
    pd.testing.assert_series_equal(right, multistage_data["week_4"])


def test_sankeyplot_uses_single_stage_list_parameter() -> None:
    assert tuple(inspect.signature(cns.sankeyplot).parameters) == (
        "data",
        "x",
        "label_rotation",
        "ax",
    )


@pytest.mark.parametrize(
    ("x", "exception", "message"),
    [
        (["baseline"], ValueError, "at least two stage columns"),
        (["baseline", 4], TypeError, "Every stage column"),
        ("baseline", TypeError, "must be a list"),
        (("baseline", "week_4"), TypeError, "must be a list"),
    ],
)
def test_sankeyplot_validates_stage_arguments(
    multistage_data: pd.DataFrame,
    x: object,
    exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(exception, match=message):
        cast(Any, cns.sankeyplot)(multistage_data, x=x)


def test_sankeyplot_validates_every_stage_column(
    multistage_data: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="missing"):
        cns.sankeyplot(multistage_data, x=["baseline", "week_4", "missing"])

    data_with_null = multistage_data.copy()
    data_with_null.loc[0, "week_4"] = None
    with pytest.raises(ValueError, match="week_4"):
        cns.sankeyplot(
            data_with_null,
            x=["baseline", "week_4", "week_12"],
        )
