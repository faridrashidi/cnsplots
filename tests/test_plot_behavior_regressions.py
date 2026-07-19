from __future__ import annotations

import sys
import types

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import LineCollection, PathCollection

import cnsplots as cns


@pytest.mark.parametrize("horizontal", [False, True])
@pytest.mark.parametrize("with_hue", [False, True])
def test_lollipop_geometry_is_consistent_across_orientations_and_hue(
    horizontal: bool,
    with_hue: bool,
) -> None:
    data = pd.DataFrame(
        {
            "category": ["A", "A", "A", "A", "B", "B", "B", "B"],
            "value": [1.0, 3.0, 2.0, 4.0, 5.0, 7.0, 6.0, 8.0],
            "hue": ["H1", "H1", "H2", "H2"] * 2,
        }
    )
    x, y = ("value", "category") if horizontal else ("category", "value")

    cns.figure(120, 120)
    ax = cns.lollipopplot(data, x=x, y=y, hue="hue" if with_hue else None)

    value_series = [[2.0, 6.0], [3.0, 7.0]] if with_hue else [[2.5, 6.5]]
    position_series = [[-0.2, 0.8], [0.2, 1.2]] if with_hue else [[0.0, 1.0]]
    scatter_collections = [
        collection
        for collection in ax.collections
        if isinstance(collection, PathCollection)
    ]
    stem_collections = [
        collection
        for collection in ax.collections
        if isinstance(collection, LineCollection)
    ]
    assert len(scatter_collections) == len(value_series)
    assert len(stem_collections) == len(value_series)
    if with_hue:
        assert ax.get_legend() is not None
        assert ax.get_legend().get_title().get_text() == "hue"
        assert [text.get_text() for text in ax.get_legend().get_texts()] == ["H1", "H2"]

    for scatter, stems, values, positions in zip(
        scatter_collections, stem_collections, value_series, position_series
    ):
        expected_offsets = (
            np.column_stack((values, positions))
            if horizontal
            else np.column_stack((positions, values))
        )
        expected_stems = [
            ([[0.0, position], [value, position]])
            if horizontal
            else ([[position, 0.0], [position, value]])
            for position, value in zip(positions, values)
        ]
        np.testing.assert_allclose(
            np.asarray(scatter.get_offsets(), dtype=float), expected_offsets
        )
        np.testing.assert_allclose(stems.get_segments(), expected_stems)


def test_lollipop_ignores_missing_order_categories_for_errors_and_tips() -> None:
    data = pd.DataFrame({"category": ["A", "A", "B", "B"], "value": range(4)})

    cns.figure(120, 120)
    ax = cns.lollipopplot(
        data,
        x="category",
        y="value",
        order=["A", "B", "missing"],
        errorbar="se",
        addtip=True,
    )

    assert [text.get_text() for text in ax.texts] == ["0.50", "2.50"]


def test_lollipop_rejects_ambiguous_palette_column_combinations() -> None:
    data = pd.DataFrame(
        {
            "category": ["A", "A", "B", "B"],
            "value": range(4),
            "hue": ["H1", "H2", "H1", "H2"],
            "palette_group": ["P1", "P1", "P2", "P2"],
        }
    )

    with pytest.raises(ValueError, match="cannot be combined"):
        cns.lollipopplot(
            data,
            x="category",
            y="value",
            hue="hue",
            palette="palette_group",
        )

    ambiguous = data.copy()
    ambiguous.loc[1, "palette_group"] = "P2"
    with pytest.raises(ValueError, match="must map each category to one label"):
        cns.lollipopplot(
            ambiguous,
            x="category",
            y="value",
            palette="palette_group",
        )


def test_survival_plots_do_not_mutate_input_dataframes(
    survival_df: pd.DataFrame,
    competing_risk_df: pd.DataFrame,
) -> None:
    survival_original = survival_df.copy(deep=True)
    cns.figure(120, 120)
    cns.survivalplot(survival_df, "time", "event", "group")
    pd.testing.assert_frame_equal(survival_df, survival_original)

    competing_risk_original = competing_risk_df.copy(deep=True)
    cns.figure(120, 120)
    cns.cumulativeincidenceplot(competing_risk_df, "time", "event", "group")
    pd.testing.assert_frame_equal(competing_risk_df, competing_risk_original)


def test_regplot_cycles_colors_when_hue_exceeds_palette() -> None:
    palette_size = len(plt.rcParams["axes.prop_cycle"].by_key()["color"])
    group_count = palette_size + 1
    values_per_group = 4
    data = pd.DataFrame(
        {
            "x": np.tile([0.0, 1.0, 2.0, 3.0], group_count),
            "y": np.tile([0.0, 1.2, 1.8, 3.2], group_count)
            + np.repeat(np.arange(group_count), values_per_group),
            "group": np.repeat(
                [f"group_{index}" for index in range(group_count)], values_per_group
            ),
        }
    )

    cns.figure(120, 120)
    ax = cns.regplot(data, x="x", y="y", hue="group")

    assert len(ax.texts) == group_count
    assert ax.texts[0].get_color() == ax.texts[palette_size].get_color()


def test_gseaplot_raises_when_backend_does_not_create_legend(
    monkeypatch: pytest.MonkeyPatch,
    gsea_plot_df: pd.DataFrame,
) -> None:
    fake_gseapy = types.SimpleNamespace(dotplot=lambda *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "gseapy", fake_gseapy)

    cns.figure(120, 120)
    with pytest.raises(RuntimeError, match="did not produce a legend"):
        cns.gseaplot(gsea_plot_df, y="Clean_Term")


def test_gseaplot_filters_significance_independently_from_color(
    monkeypatch: pytest.MonkeyPatch,
    gsea_plot_df: pd.DataFrame,
) -> None:
    captured_data: list[pd.DataFrame] = []
    captured_options: dict[str, object] = {}

    def fake_dotplot(
        data: pd.DataFrame,
        cmap: object,
        y: str,
        x: str,
        cutoff: float,
        column: str,
        ax: plt.Axes,
        top_term: int,
        size: float,
    ) -> None:
        captured_data.append(data.copy())
        captured_options.update(cmap=cmap, cutoff=cutoff, column=column)
        scatter = ax.scatter(data[x], np.arange(len(data)), c=data[column])
        plt.gcf().colorbar(scatter, ax=ax)
        handle = plt.Line2D([], [], marker="o", linestyle="none", color="black")
        ax.legend([handle], ["20"], title="size")

    monkeypatch.setitem(
        sys.modules, "gseapy", types.SimpleNamespace(dotplot=fake_dotplot)
    )
    data = gsea_plot_df.assign(score=[10.0, 20.0, 30.0])
    data.loc[data["Clean_Term"] == "Pathway B", "FDR q-val"] = 0.2

    cns.gseaplot(
        data,
        y="Clean_Term",
        color="score",
        cutoff=0.05,
        cmap="viridis",
        significance_column="FDR q-val",
    )

    assert captured_data[0]["Clean_Term"].tolist() == ["Pathway A", "Pathway C"]
    assert captured_data[0]["score"].tolist() == [10.0, 30.0]
    assert captured_options == {
        "cmap": "viridis",
        "cutoff": np.inf,
        "column": "score",
    }


def test_gseaplot_validates_significance_column(
    gsea_plot_df: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="FDR q-val"):
        cns.gseaplot(gsea_plot_df.drop(columns="FDR q-val"), y="Clean_Term")
