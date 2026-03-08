from __future__ import annotations

import sys
import types

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import cnsplots as cns


def test_survival_plots(
    survival_df: pd.DataFrame,
    survival_three_group_df: pd.DataFrame,
    competing_risk_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cns.figure(120, 120)
    ax = cns.survivalplot(
        survival_df, "time", "event", "group", hue_order=["Treatment", "Control"]
    )
    assert ax.get_ylabel() == "Overall survival probability"
    assert "HR =" in ax.texts[0].get_text()
    assert "multivariate log-rank test" in capsys.readouterr().out

    cns.figure(120, 120)
    ax2 = cns.survivalplot(survival_three_group_df, "time", "event", "group")
    assert ax2.get_xlabel() == "Time (Years)"
    assert "trend" in capsys.readouterr().out

    added: dict[str, object] = {}
    import lifelines

    monkeypatch.setattr(
        lifelines.plotting,
        "add_at_risk_counts",
        lambda *fitters, **kwargs: added.update({"fitters": fitters, **kwargs}),
    )
    cns.figure(120, 120)
    ax3 = cns.cumulativeincidenceplot(
        competing_risk_df,
        "time",
        "event",
        "group",
        show_risk_table=True,
        xticks=[0, 2, 4, 6, 8],
    )
    assert list(ax3.get_xticks()) == [0, 2, 4, 6, 8]
    assert added["rows_to_show"] == ["At risk"]
    assert "Gray's test" in capsys.readouterr().out

    cns.figure(120, 120)
    single_group = competing_risk_df[competing_risk_df["group"] == "A"].copy()
    ax4 = cns.cumulativeincidenceplot(single_group, "time", "event", "group")
    assert ax4 is plt.gca()


def test_confusionplot_metrics_and_errors(confusion_df: pd.DataFrame) -> None:
    cns.figure(120, 120)
    ax = cns.confusionplot(
        confusion_df,
        x="pred",
        y="truth",
        add_pvalue=True,
        x_order=["neg", "pos"],
        y_order=["neg", "pos"],
        positive_x="pos",
        positive_y="pos",
    )
    assert ax.get_xlabel() == "pred"
    assert len(plt.gcf().axes) == 2

    cns.figure(120, 120)
    ax2 = cns.confusionplot(confusion_df, x="pred", y="truth", annot=False)
    assert ax2 is plt.gca()

    with pytest.raises(ValueError, match="2x2 confusion matrix"):
        cns.confusionplot(
            pd.DataFrame({"pred": ["a", "b", "c"], "truth": ["a", "b", "c"]}),
            x="pred",
            y="truth",
            add_pvalue=True,
        )

    with pytest.raises(ValueError, match="Could not find negative label in y_order"):
        cns.confusionplot(
            confusion_df,
            x="pred",
            y="truth",
            add_pvalue=True,
            x_order=["neg", "pos"],
            y_order=["pos"],
            positive_y="pos",
        )

    with pytest.raises(ValueError, match="2x2 confusion matrix"):
        cns.confusionplot(
            confusion_df,
            x="pred",
            y="truth",
            add_pvalue=True,
            x_order=["pos"],
            y_order=["neg", "pos"],
            positive_x="pos",
        )

    with pytest.raises(ValueError, match="Categorical categories cannot be null"):
        cns.confusionplot(
            pd.DataFrame({"pred": ["neg", "pos"], "truth": ["neg", np.nan]}),
            x="pred",
            y="truth",
        )


def test_heatmap_and_dotplot(
    heatmap_adata: object,
    dotplot_df: pd.DataFrame,
) -> None:
    cns.figure(180, 180)
    cmp = cns.heatmapplot(
        heatmap_adata,
        layer="scaled",
        row_annotation=["cluster", "score"],
        col_annotation=["pathway", "importance"],
        row_split="cluster",
        col_split="pathway",
        row_cluster=True,
        col_cluster=True,
        colors={"cluster": {"A": "#111111", "B": "#222222"}},
        cmap="parula",
    )
    assert cmp.ax_heatmap is not None

    cns.figure(180, 180)
    cmp2 = cns.heatmapplot(
        heatmap_adata,
        row_annotation=["cluster"],
        col_annotation=["pathway"],
        colors={"cluster": {"missing": "#111111"}},
        cmap="Set1",
    )
    assert cmp2.ax_heatmap is not None

    cns.figure(160, 160)
    dp = cns.dotplot(
        dotplot_df,
        x="sample",
        y="gene",
        color="mean_expr",
        size="pct_expr",
        value="score",
    )
    assert dp.ax_heatmap is not None

    cns.figure(160, 160)
    with pytest.raises(ValueError, match="Length mismatch"):
        cns.dotplot(
            dotplot_df[["sample", "gene", "mean_expr", "pct_expr"]],
            x="sample",
            y="gene",
            color="mean_expr",
            size="pct_expr",
        )


def test_genomics_plots(
    volcano_df: pd.DataFrame,
    gsea_plot_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_adjust = types.SimpleNamespace(adjust_text=lambda *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "adjustText", fake_adjust)

    cns.figure(120, 120)
    ax = cns.volcanoplot(volcano_df)
    assert ax.get_xlabel() == "log2(fold change)"

    cns.figure(120, 120)
    ax2 = cns.volcanoplot(volcano_df, show_list=["GENE1", "GENE6"])
    assert ax2.get_ylabel() == "–log10(adjusted p-value)"

    def fake_dotplot(
        data: pd.DataFrame,
        cmap: str,
        y: str,
        x: str,
        cutoff: float,
        column: str,
        ax: object,
        top_term: int,
        size: float,
    ) -> None:
        scatter = ax.scatter(data[x], np.arange(len(data)), c=data[column], s=20)
        fig = plt.gcf()
        cbar = fig.colorbar(scatter, ax=ax)
        cbar.set_label(column)
        handles = [plt.Line2D([], [], marker="o", linestyle="none", color="black")]
        ax.legend(handles, ["20"], title="size")

    monkeypatch.setitem(
        sys.modules, "gseapy", types.SimpleNamespace(dotplot=fake_dotplot)
    )
    cns.figure(160, 140)
    ax3 = cns.gseaplot(gsea_plot_df, y="Clean_Term", color="NES", top_term=2)
    assert ax3.get_xlabel() == "Normalized Enrichment Score (NES)"


def test_sets_validation_errors(sets_fixture: dict[str, set[int]]) -> None:
    with pytest.raises(TypeError, match="must be a dictionary"):
        cns.upsetplot([])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cannot be empty"):
        cns.upsetplot({})
    with pytest.raises(TypeError, match="must be a list"):
        cns.vennplot(tuple(sets_fixture.values()), labels=["A", "B"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must contain 2 or 3 sets"):
        cns.vennplot([set()], labels=["A"])
    with pytest.raises(ValueError, match="Length of 'labels'"):
        cns.vennplot([set(), set()], labels=["A"])
