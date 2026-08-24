from __future__ import annotations

import inspect
import types
from typing import Any, TypedDict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.container import ErrorbarContainer
from matplotlib.patches import Rectangle
from pandas.testing import assert_frame_equal

import cnsplots as cns


def _plain_results() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "term": ["Treatment", "Age"],
            "effect": [0.8, 1.2],
            "ci_low": [0.6, 1.0],
            "ci_high": [1.1, 1.5],
        }
    )


class _TableKwargs(TypedDict):
    label: str
    estimate: str
    lower: str
    upper: str


def _table_kwargs() -> _TableKwargs:
    return {
        "label": "term",
        "estimate": "effect",
        "lower": "ci_low",
        "upper": "ci_high",
    }


def test_forestplot_table_uses_absolute_bounds_without_mutating_input() -> None:
    data = _plain_results()
    original = data.copy(deep=True)
    _, ax = plt.subplots()

    result = cns.forestplot(data=data, ax=ax, **_table_kwargs())

    assert result is ax
    assert_frame_equal(data, original)
    assert ax.get_xlabel() == "effect"
    assert [tick.get_text() for tick in ax.get_yticklabels()] == [
        "Treatment",
        "Age",
    ]
    assert not [line for line in ax.lines if line.get_linestyle() == "--"]
    assert len(ax.figure.axes) == 1

    errorbars = [
        container
        for container in ax.containers
        if isinstance(container, ErrorbarContainer)
    ]
    assert len(errorbars) == 1
    segments = errorbars[0].lines[2][0].get_segments()
    assert [segment[:, 0].tolist() for segment in segments] == [
        pytest.approx([0.6, 1.1]),
        pytest.approx([1.0, 1.5]),
    ]


def test_forestplot_table_supports_grouped_rows_hue_and_pvalues() -> None:
    data = pd.DataFrame(
        {
            "section": [
                "Primary",
                "Primary",
                "Subgroup",
                "Subgroup",
                "Subgroup",
                "Subgroup",
            ],
            "term": ["Outcome", "Outcome", "Outcome", "Outcome", "Age", "Age"],
            "cohort": ["A", "B", "A", "B", "A", "B"],
            "effect": [0.8, 0.9, 0.7, 0.85, 1.2, 1.1],
            "ci_low": [0.6, 0.7, 0.5, 0.65, 1.0, 0.9],
            "ci_high": [1.0, 1.1, 0.9, 1.05, 1.4, 1.3],
            "probability": [0.05, 0.1, 0.01, 0.02, 0.2, 0.4],
        }
    )
    _, ax = plt.subplots()

    result = cns.forestplot(
        data=data,
        **_table_kwargs(),
        pvalue="probability",
        group="section",
        hue="cohort",
        group_order=["Subgroup", "Primary"],
        order=["Age", "Outcome"],
        hue_order=["B", "A"],
        reference=1,
        xlabel="Risk ratio (95% CI)",
        bar_width=0.3,
        ax=ax,
    )

    assert result is ax
    assert ax.get_xlabel() == "Risk ratio (95% CI)"
    tick_labels = ax.get_yticklabels()
    assert [tick.get_text() for tick in tick_labels] == [
        "Subgroup",
        "  Age",
        "  Outcome",
        "Primary",
        "  Outcome",
    ]
    assert [tick.get_fontweight() for tick in tick_labels] == [
        "bold",
        "normal",
        "normal",
        "bold",
        "normal",
    ]
    legend = ax.get_legend()
    assert legend is not None
    assert legend.get_title().get_text() == "cohort"
    assert [text.get_text() for text in legend.get_texts()] == ["B", "A"]
    reference_lines = [line for line in ax.lines if line.get_linestyle() == "--"]
    assert len(reference_lines) == 1
    assert np.asarray(reference_lines[0].get_xdata()) == pytest.approx([1, 1])

    assert len(ax.figure.axes) == 2
    pvalue_ax = ax.figure.axes[-1]
    assert pvalue_ax.get_ylim() == pytest.approx(ax.get_ylim())
    assert pvalue_ax.get_xlabel() == "\u2013log10(p-value)"
    bars = [patch for patch in pvalue_ax.patches if isinstance(patch, Rectangle)]
    assert sorted(patch.get_width() for patch in bars) == pytest.approx(
        sorted(-np.log10(data["probability"]))
    )
    assert all(patch.get_height() == pytest.approx(0.3) for patch in bars)
    bar_centers = [patch.get_y() + patch.get_height() / 2 for patch in bars]
    assert not {4.0, 1.0}.intersection(bar_centers)


def test_forestplot_accepts_positional_table_and_complete_order() -> None:
    _, ax = plt.subplots()

    cns.forestplot(
        _plain_results(),
        add_pvalue=False,
        order=["Age", "Treatment"],
        ax=ax,
        **_table_kwargs(),
    )

    assert [tick.get_text() for tick in ax.get_yticklabels()] == [
        "Age",
        "Treatment",
    ]
    assert len(ax.figure.axes) == 1


def test_forestplot_preserves_first_appearance_within_each_group() -> None:
    data = pd.DataFrame(
        {
            "section": ["First", "First", "Second", "Second"],
            "term": ["A", "B", "C", "A"],
            "effect": [1.0, 1.1, 0.9, 1.2],
            "ci_low": [0.8, 0.9, 0.7, 1.0],
            "ci_high": [1.2, 1.3, 1.1, 1.4],
        }
    )
    _, ax = plt.subplots()

    cns.forestplot(data=data, group="section", ax=ax, **_table_kwargs())

    assert [tick.get_text() for tick in ax.get_yticklabels()] == [
        "First",
        "  A",
        "  B",
        "Second",
        "  C",
        "  A",
    ]


def test_forestplot_preserves_model_keyword_and_allows_display_overrides() -> None:
    model = types.SimpleNamespace(
        name="logistic",
        hue=None,
        results=pd.DataFrame(
            {
                "predictor": ["Age", "Stage"],
                "auc": [0.7, 0.8],
                "lower_ci": [0.1, 0.1],
                "upper_ci": [0.15, 0.1],
                "hue_group": ["All", "All"],
            }
        ),
    )
    _, ax = plt.subplots()

    cns.forestplot(
        model=model,
        reference=0.75,
        xlabel="Validation AUC",
        order=["Stage", "Age"],
        ax=ax,
    )

    assert ax.get_xlabel() == "Validation AUC"
    assert [tick.get_text() for tick in ax.get_yticklabels()] == ["Stage", "Age"]
    reference_line = next(line for line in ax.lines if line.get_linestyle() == "--")
    assert np.asarray(reference_line.get_xdata()) == pytest.approx([0.75, 0.75])


def test_forestplot_signature_exposes_table_mappings_as_keyword_only() -> None:
    parameters = inspect.signature(cns.forestplot).parameters

    assert parameters["model"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters["bar_width"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters["add_pvalue"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    for name in {
        "data",
        "label",
        "estimate",
        "lower",
        "upper",
        "pvalue",
        "group",
        "hue",
        "order",
        "group_order",
        "hue_order",
        "reference",
        "xlabel",
        "ax",
    }:
        assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({}, "exactly one"),
        (
            {"model": types.SimpleNamespace(), "data": _plain_results()},
            "exactly one",
        ),
        ({"data": "not a frame"}, "pandas DataFrame"),
        ({"data": _plain_results()}, "requires column mappings"),
        (
            {
                "data": _plain_results(),
                **{**_table_kwargs(), "estimate": "missing"},
            },
            "not found",
        ),
        (
            {
                "data": _plain_results().assign(effect=["low", "high"]),
                **_table_kwargs(),
            },
            "real numeric",
        ),
        (
            {
                "data": _plain_results().assign(ci_low=[-np.inf, 1.0]),
                **_table_kwargs(),
            },
            "finite values",
        ),
        (
            {
                "data": _plain_results().assign(ci_low=[0.9, 1.0]),
                **_table_kwargs(),
            },
            "lower <= estimate <= upper",
        ),
        (
            {
                "data": _plain_results().assign(probability=[0.0, 0.5]),
                **_table_kwargs(),
                "pvalue": "probability",
            },
            "P-values",
        ),
        (
            {
                "data": pd.concat([_plain_results().iloc[[0]]] * 2),
                **_table_kwargs(),
            },
            "exactly one row",
        ),
        (
            {"model": types.SimpleNamespace(name="linear", results=_plain_results())},
            "Unsupported fitted model",
        ),
        (
            {
                "model": types.SimpleNamespace(
                    name="logistic", results=_plain_results()
                ),
                "label": "term",
            },
            "only valid with DataFrame",
        ),
        ({"data": _plain_results(), **_table_kwargs(), "bar_width": 0}, "bar_width"),
        (
            {"data": _plain_results(), **_table_kwargs(), "reference": np.inf},
            "reference",
        ),
        (
            {"data": _plain_results(), **_table_kwargs(), "xlabel": 1},
            "xlabel",
        ),
        (
            {"data": _plain_results(), **_table_kwargs(), "order": ("Age",)},
            "must be a list",
        ),
        (
            {"data": _plain_results(), **_table_kwargs(), "order": ["Age"]},
            "every observed value",
        ),
        (
            {
                "data": _plain_results(),
                **_table_kwargs(),
                "group_order": ["group"],
            },
            "requires a 'group'",
        ),
        (
            {
                "data": _plain_results(),
                **_table_kwargs(),
                "hue_order": ["hue"],
            },
            "requires a 'hue'",
        ),
    ],
)
def test_forestplot_rejects_invalid_table_inputs(
    kwargs: dict[str, Any], match: str
) -> None:
    with pytest.raises((TypeError, ValueError), match=match):
        cns.forestplot(**kwargs)
