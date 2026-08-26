from __future__ import annotations

import inspect

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
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


def test_ridgeplot_customization_parameters_are_keyword_only() -> None:
    parameters = inspect.signature(cns.ridgeplot).parameters

    assert parameters["hue"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["overlap"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["overlap"].default == 0.5


@pytest.mark.parametrize(
    ("overlap", "expected_offsets"),
    [
        (None, [1.0, 0.5, 0.0]),
        (0.0, [2.0, 1.0, 0.0]),
        (0.25, [1.5, 0.75, 0.0]),
        (1.0, [0.0, 0.0, 0.0]),
    ],
)
def test_ridgeplot_uses_configurable_overlap(
    overlap: float | None,
    expected_offsets: list[float],
) -> None:
    data = pd.DataFrame(
        {
            "value": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            "group": ["A", "A", "B", "B", "C", "C"],
        }
    )
    _, ax = plt.subplots()

    if overlap is None:
        cns.ridgeplot(data, x="value", y="group", ax=ax)
    else:
        cns.ridgeplot(data, x="value", y="group", ax=ax, overlap=overlap)

    offsets = [
        np.asarray(collection.get_paths()[0].vertices)[:, 1].min()
        for collection in ax.collections
    ]
    assert offsets == pytest.approx(expected_offsets)


def test_ridgeplot_overlays_observed_hues_and_forwards_fill_kwargs() -> None:
    data = pd.DataFrame(
        {
            "value": [0.0, 0.5, 1.0, 2.0, 2.5, 3.0, 4.0, 4.5, 5.0],
            "group": ["A"] * 6 + ["B"] * 3,
            "condition": ["H2"] * 3 + ["H1"] * 6,
        }
    )
    _, ax = plt.subplots()

    cns.ridgeplot(
        data,
        x="value",
        y="group",
        hue="condition",
        ax=ax,
        alpha=0.35,
        linewidth=2.0,
        edgecolor="black",
        zorder=9,
    )

    assert len(ax.collections) == 3
    facecolors = [collection.get_facecolor()[0] for collection in ax.collections]
    assert not np.allclose(facecolors[0], facecolors[1])
    assert np.allclose(facecolors[1], facecolors[2])
    for collection in ax.collections:
        assert collection.get_alpha() == pytest.approx(0.35)
        assert collection.get_linewidth() == pytest.approx([2.0])
        assert np.allclose(
            collection.get_edgecolor(), [mcolors.to_rgba("black", alpha=0.35)]
        )
        assert collection.get_zorder() == 9

    assert [text.get_text() for text in ax.texts] == ["A", "B"]
    legend = ax.get_legend()
    assert legend is not None
    assert legend.get_title().get_text() == "condition"
    assert [text.get_text() for text in legend.get_texts()] == ["H2", "H1"]


def test_ridgeplot_fill_kwargs_override_default_color() -> None:
    data = pd.DataFrame(
        {
            "value": [0.0, 1.0, 2.0, 3.0],
            "group": ["A", "A", "B", "B"],
        }
    )

    ax = cns.ridgeplot(data, x="value", y="group", color="magenta")

    for collection in ax.collections:
        assert np.allclose(collection.get_facecolor(), [mcolors.to_rgba("magenta")])


@pytest.mark.parametrize(
    ("overlap", "error"),
    [
        (True, TypeError),
        ("0.5", TypeError),
        (-0.1, ValueError),
        (1.1, ValueError),
        (np.nan, ValueError),
        (np.inf, ValueError),
    ],
)
def test_ridgeplot_rejects_invalid_overlap_before_kde(
    monkeypatch: pytest.MonkeyPatch,
    overlap: object,
    error: type[Exception],
) -> None:
    data = pd.DataFrame({"value": [0.0, 1.0], "group": ["A", "A"]})

    def unexpected_kde(*args: object, **kwargs: object) -> None:
        raise AssertionError("gaussian_kde should not be called")

    monkeypatch.setattr(scipy.stats, "gaussian_kde", unexpected_kde)

    with pytest.raises(error, match="overlap"):
        cns.ridgeplot(
            data,
            x="value",
            y="group",
            overlap=overlap,  # ty: ignore[invalid-argument-type]
        )


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (
            pd.DataFrame(
                {
                    "value": [0.0, 1.0, 2.0, 3.0],
                    "group": ["A", "A", "B", "B"],
                }
            ),
            "Column",
        ),
        (
            pd.DataFrame(
                {
                    "value": [0.0, 1.0, 2.0, 3.0],
                    "group": ["A", "A", "B", "B"],
                    "condition": ["H1", None, "H1", "H1"],
                }
            ),
            "Null values",
        ),
        (
            pd.DataFrame(
                {
                    "value": [0.0, 1.0, 2.0, 3.0],
                    "group": ["A", "A", "B", "B"],
                    "condition": ["H1", "H2", "H1", "H1"],
                }
            ),
            "at least two observations",
        ),
    ],
)
def test_ridgeplot_rejects_invalid_hue_groups_before_kde(
    monkeypatch: pytest.MonkeyPatch,
    data: pd.DataFrame,
    message: str,
) -> None:
    def unexpected_kde(*args: object, **kwargs: object) -> None:
        raise AssertionError("gaussian_kde should not be called")

    monkeypatch.setattr(scipy.stats, "gaussian_kde", unexpected_kde)

    with pytest.raises(ValueError, match=message):
        cns.ridgeplot(data, x="value", y="group", hue="condition")
