from __future__ import annotations

import inspect
from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import cnsplots as cns


_CONTINUOUS_PLOTS = ("boxplot", "violinplot", "barplot", "lollipopplot")
_P_ADJUST_METHODS = ("bonferroni", "holm", "fdr_bh", "fdr_by")


@pytest.mark.parametrize(
    ("plot_name", "default_test"),
    [
        ("boxplot", "Mann-Whitney"),
        ("violinplot", "Mann-Whitney"),
        ("barplot", "t-test_welch"),
        ("lollipopplot", "t-test_welch"),
        ("stackplot", "auto"),
    ],
)
def test_statistical_options_are_keyword_only(
    plot_name: str,
    default_test: str,
) -> None:
    parameters = inspect.signature(getattr(cns, plot_name)).parameters

    assert parameters["test"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["test"].default == default_test
    assert parameters["p_adjust"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["p_adjust"].default is None


@pytest.mark.parametrize("plot_name", _CONTINUOUS_PLOTS)
def test_continuous_plots_forward_tests_and_corrections(
    plot_name: str,
    categorical_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr(
        cns.utils,
        "_p_value_helper",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    plotter = getattr(cns, plot_name)

    for test in ("Mann-Whitney", "t-test_welch"):
        for p_adjust in _P_ADJUST_METHODS:
            cns.figure(120, 120)
            plotter(
                categorical_df,
                x="group",
                y="value",
                pairs=[("A", "B")],
                test=test,
                p_adjust=p_adjust,
            )
            args, kwargs = calls[-1]
            assert args[0] == test
            assert kwargs["p_adjust"] == p_adjust
            plt.close()


@pytest.mark.parametrize(
    ("plot_name", "expected_test"),
    [
        ("boxplot", "Mann-Whitney"),
        ("violinplot", "Mann-Whitney"),
        ("barplot", "t-test_welch"),
        ("lollipopplot", "t-test_welch"),
    ],
)
def test_continuous_plot_defaults_remain_uncorrected(
    plot_name: str,
    expected_test: str,
    categorical_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr(
        cns.utils,
        "_p_value_helper",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    getattr(cns, plot_name)(
        categorical_df,
        x="group",
        y="value",
        pairs=[("A", "B")],
    )

    args, kwargs = calls[0]
    assert args[0] == expected_test
    assert kwargs["p_adjust"] is None


def test_stackplot_selects_or_overrides_test(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr(
        cns.utils,
        "_p_value_helper",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    binary = pd.DataFrame(
        {
            "group": ["A", "A", "B", "B"],
            "outcome": ["Yes", "No", "Yes", "No"],
        }
    )
    multiclass = pd.DataFrame(
        {
            "group": ["A", "A", "A", "B", "B", "B"],
            "outcome": ["One", "Two", "Three", "One", "Two", "Three"],
        }
    )

    cns.stackplot(binary, x="group", stack="outcome", pairs=[("A", "B")])
    cns.stackplot(multiclass, x="group", stack="outcome", pairs=[("A", "B")])
    cns.stackplot(
        binary,
        x="group",
        stack="outcome",
        pairs=[("A", "B")],
        test="chi-squared",
        p_adjust="fdr_bh",
    )
    cns.stackplot(
        multiclass,
        x="group",
        stack="outcome",
        pairs=[("A", "B")],
        test="fisher-exact",
        p_adjust="bonferroni",
    )

    assert [call[0][0] for call in calls] == [
        "fisher-exact",
        "chi-squared",
        "chi-squared",
        "fisher-exact",
    ]
    assert [call[1]["p_adjust"] for call in calls] == [
        None,
        None,
        "fdr_bh",
        "bonferroni",
    ]


@pytest.mark.parametrize("plot_name", (*_CONTINUOUS_PLOTS, "stackplot"))
def test_plots_reject_unsupported_statistical_options(
    plot_name: str,
    categorical_df: pd.DataFrame,
) -> None:
    plotter = getattr(cns, plot_name)
    plotting = (
        {"data": categorical_df, "x": "group", "stack": "binary"}
        if plot_name == "stackplot"
        else {"data": categorical_df, "x": "group", "y": "value"}
    )

    with pytest.raises(ValueError, match="test must be one of"):
        plotter(**plotting, test="unsupported")
    with pytest.raises(ValueError, match="p_adjust must be one of"):
        plotter(**plotting, p_adjust="BH")


def test_p_value_helper_corrects_all_resolved_pairs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DummyAnnotator:
        instances: list[DummyAnnotator] = []

        def __init__(self, ax: object, pairs: object, **plotting: object) -> None:
            self.pairs = list(cast(Any, pairs))
            self.plotting = plotting
            self.configured: dict[str, object] = {}
            self.pvalues: list[float] | None = None
            self._pvalue_format: object = None
            self.instances.append(self)

        def configure(self, **kwargs: object) -> None:
            self.configured = kwargs

        def apply_and_annotate(self) -> None:
            return None

        def set_pvalues(self, pvalues: list[float]) -> None:
            self.pvalues = pvalues

        def annotate(self) -> None:
            return None

    monkeypatch.setattr(cns.utils, "Annotator", DummyAnnotator)
    data = pd.DataFrame(
        {
            "group": [group for group in "ABCDE" for _ in range(2)],
            "value": list(range(10)),
        }
    )
    _, ax = plt.subplots()

    cns.utils._p_value_helper(
        "Mann-Whitney",
        data,
        ax,
        {"x": "group", "y": "value"},
        "all",
        p_adjust="holm",
    )

    continuous_annotator = DummyAnnotator.instances[-1]
    assert len(continuous_annotator.pairs) == 10
    assert continuous_annotator.configured["comparisons_correction"] == "holm"

    contingency = pd.DataFrame(
        [[3, 1], [1, 3]],
        index=pd.Index(["A", "B"]),
        columns=pd.Index(["Yes", "No"]),
    )
    cns.utils._p_value_helper(
        "fisher-exact",
        data,
        ax,
        {"x": "group", "y": "value"},
        [("A", "B")],
        contingency=contingency,
        p_adjust="fdr_by",
    )

    contingency_annotator = DummyAnnotator.instances[-1]
    assert contingency_annotator.configured["test"] is None
    assert contingency_annotator.configured["comparisons_correction"] == "fdr_by"
    assert contingency_annotator.pvalues is not None
    assert len(contingency_annotator.pvalues) == 1
