"""Data generation for the documentation showcase."""

from __future__ import annotations

from importlib.abc import Traversable
from importlib import resources
from typing import TYPE_CHECKING, Literal, TypeAlias, overload

if TYPE_CHECKING:
    import pandas as pd
    from anndata import AnnData

    _ShowcaseData: TypeAlias = tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        AnnData,
        pd.DataFrame,
        list[set[str]],
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        dict[str, set[str]],
    ]
    _ShowcaseDataWithImages: TypeAlias = tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        AnnData,
        pd.DataFrame,
        list[set[str]],
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        dict[str, set[str]],
        Traversable,
    ]
else:
    # Keep importing the datasets namespace lightweight while allowing
    # typing.get_type_hints() to resolve the public function at runtime.
    _ShowcaseData = tuple[object, ...]
    _ShowcaseDataWithImages = tuple[object, ...]


def _showcase_images() -> Traversable:
    """Return the packaged showcase image directory."""
    return resources.files("cnsplots.datasets").joinpath("_data").joinpath("showcase")


@overload
def get_showcase_data(
    *, include_showcase_images: Literal[False] = False
) -> _ShowcaseData: ...


@overload
def get_showcase_data(
    *, include_showcase_images: Literal[True]
) -> _ShowcaseDataWithImages: ...


@overload
def get_showcase_data(
    *, include_showcase_images: bool
) -> _ShowcaseData | _ShowcaseDataWithImages: ...


def get_showcase_data(
    *, include_showcase_images: bool = False
) -> _ShowcaseData | _ShowcaseDataWithImages:
    """Load deterministic showcase datasets and optional packaged images.

    Parameters
    ----------
    include_showcase_images : bool, default: False
        When True, append the traversable packaged image directory to the
        returned tuple.
    """
    import numpy as np
    import pandas as pd
    import scanpy as sc

    from cnsplots.datasets._loader import load_dataset

    rng = np.random.default_rng(42)
    survival_data = []
    for grp, scale in [("Treatment", 36), ("Control", 24)]:
        times = rng.exponential(scale=scale, size=50)
        events = rng.binomial(1, 0.7, 50)
        for time, event in zip(times, events):
            survival_data.append({"time": time, "event": event, "group": grp})
    survival_df = pd.DataFrame(survival_data)
    survival_df["age"] = rng.normal(60, 10, len(survival_df)).astype(int)
    survival_df["stage"] = rng.choice(["I", "II", "III"], len(survival_df))

    iris_df = load_dataset("iris")
    tips_df = load_dataset("tips")
    blobs = sc.datasets.blobs()
    blobs.obs["TP53"] = rng.random(blobs.shape[0])
    blobs.obs["KRAS"] = rng.random(blobs.shape[0])
    blobs.var["Ensemble"] = [f"ens{x}" for x in rng.integers(0, 3, blobs.shape[1])]
    selected = pd.Series(pd.NA, index=blobs.obs_names, dtype="string")
    tp53_values = np.asarray(blobs.obs["TP53"], dtype=float)
    selected[tp53_values > 0.95] = "o"
    blobs.obs["Selected"] = selected
    blobs.obs["Cluster"] = pd.Categorical(
        [f"C{x}" for x in rng.integers(0, 4, blobs.shape[0])]
    )
    blobs_matrix = np.asarray(blobs.X)
    blobs.X = blobs_matrix - blobs_matrix.mean()

    n_genes = 500
    logfc = rng.normal(0, 1.5, n_genes)
    pvals = 10 ** (-np.abs(logfc) * rng.uniform(0.5, 3, n_genes))
    pvals = np.clip(pvals, 1e-50, 1)
    volcano_df = pd.DataFrame(
        {
            "log2FoldChange": logfc,
            "-log10(adjp)": -np.log10(pvals),
            "symbol": [f"Gene{i}" for i in range(n_genes)],
        }
    )

    gene_sets = [
        {f"Gene{i}" for i in rng.choice(200, 80, replace=False)},
        {f"Gene{i}" for i in rng.choice(200, 90, replace=False)},
        {f"Gene{i}" for i in rng.choice(200, 70, replace=False)},
    ]

    slope_rows = []
    for mean, site, label in [
        (1, "site1", "healthy"),
        (3, "site2", "healthy"),
        (0, "site3", "healthy"),
        (1, "site1", "disease"),
        (1, "site2", "disease"),
        (3, "site3", "disease"),
    ]:
        for subject, value in enumerate(rng.normal(loc=mean, size=15)):
            slope_rows.append(
                {
                    "value": float(value),
                    "site": site,
                    "label": label,
                    "pair": f"{site}_{subject}",
                }
            )
    slope_df = pd.DataFrame(
        slope_rows,
        columns=pd.Index(["value", "site", "label", "pair"]),
    )

    y_true = rng.binomial(1, 0.4, 200)
    roc_df = pd.DataFrame(
        {
            "label": y_true,
            "Model A": y_true * 0.5 + (1 - y_true) * 0.3 + rng.normal(0, 0.25, 200),
            "Model B": y_true * 0.6 + (1 - y_true) * 0.2 + rng.normal(0, 0.2, 200),
        }
    )

    confusion_df = pd.DataFrame(
        {
            "truth": ["Neg"] * 18 + ["Pos"] * 12,
            "pred": ["Neg"] * 15 + ["Pos"] * 3 + ["Neg"] * 2 + ["Pos"] * 10,
        }
    )

    line_df = pd.DataFrame(
        {
            "timepoint": list(range(6)) * 2,
            "signal": [
                0.15,
                0.22,
                0.38,
                0.55,
                0.64,
                0.72,
                0.12,
                0.18,
                0.29,
                0.36,
                0.43,
                0.50,
            ],
            "condition": ["Control"] * 6 + ["Treatment"] * 6,
        }
    )

    cumulative_incidence_rows = []
    for group, scale, event_probs in [
        ("Control", 18, [0.22, 0.56, 0.22]),
        ("Treatment", 26, [0.30, 0.40, 0.30]),
    ]:
        times = rng.exponential(scale=scale, size=60)
        events = rng.choice([0, 1, 2], size=60, p=event_probs)
        for time, event in zip(times, events):
            cumulative_incidence_rows.append(
                {"time": float(time), "event": int(event), "group": group}
            )
    cumulative_incidence_df = pd.DataFrame(cumulative_incidence_rows)

    n_patients = 240
    risk = rng.choice(["Low", "High"], size=n_patients, p=[0.58, 0.42])
    stage = rng.choice(["I", "II"], size=n_patients, p=[0.55, 0.45])
    age = rng.normal(61, 9, size=n_patients)
    marker = rng.lognormal(mean=1.2, sigma=0.35, size=n_patients)
    hazard_scale = np.where(risk == "High", 1.35, 0.85) * np.where(
        stage == "II", 1.2, 0.95
    )
    forest_df = pd.DataFrame(
        {
            "time": rng.exponential(scale=30 / hazard_scale, size=n_patients),
            "event": rng.binomial(
                1,
                np.where(risk == "High", 0.72, 0.48)
                + np.where(stage == "II", 0.06, -0.02),
                size=n_patients,
            ),
            "risk": risk,
            "stage": stage,
            "age": age,
            "marker": marker,
        }
    )

    genes = np.array([f"Gene{x}" for x in range(1, 61)])
    upset_sets = {
        "RNA": set(genes[:18]) | set(genes[24:30]) | set(genes[40:44]),
        "ATAC": set(genes[8:28]) | set(genes[34:40]),
        "WES": set(genes[4:16]) | set(genes[22:34]) | set(genes[48:54]),
        "CRISPR": set(genes[:6])
        | set(genes[14:24])
        | set(genes[30:33])
        | set(genes[44:52]),
    }

    data = (
        iris_df,
        tips_df,
        survival_df,
        blobs.T,
        volcano_df,
        gene_sets,
        roc_df,
        slope_df,
        confusion_df,
        line_df,
        cumulative_incidence_df,
        forest_df,
        upset_sets,
    )
    if include_showcase_images:
        return (*data, _showcase_images())
    return data
