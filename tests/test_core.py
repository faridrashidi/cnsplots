from __future__ import annotations

import builtins
import re
import subprocess
import sys
import types
from collections.abc import Iterable, Mapping, Sequence
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import anndata as ad
import matplotlib as mpl
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import matplotlib.colorbar
import numpy as np
import pandas as pd
import pytest
import seaborn as sns
from lxml import etree
from matplotlib.backend_bases import DrawEvent, Event
from matplotlib.legend import Legend

import cnsplots as cns
from cnsplots import _settings, _setup, _svg, _utils, _validation


def _panel_label_padding(ax, text) -> tuple[float, float]:
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    axes_bbox = ax.get_window_extent(renderer=renderer)
    text_bbox = text.get_window_extent(renderer=renderer)
    return axes_bbox.x0 - text_bbox.x1, text_bbox.y0 - axes_bbox.y1


def _panel_label_left_gap(ax, text) -> float:
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    tight_bbox = ax.yaxis.get_tightbbox(renderer=renderer)
    if tight_bbox is None:
        return 0.0
    text_bbox = text.get_window_extent(renderer=renderer)
    return tight_bbox.x0 - text_bbox.x1


def _panel_label_title_gap(ax, text) -> float:
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    text_bbox = text.get_window_extent(renderer=renderer)
    title_bbox = ax.title.get_window_extent(renderer=renderer)
    return text_bbox.y0 - title_bbox.y1


def _panel_label_top_gap(ax, text) -> float:
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    text_bbox = text.get_window_extent(renderer=renderer)
    axes_bbox = ax.get_window_extent(renderer=renderer)
    top_edge = float(axes_bbox.y1)
    topmost = top_edge

    artists = [
        ax.title,
        ax.xaxis.label,
        ax.xaxis.get_offset_text(),
        *ax.get_xticklabels(),
    ]
    legend = ax.get_legend()
    if legend is not None:
        artists.append(legend)
    artists.extend(artist for artist in ax.texts if artist is not text)
    artists.extend(artist for artist in ax.lines if not artist.get_clip_on())
    artists.extend(artist for artist in ax.collections if not artist.get_clip_on())
    artists.extend(artist for artist in ax.patches if not artist.get_clip_on())
    artists.extend(artist for artist in ax.artists if not artist.get_clip_on())

    for artist in artists:
        if not artist.get_visible():
            continue
        bbox = artist.get_window_extent(renderer=renderer)
        if bbox.width <= 0 and bbox.height <= 0:
            continue
        if bbox.y1 > top_edge:
            topmost = max(topmost, float(bbox.y1))

    return text_bbox.y0 - topmost


def _pdf_media_box_size(path: Path) -> tuple[float, float]:
    match = re.search(
        rb"/MediaBox\s*\[\s*([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\s*\]",
        path.read_bytes(),
    )
    if match is None:
        raise AssertionError(f"MediaBox not found in {path}")
    x0, y0, x1, y1 = (float(value) for value in match.groups())
    return x1 - x0, y1 - y0


def _panel_column_origin(mp: cns.multipanel, panel_idx: int) -> float:
    panel = mp._panels[panel_idx]
    return (
        mp._get_panel_position(panel_idx)[0]
        - panel["margin_left"]
        - mp._get_left_reserve_px(panel)
    )


def _bbox_is_within(fig_bbox, artist_bbox, *, pad: float = 0.8) -> bool:
    return (
        artist_bbox.x0 >= fig_bbox.x0 - pad
        and artist_bbox.y0 >= fig_bbox.y0 - pad
        and artist_bbox.x1 <= fig_bbox.x1 + pad
        and artist_bbox.y1 <= fig_bbox.y1 + pad
    )


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
    assert settings.savefig_bbox == "standard"
    assert settings.savefig_transparent is True
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
    settings.panel_pad_left = 21
    settings.panel_pad_top = 2
    settings.panel_margin_top = 2
    settings.panel_margin_bottom = 4
    settings.panel_margin_left = 1
    settings.panel_margin_right = 3
    settings.panel_label_fontname = "DejaVu Sans"
    settings.panel_label_fontweight = 500
    settings.legend_out_bbox_to_anchor = (1.1, 1.2)
    settings.legend_out_loc = "lower left"
    settings.legend_out_markerscale = 2
    assert "CNSSettings(" in repr(settings)
    assert "title_fontweight='normal'" in repr(settings)
    assert "figure_width=180" in repr(settings)
    assert "font_sans_serif=('Arial', 'DejaVu Sans')" in repr(settings)
    assert "panel_label_left" not in repr(settings)
    assert "panel_label_top" not in repr(settings)
    assert "panel_label_offset_x" not in repr(settings)

    with pytest.raises(AttributeError, match="panel_label_left"):
        settings.panel_label_left = 11
    with pytest.raises(AttributeError, match="panel_label_left"):
        with settings.context(panel_label_left=11):
            pass
    with pytest.raises(AttributeError, match="panel_label_top"):
        settings.panel_label_top = 13
    with pytest.raises(AttributeError, match="panel_label_top"):
        with settings.context(panel_label_top=13):
            pass
    with pytest.raises(AttributeError, match="panel_label_offset_x"):
        settings.panel_label_offset_x = -0.3
    with pytest.raises(AttributeError, match="panel_label_offset_x"):
        with settings.context(panel_label_offset_x=-0.3):
            pass

    with settings.context(
        title_fontsize=12,
        title_fontweight=600,
        palette_qual="Dark2",
        legend_fontsize=None,
        scanpy_figsize=(5.0, 4.0),
        panel_margin_top=6,
        panel_margin_bottom=8,
        panel_margin_left=5,
        panel_margin_right=7,
    ) as ctx:
        assert ctx.title_fontsize == 12
        assert ctx.title_fontweight == 600
        assert settings.palette_qual == "Dark2"
        assert ctx.legend_fontsize is None
        assert ctx.scanpy_figsize == (5.0, 4.0)
        assert ctx.panel_margin_top == 6
        assert ctx.panel_margin_bottom == 8
        assert ctx.panel_margin_left == 5
        assert ctx.panel_margin_right == 7
    assert settings.title_fontsize == 10
    assert settings.title_fontweight == "normal"
    assert settings.palette_qual == "Set2"
    assert settings.legend_fontsize == 11
    assert settings.scanpy_figsize == (3.0, 4.0)
    assert settings.panel_margin_top == 2
    assert settings.panel_margin_bottom == 4
    assert settings.panel_margin_left == 1
    assert settings.panel_margin_right == 3

    with pytest.raises(AttributeError, match="not a valid setting"):
        settings.panel_margin = (1, 2, 3, 4)
    with pytest.raises(AttributeError, match="not a valid setting"):
        with settings.context(panel_margin=(5, 6, 7, 8)):
            pass

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
        settings.palette_qual = 1
    with pytest.raises(TypeError):
        settings.palette_seq = 1
    with pytest.raises(TypeError):
        settings.title_fontsize = "1"
    with pytest.raises(ValueError):
        settings.title_fontsize = 0
    with pytest.raises(TypeError):
        settings.title_fontweight = []
    with pytest.raises(TypeError, match="title_fontweight must be a string or integer"):
        settings.title_fontweight = 1.5
    with pytest.raises(TypeError):
        settings.fontsize_legend = "1"
    with pytest.raises(ValueError):
        settings.fontsize_legend = 0
    with pytest.raises(TypeError):
        settings.axes_linewidth = "1"
    with pytest.raises(ValueError):
        settings.axes_linewidth = 0
    with pytest.raises(TypeError):
        settings.verbosity = 1.5
    with pytest.raises(ValueError):
        settings.verbosity = -1

    settings.reset()
    assert settings.palette_qual == "Ecotyper1"
    assert settings.title_fontweight == "bold"
    assert settings.savefig_bbox == "standard"
    assert settings.savefig_transparent is True
    assert settings.legend_fontsize is None
    assert settings.scanpy_figsize == (2.5, 2.5)
    assert settings.panel_pad_left == 0
    assert settings.panel_pad_top == 0
    assert settings.panel_margin_top == 0
    assert settings.panel_margin_bottom == 10
    assert settings.panel_margin_left == 0
    assert settings.panel_margin_right == 10
    assert settings.font_sans_serif == (
        "Helvetica",
        "Helvetica Neue",
        "Arial",
        "DejaVu Sans",
    )
    assert settings.panel_label_fontname == "Helvetica"


def test_settings_validation_errors() -> None:
    settings = _settings.CNSSettings()

    with pytest.raises(TypeError):
        settings.palette_qual = 1
    with pytest.raises(TypeError):
        settings.palette_seq = 1
    with pytest.raises(TypeError):
        settings.title_fontsize = "1"
    with pytest.raises(TypeError):
        settings.figure_width = None
    with pytest.raises(ValueError):
        settings.title_fontsize = 0
    with pytest.raises(TypeError):
        settings.title_fontweight = []
    with pytest.raises(TypeError):
        settings.panel_label_fontweight = None
    with pytest.raises(TypeError, match="title_fontweight must be a string or integer"):
        settings.title_fontweight = 1.5
    with pytest.raises(TypeError):
        settings.fontsize_legend = "1"
    with pytest.raises(ValueError):
        settings.fontsize_legend = 0
    with pytest.raises(TypeError):
        settings.axes_linewidth = "1"
    with pytest.raises(ValueError):
        settings.axes_linewidth = 0
    with pytest.raises(TypeError):
        settings.verbosity = 1.5
    with pytest.raises(ValueError):
        settings.verbosity = -1
    with pytest.raises(TypeError):
        settings.axes_grid = "yes"
    with pytest.raises(TypeError):
        settings.axes_titlelocation = 1
    with pytest.raises(ValueError, match="axes_titlelocation must be one of"):
        settings.axes_titlelocation = "top"
    with pytest.raises(TypeError):
        settings.font_sans_serif = "Arial"
    with pytest.raises(TypeError):
        settings.font_sans_serif = ["Arial", 1]
    with pytest.raises(ValueError):
        settings.font_sans_serif = []
    with pytest.raises(TypeError):
        settings.scanpy_figsize = "big"
    with pytest.raises(ValueError):
        settings.scanpy_figsize = (1.0,)
    with pytest.raises(TypeError):
        settings.legend_fontsize = "big"
    with pytest.raises(ValueError):
        settings.legend_markerscale = -1
    with pytest.raises(TypeError):
        settings.panel_margin_top = "big"
    with pytest.raises(ValueError):
        settings.panel_margin_left = -1
    with pytest.raises(TypeError):
        settings.pdf_fonttype = 1.5
    with pytest.raises(ValueError):
        settings.pdf_fonttype = 0
    with pytest.raises(TypeError):
        settings.legend_out_loc = 1
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
        assert "Cell" in mpl.colormaps
        assert "Nature" in mpl.colormaps
        assert "Science" in mpl.colormaps
        assert "NPG" not in mpl.colormaps
        assert "AAAS" not in mpl.colormaps

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
    mp = cns.multipanel(max_width=220, title="Figure Bold")
    ax = mp.panel("A", width=80, height=60)
    ax.set_title("Panel Bold")
    ax.text(0.5, 0.3, "Plain")
    bold_texts = _svg._collect_bold_texts()
    assert "Figure Bold" in bold_texts
    assert "Panel Bold" in bold_texts
    assert "A" in bold_texts

    svg_in = output_dir / "input.svg"
    svg_out = output_dir / "output.svg"
    svg_in.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg">
<g clip-path="url(#c1)">
<text x="1" y="1" font-family="EDQXKT+Helvetica-Bold"><tspan x="1" y="1">Panel Bold</tspan></text>
<text x="2" y="2" font-family="EDQXKT+Helvetica-Bold"><tspan x="2" y="2">Figure Bold</tspan></text>
<text x="3" y="3" font-family="EDQXKT+Helvetica-Oblique">Italic</text>
<text x="4" y="4">No Font</text>
</g>
</svg>""",
        encoding="utf-8",
    )
    _svg._correct_svg(str(svg_in), str(svg_out), {"Panel Bold", "Figure Bold"})
    root = etree.parse(str(svg_out)).getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}
    text_els = root.xpath(".//svg:text", namespaces=ns)
    assert len(text_els) == 4
    assert text_els[0].get("font-family") == "Helvetica"
    assert text_els[0].get("font-weight") == "bold"
    assert text_els[1].get("font-family") == "Helvetica"
    assert text_els[1].get("font-weight") == "bold"
    assert text_els[2].get("font-family") == "Helvetica"
    assert text_els[2].get("font-style") == "italic"
    assert text_els[3].get("font-family") is None
    assert all(text_el.get("clip-path") == "url(#c1)" for text_el in text_els)

    svg_image_in = output_dir / "input-image.svg"
    svg_image_out = output_dir / "output-image.svg"
    svg_image_in.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g clip-path="url(#img-clip)" transform="translate(10 20) scale(4)">
  <image width="12" height="8" xlink:href="data:image/png;base64,AA==" />
</g>
</svg>""",
        encoding="utf-8",
    )
    _svg._correct_svg(str(svg_image_in), str(svg_image_out))
    image_root = etree.parse(str(svg_image_out)).getroot()
    image_el = image_root.xpath(".//svg:image", namespaces=ns)[0]
    assert not image_root.xpath(".//svg:g", namespaces=ns)
    assert image_el.get("clip-path") == "url(#img-clip)"
    assert image_el.get("transform") == "translate(10 20) scale(4)"

    root2 = etree.fromstring(
        b'<svg xmlns="http://www.w3.org/2000/svg"><g><g><text>hello</text></g></g></svg>'
    )
    _svg._flatten_groups(root2, ns)
    assert not root2.xpath(".//svg:g", namespaces=ns)

    root3 = etree.fromstring(
        b'<svg xmlns="http://www.w3.org/2000/svg"><g transform="translate(1 2)"><g transform="scale(4)"><path transform="rotate(15)" d="M0 0L1 1"/></g></g></svg>'
    )
    _svg._flatten_groups(root3, ns)
    path_el = root3.xpath(".//svg:path", namespaces=ns)[0]
    assert not root3.xpath(".//svg:g", namespaces=ns)
    assert path_el.get("transform") == "translate(1 2) scale(4) rotate(15)"

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
    original_dpi = plt.gcf().dpi
    original_plt_savefig = _utils.plt.savefig
    saved_png_meta: dict[str, float] = {}

    def fake_png_savefig(*args: object, **kwargs: object) -> None:
        saved_png_meta["fig_dpi"] = plt.gcf().dpi
        dpi = kwargs.get("dpi", plt.gcf().dpi)
        assert isinstance(dpi, (int, float))
        saved_png_meta["dpi_kwarg"] = float(dpi)

    monkeypatch.setattr(_utils.plt, "savefig", fake_png_savefig)
    with cns.settings.context(savefig_dpi=300):
        cns.savefig(str(output_dir / "captured.png"))
    assert saved_png_meta["fig_dpi"] == pytest.approx(300)
    assert saved_png_meta["dpi_kwarg"] == pytest.approx(300)
    assert plt.gcf().dpi == pytest.approx(original_dpi)
    monkeypatch.setattr(_utils.plt, "savefig", original_plt_savefig)

    cns.figure(120, 120)
    plt.plot([0, 1], [0, 1])
    original_svg_dpi = plt.gcf().dpi
    saved_svg_meta: dict[str, float] = {}

    def fake_save_svg(filepath: str, root: str) -> None:
        saved_svg_meta["fig_dpi"] = plt.gcf().dpi
        Path(filepath).write_text("<svg xmlns='http://www.w3.org/2000/svg' />")

    monkeypatch.setattr(_utils, "_save_svg", fake_save_svg)
    with cns.settings.context(savefig_dpi=300):
        cns.savefig(str(output_dir / "captured.svg"))
    assert saved_svg_meta["fig_dpi"] == pytest.approx(300)
    assert plt.gcf().dpi == pytest.approx(original_svg_dpi)

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


def test_savefig_default_bounds_match_jpg_and_pdf(
    output_dir: Path,
    categorical_df: pd.DataFrame,
) -> None:
    output_dir.mkdir(parents=True)
    cns.settings.reset()
    try:
        mp = cns.multipanel(max_width=220, title="Figure 1", loc="left")

        mp.panel("A", 90, 70, color_cycle=[cns.VIOLET])
        ax = cns.boxplot(data=categorical_df, x="group", y="value")
        ax.set_title("Boxplot")

        mp.panel("B", 90, 70, color_cycle="BlueRed")
        ax = cns.stripplot(data=categorical_df, x="group", y="value", hue="hue")
        ax.set_title("Stripplot")

        jpg_path = output_dir / "figure.jpg"
        pdf_path = output_dir / "figure.pdf"
        cns.savefig(str(jpg_path))
        cns.savefig(str(pdf_path))

        jpg_height, jpg_width = plt.imread(str(jpg_path)).shape[:2]
        pdf_width_pt, pdf_height_pt = _pdf_media_box_size(pdf_path)
        scale = float(cns.settings.savefig_dpi) / 72

        assert jpg_width == pytest.approx(pdf_width_pt * scale, abs=1)
        assert jpg_height == pytest.approx(pdf_height_pt * scale, abs=1)
    finally:
        cns.settings.reset()


def test_savefig_heatmap_multipanel_exports_without_pdf_renderer(
    output_dir: Path,
    heatmap_adata: ad.AnnData,
) -> None:
    pdf_path = output_dir / "heatmap.pdf"
    svg_path = output_dir / "heatmap.svg"

    mp = cns.multipanel(max_width=240, title="Figure 1", loc="left")
    mp.panel("A", 120, 120)
    cmp = cns.heatmapplot(
        heatmap_adata,
        label="Z-score",
        row_annotation=["cluster"],
        col_annotation=["pathway"],
        row_cluster=True,
        col_cluster=True,
        show_rownames=True,
        show_colnames=True,
    )
    cmp.ax.set_title("Heatmap")

    cns.savefig(str(pdf_path))
    cns.savefig(str(svg_path))

    assert pdf_path.exists()
    assert svg_path.exists()


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
        panel_pad_left=14,
        panel_pad_top=5,
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
        panel_pad_left, panel_pad_top = _panel_label_padding(ax, panel_text)
        assert panel_text.get_text() == "A"
        assert panel_pad_left == pytest.approx(14, abs=0.5)
        assert panel_pad_top == pytest.approx(5, abs=0.5)
        assert panel_text.get_fontproperties().get_name() == "DejaVu Sans"
        assert panel_text.get_fontweight() == "normal"
        assert panel_text.get_ha() == "right"
        assert panel_text.get_va() == "bottom"

        _utils.add_panel_label("B", pad_left=9, pad_top=4)
        override_text = plt.gca().texts[-1]
        override_pad_left, override_pad_top = _panel_label_padding(ax, override_text)
        assert override_pad_left == pytest.approx(9, abs=0.5)
        assert override_pad_top == pytest.approx(4, abs=0.5)

        with pytest.raises(TypeError, match="offset_x"):
            cast(Any, _utils.add_panel_label)("C", offset_x=-0.2, offset_y=1.05)

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
    assert len(_utils.palettes("Cell")) == 10
    assert len(_utils.palettes("Nature")) == 10
    assert len(_utils.palettes("Science")) == 10
    assert _utils.palettes("BuRd_custom").name == "BuRd_custom"
    assert isinstance(_utils.palettes("NPG"), RuntimeError)
    assert isinstance(_utils.palettes("AAAS"), RuntimeError)
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


def test_figure_autofit_keeps_stackplot_title_and_legend_in_bounds() -> None:
    tips = sns.load_dataset("tips")

    with cns.settings.context(figure_autofit=True):
        cns.figure(120, 100)
        fig = plt.gcf()
        initial_size = tuple(fig.get_size_inches())

        ax = cns.stackplot(
            data=tips,
            x="sex",
            y="day",
            width=0.4,
            normalize=True,
            addtip=True,
        )
        ax.set_title("Normalized Stacked Bar (with labels)")

        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        legend = ax.get_legend()
        title_bbox = ax.title.get_window_extent(renderer=renderer)
        ylabel_bbox = ax.yaxis.label.get_window_extent(renderer=renderer)
        content_bbox = fig._cnsplots_autofit_manager._get_content_bbox(renderer)

        assert legend is not None
        assert fig.get_size_inches()[0] > initial_size[0]
        assert content_bbox is not None
        assert _bbox_is_within(fig.bbox, title_bbox)
        assert _bbox_is_within(fig.bbox, legend.get_window_extent(renderer=renderer))
        assert ylabel_bbox.x0 == pytest.approx(fig.bbox.x0, abs=1.0)
        assert content_bbox.x0 == pytest.approx(fig.bbox.x0, abs=1.0)
        assert content_bbox.x1 == pytest.approx(fig.bbox.x1, abs=1.0)
        assert content_bbox.y0 == pytest.approx(fig.bbox.y0, abs=1.0)
        assert content_bbox.y1 == pytest.approx(fig.bbox.y1, abs=1.0)


def test_figure_autofit_handles_generic_matplotlib_overflow() -> None:
    with cns.settings.context(figure_autofit=True):
        cns.figure(120, 100)
        fig = plt.gcf()
        initial_size = tuple(fig.get_size_inches())
        ax = plt.gca()
        ax.plot([0, 1], [0, 1], label="Series")
        legend = ax.legend(loc="upper left", bbox_to_anchor=(1, 1.02))
        fig_title = fig.suptitle("A Generic Figure-Level Title That Needs More Width")
        outside_text = ax.text(1.02, 1.05, "Outside note", transform=ax.transAxes)
        unclipped_line = ax.plot(
            [0, 1],
            [1.04, 1.04],
            transform=ax.transAxes,
            clip_on=False,
            color="black",
        )[0]
        figure_artist = mlines.Line2D(
            [10, float(fig.bbox.width) + 40],
            [float(fig.bbox.height) - 8, float(fig.bbox.height) - 8],
            transform=mtransforms.IdentityTransform(),
            clip_on=False,
            color="black",
        )
        fig.add_artist(figure_artist)

        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        content_bbox = fig._cnsplots_autofit_manager._get_content_bbox(renderer)

        assert fig.get_size_inches()[0] > initial_size[0]
        assert content_bbox is not None
        assert _bbox_is_within(fig.bbox, fig_title.get_window_extent(renderer=renderer))
        assert _bbox_is_within(fig.bbox, legend.get_window_extent(renderer=renderer))
        assert _bbox_is_within(
            fig.bbox, outside_text.get_window_extent(renderer=renderer)
        )
        assert _bbox_is_within(
            fig.bbox, unclipped_line.get_window_extent(renderer=renderer)
        )
        assert _bbox_is_within(
            fig.bbox, figure_artist.get_window_extent(renderer=renderer)
        )
        assert content_bbox.x0 == pytest.approx(fig.bbox.x0, abs=1.0)
        assert content_bbox.x1 == pytest.approx(fig.bbox.x1, abs=1.0)
        assert content_bbox.y0 == pytest.approx(fig.bbox.y0, abs=1.0)
        assert content_bbox.y1 == pytest.approx(fig.bbox.y1, abs=1.0)


def test_figure_autofit_ignores_hidden_helper_axes_for_clustered_heatmap() -> None:
    rng = np.random.default_rng(42)
    n_rows = 120
    n_cols = 10
    n_groups = 5
    row_groups = np.repeat(np.arange(n_groups), n_rows // n_groups)
    base_profile = np.linspace(-1.0, 1.0, n_cols)
    group_profiles = np.vstack(
        [
            np.roll(base_profile, shift) + np.linspace(0.0, 0.8, n_groups)[shift]
            for shift in range(n_groups)
        ]
    )
    matrix = np.vstack(
        [
            group_profiles[group] + rng.normal(scale=0.12, size=n_cols)
            for group in row_groups
        ]
    )
    adata = ad.AnnData(matrix)
    adata.obs_names = [str(i) for i in range(n_rows)]
    adata.var_names = [str(i) for i in range(n_cols)]
    selected = pd.Series(pd.NA, index=adata.obs_names, dtype="string")
    selected[np.linspace(0.0, 1.0, n_rows) > 0.96] = "o"
    adata.obs["selected"] = selected
    adata.obs["mitf"] = np.linspace(0.0, 1.0, n_rows)
    adata.obs["blobs"] = pd.Categorical([f"C{group}" for group in row_groups])
    adata.var["ensemble"] = pd.Categorical([f"ens{i % 3}" for i in range(n_cols)])

    with cns.settings.context(figure_autofit=True):
        cns.figure(300, 250)
        fig = plt.gcf()
        initial_bbox = fig.bbox.frozen()
        cmp = cns.heatmapplot(
            adata,
            label="Expression",
            xlabel="Genes",
            ylabel="Samples",
            row_annotation=["selected", "mitf", "blobs"],
            col_annotation=["ensemble"],
            row_split=5,
            row_cluster=True,
            col_cluster=True,
            row_cluster_method="ward",
            row_cluster_metric="euclidean",
            col_cluster_method="ward",
            col_cluster_metric="euclidean",
            show_rownames=True,
            show_colnames=True,
            xticklabels_fontsize=7,
            yticklabels_fontsize=7,
            row_dendrogram=True,
            col_dendrogram=True,
            row_split_gap=1,
            col_split_gap=1,
            legend_hpad=-2,
            legend_vpad=6,
            legend_width=20,
        )
        cmp.ax.set_title("Basic Heatmapplot")

        assert cmp.ax_heatmap is not None

        fig.canvas.draw()
        first_bbox = fig.bbox.frozen()
        renderer = fig.canvas.get_renderer()
        fig.canvas.draw()
        second_bbox = fig.bbox.frozen()
        legends = [obj for obj in cmp.cbars if isinstance(obj, Legend)]

        assert float(first_bbox.width) < float(initial_bbox.width) * 2.0
        assert float(first_bbox.height) < float(initial_bbox.height) * 2.0
        assert second_bbox.bounds == pytest.approx(first_bbox.bounds, abs=1.0)
        assert _bbox_is_within(
            fig.bbox,
            cmp.ax.title.get_window_extent(renderer=renderer),
        )
        assert len(legends) == 2
        for legend in legends:
            assert _bbox_is_within(
                fig.bbox,
                legend.get_window_extent(renderer=renderer),
            )
        heatmap_bbox = cmp.ax_heatmap.get_window_extent(renderer=renderer)
        for legend_ax in cmp.legend_axes:
            assert (
                legend_ax.get_window_extent(renderer=renderer).x0
                >= heatmap_bbox.x1 - 1.0
            )
        colorbars = [obj for obj in cmp.cbars if isinstance(obj, mpl.colorbar.Colorbar)]
        assert colorbars
        for cbar in colorbars:
            assert _bbox_is_within(
                fig.bbox,
                cbar.ax.get_window_extent(renderer=renderer),
            )
            assert (
                cbar.ax.get_window_extent(renderer=renderer).x0 >= heatmap_bbox.x1 - 1.0
            )
        assert len(cmp.ax_col_dendrogram_axes) == 1
        assert _bbox_is_within(
            fig.bbox,
            cmp.ax_col_dendrogram_axes[0].get_window_extent(renderer=renderer),
        )


def test_figure_autofit_can_be_disabled() -> None:
    with cns.settings.context(figure_autofit=False):
        cns.figure(120, 100)
        fig = plt.gcf()
        initial_size = tuple(fig.get_size_inches())
        ax = plt.gca()
        ax.plot([0, 1], [0, 1], label="Series")
        legend = ax.legend(loc="upper left", bbox_to_anchor=(1, 1.02))
        ax.set_title("Normalized Stacked Bar (with labels)")

        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()

        assert tuple(fig.get_size_inches()) == pytest.approx(initial_size)
        assert not _bbox_is_within(fig.bbox, ax.title.get_window_extent(renderer))
        assert not _bbox_is_within(fig.bbox, legend.get_window_extent(renderer))


def test_figure_autofit_internal_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    cns.figure(120, 120)
    fig = plt.gcf()
    manager = fig._cnsplots_autofit_manager
    original_cid = manager._draw_event_cid

    manager._connect_draw_handler()
    assert manager._draw_event_cid == original_cid
    assert manager._get_canvas_renderer(object()) is None

    class TightBBoxArtist:
        def get_tightbbox(self, renderer: object) -> mtransforms.Bbox:
            return mtransforms.Bbox.from_bounds(1, 2, 3, 4)

    class WindowExtentFallbackArtist:
        def get_window_extent(
            self,
            renderer: object | None = None,
        ) -> mtransforms.Bbox:
            if renderer is not None:
                raise TypeError
            return mtransforms.Bbox.from_bounds(5, 6, 7, 8)

    assert manager._get_artist_bbox(TightBBoxArtist(), cast(Any, object())) is not None
    fallback_bbox = manager._get_artist_bbox(
        WindowExtentFallbackArtist(),
        cast(Any, object()),
    )
    assert fallback_bbox is not None
    assert fallback_bbox.bounds == pytest.approx((5, 6, 7, 8))
    assert manager._get_artist_bbox(object(), cast(Any, object())) is None
    assert manager._figure_has_expanded() is False
    assert manager._tighten_single_axes_horizontal_layout(cast(Any, object())) is False
    assert manager._get_content_bbox(cast(Any, object())) is None
    assert manager._measure_overflow_px(cast(Any, object())) == (0.0, 0.0, 0.0, 0.0)
    assert manager._crop_canvas_to_content(cast(Any, object())) is False

    manager._on_draw(cast(Any, object()))

    other_fig = plt.figure()
    other_fig.canvas.draw()
    other_event = DrawEvent(
        "draw_event",
        other_fig.canvas,
        other_fig.canvas.get_renderer(),
    )
    manager._on_draw(other_event)

    original_canvas = fig.canvas
    seen_canvases: list[str] = []
    monkeypatch.setattr(
        manager,
        "_on_draw",
        lambda event: seen_canvases.append(
            type(getattr(event, "canvas", None)).__name__
        ),
    )
    _utils._preflight_autofit_for_export(fig)
    assert seen_canvases == ["FigureCanvasAgg"]
    assert fig.canvas is original_canvas
    seen_canvases.clear()
    with cns.settings.context(figure_autofit=False):
        _utils._preflight_autofit_for_export(fig)
    assert seen_canvases == []

    cns.figure(120, 100)
    fig2 = plt.gcf()
    manager2 = fig2._cnsplots_autofit_manager
    ax2 = plt.gca()
    ax2.plot([0, 1], [0, 1], label="Series")
    ax2.legend(loc="upper left", bbox_to_anchor=(1, 1.02))
    ax2.set_title("Normalized Stacked Bar (with labels)")
    fig2.canvas.draw()
    assert manager2._figure_has_expanded() is True
    manager2._is_relayout_in_draw = True
    fig2.canvas.draw()
    manager2._is_relayout_in_draw = False
    monkeypatch.setattr(manager2, "_get_canvas_renderer", lambda canvas: None)
    manager2._on_draw(DrawEvent("draw_event", fig2.canvas, fig2.canvas.get_renderer()))

    cns.figure(120, 120)
    fig3 = plt.gcf()
    ax3 = fig3.add_subplot(121)
    fig3.add_subplot(122)
    ax3.plot([0, 1], [0, 1])
    fig3.canvas.draw()
    assert (
        fig3._cnsplots_autofit_manager._tighten_single_axes_horizontal_layout(
            fig3.canvas.get_renderer()
        )
        is False
    )

    zero_size_manager = object.__new__(_utils._FigureAutofitManager)
    zero_size_manager.fig = types.SimpleNamespace(
        bbox=mtransforms.Bbox.from_bounds(0, 0, 0, 0)
    )
    zero_size_manager._grow_canvas(1, 1, 1, 1)
    assert zero_size_manager._resize_canvas(-1, -1, -1, -1) is False

    collapsed_manager = object.__new__(_utils._FigureAutofitManager)
    collapsed_manager.fig = types.SimpleNamespace(
        bbox=mtransforms.Bbox.from_bounds(0, 0, 10, 10),
        dpi=100,
        get_axes=lambda: [],
        set_size_inches=lambda *args, **kwargs: None,
    )
    assert collapsed_manager._resize_canvas(-11, 0, 0, 0) is False


def test_figure_autofit_tighten_single_axes_helper_branches() -> None:
    class DummyArtist:
        def __init__(self, visible: bool = True) -> None:
            self._visible = visible

        def get_visible(self) -> bool:
            return self._visible

    class DummyTitle:
        def __init__(self, text: str = "") -> None:
            self._text = text
            self._x = 0.5

        def get_text(self) -> str:
            return self._text

        def get_position(self) -> tuple[float, float]:
            return self._x, 0.0

        def set_x(self, value: float) -> None:
            self._x = value

    class DummyAxes:
        def __init__(
            self,
            *,
            position: tuple[float, float, float, float] = (0.2, 0.1, 0.5, 0.5),
            extents: list[mtransforms.Bbox] | None = None,
            left_title: str = "",
            right_title: str = "",
        ) -> None:
            self._position = list(position)
            self._extents = list(
                extents or [mtransforms.Bbox.from_bounds(20, 20, 50, 40)]
            )
            self.title = DummyTitle("Center")
            self._left_title = DummyTitle(left_title)
            self._right_title = DummyTitle(right_title)

        def get_window_extent(
            self,
            renderer: object | None = None,
        ) -> mtransforms.Bbox:
            if len(self._extents) > 1:
                return self._extents.pop(0)
            return self._extents[0]

        def get_position(self) -> mtransforms.Bbox:
            return mtransforms.Bbox.from_bounds(*self._position)

        def set_position(self, position: list[float]) -> None:
            self._position = list(position)

    manager = object.__new__(_utils._FigureAutofitManager)
    renderer = cast(Any, object())

    invisible_ax = DummyAxes()
    manager.fig = types.SimpleNamespace(
        bbox=mtransforms.Bbox.from_bounds(0, 0, 100, 100),
        get_axes=lambda: [invisible_ax],
    )
    manager._iter_axes_non_title_artists = lambda ax: iter([DummyArtist(False)])
    manager._get_artist_bbox = lambda artist, renderer: mtransforms.Bbox.from_bounds(
        5, 5, 10, 10
    )
    assert manager._tighten_single_axes_horizontal_layout(renderer) is False

    zero_width_ax = DummyAxes(extents=[mtransforms.Bbox.from_bounds(20, 20, 0, 40)])
    manager.fig = types.SimpleNamespace(
        bbox=mtransforms.Bbox.from_bounds(0, 0, 100, 100),
        get_axes=lambda: [zero_width_ax],
    )
    manager._iter_axes_non_title_artists = lambda ax: iter([DummyArtist()])
    manager._get_artist_bbox = lambda artist, renderer: mtransforms.Bbox.from_bounds(
        5, 5, 10, 10
    )
    assert manager._tighten_single_axes_horizontal_layout(renderer) is False

    clamped_ax = DummyAxes(position=(0.001, 0.1, 0.5, 0.5))
    manager.fig = types.SimpleNamespace(
        bbox=mtransforms.Bbox.from_bounds(0, 0, 100, 100),
        get_axes=lambda: [clamped_ax],
    )
    manager._iter_axes_non_title_artists = lambda ax: iter([DummyArtist()])
    manager._get_artist_bbox = lambda artist, renderer: mtransforms.Bbox.from_bounds(
        5, 5, 10, 10
    )
    assert manager._tighten_single_axes_horizontal_layout(renderer) is False

    updated_zero_ax = DummyAxes(
        extents=[
            mtransforms.Bbox.from_bounds(20, 20, 50, 40),
            mtransforms.Bbox.from_bounds(20, 20, 0, 40),
        ]
    )
    manager.fig = types.SimpleNamespace(
        bbox=mtransforms.Bbox.from_bounds(0, 0, 100, 100),
        get_axes=lambda: [updated_zero_ax],
    )
    manager._iter_axes_non_title_artists = lambda ax: iter([DummyArtist()])
    manager._get_artist_bbox = lambda artist, renderer: mtransforms.Bbox.from_bounds(
        5, 5, 10, 10
    )
    assert manager._tighten_single_axes_horizontal_layout(renderer) is True

    titled_ax = DummyAxes(left_title="Left", right_title="Right")
    manager.fig = types.SimpleNamespace(
        bbox=mtransforms.Bbox.from_bounds(0, 0, 100, 100),
        get_axes=lambda: [titled_ax],
    )
    manager._iter_axes_non_title_artists = lambda ax: iter([DummyArtist()])
    manager._get_artist_bbox = lambda artist, renderer: mtransforms.Bbox.from_bounds(
        5, 5, 10, 10
    )
    assert manager._tighten_single_axes_horizontal_layout(renderer) is True
    assert titled_ax._left_title.get_position()[0] > 0.5
    assert titled_ax._right_title.get_position()[0] > 0.5


def test_figure_autofit_iter_axes_non_title_artists_counts_axis_off_patch() -> None:
    cns.figure(120, 120)
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_axis_off()

    artists = list(fig._cnsplots_autofit_manager._iter_axes_non_title_artists(ax))

    assert ax.patch in artists


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
        panel_pad_left=14,
        panel_pad_top=5,
        panel_margin_top=7,
        panel_margin_bottom=9,
        panel_margin_left=6,
        panel_margin_right=8,
        panel_label_fontname="DejaVu Sans",
        panel_label_fontweight="normal",
    ):
        mp = cns.multipanel(title="Overview")
        ax = mp.panel()
        panel = mp._panels[0]

        assert mp._max_width == 180
        assert mp.fig.dpi == 160
        assert mp._title_text is not None
        assert mp._title_text.get_ha() == "left"
        assert ax.get_position().width == pytest.approx(70 / 180)
        ax.yaxis.set_visible(False)
        assert panel["width"] == 70
        assert panel["height"] == 50
        assert panel["pad_left"] == 14
        assert panel["pad_top"] == 5
        label_text = mp._label_texts["A"]
        label_pad_left, label_pad_top = _panel_label_padding(ax, label_text)
        assert label_pad_left == pytest.approx(14, abs=0.5)
        assert label_pad_top == pytest.approx(5, abs=0.5)
        assert label_text.get_fontproperties().get_name() == "DejaVu Sans"
        assert label_text.get_fontweight() == "normal"
        assert label_text.get_ha() == "right"
        assert label_text.get_va() == "bottom"


def test_multipanel_pad_left_matches_rendered_left_gap() -> None:
    mp = cns.multipanel(max_width=240)
    ax = mp.panel(
        "A",
        width=80,
        height=60,
        pad_left=18,
        pad_top=4,
        margin_left=0,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
    )
    ax.plot([0, 1], [0, 10])
    ax.set_ylabel("Expression")
    ax.set_yticks([0, 5, 10])

    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    label_text = mp._label_texts["A"]
    gap = _panel_label_left_gap(ax, label_text)
    assert gap == pytest.approx(18, abs=0.6)
    assert label_text.get_window_extent(renderer=renderer).x0 >= -0.8


def test_multipanel_pad_left_delta_updates_rendered_gap() -> None:
    mp = cns.multipanel(max_width=420)
    ax_a = mp.panel(
        "A",
        width=80,
        height=60,
        pad_left=8,
        pad_top=4,
        margin_left=0,
        margin_top=0,
        margin_right=10,
        margin_bottom=0,
    )
    ax_b = mp.panel(
        "B",
        width=80,
        height=60,
        pad_left=28,
        pad_top=4,
        margin_left=0,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
    )
    for ax in (ax_a, ax_b):
        ax.plot([0, 1], [0, 10])
        ax.set_ylabel("Expression")
        ax.set_yticks([0, 5, 10])

    gap_a = _panel_label_left_gap(ax_a, mp._label_texts["A"])
    gap_b = _panel_label_left_gap(ax_b, mp._label_texts["B"])

    assert gap_a == pytest.approx(8, abs=0.6)
    assert gap_b == pytest.approx(28, abs=0.6)
    assert gap_b - gap_a == pytest.approx(20, abs=0.8)


def test_multipanel_pad_top_matches_rendered_title_gap() -> None:
    mp = cns.multipanel(max_width=240)
    ax = mp.panel(
        "A",
        width=80,
        height=60,
        pad_left=0,
        pad_top=12,
        margin_left=0,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
    )
    ax.plot([0, 1], [0, 10])
    ax.set_title("Barplot")

    gap = _panel_label_title_gap(ax, mp._label_texts["A"])
    assert gap == pytest.approx(12, abs=0.8)


def test_multipanel_pad_top_delta_updates_rendered_title_gap() -> None:
    mp = cns.multipanel(max_width=420)
    ax_a = mp.panel(
        "A",
        width=80,
        height=60,
        pad_left=0,
        pad_top=4,
        margin_left=0,
        margin_top=0,
        margin_right=10,
        margin_bottom=0,
    )
    ax_b = mp.panel(
        "B",
        width=80,
        height=60,
        pad_left=0,
        pad_top=18,
        margin_left=0,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
    )
    for ax in (ax_a, ax_b):
        ax.plot([0, 1], [0, 10])
        ax.set_title("Barplot")

    gap_a = _panel_label_title_gap(ax_a, mp._label_texts["A"])
    gap_b = _panel_label_title_gap(ax_b, mp._label_texts["B"])

    assert gap_a == pytest.approx(4, abs=0.8)
    assert gap_b == pytest.approx(18, abs=0.8)
    assert gap_b - gap_a == pytest.approx(14, abs=1.0)


def test_multipanel_pad_top_matches_topmost_panel_content_gap() -> None:
    tips = sns.load_dataset("tips")
    mp = cns.multipanel(max_width=240)
    ax = mp.panel(
        "A",
        width=100,
        height=70,
        pad_left=0,
        pad_top=10,
        margin_left=0,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
    )
    cns.stripplot(data=tips, x="day", y="tip", hue="sex", ax=ax)
    legend = ax.get_legend()
    assert legend is not None
    ax.legend(
        handles=legend.legend_handles,
        labels=[text.get_text() for text in legend.get_texts()],
        title=legend.get_title().get_text(),
        loc="upper left",
        bbox_to_anchor=(-0.02, 1.0),
        borderaxespad=0,
        markerscale=1,
    )
    ax.set_title("Stripplot")

    gap = _panel_label_top_gap(ax, mp._label_texts["A"])
    assert gap == pytest.approx(10, abs=1.0)


def test_multipanel_pad_top_matches_image_title_gap_with_axis_off() -> None:
    mp = cns.multipanel(max_width=260)
    ax = mp.panel(
        "A",
        width=90,
        height=60,
        pad_left=0,
        pad_top=10,
        margin_left=0,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
    )
    ax.imshow(np.zeros((8, 8, 3)))
    ax.set_title("Pathology Image")
    ax.set_axis_off()

    gap = _panel_label_title_gap(ax, mp._label_texts["A"])
    assert gap == pytest.approx(10, abs=0.8)


def test_multipanel_recreates_panel_label_after_axes_clear(
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True)
    output_path = output_dir / "placeholder_panel.png"
    mp = cns.multipanel(max_width=240)
    ax = mp.panel(
        "A",
        width=100,
        height=100,
        pad_left=0,
        pad_top=8,
        margin_left=0,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
    )
    cns.placeholderplot("Placeholder")
    ax.set_title("?")

    mp.fig.savefig(output_path, dpi=300)

    assert output_path.exists()
    label_text = mp._label_texts["A"]
    assert label_text.figure is mp.fig
    assert _panel_label_title_gap(ax, label_text) == pytest.approx(8, abs=1.0)


def test_multipanel_top_row_label_stays_visible() -> None:
    mp = cns.multipanel(max_width=240, title="Figure 1")
    ax = mp.panel(
        "A",
        width=80,
        height=60,
        pad_left=0,
        pad_top=0,
        margin_left=0,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
    )
    ax.plot([0, 1], [0, 10])
    ax.set_ylabel("Expression")

    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    fig_bbox = ax.figure.bbox
    label_bbox = mp._label_texts["A"].get_window_extent(renderer=renderer)

    assert label_bbox.y1 <= fig_bbox.y1 + 0.8


def test_multipanel_update_preserves_existing_figure_dpi() -> None:
    mp = cns.multipanel(max_width=200, title="Figure 1")
    ax = mp.panel("A", width=80, height=60)
    ax.plot([0, 1], [0, 1])
    ax.set_title("Plot")

    mp.fig.set_dpi(300)
    mp._create_or_update_figure()

    assert mp.fig.dpi == pytest.approx(300)


def test_multipanel_high_dpi_save_keeps_top_content_in_bounds(
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True)
    output_path = output_dir / "multipanel_high_dpi.png"
    mp = cns.multipanel(max_width=220, title="Figure 1", loc="left")
    ax = mp.panel(
        "A",
        width=80,
        height=60,
        pad_left=12,
        pad_top=10,
        margin_left=0,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
    )
    ax.plot([0, 1], [0, 1], color="black")
    ax.set_title("Plot")

    captures: list[tuple[object, object, object]] = []

    def on_draw(event: object) -> None:
        renderer = event.renderer
        captures.append(
            (
                mp.fig.bbox.frozen(),
                mp._label_texts["A"].get_window_extent(renderer=renderer).frozen(),
                mp._title_text.get_window_extent(renderer=renderer).frozen(),
            )
        )

    cid = mp.fig.canvas.mpl_connect("draw_event", on_draw)
    try:
        mp.fig.savefig(output_path, dpi=300)
    finally:
        mp.fig.canvas.mpl_disconnect(cid)

    assert output_path.exists()
    assert captures
    fig_bbox, label_bbox, title_bbox = captures[-1]
    assert _bbox_is_within(fig_bbox, label_bbox)
    assert _bbox_is_within(fig_bbox, title_bbox)


def test_multipanel_margin_args_inherit_settings_defaults() -> None:
    with cns.settings.context(
        panel_margin_top=7,
        panel_margin_bottom=9,
        panel_margin_left=6,
        panel_margin_right=8,
    ):
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


def test_multipanel_artist_bbox_and_top_artist_helpers() -> None:
    mp = cns.multipanel(max_width=240)
    ax = mp.panel(
        "A",
        width=80,
        height=60,
        pad_left=0,
        pad_top=0,
        margin_left=0,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
    )
    label_text = mp._label_texts["A"]
    extra_text = ax.text(0.5, 1.15, "extra", transform=ax.transAxes)
    unclipped_line = ax.plot(
        [0, 1],
        [1.05, 1.05],
        transform=ax.transAxes,
        clip_on=False,
    )[0]

    artists = list(mp._iter_top_decoration_artists(ax, label_text))
    assert extra_text in artists
    assert unclipped_line in artists
    assert label_text not in artists

    class WindowExtentOnlyArtist:
        def get_window_extent(self) -> mtransforms.Bbox:
            return mtransforms.Bbox.from_bounds(1, 2, 3, 4)

    bbox = mp._get_artist_bbox(WindowExtentOnlyArtist(), cast(Any, None))
    assert bbox is not None
    assert bbox.bounds == pytest.approx((1, 2, 3, 4))
    assert mp._get_artist_bbox(object(), cast(Any, None)) is None


def test_multipanel_measure_top_decoration_skips_missing_bbox(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mp = cns.multipanel(max_width=240)
    ax = mp.panel("A", width=80, height=60)
    label_text = mp._label_texts["A"]
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()

    class DummyArtist:
        def get_visible(self) -> bool:
            return True

    monkeypatch.setattr(
        mp,
        "_iter_top_decoration_artists",
        lambda ax, label_text: iter([DummyArtist()]),
    )
    monkeypatch.setattr(mp, "_get_artist_bbox", lambda artist, renderer: None)

    assert mp._measure_top_decoration_height_px(ax, label_text, renderer) == 0


def test_multipanel_update_left_layout_metrics_skips_missing_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mp = cns.multipanel(max_width=240)
    mp.panel("A", width=80, height=60)
    mp._panels.append({"_is_spacer": True})
    mp._panels.append({"label": "B"})
    mp._label_texts.pop("A")

    monkeypatch.setattr(
        mp,
        "_measure_left_decoration_width_px",
        lambda ax, renderer: 5.0,
    )

    assert mp._update_left_layout_metrics(cast(Any, object())) is True
    assert mp._panels[0]["left_decoration_width_px"] == pytest.approx(5.0)


def test_multipanel_panel_rejects_margin_tuple_argument() -> None:
    mp = cns.multipanel(max_width=150)

    with pytest.raises(TypeError, match="unexpected keyword argument 'margin'"):
        mp.panel("A", width=60, height=40, margin=(0, 0, 10, 10))  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="unexpected keyword argument 'label_left'"):
        mp.panel("A", width=60, height=40, label_left=10)  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="unexpected keyword argument 'label_top'"):
        mp.panel("A", width=60, height=40, label_top=12)  # type: ignore[call-arg]


def test_multipanel_linked_helper_capture_guard_without_figure() -> None:
    mp = cns.multipanel(max_width=240)

    mp._refresh_known_figure_axes_ids()

    assert mp._capture_linked_helper_axes() is False


def test_multipanel_linked_helper_discovery_guard_branches() -> None:
    mp = cns.multipanel(max_width=240)
    host_ax = mp.panel("A", width=80, height=60)
    panel = mp._panels[0]
    artist = cast(Any, host_ax.scatter([1.0], [1.0], c=[0.1]))

    artist.colorbar = types.SimpleNamespace(ax=host_ax)
    assert list(mp._iter_linked_helper_axes(host_ax, panel)) == []

    other_fig = plt.figure()
    try:
        other_ax = other_fig.add_axes((0.1, 0.2, 0.2, 0.3))
        artist.colorbar = types.SimpleNamespace(ax=other_ax)
        assert list(mp._iter_linked_helper_axes(host_ax, panel)) == []
    finally:
        plt.close(other_fig)

    helper_ax = mp.fig.add_axes((0.8, 0.2, 0.05, 0.5))
    setattr(helper_ax, "_colorbar_info", {"parents": []})
    artist.colorbar = types.SimpleNamespace(ax=helper_ax)
    assert list(mp._iter_linked_helper_axes(host_ax, panel)) == []


def test_multipanel_linked_helper_discovery_skips_known_and_duplicate_axes() -> None:
    mp = cns.multipanel(max_width=240)
    host_ax = mp.panel("A", width=80, height=60)
    panel = mp._panels[0]
    artist_a = cast(Any, host_ax.scatter([1.0], [1.0], c=[0.1]))
    artist_b = cast(Any, host_ax.scatter([2.0], [2.0], c=[0.2]))
    helper_ax = mp.fig.add_axes((0.8, 0.2, 0.05, 0.5))
    setattr(helper_ax, "_colorbar_info", {"parents": [host_ax]})

    artist_a.colorbar = types.SimpleNamespace(ax=helper_ax)
    panel["known_figure_axes_ids"] = {id(host_ax), id(helper_ax)}
    assert list(mp._iter_linked_helper_axes(host_ax, panel)) == []

    artist_b.colorbar = types.SimpleNamespace(ax=helper_ax)
    panel["known_figure_axes_ids"] = {id(host_ax)}
    assert list(mp._iter_linked_helper_axes(host_ax, panel)) == [helper_ax]


def test_multipanel_helper_snapshot_skips_foreign_axes() -> None:
    mp = cns.multipanel(max_width=240)
    mp.panel("A", width=80, height=60)
    panel = mp._panels[0]
    panel.pop("known_figure_axes_ids", None)
    original_ax = mp._created_axes["A"]

    other_fig = plt.figure()
    try:
        foreign_ax = other_fig.add_axes((0.1, 0.2, 0.2, 0.3))
        mp._created_axes["A"] = foreign_ax

        mp._refresh_known_figure_axes_ids()

        assert "known_figure_axes_ids" not in panel
        assert mp._capture_linked_helper_axes() is False
    finally:
        mp._created_axes["A"] = original_ax
        plt.close(other_fig)


def test_multipanel_draw_helpers_handle_guard_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mp = cns.multipanel(max_width=240)
    ax = mp.panel("A", width=80, height=60)
    renderer = ax.figure.canvas.get_renderer()

    assert mp._get_canvas_renderer(types.SimpleNamespace(get_renderer=None)) is None

    mp._on_draw(Event("resize_event", mp.fig.canvas))

    other_fig = plt.figure()
    try:
        other_renderer = other_fig.canvas.get_renderer()
        mp._on_draw(DrawEvent("draw_event", other_fig.canvas, other_renderer))
    finally:
        plt.close(other_fig)

    created = {"count": 0}
    drawn = {"count": 0}

    monkeypatch.setattr(
        mp,
        "_update_left_layout_metrics",
        lambda renderer: True,
    )
    monkeypatch.setattr(
        mp,
        "_create_or_update_figure",
        lambda: created.__setitem__("count", created["count"] + 1),
    )
    monkeypatch.setattr(
        mp.fig.canvas,
        "draw",
        lambda: drawn.__setitem__("count", drawn["count"] + 1),
    )
    monkeypatch.setattr(mp, "_get_canvas_renderer", lambda canvas: None)

    mp._on_draw(DrawEvent("draw_event", mp.fig.canvas, renderer))

    assert created["count"] == 1
    assert drawn["count"] == 1
    assert mp._is_relayout_in_draw is False


@pytest.mark.parametrize("loc", ["left", "center", "right"])
def test_multipanel_title_alignment_and_default_fontweight(loc: str) -> None:
    mp = cns.multipanel(max_width=200, title="Overview", loc=loc)
    mp.panel("A", width=60, height=40)
    left_bound_px, right_bound_px = mp._get_content_horizontal_bounds_px()
    expected_x = {
        "left": left_bound_px / 200,
        "center": (left_bound_px + right_bound_px) / 2 / 200,
        "right": right_bound_px / 200,
    }[loc]

    assert mp._title_text is not None
    assert mp._title_text.get_text() == "Overview"
    assert mp._title_text.get_ha() == loc
    assert mp._title_text.get_fontweight() == "bold"
    assert mp._title_text.get_position()[0] == pytest.approx(expected_x)
    assert mp._label_texts["A"].get_ha() == "right"
    assert mp._label_texts["A"].get_va() == "bottom"


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
    _, right_bound_px = mp._get_content_horizontal_bounds_px()

    assert mp._title_text is original_title_text
    assert mp._title_text.get_text() == "Updated Overview"
    assert mp._title_text.get_ha() == "right"
    assert mp._title_text.get_va() == "center"
    assert mp._title_text.get_fontweight() == "normal"
    assert mp._title_text.get_position()[0] == pytest.approx(right_bound_px / 200)
    assert mp._label_texts["A"].get_ha() == "right"
    assert mp._label_texts["A"].get_va() == "bottom"


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
        pad_left=0,
        pad_top=0,
        margin_left=10,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
        below="B",
    )

    assert mp._get_panel_position(0)[0] == mp._get_panel_position(1)[0]


def test_multipanel_below_aligns_to_parent_column_after_left_relayout() -> None:
    mp = cns.multipanel(max_width=540)
    ax_b = mp.panel(
        "B",
        width=145,
        height=128,
        pad_left=12,
        pad_top=0,
        margin_left=10,
        margin_top=0,
        margin_right=0,
        margin_bottom=10,
    )
    ax_c = mp.panel(
        "C",
        width=145,
        height=128,
        pad_left=18,
        pad_top=0,
        margin_left=10,
        margin_top=0,
        margin_right=0,
        margin_bottom=0,
        below="B",
    )
    ax_b.plot([0, 1], [0, 1000])
    ax_c.plot([0, 1], [0, 10])
    ax_b.set_ylabel("Parent")
    ax_c.set_ylabel("Child")
    ax_b.set_yticks([0, 500, 1000])
    ax_c.set_yticks([0, 5, 10])

    assert _panel_column_origin(mp, 0) == pytest.approx(
        _panel_column_origin(mp, 1),
        abs=0.8,
    )
