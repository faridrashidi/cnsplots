from __future__ import annotations

from collections.abc import Callable
from contextlib import nullcontext

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from matplotlib.rcsetup import cycler

import cnsplots as cns


@pytest.mark.parametrize("configure", [cns.setup_matplotlib, cns.figure])
@pytest.mark.parametrize("custom_style", [False, True])
def test_context_restores_style_and_preserves_artists(
    configure: Callable[[], None], custom_style: bool
) -> None:
    with mpl.rc_context():
        mpl.rcdefaults()
        if custom_style:
            mpl.rcParams.update(
                {
                    "axes.labelsize": 17,
                    "font.family": ["monospace"],
                    "axes.prop_cycle": cycler(color=["red", "blue"]),
                    "image.cmap": "plasma",
                }
            )
        before = mpl.rcParams.copy()
        _, before_ax = plt.subplots()
        overrides = {
            "title_fontsize": 23,
            "font_family": "serif",
            "font_sans_serif": ["DejaVu Sans"],
            "palette_qual": "Set2",
            "palette_seq": "parula",
        }
        previous_settings = {key: getattr(cns.settings, key) for key in overrides}

        with cns.settings.context(**overrides) as settings:
            assert settings is cns.settings
            configure()
            ax = plt.gcf().add_subplot()
            label = ax.set_xlabel("Temporary style")
            (line,) = ax.plot([0, 1], [0, 1])
            color = mpl.rcParams["axes.prop_cycle"].by_key()["color"][0]
            assert color == cns.palettes("Set2")[0]
            assert label.get_fontsize() == 23
            assert label.get_fontfamily() == ["serif"]
            assert mpl.rcParams["font.sans-serif"] == ["DejaVu Sans"]
            assert mpl.rcParams["image.cmap"] == "parula"

        assert mpl.rcParams == before
        assert {
            key: getattr(cns.settings, key) for key in overrides
        } == previous_settings
        _, after_ax = plt.subplots()
        assert (
            after_ax.xaxis.label.get_fontsize() == before_ax.xaxis.label.get_fontsize()
        )
        assert after_ax.xaxis.label.get_fontfamily() == before["font.family"]
        (after_line,) = after_ax.plot([0, 1], [0, 1])
        assert after_line.get_color() == before["axes.prop_cycle"].by_key()["color"][0]
        assert label.get_fontsize() == 23
        assert label.get_fontfamily() == ["serif"]
        assert line.get_color() == color


@pytest.mark.parametrize("raise_error", [False, True])
def test_nested_contexts_restore_each_style(raise_error: bool) -> None:
    with mpl.rc_context():
        before = mpl.rcParams.copy()
        previous_fontsize = cns.settings.title_fontsize
        previous_palette = cns.settings.palette_qual
        with cns.settings.context(title_fontsize=19, palette_qual="Dark2"):
            cns.figure()
            outer = mpl.rcParams.copy()
            with (
                pytest.raises(RuntimeError, match="inner")
                if raise_error
                else nullcontext()
            ):
                with cns.settings.context(title_fontsize=29, palette_qual="Set2"):
                    cns.setup_matplotlib()
                    assert mpl.rcParams["axes.labelsize"] == 29
                    assert mpl.rcParams["axes.prop_cycle"] != outer["axes.prop_cycle"]
                    if raise_error:
                        raise RuntimeError("inner")
            assert mpl.rcParams == outer
            assert cns.settings.title_fontsize == 19
            assert cns.settings.palette_qual == "Dark2"
        assert mpl.rcParams == before
        assert cns.settings.title_fontsize == previous_fontsize
        assert cns.settings.palette_qual == previous_palette


def test_context_restores_style_when_exception_escapes() -> None:
    with mpl.rc_context():
        before = mpl.rcParams.copy()
        previous_fontsize = cns.settings.title_fontsize
        with pytest.raises(RuntimeError, match="plot failed"):
            with cns.settings.context(title_fontsize=23):
                cns.figure()
                raise RuntimeError("plot failed")
        assert mpl.rcParams == before
        assert cns.settings.title_fontsize == previous_fontsize


def test_context_without_overrides_restores_explicit_setup_style() -> None:
    with mpl.rc_context():
        before = mpl.rcParams.copy()
        with cns.settings.context():
            cns.setup_matplotlib(
                title_fontsize=31, color_cycle=["red", "blue"], color_map="plasma"
            )
            assert mpl.rcParams["axes.labelsize"] == 31
            assert mpl.rcParams["axes.prop_cycle"].by_key()["color"] == cns.palettes(
                ["red", "blue"]
            )
            assert mpl.rcParams["image.cmap"] == "plasma"
        assert mpl.rcParams == before
