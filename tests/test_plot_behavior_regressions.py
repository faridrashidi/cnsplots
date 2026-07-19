from __future__ import annotations

import sys
import types

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import cnsplots as cns


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
