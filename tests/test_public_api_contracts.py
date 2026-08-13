from __future__ import annotations

import ast
import builtins
import inspect
import re
import subprocess
import sys
import types
from collections.abc import Mapping, Sequence
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast, get_type_hints

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.text import Text

import cnsplots as cns


_PUBLIC_PLOT_NAMES = frozenset(
    {
        "barplot",
        "boxplot",
        "confusionplot",
        "cumulativeincidenceplot",
        "distplot",
        "donutplot",
        "dotplot",
        "dumbbellplot",
        "forestplot",
        "gseaplot",
        "heatmapplot",
        "histplot",
        "kdeplot",
        "lineplot",
        "lollipopplot",
        "phyloplot",
        "pieplot",
        "placeholderplot",
        "qqplot",
        "regplot",
        "ridgeplot",
        "rocplot",
        "sankeyplot",
        "scatterplot",
        "slopeplot",
        "stackplot",
        "stripplot",
        "survivalplot",
        "upsetplot",
        "vennplot",
        "violinplot",
        "volcanoplot",
    }
)

_SEABORN_WRAPPER_PARAMETERS = {
    "histplot": (
        "data",
        "x",
        "y",
        "hue",
        "weights",
        "stat",
        "bins",
        "binwidth",
        "binrange",
        "discrete",
        "cumulative",
        "common_bins",
        "common_norm",
        "multiple",
        "element",
        "fill",
        "shrink",
        "kde",
        "kde_kws",
        "line_kws",
        "thresh",
        "pthresh",
        "pmax",
        "cbar",
        "cbar_ax",
        "cbar_kws",
        "palette",
        "hue_order",
        "hue_norm",
        "color",
        "log_scale",
        "legend",
        "ax",
        "kwargs",
    ),
    "lineplot": (
        "data",
        "x",
        "y",
        "hue",
        "size",
        "style",
        "units",
        "weights",
        "palette",
        "hue_order",
        "hue_norm",
        "sizes",
        "size_order",
        "size_norm",
        "dashes",
        "markers",
        "style_order",
        "estimator",
        "errorbar",
        "n_boot",
        "seed",
        "orient",
        "sort",
        "err_style",
        "err_kws",
        "legend",
        "ci",
        "ax",
        "kwargs",
    ),
}


def _pdf_media_box_size(path: Path) -> tuple[float, float]:
    match = re.search(
        rb"/MediaBox\s*\[\s*([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\s*\]",
        path.read_bytes(),
    )
    if match is None:
        raise AssertionError(f"MediaBox not found in {path}")
    x0, y0, x1, y1 = (float(value) for value in match.groups())
    return x1 - x0, y1 - y0


def _svg_view_box_size(path: Path) -> tuple[float, float]:
    match = re.search(
        r'viewBox="[-+]?\d*\.?\d+ [-+]?\d*\.?\d+ ([-+]?\d*\.?\d+) ([-+]?\d*\.?\d+)"',
        path.read_text(encoding="utf-8"),
    )
    if match is None:
        raise AssertionError(f"viewBox not found in {path}")
    width, height = (float(value) for value in match.groups())
    return width, height


def test_root_import_is_lazy_and_side_effect_free() -> None:
    script = """
import logging
import sys
import warnings

logger_levels = {
    "cnsplots": 11,
    "fontTools": 12,
    "matplotlib": 13,
}
for logger_name, level in logger_levels.items():
    logging.getLogger(logger_name).setLevel(level)
warning_filters = list(warnings.filters)
modules_before = set(sys.modules)

import cnsplots

assert list(warnings.filters) == warning_filters
assert all(
    logging.getLogger(name).level == level for name, level in logger_levels.items()
)
new_modules = set(sys.modules) - modules_before
assert not any(name.startswith("cnsplots.") for name in new_modules)
heavy_modules = {
    "Bio",
    "PyComplexHeatmap",
    "gseapy",
    "lifelines",
    "matplotlib",
    "numpy",
    "pandas",
    "scanpy",
    "scipy",
    "seaborn",
    "sklearn",
    "statsmodels",
}
assert not ({name.split(".")[0] for name in new_modules} & heavy_modules)

_ = cnsplots.settings
assert list(warnings.filters) == warning_filters
assert all(
    logging.getLogger(name).level == level for name, level in logger_levels.items()
)

_ = cnsplots.barplot
assert "cnsplots.plots._categorical" in sys.modules
assert not {
    "cnsplots.plots._genomics",
    "cnsplots.plots._heatmap",
    "cnsplots.plots._sets",
    "cnsplots.plots._survival",
} & set(sys.modules)
"""
    subprocess.run([sys.executable, "-c", script], check=True)

    src_path = Path(__file__).parents[1] / "src"
    no_site_script = (
        f"import sys; sys.path.insert(0, {str(src_path)!r}); "
        "import cnsplots; assert len(cnsplots.__all__) == 64"
    )
    subprocess.run([sys.executable, "-S", "-c", no_site_script], check=True)


def test_lazy_facade_introspection() -> None:
    import cnsplots.plots as plots

    assert set(cns.__all__) <= set(dir(cns))
    assert set(plots.__all__) <= set(dir(plots))
    assert plots.barplot is cns.barplot
    assert plots.__dict__["barplot"] is plots.barplot

    with pytest.raises(AttributeError, match="missing_public_name"):
        getattr(cns, "missing_public_name")
    with pytest.raises(AttributeError, match="missing_plot_name"):
        getattr(plots, "missing_plot_name")


def test_internal_modules_do_not_import_root_facade() -> None:
    source_root = Path(__file__).parents[1] / "src" / "cnsplots"
    offenders: list[str] = []
    for path in source_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name == "cnsplots" for alias in node.names
            ):
                offenders.append(f"{path.relative_to(source_root)}:{node.lineno}")
            if isinstance(node, ast.ImportFrom) and node.module == "cnsplots":
                offenders.append(f"{path.relative_to(source_root)}:{node.lineno}")

    assert offenders == []


def test_public_namespace_contract() -> None:
    assert cns.__version__ == version("cnsplots")
    assert all(not name.startswith("_") for name in cns.__all__)
    assert all(hasattr(cns, name) for name in cns.__all__)
    assert cns.methods.CoxModel is cns.CoxModel
    assert cns.methods.LogisticModel is cns.LogisticModel
    assert cns.methods.prerank is cns.prerank
    assert cns.validation.validate_dataframe is not None
    assert cns.utils.figure is cns.figure

    namespace: dict[str, object] = {}
    exec("from cnsplots import *", namespace)
    assert namespace["boxplot"] is cns.boxplot
    assert namespace["placeholderplot"] is cns.placeholderplot
    assert namespace["save"] is cns.save
    assert namespace["savefig"] is cns.savefig
    assert cns.save is cns.savefig
    assert namespace["validation"] is cns.validation


def test_public_callable_annotations_resolve() -> None:
    missing_annotations: dict[str, list[str]] = {}
    unresolved_annotations: dict[str, str] = {}

    for name in cns.__all__:
        value = getattr(cns, name)
        if not (inspect.isfunction(value) or inspect.isclass(value)):
            continue

        signature = inspect.signature(value)
        hint_target = value.__init__ if inspect.isclass(value) else value
        missing = [
            parameter.name
            for parameter in signature.parameters.values()
            if parameter.annotation is inspect.Parameter.empty
        ]
        if signature.return_annotation is inspect.Signature.empty:
            missing.append("return")
        if missing:
            missing_annotations[name] = missing

        try:
            get_type_hints(hint_target)
        except (NameError, TypeError) as exc:
            unresolved_annotations[name] = str(exc)

    assert missing_annotations == {}
    assert unresolved_annotations == {}


def test_public_plot_axes_signature_and_return_contract() -> None:
    import cnsplots.plots as plots
    from cnsplots.helpers._heatmap import (
        ClusterMapPlotterNew,
        DotClustermapPlotterNew,
    )
    from matplotlib_venn._common import VennDiagram

    assert set(plots.__all__) == _PUBLIC_PLOT_NAMES
    assert all(getattr(plots, name) is getattr(cns, name) for name in plots.__all__)

    return_types: dict[str, object] = {}
    for name in sorted(_PUBLIC_PLOT_NAMES):
        plotter = getattr(cns, name)
        ax_parameter = inspect.signature(plotter).parameters["ax"]
        assert ax_parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert ax_parameter.default is None

        hints = get_type_hints(plotter)
        assert hints["ax"] == Axes | None
        return_types[name] = hints["return"]

    specialized_returns = {
        "heatmapplot": ClusterMapPlotterNew,
        "dotplot": DotClustermapPlotterNew,
        "upsetplot": dict[str, Axes | None],
        "vennplot": VennDiagram,
    }
    assert {
        name: return_types.pop(name) for name in specialized_returns
    } == specialized_returns
    assert set(return_types.values()) == {Axes}


@pytest.mark.parametrize(
    ("plot_name", "seaborn_plotter"),
    [("histplot", sns.histplot), ("lineplot", sns.lineplot)],
)
def test_public_seaborn_wrapper_signature_contract(
    plot_name: str,
    seaborn_plotter: Any,
) -> None:
    wrapper_parameters = inspect.signature(getattr(cns, plot_name)).parameters
    seaborn_parameters = inspect.signature(seaborn_plotter).parameters

    assert tuple(wrapper_parameters) == _SEABORN_WRAPPER_PARAMETERS[plot_name]
    assert tuple(wrapper_parameters) == tuple(seaborn_parameters)
    assert {
        name: (parameter.kind, parameter.default)
        for name, parameter in wrapper_parameters.items()
    } == {
        name: (parameter.kind, parameter.default)
        for name, parameter in seaborn_parameters.items()
    }


def test_public_vennplot_backend_return_contract() -> None:
    _, ax = plt.subplots()
    venn = cns.vennplot([{1, 2}, {2, 3}], ["A", "B"], ax=ax)

    assert venn.get_label_by_id("11").get_text() == "1"
    assert venn.get_patch_by_id("11").axes is ax


def test_public_stackplot_signature_contract() -> None:
    parameters = inspect.signature(cns.stackplot).parameters
    assert parameters["x"].default is None
    assert parameters["y"].default is None
    assert parameters["stack"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["stack"].default is inspect.Parameter.empty
    assert "horizontal" not in parameters
    assert "add_count" in parameters
    assert "add_tip" not in parameters


@pytest.mark.parametrize(
    ("plot_name", "canonical_names", "removed_names"),
    [
        ("barplot", {"add_tip", "hue", "order", "hue_order"}, {"addtip"}),
        (
            "boxplot",
            {"add_count", "hue", "order", "hue_order"},
            {"addcount"},
        ),
        (
            "violinplot",
            {"add_box", "add_count", "hue", "order", "hue_order"},
            {"addcount"},
        ),
        (
            "lollipopplot",
            {"add_tip", "hue", "order", "hue_order"},
            {"addtip"},
        ),
        (
            "stackplot",
            {"add_count", "order", "stack_order"},
            {"addcount", "bar_order"},
        ),
        (
            "stripplot",
            {"add_count", "hue", "order", "hue_order"},
            {"addcount"},
        ),
        ("pieplot", {"order"}, {"hue_order"}),
        ("donutplot", {"order"}, {"hue_order"}),
        ("distplot", {"hue", "hue_order"}, set()),
        ("kdeplot", {"hue", "hue_order"}, set()),
        ("histplot", {"hue", "hue_order"}, set()),
        ("scatterplot", {"hue", "hue_order"}, set()),
        ("lineplot", {"hue", "hue_order"}, set()),
        ("regplot", {"add_equation", "hue", "hue_order", "method"}, set()),
        ("slopeplot", {"hue", "hue_order"}, set()),
        ("dumbbellplot", {"hue", "hue_order", "order"}, set()),
    ],
)
def test_public_plot_naming_contract(
    plot_name: str,
    canonical_names: set[str],
    removed_names: set[str],
) -> None:
    parameters = inspect.signature(getattr(cns, plot_name)).parameters

    assert canonical_names <= set(parameters)
    assert removed_names.isdisjoint(parameters)


def test_removed_plot_keywords_name_their_replacements(
    categorical_df: pd.DataFrame,
) -> None:
    calls = [
        (cns.barplot, "addtip", "add_tip"),
        (cns.boxplot, "addcount", "add_count"),
        (cns.violinplot, "addcount", "add_count"),
        (cns.stripplot, "addcount", "add_count"),
    ]

    for plotter, removed, replacement in calls:
        with pytest.raises(TypeError, match=replacement):
            cast(Any, plotter)(
                categorical_df,
                x="group",
                y="value",
                **{removed: True},
            )


def test_public_validation_contract(heatmap_adata: object) -> None:
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"], "c": [None, 1]})

    cns.validation.validate_dataframe(df, "data", "func")
    with pytest.raises(TypeError, match="must be a pandas DataFrame"):
        cns.validation.validate_dataframe([], "data", "func")

    cns.validation.validate_anndata(heatmap_adata, "adata", "func")
    with pytest.raises(TypeError, match="must be an AnnData object"):
        cns.validation.validate_anndata(df, "adata", "func")

    cns.validation.validate_column_exists(df, "a", "x", "func")
    with pytest.raises(ValueError, match="not found in data"):
        cns.validation.validate_column_exists(df, "missing", "x", "func")

    cns.validation.validate_columns_exist(df, ["a", "b"], "func")
    with pytest.raises(ValueError, match="Column\\(s\\)"):
        cns.validation.validate_columns_exist(df, ["a", "missing"], "func")

    cns.validation.validate_adata_layer(heatmap_adata, "scaled", "func")
    with pytest.raises(ValueError, match="Available layers"):
        cns.validation.validate_adata_layer(heatmap_adata, "missing", "func")

    cns.validation.validate_adata_obs_columns(heatmap_adata, ["cluster"], "func")
    with pytest.raises(ValueError, match="adata.obs"):
        cns.validation.validate_adata_obs_columns(heatmap_adata, ["missing"], "func")

    cns.validation.validate_adata_var_columns(heatmap_adata, ["pathway"], "func")
    with pytest.raises(ValueError, match="adata.var"):
        cns.validation.validate_adata_var_columns(heatmap_adata, ["missing"], "func")

    getattr(heatmap_adata, "uns")["tree"] = "(cell1);"
    cns.validation.validate_adata_uns_keys(heatmap_adata, "tree", "func")
    with pytest.raises(ValueError, match="adata.uns"):
        cns.validation.validate_adata_uns_keys(heatmap_adata, ["missing"], "func")

    cns.validation.validate_dataframe_not_empty(df, "func")
    with pytest.raises(ValueError, match="Data is empty"):
        cns.validation.validate_dataframe_not_empty(df.iloc[0:0], "func")

    cns.validation.validate_no_nulls(df, ["a"], "func")
    with pytest.raises(ValueError, match="Null values found"):
        cns.validation.validate_no_nulls(df, ["c"], "func")
    cns.validation.validate_no_nulls(df, ["c"], "func", allow_partial=True)
    with pytest.raises(ValueError, match="contain only null values"):
        cns.validation.validate_no_nulls(
            pd.DataFrame({"only_nulls": [None, None]}),
            ["only_nulls"],
            "func",
            allow_partial=True,
        )

    cns.validation.validate_column_type(df, "a", ["numeric"], "func")
    cns.validation.validate_column_type(df, "b", ["string"], "func")
    cns.validation.validate_column_type(
        pd.DataFrame({"text": pd.Series(["x", "y"], dtype="string")}),
        "text",
        ["string"],
        "func",
    )
    with pytest.raises(ValueError, match="must be numeric"):
        cns.validation.validate_column_type(df, "b", ["numeric"], "func")
    with pytest.raises(ValueError, match="must be categorical"):
        cns.validation.validate_column_type(df, "a", ["string"], "func")

    cns.validation.validate_sufficient_data(df, "a", 2, "func")
    with pytest.raises(ValueError, match="at least 3"):
        cns.validation.validate_sufficient_data(df, "a", 3, "func")

    cns.validation.validate_binary_column(pd.DataFrame({"b": [0, 1, 0]}), "b", "func")
    with pytest.raises(ValueError, match="exactly 2 unique values"):
        cns.validation.validate_binary_column(
            pd.DataFrame({"b": [0, 1, 2]}), "b", "func"
        )

    cns.validation.validate_categorical_has_levels(
        df, "b", min_levels=2, max_levels=2, function_name="func"
    )
    with pytest.raises(ValueError, match="at least 3"):
        cns.validation.validate_categorical_has_levels(
            df, "b", min_levels=3, function_name="func"
        )
    with pytest.raises(ValueError, match="at most 1"):
        cns.validation.validate_categorical_has_levels(
            df, "b", max_levels=1, function_name="func"
        )

    cns.validation.validate_numeric_range(
        df, "a", min_val=1, max_val=2, function_name="func"
    )
    with pytest.raises(ValueError, match="less than 2"):
        cns.validation.validate_numeric_range(df, "a", min_val=2, function_name="func")
    with pytest.raises(ValueError, match="greater than 1"):
        cns.validation.validate_numeric_range(df, "a", max_val=1, function_name="func")

    cns.validation.validate_pairs_format("all", df, "b", "func")
    cns.validation.validate_pairs_format([("x", "y")], df, "b", "func")
    with pytest.raises(ValueError, match="must be a list of tuples"):
        cns.validation.validate_pairs_format(("x", "y"), df, "b", "func")
    with pytest.raises(ValueError, match="2 elements"):
        cns.validation.validate_pairs_format([("x", "y", "z")], df, "b", "func")
    with pytest.raises(ValueError, match="Pair value 'missing'"):
        cns.validation.validate_pairs_format([("x", "missing")], df, "b", "func")

    cns.validation.validate_length_match([1], [2], "a", "b", "func")
    with pytest.raises(ValueError, match="matching lengths"):
        cns.validation.validate_length_match([1], [1, 2], "a", "b", "func")

    assert list(cns.validation.safe_column_access(df, "a", "func")) == [1, 2]
    assert cns.validation.safe_column_access(df, "missing", "func", default=3) == 3
    with pytest.raises(ValueError, match="Available columns"):
        cns.validation.safe_column_access(df, "missing", "func")

    assert cns.validation.safe_numeric_conversion(2, "func") == 2
    assert cns.validation.safe_numeric_conversion("2.5", "func", "ctx") == 2.5
    with pytest.raises(ValueError, match="Cannot convert NaN"):
        cns.validation.safe_numeric_conversion(np.nan, "func", "ctx")
    with pytest.raises(ValueError, match="Cannot convert value to numeric"):
        cns.validation.safe_numeric_conversion("bad", "func", "ctx")

    assert np.isnan(cns.validation.safe_division(1, 0))
    assert cns.validation.safe_division(4, 2) == 2


def test_public_validate_anndata_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> object:
        if name == "anndata":
            raise ImportError("missing")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="Install with: pip install anndata"):
        cns.validation.validate_anndata(object(), "adata", "func")


def test_public_cox_model_and_forestplot_contract(
    survival_df: pd.DataFrame,
) -> None:
    model = cns.CoxModel(
        survival_df,
        duration="time",
        event="event",
        variates=["age", "C(stage)"],
    )
    model.fit()
    assert model.results is not None
    assert set(model.results.columns) == {
        "display_label",
        "exp(coef)",
        "exp(coef) lower_err",
        "exp(coef) upper_err",
        "exp(coef) lower 95%",
        "exp(coef) upper 95%",
        "log10_pvalue",
        "analysis",
        "covariate",
        "hue_group",
        "p",
    }

    model_hue = cns.CoxModel(
        survival_df,
        duration="time",
        event="event",
        variates=["age"],
        hue="group",
    )
    model_hue.fit()
    cns.figure(120, 120)
    ax = cns.forestplot(model_hue)
    assert ax.get_xlabel() == "Hazard ratio (95% CI)"


def test_public_logistic_model_contract(roc_df: pd.DataFrame) -> None:
    data = pd.concat(
        [
            roc_df.rename(
                columns={"truth": "event", "model_a": "score", "model_b": "other"}
            )
        ]
        * 4,
        ignore_index=True,
    )
    data["group"] = ["A"] * 12 + ["B"] * 12

    model = cns.LogisticModel(data, event="event", variates=["score"])
    model.fit()
    assert model.results is not None
    assert list(model.results.columns) == [
        "predictor",
        "auc",
        "lower_ci",
        "upper_ci",
        "hue_group",
    ]

    data_bad = data.copy()
    data_bad.loc[data_bad["group"] == "A", "event"] = 1
    model_hue = cns.LogisticModel(
        data_bad, event="event", variates=["score", "missing_col"], hue="group"
    )
    with pytest.warns(RuntimeWarning) as caught:
        model_hue.fit()
    messages = [str(warning.message) for warning in caught]
    assert any("No variance in outcome" in message for message in messages)
    assert any("Error fitting missing_col" in message for message in messages)

    model_empty = cns.LogisticModel(
        data_bad[data_bad["group"] == "A"],
        event="event",
        variates=["score"],
        hue="group",
    )
    with pytest.warns(RuntimeWarning) as empty_caught:
        model_empty.fit()
    empty_messages = [str(warning.message) for warning in empty_caught]
    assert any("No variance in outcome" in message for message in empty_messages)
    assert any("No successful model fits" in message for message in empty_messages)

    cns.figure(120, 120)
    ax = cns.forestplot(model, add_pvalue=False)
    assert ax.get_xlabel() == "AUC (95% CI)"


def test_public_forestplot_validation_errors() -> None:
    with pytest.raises(ValueError, match="results"):
        cns.forestplot(types.SimpleNamespace(name="cox"))
    with pytest.raises(ValueError, match="name"):
        cns.forestplot(types.SimpleNamespace(results=pd.DataFrame({"a": [1]})))
    with pytest.raises(ValueError, match="Data is empty"):
        cns.forestplot(types.SimpleNamespace(name="cox", results=pd.DataFrame()))


def test_public_prerank_contract(
    fake_gseapy_result: types.SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = pd.DataFrame({"gene": ["a", "b", "c"], "rank": [3, 2, 1]})
    fake_gp = types.SimpleNamespace(prerank=lambda **kwargs: fake_gseapy_result)
    monkeypatch.setitem(sys.modules, "gseapy", fake_gp)
    res = cns.prerank(data, {"set": ["A", "B"]}, "gene", "rank", permutation_num=10)
    assert list(res["Clean_Term"]) == [
        "NF-κB Signaling",
        "DNA Repair",
        "Reactome IL-6 and TGF Signaling",
    ]


def test_public_prerank_and_gseaplot_use_real_gseapy_backend() -> None:
    genes = [f"G{index:02d}" for index in range(60)]
    ranked = pd.DataFrame(
        {
            "gene": [gene.lower() for gene in genes],
            "rank": np.linspace(5, -5, len(genes)),
        }
    )
    gene_sets = {
        "HALLMARK_TOP_PATHWAY": genes[:20],
        "GO_BOTTOM_PATHWAY": genes[-20:],
    }

    result = cns.prerank(
        ranked,
        gene_sets,
        name_gene="gene",
        name_rank="rank",
        permutation_num=10,
    )

    assert set(result["Clean_Term"]) == {"Top Pathway", "Bottom Pathway"}
    nes_by_term = result.set_index("Term")["NES"].astype(float)
    assert nes_by_term["HALLMARK_TOP_PATHWAY"] > 1.5
    assert nes_by_term["GO_BOTTOM_PATHWAY"] < -1.5
    assert (result["FDR q-val"].astype(float) < 0.25).all()

    cns.figure(140, 160)
    ax = cns.gseaplot(result, y="Clean_Term", top_term=2)
    offsets = np.asarray(ax.collections[0].get_offsets(), dtype=float)
    rendered_nes = {
        label.get_text(): offset[0]
        for label, offset in zip(ax.get_yticklabels(), offsets, strict=True)
    }
    expected_nes = result.set_index("Clean_Term")["NES"].astype(float).to_dict()
    assert rendered_nes == pytest.approx(expected_nes)


def test_gseaplot_direct_call_resolves_default_colormap_locally() -> None:
    src_path = Path(__file__).parents[1] / "src"
    script = f"""
import sys
sys.path.insert(0, {str(src_path)!r})

import matplotlib
matplotlib.use("Agg", force=True)
import pandas as pd

import cnsplots as cns

assert "BuRd_custom" not in matplotlib.colormaps
data = pd.DataFrame(
    {{
        "Term": ["Significant", "Not significant"],
        "NES": [2.0, -1.5],
        "FDR q-val": [0.01, 0.2],
    }}
)
ax = cns.gseaplot(data, y="Term")
assert [label.get_text() for label in ax.get_yticklabels()] == ["Significant"]
assert "BuRd_custom" not in matplotlib.colormaps
"""
    subprocess.run([sys.executable, "-c", script], check=True)


def test_public_prerank_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> object:
        if name == "gseapy":
            raise ImportError("missing")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="Install with: pip install gseapy"):
        cns.prerank(
            pd.DataFrame({"gene": ["a"], "rank": [1]}),
            {"set": ["A"]},
            "gene",
            "rank",
        )


def test_public_figure_uses_width_first_order() -> None:
    parameters = list(inspect.signature(cns.figure).parameters)
    assert parameters[:2] == ["width", "height"]

    cns.figure(96, 72)

    assert tuple(plt.gcf().get_size_inches()) == pytest.approx((96 / 72, 72 / 72))


def test_public_figure_and_save_alias_contract(output_dir: Path) -> None:
    png_path = output_dir / "nested" / "plot.png"
    pdf_path = output_dir / "nested" / "plot.pdf"
    svg_path = output_dir / "nested" / "plot.svg"

    cns.figure(96, 72)
    plt.plot([0, 1], [0, 1])
    plt.title("Contract Export")

    cns.save(str(png_path))
    cns.savefig(str(pdf_path))
    cns.save(str(svg_path))

    assert png_path.exists()
    assert pdf_path.exists()
    assert svg_path.exists()

    png_height, png_width = plt.imread(str(png_path)).shape[:2]
    pdf_width_pt, pdf_height_pt = _pdf_media_box_size(pdf_path)
    svg_width_pt, svg_height_pt = _svg_view_box_size(svg_path)
    scale = float(cns.settings.savefig_dpi) / 72

    assert png_width == pytest.approx(pdf_width_pt * scale, abs=1)
    assert png_height == pytest.approx(pdf_height_pt * scale, abs=1)
    assert png_width == pytest.approx(svg_width_pt * scale, abs=1)
    assert png_height == pytest.approx(svg_height_pt * scale, abs=1)
    assert "<svg" in svg_path.read_text(encoding="utf-8")


def test_public_settings_context_changes_plot_and_export_contract(
    categorical_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    default_png = output_dir / "default.png"
    default_pdf = output_dir / "default.pdf"
    default_svg = output_dir / "default.svg"
    custom_png = output_dir / "custom.png"
    custom_pdf = output_dir / "custom.pdf"
    custom_svg = output_dir / "custom.svg"

    cns.settings.reset()
    try:
        cns.figure(72, 72)
        plt.plot([0, 1], [0, 1])
        cns.savefig(str(default_png))
        cns.savefig(str(default_pdf))
        cns.savefig(str(default_svg))

        with cns.settings.context(
            savefig_dpi=72,
            title_fontweight="normal",
        ):
            cns.figure(72, 72)
            ax = cns.boxplot(categorical_df, x="group", y="value")
            ax.set_title("Styled Title")
            cns.savefig(str(custom_png))
            cns.savefig(str(custom_pdf))
            cns.savefig(str(custom_svg))
            assert ax.title.get_fontweight() == "normal"

        default_height, default_width = plt.imread(str(default_png)).shape[:2]
        custom_height, custom_width = plt.imread(str(custom_png)).shape[:2]
        default_pdf_width_pt, default_pdf_height_pt = _pdf_media_box_size(default_pdf)
        custom_pdf_width_pt, custom_pdf_height_pt = _pdf_media_box_size(custom_pdf)
        default_svg_width_pt, default_svg_height_pt = _svg_view_box_size(default_svg)
        custom_svg_width_pt, custom_svg_height_pt = _svg_view_box_size(custom_svg)
        default_scale = float(cns.settings.savefig_dpi) / 72
        custom_scale = 72 / 72
        assert default_width == pytest.approx(
            default_pdf_width_pt * default_scale, abs=1
        )
        assert default_height == pytest.approx(
            default_pdf_height_pt * default_scale,
            abs=1,
        )
        assert custom_width == pytest.approx(custom_pdf_width_pt * custom_scale, abs=1)
        assert custom_height == pytest.approx(
            custom_pdf_height_pt * custom_scale,
            abs=1,
        )
        assert default_width == pytest.approx(
            default_svg_width_pt * default_scale, abs=1
        )
        assert default_height == pytest.approx(
            default_svg_height_pt * default_scale,
            abs=1,
        )
        assert custom_width == pytest.approx(custom_svg_width_pt * custom_scale, abs=1)
        assert custom_height == pytest.approx(
            custom_svg_height_pt * custom_scale,
            abs=1,
        )
    finally:
        cns.settings.reset()


def test_public_multipanel_layout_contract(
    categorical_df: pd.DataFrame,
    numeric_df: pd.DataFrame,
) -> None:
    parameters = list(inspect.signature(cns.multipanel.panel).parameters)
    assert parameters[2:4] == ["width", "height"]

    mp = cns.multipanel(max_width=120, title="Overview", loc="left")

    mp.panel("A", 70, 60)
    ax1 = cns.boxplot(categorical_df, x="group", y="value")

    mp.panel("B", 70, 60)
    ax2 = cns.scatterplot(numeric_df, x="x", y="y")

    fig = plt.gcf()
    fig.canvas.draw()
    renderer = cast(FigureCanvasAgg, fig.canvas).get_renderer()

    assert ax2.get_position().y0 < ax1.get_position().y0

    ax1_bbox = ax1.get_window_extent(renderer=renderer)
    ax2_bbox = ax2.get_window_extent(renderer=renderer)
    display_scale = fig.dpi / 72
    assert (ax1_bbox.width, ax1_bbox.height) == pytest.approx(
        (70 * display_scale, 60 * display_scale)
    )
    assert (ax2_bbox.width, ax2_bbox.height) == pytest.approx(
        (70 * display_scale, 60 * display_scale)
    )
    title = next(text for text in fig.findobj(Text) if text.get_text() == "Overview")
    title_bbox = title.get_window_extent(renderer=renderer)

    label_a = next(
        text
        for text in fig.findobj(Text)
        if text.get_text() == "A"
        and text.get_window_extent(renderer=renderer).width > 1
        and text.get_window_extent(renderer=renderer).height > 1
        and text.get_window_extent(renderer=renderer).x1 < ax1_bbox.x0
    )
    label_b = next(
        text
        for text in fig.findobj(Text)
        if text.get_text() == "B"
        and text.get_window_extent(renderer=renderer).width > 1
        and text.get_window_extent(renderer=renderer).height > 1
        and text.get_window_extent(renderer=renderer).x1 < ax2_bbox.x0
    )
    label_a_bbox = label_a.get_window_extent(renderer=renderer)
    label_b_bbox = label_b.get_window_extent(renderer=renderer)

    assert title.get_horizontalalignment() == "left"
    assert title_bbox.y0 > ax1_bbox.y1
    assert label_a_bbox.x1 < ax1_bbox.x0
    assert label_a_bbox.y0 >= ax1_bbox.y1
    assert label_b_bbox.x1 < ax2_bbox.x0
    assert label_b_bbox.y0 >= ax2_bbox.y1
