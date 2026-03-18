from __future__ import annotations

import builtins
import subprocess
import sys
import types
from collections.abc import Iterable, Mapping, Sequence
from importlib.metadata import version
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from lxml import etree

import cnsplots as cns
from cnsplots import _settings, _setup, _svg, _utils, _validation


def test_public_api_exports_resolve() -> None:
    assert cns.__version__ == version("cnsplots")
    assert cns.boxplot is not None
    assert cns.placeholderplot is not None
    assert cns.scatterplot is not None
    assert cns.methods.CoxModel is cns.CoxModel
    assert cns.methods.LogisticModel is cns.LogisticModel
    assert cns.validation.validate_dataframe is _validation.validate_dataframe
    assert cns.utils.figure is _utils.figure

    namespace: dict[str, object] = {}
    exec("from cnsplots import *", namespace)
    assert namespace["boxplot"] is cns.boxplot
    assert namespace["placeholderplot"] is cns.placeholderplot
    assert namespace["savefig"] is cns.savefig


def test_validation_helpers(heatmap_adata: object) -> None:
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"], "c": [None, 1]})

    _validation.validate_dataframe(df, "data", "func")
    with pytest.raises(TypeError, match="must be a pandas DataFrame"):
        _validation.validate_dataframe([], "data", "func")

    _validation.validate_anndata(heatmap_adata, "adata", "func")
    with pytest.raises(TypeError, match="must be an AnnData object"):
        _validation.validate_anndata(df, "adata", "func")

    _validation.validate_column_exists(df, "a", "x", "func")
    with pytest.raises(ValueError, match="not found in data"):
        _validation.validate_column_exists(df, "missing", "x", "func")

    _validation.validate_columns_exist(df, ["a", "b"], "func")
    with pytest.raises(ValueError, match="Column\\(s\\)"):
        _validation.validate_columns_exist(df, ["a", "missing"], "func")

    _validation.validate_adata_layer(heatmap_adata, "scaled", "func")
    with pytest.raises(ValueError, match="Available layers"):
        _validation.validate_adata_layer(heatmap_adata, "missing", "func")

    _validation.validate_adata_obs_columns(heatmap_adata, ["cluster"], "func")
    with pytest.raises(ValueError, match="adata.obs"):
        _validation.validate_adata_obs_columns(heatmap_adata, ["missing"], "func")

    _validation.validate_adata_var_columns(heatmap_adata, ["pathway"], "func")
    with pytest.raises(ValueError, match="adata.var"):
        _validation.validate_adata_var_columns(heatmap_adata, ["missing"], "func")

    _validation.validate_dataframe_not_empty(df, "func")
    with pytest.raises(ValueError, match="Data is empty"):
        _validation.validate_dataframe_not_empty(df.iloc[0:0], "func")

    _validation.validate_no_nulls(df, ["a"], "func")
    with pytest.raises(ValueError, match="Null values found"):
        _validation.validate_no_nulls(df, ["c"], "func")
    _validation.validate_no_nulls(df, ["c"], "func", allow_partial=True)
    with pytest.raises(ValueError, match="contain only null values"):
        _validation.validate_no_nulls(
            pd.DataFrame({"only_nulls": [None, None]}),
            ["only_nulls"],
            "func",
            allow_partial=True,
        )

    _validation.validate_column_type(df, "a", ["numeric"], "func")
    _validation.validate_column_type(df, "b", ["string"], "func")
    with pytest.raises(ValueError, match="must be numeric"):
        _validation.validate_column_type(df, "b", ["numeric"], "func")
    with pytest.raises(ValueError, match="must be categorical"):
        _validation.validate_column_type(df, "a", ["string"], "func")

    _validation.validate_sufficient_data(df, "a", 2, "func")
    with pytest.raises(ValueError, match="at least 3"):
        _validation.validate_sufficient_data(df, "a", 3, "func")

    _validation.validate_binary_column(pd.DataFrame({"b": [0, 1, 0]}), "b", "func")
    with pytest.raises(ValueError, match="exactly 2 unique values"):
        _validation.validate_binary_column(pd.DataFrame({"b": [0, 1, 2]}), "b", "func")

    _validation.validate_categorical_has_levels(
        df, "b", min_levels=2, max_levels=2, function_name="func"
    )
    with pytest.raises(ValueError, match="at least 3"):
        _validation.validate_categorical_has_levels(
            df, "b", min_levels=3, function_name="func"
        )
    with pytest.raises(ValueError, match="at most 1"):
        _validation.validate_categorical_has_levels(
            df, "b", max_levels=1, function_name="func"
        )

    _validation.validate_numeric_range(
        df, "a", min_val=1, max_val=2, function_name="func"
    )
    with pytest.raises(ValueError, match="less than 2"):
        _validation.validate_numeric_range(df, "a", min_val=2, function_name="func")
    with pytest.raises(ValueError, match="greater than 1"):
        _validation.validate_numeric_range(df, "a", max_val=1, function_name="func")

    _validation.validate_pairs_format("all", df, "b", "func")
    _validation.validate_pairs_format([("x", "y")], df, "b", "func")
    with pytest.raises(ValueError, match="must be a list of tuples"):
        _validation.validate_pairs_format(("x", "y"), df, "b", "func")
    with pytest.raises(ValueError, match="2 elements"):
        _validation.validate_pairs_format([("x", "y", "z")], df, "b", "func")
    with pytest.raises(ValueError, match="Pair value 'missing'"):
        _validation.validate_pairs_format([("x", "missing")], df, "b", "func")

    _validation.validate_length_match([1], [2], "a", "b", "func")
    with pytest.raises(ValueError, match="matching lengths"):
        _validation.validate_length_match([1], [1, 2], "a", "b", "func")

    assert list(_validation.safe_column_access(df, "a", "func")) == [1, 2]
    assert _validation.safe_column_access(df, "missing", "func", default=3) == 3
    with pytest.raises(ValueError, match="Available columns"):
        _validation.safe_column_access(df, "missing", "func")

    assert _validation.safe_numeric_conversion(2, "func") == 2
    assert _validation.safe_numeric_conversion("2.5", "func", "ctx") == 2.5
    with pytest.raises(ValueError, match="Cannot convert NaN"):
        _validation.safe_numeric_conversion(np.nan, "func", "ctx")
    with pytest.raises(ValueError, match="Cannot convert value to numeric"):
        _validation.safe_numeric_conversion("bad", "func", "ctx")

    assert np.isnan(_validation.safe_division(1, 0))
    assert _validation.safe_division(4, 2) == 2


def test_validate_anndata_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
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
        _validation.validate_anndata(object(), "adata", "func")


def test_settings_behavior() -> None:
    settings = _settings.CNSSettings()
    assert settings.palette_qual == "Ecotyper1"
    settings.palette_qual = "Set2"
    settings.palette_seq = "parula"
    settings.title_fontsize = 10
    settings.title_fontweight = "normal"
    settings.fontsize_legend = 9
    settings.axes_linewidth = 1.0
    settings.verbosity = 0
    settings.mathtext_fontset = "stix"
    settings.font_family = "serif"
    settings.font_sans_serif = ["Arial", "DejaVu Sans"]
    settings.savefig_bbox = "standard"
    settings.savefig_pad_inches = 0.1
    settings.savefig_dpi = 300
    settings.savefig_transparent = False
    settings.svg_fonttype = "path"
    settings.pdf_fonttype = 3
    settings.axes_titlelocation = "left"
    settings.axes_grid = True
    settings.axes_spines_top = True
    settings.axes_spines_right = True
    settings.axes_edgecolor = "red"
    settings.axes_labelcolor = "blue"
    settings.axes_labelpad = 5
    settings.axes_titlepad = 6
    settings.axes_xmargin = 0.1
    settings.axes_ymargin = 0.2
    settings.legend_fontsize = 11
    settings.legend_title_fontsize = 12
    settings.legend_frameon = True
    settings.legend_markerscale = 1.2
    settings.legend_handlelength = 1.3
    settings.legend_handleheight = 1.4
    settings.legend_handletextpad = 0.4
    settings.xtick_bottom = False
    settings.xtick_color = "purple"
    settings.xtick_major_size = 3
    settings.xtick_major_width = 0.9
    settings.xtick_major_pad = 2
    settings.xtick_alignment = "right"
    settings.xtick_labelrotation = 15
    settings.ytick_left = False
    settings.ytick_color = "green"
    settings.ytick_major_size = 4
    settings.ytick_major_width = 1.1
    settings.ytick_major_pad = 3
    settings.ytick_alignment = "top"
    settings.ytick_labelrotation = 20
    settings.setup_ax_colorbar_label = "Configured"
    settings.scanpy_use_default_style = True
    settings.scanpy_figsize = (3.0, 4.0)
    settings.scanpy_facecolor = "ivory"
    settings.ggplot_fontsize = 11
    settings.ggplot_font_family = "mono"
    settings.ggplot_font_face = "bold"
    settings.ggplot_text_color = "gray20"
    settings.figure_width = 180
    settings.figure_height = 120
    settings.figure_dpi = 200
    settings.multipanel_max_width = 600
    settings.multipanel_title_loc = "right"
    settings.multipanel_title_height_min = 14
    settings.multipanel_title_height_pad = 5
    settings.panel_width = 160
    settings.panel_height = 140
    settings.panel_label_left = 11
    settings.panel_label_top = 13
    settings.panel_pad_left = 21
    settings.panel_pad_top = 2
    settings.panel_margin = (1, 2, 3, 4)
    settings.panel_label_fontname = "DejaVu Sans"
    settings.panel_label_fontweight = 500
    settings.panel_label_offset_x = -0.3
    settings.panel_label_offset_y = 1.2
    settings.legend_out_bbox_to_anchor = (1.1, 1.2)
    settings.legend_out_loc = "lower left"
    settings.legend_out_markerscale = 2
    assert "CNSSettings(" in repr(settings)
    assert "title_fontweight='normal'" in repr(settings)
    assert "figure_width=180" in repr(settings)
    assert "font_sans_serif=('Arial', 'DejaVu Sans')" in repr(settings)

    with settings.context(
        title_fontsize=12,
        title_fontweight=600,
        palette_qual="Dark2",
        legend_fontsize=None,
        scanpy_figsize=(5.0, 4.0),
        panel_margin=(5, 6, 7, 8),
    ) as ctx:
        assert ctx.title_fontsize == 12
        assert ctx.title_fontweight == 600
        assert settings.palette_qual == "Dark2"
        assert ctx.legend_fontsize is None
        assert ctx.scanpy_figsize == (5.0, 4.0)
        assert ctx.panel_margin == (5, 6, 7, 8)
    assert settings.title_fontsize == 10
    assert settings.title_fontweight == "normal"
    assert settings.palette_qual == "Set2"
    assert settings.legend_fontsize == 11
    assert settings.scanpy_figsize == (3.0, 4.0)
    assert settings.panel_margin == (1, 2, 3, 4)

    with pytest.raises(AttributeError, match="not a valid setting"):
        with settings.context(unknown=1):
            pass
    with pytest.raises(AttributeError, match="not a valid setting"):
        with settings.context(fontsize_title=12):
            pass
    with pytest.raises(AttributeError, match="not a valid setting"):
        with settings.context(fontweight_title="normal"):
            pass
    with pytest.raises(AttributeError, match="not a valid setting"):
        with settings.context(linewidth_axes=1.0):
            pass
    with pytest.raises(AttributeError, match="not a valid setting"):
        _ = settings.fontsize_title
    with pytest.raises(AttributeError, match="not a valid setting"):
        _ = settings.fontweight_title
    with pytest.raises(AttributeError, match="not a valid setting"):
        _ = settings.linewidth_axes
    with pytest.raises(AttributeError, match="not a valid setting"):
        setattr(settings, "fontsize_title", 10)
    with pytest.raises(AttributeError, match="not a valid setting"):
        setattr(settings, "fontweight_title", "normal")
    with pytest.raises(AttributeError, match="not a valid setting"):
        setattr(settings, "linewidth_axes", 1.0)
    with pytest.raises(AttributeError, match="has no attribute '_missing_setting'"):
        _ = settings._missing_setting

    with pytest.raises(TypeError):
        settings.palette_qual = 1  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.palette_seq = 1  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.title_fontsize = "1"  # type: ignore[assignment]
    with pytest.raises(ValueError):
        settings.title_fontsize = 0
    with pytest.raises(TypeError):
        settings.title_fontweight = []  # type: ignore[assignment]
    with pytest.raises(TypeError, match="title_fontweight must be a string or integer"):
        settings.title_fontweight = 1.5  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.fontsize_legend = "1"  # type: ignore[assignment]
    with pytest.raises(ValueError):
        settings.fontsize_legend = 0
    with pytest.raises(TypeError):
        settings.axes_linewidth = "1"  # type: ignore[assignment]
    with pytest.raises(ValueError):
        settings.axes_linewidth = 0
    with pytest.raises(TypeError):
        settings.verbosity = 1.5  # type: ignore[assignment]
    with pytest.raises(ValueError):
        settings.verbosity = -1

    settings.reset()
    assert settings.palette_qual == "Ecotyper1"
    assert settings.title_fontweight == "bold"
    assert settings.legend_fontsize is None
    assert settings.scanpy_figsize == (2.5, 2.5)
    assert settings.panel_margin == (10, 0, 0, 20)
    assert settings.font_sans_serif[0] == "Helvetica"


def test_settings_validation_errors() -> None:
    settings = _settings.CNSSettings()

    with pytest.raises(TypeError):
        settings.palette_qual = 1  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.palette_seq = 1  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.title_fontsize = "1"  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.figure_width = None  # type: ignore[assignment]
    with pytest.raises(ValueError):
        settings.title_fontsize = 0
    with pytest.raises(TypeError):
        settings.title_fontweight = []  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.panel_label_fontweight = None  # type: ignore[assignment]
    with pytest.raises(TypeError, match="title_fontweight must be a string or integer"):
        settings.title_fontweight = 1.5  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.fontsize_legend = "1"  # type: ignore[assignment]
    with pytest.raises(ValueError):
        settings.fontsize_legend = 0
    with pytest.raises(TypeError):
        settings.axes_linewidth = "1"  # type: ignore[assignment]
    with pytest.raises(ValueError):
        settings.axes_linewidth = 0
    with pytest.raises(TypeError):
        settings.verbosity = 1.5  # type: ignore[assignment]
    with pytest.raises(ValueError):
        settings.verbosity = -1
    with pytest.raises(TypeError):
        settings.axes_grid = "yes"  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.axes_titlelocation = 1  # type: ignore[assignment]
    with pytest.raises(ValueError, match="axes_titlelocation must be one of"):
        settings.axes_titlelocation = "top"
    with pytest.raises(TypeError):
        settings.font_sans_serif = "Arial"  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.font_sans_serif = ["Arial", 1]  # type: ignore[list-item]
    with pytest.raises(ValueError):
        settings.font_sans_serif = []  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.scanpy_figsize = "big"  # type: ignore[assignment]
    with pytest.raises(ValueError):
        settings.scanpy_figsize = (1.0,)  # type: ignore[assignment]
    with pytest.raises(TypeError):
        settings.legend_fontsize = "big"  # type: ignore[assignment]
    with pytest.raises(ValueError):
        settings.legend_markerscale = -1
    with pytest.raises(TypeError):
        settings.pdf_fonttype = 1.5  # type: ignore[assignment]
    with pytest.raises(ValueError):
        settings.pdf_fonttype = 0
    with pytest.raises(TypeError):
        settings.legend_out_loc = 1  # type: ignore[assignment]
    with pytest.raises(ValueError, match="legend_out_loc must be one of"):
        settings.legend_out_loc = "corner"


def test_ensure_helvetica_bold_branches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(_setup, "_HELVETICA_BOLD_REGISTERED", True)
    _setup._ensure_helvetica_bold()

    monkeypatch.setattr(_setup, "_HELVETICA_BOLD_REGISTERED", False)
    fake_font = types.SimpleNamespace(name="Helvetica", weight=700)
    monkeypatch.setattr(
        _setup.fm,
        "fontManager",
        types.SimpleNamespace(ttflist=[fake_font], addfont=lambda _p: None),
    )
    _setup._ensure_helvetica_bold()
    assert _setup._HELVETICA_BOLD_REGISTERED is True

    monkeypatch.setattr(_setup, "_HELVETICA_BOLD_REGISTERED", False)
    monkeypatch.setattr(
        _setup.fm,
        "fontManager",
        types.SimpleNamespace(ttflist=[], addfont=lambda _p: None),
    )
    monkeypatch.setattr(_setup.sys, "platform", "linux")
    _setup._ensure_helvetica_bold()
    assert _setup._HELVETICA_BOLD_REGISTERED is False

    monkeypatch.setattr(_setup.sys, "platform", "darwin")
    monkeypatch.setattr(_setup.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(_setup.Path, "exists", lambda self: False)
    _setup._ensure_helvetica_bold()


def test_setup_functions(monkeypatch: pytest.MonkeyPatch) -> None:
    cns.settings.reset()
    with cns.settings.context(
        legend_fontsize=11,
        legend_title_fontsize=12,
        axes_titlelocation="left",
        axes_grid=True,
        axes_spines_top=True,
        axes_spines_right=True,
        axes_edgecolor="green",
        axes_labelcolor="purple",
        axes_labelpad=5,
        axes_titlepad=6,
        axes_xmargin=0.2,
        axes_ymargin=0.3,
        xtick_bottom=False,
        xtick_color="red",
        xtick_major_size=3,
        xtick_major_width=1.2,
        xtick_major_pad=2,
        xtick_alignment="right",
        xtick_labelrotation=15,
        ytick_left=False,
        ytick_color="blue",
        ytick_major_size=4,
        ytick_major_width=1.4,
        ytick_major_pad=3,
        ytick_alignment="top",
        ytick_labelrotation=20,
        setup_ax_colorbar_label="Configured",
        scanpy_use_default_style=True,
        scanpy_figsize=(3.0, 4.0),
        scanpy_facecolor="ivory",
        ggplot_fontsize=11,
        ggplot_font_family="mono",
        ggplot_font_face="bold",
        ggplot_text_color="gray20",
    ):
        _setup.setup_matplotlib()
        assert mpl.rcParams["legend.fontsize"] == 11
        assert mpl.rcParams["legend.title_fontsize"] == 12
        assert mpl.rcParams["axes.titlelocation"] == "left"
        assert mpl.rcParams["axes.grid"] is True
        assert mpl.rcParams["axes.spines.top"] is True
        assert mpl.rcParams["axes.spines.right"] is True
        assert mpl.rcParams["axes.edgecolor"] == "green"
        assert mpl.rcParams["axes.labelcolor"] == "purple"
        assert mpl.rcParams["xtick.bottom"] is False
        assert mpl.rcParams["xtick.color"] == "red"
        assert mpl.rcParams["ytick.left"] is False
        assert mpl.rcParams["ytick.color"] == "blue"

    _setup.setup_matplotlib(
        color_cycle="Set2",
        color_map="parula",
        title_fontsize=9,
        title_fontweight="normal",
        fontsize_legend=8,
        axes_linewidth=1.2,
    )
    assert mpl.rcParams["axes.labelsize"] == 9
    assert mpl.rcParams["axes.titleweight"] == "normal"
    assert mpl.rcParams["image.cmap"] == "parula"
    with cns.settings.context(
        title_fontsize=13,
        legend_fontsize=None,
        legend_title_fontsize=None,
    ):
        _setup.setup_matplotlib(title_fontsize=14)
        assert mpl.rcParams["legend.fontsize"] == 14
        assert mpl.rcParams["legend.title_fontsize"] == 14
    with pytest.raises(TypeError, match="title_fontweight must be a string or integer"):
        _setup.setup_matplotlib(title_fontweight=1.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="unexpected keyword argument 'fontsize_title'"):
        _setup.setup_matplotlib(fontsize_title=9)  # type: ignore[call-arg]
    with pytest.raises(
        TypeError, match="unexpected keyword argument 'fontweight_title'"
    ):
        _setup.setup_matplotlib(fontweight_title="normal")  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="unexpected keyword argument 'linewidth_axes'"):
        _setup.setup_matplotlib(linewidth_axes=1.2)  # type: ignore[call-arg]

    fig, ax = plt.subplots()
    heat = ax.pcolormesh(np.array([[1, 2], [3, 4]]))
    fig.colorbar(heat, ax=ax)
    ax.set_title("Title")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    with cns.settings.context(
        axes_titlelocation="left",
        axes_grid=True,
        axes_spines_top=True,
        axes_spines_right=True,
        axes_edgecolor="green",
        axes_labelcolor="purple",
        axes_labelpad=5,
        axes_titlepad=6,
        axes_xmargin=0.2,
        axes_ymargin=0.3,
        xtick_bottom=False,
        xtick_color="red",
        xtick_major_size=3,
        xtick_major_width=1.2,
        xtick_major_pad=2,
        xtick_alignment="right",
        xtick_labelrotation=15,
        ytick_left=False,
        ytick_color="blue",
        ytick_major_size=4,
        ytick_major_width=1.4,
        ytick_major_pad=3,
        ytick_alignment="top",
        ytick_labelrotation=20,
        setup_ax_colorbar_label="Configured",
    ):
        _setup.setup_ax(
            ax,
            title_fontsize=10,
            title_fontweight="normal",
            fontsize_legend=9,
            axes_linewidth=1.1,
        )
        fig.canvas.draw()
        assert ax.get_xlabel() == "X"
        assert ax._left_title.get_text() == "Title"
        assert ax.xaxis.label.get_color() == "purple"
        assert ax.xaxis.labelpad == 5
        assert ax.spines["top"].get_visible() is True
        assert ax.spines["right"].get_visible() is True
        assert ax.spines["bottom"].get_edgecolor() == mpl.colors.to_rgba("green")
        assert ax.get_xticklabels()[0].get_ha() == "right"
        assert ax.get_yticklabels()[0].get_va() == "top"
        assert heat.colorbar.ax.get_ylabel() == "Configured"
        assert heat.colorbar.ax.yaxis.label.get_color() == "purple"
    with pytest.raises(TypeError, match="title_fontweight must be a string or integer"):
        _setup.setup_ax(ax, title_fontweight=1.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="unexpected keyword argument 'fontsize_title'"):
        _setup.setup_ax(ax, fontsize_title=10)  # type: ignore[call-arg]
    with pytest.raises(
        TypeError, match="unexpected keyword argument 'fontweight_title'"
    ):
        _setup.setup_ax(ax, fontweight_title="normal")  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="unexpected keyword argument 'linewidth_axes'"):
        _setup.setup_ax(ax, linewidth_axes=1.1)  # type: ignore[call-arg]

    fig2, ax2 = plt.subplots()
    ax2.plot([0, 1], [0, 1])
    _setup.setup_ax(ax2, colorbar_label="")

    calls: dict[str, object] = {}
    fake_scanpy = types.SimpleNamespace(
        set_figure_params=lambda **kwargs: calls.update(kwargs)
    )
    monkeypatch.setitem(sys.modules, "scanpy", fake_scanpy)
    with cns.settings.context(
        scanpy_use_default_style=True,
        scanpy_figsize=(3.0, 4.0),
        scanpy_facecolor="ivory",
    ):
        _setup.setup_scanpy()
    assert calls == {"scanpy": True, "figsize": (3.0, 4.0), "facecolor": "ivory"}

    with cns.settings.context(
        ggplot_fontsize=11,
        ggplot_font_family="mono",
        ggplot_font_face="bold",
        ggplot_text_color="gray20",
    ):
        gg = _setup.setup_ggplot()
    assert "theme_custom" in gg
    assert "fontsize <- 11" in gg
    assert 'family = "mono"' in gg
    assert 'face = "bold"' in gg
    assert 'color = "gray20"' in gg


def test_svg_helpers_and_export(
    output_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir.mkdir(parents=True)
    cns.figure(120, 120)
    ax = plt.gca()
    ax.text(0.5, 0.5, "Bold", fontweight="bold")
    ax.text(0.5, 0.3, "Plain")
    bold_texts = _svg._collect_bold_texts()
    assert "Bold" in bold_texts

    svg_in = output_dir / "input.svg"
    svg_out = output_dir / "output.svg"
    svg_in.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg">
<g clip-path="url(#c1)"><text x="1" y="1"><tspan x="1" y="1">Bold</tspan></text></g>
</svg>""",
        encoding="utf-8",
    )
    _svg._correct_svg(str(svg_in), str(svg_out), {"Bold"})
    root = etree.parse(str(svg_out)).getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}
    text_el = root.xpath(".//svg:text", namespaces=ns)[0]
    assert text_el.get("font-weight") == "bold"
    assert text_el.get("clip-path") == "url(#c1)"

    root2 = etree.fromstring(
        b'<svg xmlns="http://www.w3.org/2000/svg"><g><g><text>hello</text></g></g></svg>'
    )
    _svg._flatten_groups(root2, ns)
    assert not root2.xpath(".//svg:g", namespaces=ns)

    cns.figure(120, 120)
    plt.plot([0, 1], [0, 1])
    png_path = output_dir / "plot.png"
    svg_path = output_dir / "plot.svg"
    cns.savefig(str(png_path))
    cns.savefig(str(svg_path))
    assert png_path.exists()
    assert svg_path.exists()

    cns.figure(120, 120)
    plt.plot([0, 1], [0, 1])
    success_path = output_dir / "optimized.svg"
    corrected: dict[str, object] = {}

    def fake_run(args: list[str], **kwargs: object) -> object:
        optimized_svg = Path(args[7].replace("%d", "1"))
        optimized_svg.write_text(
            "<svg xmlns='http://www.w3.org/2000/svg' />", encoding="utf-8"
        )
        return types.SimpleNamespace(returncode=0)

    def fake_correct(
        input_file: str, output_file: str, bold_texts: set[str] | None = None
    ) -> None:
        corrected["input_file"] = input_file
        corrected["bold_texts"] = bold_texts
        Path(output_file).write_text(
            "<svg xmlns='http://www.w3.org/2000/svg' />", encoding="utf-8"
        )

    monkeypatch.setattr(_svg.subprocess, "run", fake_run)
    monkeypatch.setattr(_svg, "_correct_svg", fake_correct)
    _svg._save_svg(str(success_path), str(output_dir / "optimized"))
    assert success_path.exists()
    assert str(corrected["input_file"]).endswith("1.svg")
    assert isinstance(corrected["bold_texts"], set)

    cns.figure(120, 120)
    plt.plot([0, 1], [0, 1])

    def missing_run(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError("mutool")

    monkeypatch.setattr(_svg.subprocess, "run", missing_run)
    missing_path = output_dir / "missing-mutool.svg"
    with pytest.warns(RuntimeWarning, match="mutool"):
        _svg._save_svg(str(missing_path), str(output_dir / "missing-mutool"))
    assert missing_path.exists()

    cns.figure(120, 120)
    plt.plot([0, 1], [0, 1])

    def fail_run(*args: object, **kwargs: object) -> object:
        raise subprocess.CalledProcessError(1, ["mutool"], stderr=b"boom")

    monkeypatch.setattr(_svg.subprocess, "run", fail_run)
    failed_path = output_dir / "failed.svg"
    with pytest.warns(RuntimeWarning, match="boom"):
        _svg._save_svg(str(failed_path), str(output_dir / "failed"))
    assert failed_path.exists()


def test_utils_helpers_and_showcase_data(
    monkeypatch: pytest.MonkeyPatch,
    categorical_df: pd.DataFrame,
    heatmap_adata: object,
    showcase_bundle: tuple[pd.DataFrame, ...],
) -> None:
    cns.settings.reset()
    with cns.settings.context(
        figure_width=160,
        figure_height=110,
        figure_dpi=180,
        legend_out_bbox_to_anchor=(1.3, 1.4),
        legend_out_loc="lower left",
        legend_out_markerscale=2,
        panel_label_fontname="DejaVu Sans",
        panel_label_fontweight="normal",
        panel_label_offset_x=-0.2,
        panel_label_offset_y=1.05,
    ):
        cns.figure()
        assert plt.gcf().dpi == 180
        assert plt.gcf().get_size_inches()[0] == pytest.approx(160 / 72)
        assert plt.gcf().get_size_inches()[1] == pytest.approx(110 / 72)
        plt.close(plt.gcf())

        cns.figure(100, 100, color_cycle="Set1", color_map="parula")
        assert plt.gcf().dpi == 180

        fig, ax = plt.subplots()
        ax.plot([0, 1], [1, 2], label="L1")
        ax.legend(title="Legend")
        _utils.take_legend_out(title="Moved")
        legend = ax.get_legend()
        assert legend.get_title().get_text() == "Moved"
        assert legend.markerscale == 2
        assert legend.get_bbox_to_anchor()._bbox.x0 == pytest.approx(1.3)
        assert legend.get_bbox_to_anchor()._bbox.y0 == pytest.approx(1.4)

        _utils.add_panel_label("A")
        panel_text = plt.gca().texts[-1]
        assert panel_text.get_text() == "A"
        assert panel_text.get_position() == (-0.2, 1.05)
        assert panel_text.get_fontproperties().get_name() == "DejaVu Sans"
        assert panel_text.get_fontweight() == "normal"

    assert len(_utils.get_hexcolors_from_apalette([0, 1], "Set1")) == 2
    assert _utils.get_hexcolors_from_apalette([0, 1], ["#111111", "#222222"]) == [
        "#111111",
        "#222222",
    ]
    assert _utils._is_qualitative_cmap("Set1") is True
    assert _utils._is_qualitative_cmap("viridis") is False
    assert len(_utils._get_hex_colors_from_colorbar("viridis", 3)) == 4

    fig2, ax2 = plt.subplots()
    ax2.scatter([0, 1], [0, 1], label="Group", edgecolors="black")
    ax2.legend()
    _utils._remove_edge_from_legend_items(ax2)
    assert _utils._has_non_ascii("β") is True
    assert _utils._has_non_ascii("ABC") is False

    fig3, ax3 = plt.subplots()
    ax3.set_title("β")
    ax3.set_xlabel("x")
    ax3.plot([0, 1], [0, 1], label="α")
    ax3.legend(title="μ")
    _utils.apply_unicode_font(ax3)
    assert ax3.title.get_fontfamily()[0] == "DejaVu Sans"

    fig4, ax4 = plt.subplots()
    sns = pytest.importorskip("seaborn")
    sns.boxplot(data=categorical_df, x="group", y="value", ax=ax4)
    _utils._addcount_helper(categorical_df, "group", ax4)
    assert "(n=" in ax4.get_xticklabels()[0].get_text()

    class DummyResult:
        pvalue = 0.01
        test_short_name = "T"
        significance_suffix = ""

    class DummyAnnotator:
        last: "DummyAnnotator | None" = None

        def __init__(
            self, ax: object, pairs: Iterable[object], **plotting: object
        ) -> None:
            self.ax = ax
            self.pairs = list(pairs)
            self.plotting = plotting
            self._pvalue_format = None
            self.configured: dict[str, object] = {}
            self.pvalues = None
            DummyAnnotator.last = self

        def configure(self, **kwargs: object) -> None:
            self.configured = kwargs

        def apply_and_annotate(self) -> None:
            return None

        def set_pvalues(self, pvalues: list[float]) -> None:
            self.pvalues = pvalues

        def annotate(self) -> None:
            return None

    monkeypatch.setattr(_utils, "Annotator", DummyAnnotator)

    fig5, ax5 = plt.subplots()
    plotting = {
        "x": "group",
        "y": "value",
        "hue": "hue",
        "order": ["A", "B", "C"],
        "hue_order": ["H1", "H2"],
    }
    _utils._p_value_helper("t-test_welch", categorical_df, ax5, plotting.copy(), "hue")
    assert DummyAnnotator.last is not None
    assert DummyAnnotator.last.pairs

    _utils._p_value_helper(
        "Mann-Whitney",
        categorical_df,
        ax5,
        {"x": "group", "y": "value"},
        "all",
        format="full",
    )
    formatter = DummyAnnotator.last._pvalue_format
    formatted = formatter.format_data(DummyResult())
    assert formatted.startswith("$T P = ")
    assert r"\times 10^{-2}$" in formatted

    contingency = pd.DataFrame(
        [[3, 1], [1, 3]],
        index=pd.Index(["A", "B"]),
        columns=pd.Index(["Yes", "No"]),
    )
    _utils._p_value_helper(
        "fisher-exact",
        categorical_df,
        ax5,
        {"x": "group", "y": "value", "order": ["A", "B"]},
        [("A", "B")],
        contingency=contingency,
    )
    assert DummyAnnotator.last.pvalues is not None

    _utils._p_value_helper(
        "chi-squared",
        categorical_df,
        ax5,
        {"x": "group", "y": "value", "order": ["A", "B"]},
        [("A", "B")],
        contingency=contingency,
    )

    assert len(_utils.palettes(["#111111", "#222222"])) == 2
    assert _utils.palettes("Set1")
    assert _utils.palettes("BuRd_custom").name == "BuRd_custom"
    assert isinstance(_utils.palettes("Wrong Choice!"), RuntimeError)

    fake_sns = types.SimpleNamespace(
        load_dataset=lambda name: (
            showcase_bundle[0] if name == "iris" else showcase_bundle[1]
        )
    )
    fake_sc = types.SimpleNamespace(
        datasets=types.SimpleNamespace(blobs=lambda: heatmap_adata.copy())
    )
    monkeypatch.setitem(sys.modules, "seaborn", fake_sns)
    monkeypatch.setitem(sys.modules, "scanpy", fake_sc)
    data = _utils.get_showcase_data()
    assert len(data) == 10
    data_with_assets = _utils.get_showcase_data(
        include_showcase_images=True,
        caller_file=Path(__file__).resolve().parents[1]
        / "examples"
        / "plot_320_multipanel.py",
    )
    assert len(data_with_assets) == 11
    assert data_with_assets[-1].name == "assets"

    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    module_globals: dict[str, object] = {"_utils": _utils}
    exec(
        "result = _utils.get_showcase_data(include_showcase_images=True)",
        module_globals,
    )
    data_without_file = module_globals["result"]
    assert isinstance(data_without_file, tuple)
    assert len(data_without_file) == 11
    assert data_without_file[-1].name == "assets"


def test_multipanel_layout() -> None:
    mp = cns.multipanel(max_width=150)
    ax_a = mp.panel(
        "A",
        width=60,
        height=40,
        margin_left=0,
        margin_top=0,
        margin_right=10,
        margin_bottom=10,
    )
    ax_b = mp.panel(
        "B",
        width=60,
        height=40,
        margin_left=0,
        margin_top=0,
        margin_right=10,
        margin_bottom=10,
    )
    mp.newline()
    ax_c = mp.panel("C", width=60, height=40, below="A")
    assert ax_a is mp.get_axes("A")
    assert ax_b is mp.get_axes("B")
    assert ax_c is mp.get_axes("C")
    assert mp.get_axes("missing") is None
    assert len(mp.axes) == 3


def test_multipanel_settings_defaults_and_label_style() -> None:
    with cns.settings.context(
        figure_dpi=160,
        multipanel_max_width=180,
        multipanel_title_loc="left",
        panel_width=70,
        panel_height=50,
        panel_label_left=11,
        panel_label_top=13,
        panel_pad_left=14,
        panel_pad_top=5,
        panel_margin=(6, 7, 8, 9),
        panel_label_fontname="DejaVu Sans",
        panel_label_fontweight="normal",
    ):
        mp = cns.multipanel(title="Overview")
        ax = mp.panel()

        assert mp._max_width == 180
        assert mp.fig.dpi == 160
        assert mp._title_text is not None
        assert mp._title_text.get_ha() == "left"
        assert ax.get_position().width == pytest.approx(70 / 180)
        assert mp._label_texts["A"].get_fontproperties().get_name() == "DejaVu Sans"
        assert mp._label_texts["A"].get_fontweight() == "normal"


def test_multipanel_margin_args_inherit_settings_defaults() -> None:
    with cns.settings.context(panel_margin=(6, 7, 8, 9)):
        mp = cns.multipanel(max_width=180)
        mp.panel(
            "A",
            width=60,
            height=40,
            margin_left=1,
            margin_bottom=2,
        )

    panel = mp._panels[0]
    assert panel["margin_left"] == 1
    assert panel["margin_top"] == 7
    assert panel["margin_right"] == 8
    assert panel["margin_bottom"] == 2


def test_multipanel_panel_rejects_margin_tuple_argument() -> None:
    mp = cns.multipanel(max_width=150)

    with pytest.raises(TypeError, match="unexpected keyword argument 'margin'"):
        mp.panel("A", width=60, height=40, margin=(0, 0, 10, 10))  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("loc", "expected_x"),
    [
        ("left", 10 / 200),
        ("center", 55 / 200),
        ("right", 100 / 200),
    ],
)
def test_multipanel_title_alignment_and_default_fontweight(
    loc: str, expected_x: float
) -> None:
    mp = cns.multipanel(max_width=200, title="Overview", loc=loc)
    mp.panel("A", width=60, height=40)

    assert mp._title_text is not None
    assert mp._title_text.get_text() == "Overview"
    assert mp._title_text.get_ha() == loc
    assert mp._title_text.get_fontweight() == "bold"
    assert mp._title_text.get_position()[0] == pytest.approx(expected_x)
    assert mp._label_texts["A"].get_ha() == "left"


def test_multipanel_title_fontweight_and_height_reservation() -> None:
    mp_plain = cns.multipanel(max_width=200)
    mp_plain.panel("A", width=60, height=40)

    mp_titled = cns.multipanel(
        max_width=200,
        title="Overview",
        title_fontweight="normal",
    )
    mp_titled.panel("A", width=60, height=40)

    plain_height_px = mp_plain.fig.get_size_inches()[1] * 72
    titled_height_px = mp_titled.fig.get_size_inches()[1] * 72
    expected_delta = max(
        cns.settings.multipanel_title_height_min,
        cns.settings.title_fontsize + cns.settings.multipanel_title_height_pad,
    )

    assert mp_titled._title_text is not None
    assert mp_titled._title_text.get_fontweight() == "normal"
    assert titled_height_px - plain_height_px == pytest.approx(expected_delta)


def test_multipanel_title_updates_existing_artist() -> None:
    mp = cns.multipanel(max_width=200, title="Overview", loc="left")
    mp.panel("A", width=60, height=40)

    original_title_text = mp._title_text
    assert original_title_text is not None

    mp._title = "Updated Overview"
    mp._title_loc = "right"
    mp._title_fontweight = "normal"
    mp._create_or_update_figure()

    assert mp._title_text is original_title_text
    assert mp._title_text.get_text() == "Updated Overview"
    assert mp._title_text.get_ha() == "right"
    assert mp._title_text.get_va() == "center"
    assert mp._title_text.get_fontweight() == "normal"
    assert mp._title_text.get_position()[0] == pytest.approx(100 / 200)
    assert mp._label_texts["A"].get_ha() == "left"
    assert mp._label_texts["A"].get_va() == "center"


def test_multipanel_title_can_be_removed() -> None:
    mp = cns.multipanel(max_width=200, title="Overview")
    mp.panel("A", width=60, height=40)

    assert mp._title_text is not None

    mp._title = None
    mp._create_or_update_figure()

    assert mp._title_text is None


def test_multipanel_title_invalid_loc_raises() -> None:
    with pytest.raises(ValueError, match="loc must be one of"):
        cns.multipanel(title="Overview", loc="top")


def test_multipanel_title_invalid_fontweight_raises() -> None:
    with pytest.raises(TypeError, match="title_fontweight must be a string or integer"):
        cns.multipanel(title="Overview", title_fontweight=1.5)  # type: ignore[arg-type]
    with pytest.raises(
        TypeError, match="unexpected keyword argument 'fontweight_title'"
    ):
        cns.multipanel(title="Overview", fontweight_title="normal")  # type: ignore[call-arg]


def test_multipanel_below_aligns_to_parent_column() -> None:
    mp = cns.multipanel(max_width=540)
    mp.panel(
        "B",
        width=145,
        height=128,
        label_left=10,
        label_top=12,
        pad_left=0,
        pad_top=0,
        margin_left=10,
        margin_top=0,
        margin_right=0,
        margin_bottom=10,
    )
    mp.panel(
        "C",
        width=145,
        height=128,
        label_left=10,
        label_top=12,
        pad_left=0,
        pad_top=0,
        margin_left=10,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
        below="B",
    )

    assert mp._get_panel_position(0)[0] == mp._get_panel_position(1)[0]
