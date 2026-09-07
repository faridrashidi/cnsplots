"""Tests for the cache used to register the macOS Helvetica bold face."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import fontTools.ttLib
import pytest

from cnsplots import _setup


@pytest.fixture
def font_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Mock, Mock]:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    monkeypatch.setattr(_setup, "_HELVETICA_BOLD_REGISTERED", False)
    monkeypatch.setattr(_setup.sys, "platform", "darwin")
    real_exists = Path.exists
    monkeypatch.setattr(
        Path,
        "exists",
        lambda path: (
            path == Path("/System/Library/Fonts/Helvetica.ttc") or real_exists(path)
        ),
    )

    manager = Mock(ttflist=[])
    manager.addfont.side_effect = lambda path: manager.ttflist.append(
        SimpleNamespace(name="Helvetica", weight=700)
    )
    monkeypatch.setattr(_setup.fm, "fontManager", manager)
    face = MagicMock()
    face["name"].getDebugName.side_effect = ["Helvetica", "Bold"]
    face.save.side_effect = lambda path: Path(path).write_bytes(b"cached bold font")
    collection = Mock(return_value=Mock(fonts=[face]))
    monkeypatch.setattr(fontTools.ttLib, "TTCollection", collection)
    return collection, manager


def test_helvetica_extraction_uses_configured_cache_only(
    font_cache: tuple[Mock, Mock], tmp_path: Path
) -> None:
    collection, manager = font_cache

    _setup._ensure_helvetica_bold()

    font_path = tmp_path / "cache/cnsplots/fonts/Helvetica-Bold.ttf"
    assert font_path.read_bytes() == b"cached bold font"
    assert list(tmp_path.iterdir()) == [tmp_path / "cache"]
    collection.assert_called_once_with(str(Path("/System/Library/Fonts/Helvetica.ttc")))
    manager.addfont.assert_called_once_with(str(font_path))
    assert _setup._HELVETICA_BOLD_REGISTERED

    _setup._ensure_helvetica_bold()
    manager.addfont.assert_called_once()


@pytest.mark.parametrize("cache_home", [None, "", "relative/cache"])
def test_helvetica_default_cache(
    font_cache: tuple[Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    cache_home: str | None,
) -> None:
    if cache_home is None:
        monkeypatch.delenv("XDG_CACHE_HOME")
    else:
        monkeypatch.setenv("XDG_CACHE_HOME", cache_home)

    _setup._ensure_helvetica_bold()

    font_path = tmp_path / "home/.cache/cnsplots/fonts/Helvetica-Bold.ttf"
    assert font_path.read_bytes() == b"cached bold font"
    assert list(tmp_path.iterdir()) == [tmp_path / "home"]
    font_cache[1].addfont.assert_called_once_with(str(font_path))


def test_helvetica_reuses_cached_font_without_writing(
    font_cache: tuple[Mock, Mock], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    font_path = tmp_path / "cache/cnsplots/fonts/Helvetica-Bold.ttf"
    font_path.parent.mkdir(parents=True)
    font_path.write_bytes(b"existing font")
    mkdir = Mock(side_effect=PermissionError("read-only cache"))
    monkeypatch.setattr(Path, "mkdir", mkdir)

    _setup._ensure_helvetica_bold()

    mkdir.assert_not_called()
    font_cache[0].assert_not_called()
    font_cache[1].addfont.assert_called_once_with(str(font_path))
    assert font_path.read_bytes() == b"existing font"
    assert _setup._HELVETICA_BOLD_REGISTERED


@pytest.mark.parametrize("failure", ["unavailable", "mkdir", "save"])
def test_helvetica_unwritable_cache_does_not_fall_back(
    font_cache: tuple[Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: str,
) -> None:
    if failure == "unavailable":
        (tmp_path / "cache").write_text("not a directory")
    elif failure == "mkdir":
        monkeypatch.setattr(
            Path, "mkdir", Mock(side_effect=PermissionError("read-only cache"))
        )
    else:
        font_cache[0].return_value.fonts[0].save.side_effect = PermissionError(
            "read-only font directory"
        )

    _setup._ensure_helvetica_bold()

    font_cache[1].addfont.assert_not_called()
    assert not _setup._HELVETICA_BOLD_REGISTERED
    assert not (tmp_path / "home").exists()
    assert not (tmp_path / "cache/cnsplots/fonts/Helvetica-Bold.ttf").exists()


def test_helvetica_unavailable_home_is_graceful(
    font_cache: tuple[Mock, Mock], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("XDG_CACHE_HOME")
    monkeypatch.setattr(Path, "home", Mock(side_effect=RuntimeError("no home")))

    _setup._ensure_helvetica_bold()

    font_cache[0].assert_not_called()
    font_cache[1].addfont.assert_not_called()
    assert not _setup._HELVETICA_BOLD_REGISTERED
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("platform", ["linux", "win32"])
def test_helvetica_non_macos_does_not_create_cache(
    font_cache: tuple[Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    platform: str,
) -> None:
    monkeypatch.setattr(_setup.sys, "platform", platform)

    _setup._ensure_helvetica_bold()

    font_cache[0].assert_not_called()
    font_cache[1].addfont.assert_not_called()
    assert not list(tmp_path.iterdir())
