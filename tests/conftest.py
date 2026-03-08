from __future__ import annotations

import types
from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def _seed_and_close_figures() -> None:
    np.random.seed(42)
    yield
    plt.close("all")


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "outputs"


@pytest.fixture
def categorical_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "group": ["A"] * 4 + ["B"] * 4 + ["C"] * 4,
            "value": [1.0, 1.3, 1.1, 1.4, 2.0, 2.2, 2.1, 2.3, 3.0, 3.1, 3.3, 3.2],
            "hue": ["H1", "H1", "H2", "H2"] * 3,
            "palette_group": ["P1"] * 4 + ["P2"] * 4 + ["P3"] * 4,
            "binary": ["No", "Yes"] * 6,
        }
    )


@pytest.fixture
def stack_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "treatment": [
                "A",
                "A",
                "A",
                "A",
                "B",
                "B",
                "B",
                "B",
                "C",
                "C",
                "C",
                "C",
            ],
            "response": [
                "Yes",
                "No",
                "Yes",
                "No",
                "Yes",
                "Yes",
                "No",
                "No",
                "No",
                "No",
                "Yes",
                "Yes",
            ],
        }
    )


@pytest.fixture
def numeric_df() -> pd.DataFrame:
    x = np.arange(1, 13, dtype=float)
    y = x * 1.5 + np.array(
        [0.1, -0.2, 0.3, -0.1, 0.2, 0.0, 0.1, -0.3, 0.2, -0.1, 0.4, 0.0]
    )
    return pd.DataFrame(
        {
            "x": x,
            "y": y,
            "group": ["G1"] * 6 + ["G2"] * 6,
            "color_group": ["C1", "C2", "C1", "C2", "C1", "C2"] * 2,
            "category": ["A", "A", "B", "B", "C", "C"] * 2,
        }
    )


@pytest.fixture
def line_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": [0, 1, 2, 0, 1, 2],
            "value": [1.0, 1.5, 2.0, 1.2, 1.4, 2.1],
            "condition": ["A", "A", "A", "B", "B", "B"],
        }
    )


@pytest.fixture
def survival_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": [5, 6, 7, 8, 10, 12, 4, 5, 6, 8, 9, 11],
            "event": [1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1],
            "group": ["Control"] * 6 + ["Treatment"] * 6,
            "stage": ["I", "I", "II", "II", "III", "III"] * 2,
            "age": [55, 59, 61, 64, 67, 69, 54, 58, 60, 63, 66, 70],
        }
    )


@pytest.fixture
def survival_three_group_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": [3, 4, 5, 6, 7, 8, 4, 5, 6, 7, 8, 9, 5, 6, 7, 8, 9, 10],
            "event": [1, 0, 1, 1, 0, 1] * 3,
            "group": ["Low"] * 6 + ["Mid"] * 6 + ["High"] * 6,
        }
    )


@pytest.fixture
def competing_risk_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": [1, 2, 3, 4, 5, 6, 2, 3, 4, 5, 6, 7],
            "event": [1, 0, 2, 1, 0, 2, 1, 2, 0, 1, 2, 0],
            "group": ["A"] * 6 + ["B"] * 6,
        }
    )


@pytest.fixture
def roc_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "truth": [0, 0, 0, 1, 1, 1],
            "model_a": [0.10, 0.20, 0.35, 0.60, 0.80, 0.95],
            "model_b": [0.05, 0.25, 0.30, 0.55, 0.75, 0.90],
        }
    )


@pytest.fixture
def confusion_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "pred": ["neg", "neg", "neg", "pos", "pos", "pos", "pos", "neg"],
            "truth": ["neg", "neg", "pos", "pos", "pos", "neg", "pos", "neg"],
        }
    )


@pytest.fixture
def volcano_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "log2FoldChange": [-2.0, -1.2, -0.2, 0.1, 1.4, 2.2],
            "-log10(adjp)": [4.0, 3.0, 0.5, 0.2, 3.5, 5.0],
            "symbol": ["GENE1", "GENE2", "GENE3", "GENE4", "GENE5", "GENE6"],
        }
    )


@pytest.fixture
def gsea_plot_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Term": ["PATHWAY_A", "PATHWAY_B", "PATHWAY_C"],
            "Clean_Term": ["Pathway A", "Pathway B", "Pathway C"],
            "NES": [2.1, -1.8, 1.6],
            "FDR q-val": [0.01, 0.02, 0.03],
        }
    )


@pytest.fixture
def dotplot_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sample": ["S1", "S2", "S1", "S2"],
            "gene": ["G1", "G1", "G2", "G2"],
            "mean_expr": [0.2, 0.5, 0.7, 0.1],
            "pct_expr": [10, 50, 80, 30],
            "score": [1.0, 2.0, 3.0, 4.0],
        }
    )


@pytest.fixture
def sankey_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source": ["Start", "Start", "Middle", "Middle", "End", "End"],
            "target": ["Middle", "End", "End", "Start", "Start", "Middle"],
        }
    )


@pytest.fixture
def sets_fixture() -> dict[str, set[int]]:
    return {"A": {1, 2, 3}, "B": {2, 3, 4}, "C": {3, 4, 5}}


@pytest.fixture
def heatmap_adata() -> ad.AnnData:
    adata = ad.AnnData(
        np.array(
            [
                [0.1, 0.4, 0.7, 1.0],
                [0.2, 0.5, 0.8, 1.1],
                [0.3, 0.6, 0.9, 1.2],
            ]
        )
    )
    adata.obs_names = ["cell1", "cell2", "cell3"]
    adata.var_names = ["gene1", "gene2", "gene3", "gene4"]
    adata.obs["cluster"] = pd.Categorical(["A", "A", "B"])
    adata.obs["score"] = [0.1, 0.5, 0.9]
    adata.var["pathway"] = pd.Categorical(["P1", "P1", "P2", "P2"])
    adata.var["importance"] = [1, 2, 3, 4]
    adata.layers["scaled"] = adata.X * 2
    return adata


@pytest.fixture
def phylo_adata() -> ad.AnnData:
    adata = ad.AnnData(np.array([[0, 1], [1, 0], [0, 1]], dtype=float))
    adata.obs_names = ["cell1", "cell2", "cell3"]
    adata.var_names = ["mut1", "mut2"]
    adata.obs["group"] = pd.Categorical(["A", "B", "A"])
    adata.layers["trisicell_output"] = np.array([[0, 1], [1, 0], [0, 1]], dtype=float)
    adata.uns["tree"] = "((cell1:1,cell2:1):1,cell3:1);"
    return adata


@pytest.fixture
def showcase_bundle(
    categorical_df: pd.DataFrame,
    survival_df: pd.DataFrame,
    heatmap_adata: ad.AnnData,
    volcano_df: pd.DataFrame,
    sets_fixture: dict[str, set[int]],
    roc_df: pd.DataFrame,
) -> tuple[pd.DataFrame, ...]:
    slope_df = pd.DataFrame(
        {
            "value": [1.0, 2.0, 1.2, 2.2, 0.8, 1.8],
            "site": ["site1", "site1", "site2", "site2", "site3", "site3"],
            "label": ["healthy", "disease"] * 3,
        }
    )
    return (
        categorical_df.rename(columns={"group": "species", "value": "sepal_length"})[
            ["species", "sepal_length"]
        ],
        categorical_df.rename(columns={"group": "day", "value": "total_bill"})[
            ["day", "total_bill", "hue"]
        ],
        survival_df[["time", "event", "group", "age", "stage"]],
        heatmap_adata,
        volcano_df,
        list(sets_fixture.values()),
        roc_df.rename(
            columns={"truth": "label", "model_a": "Model A", "model_b": "Model B"}
        ),
        slope_df,
    )


@pytest.fixture
def fake_gseapy_result() -> types.SimpleNamespace:
    res2d = pd.DataFrame(
        {
            "Term": [
                "HALLMARK_NFKB_SIGNALING",
                "GO_DNA_REPAIR",
                "Reactome_Il6_And_Tgf_Signaling",
            ],
            "NES": [2.2, -2.0, 1.7],
            "FDR q-val": [0.01, 0.02, 0.20],
        }
    )
    return types.SimpleNamespace(res2d=res2d)
