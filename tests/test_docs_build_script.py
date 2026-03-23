from __future__ import annotations

import importlib.util
from contextlib import contextmanager
from pathlib import Path


def _load_docs_build_script():
    script_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "_scripts"
        / "build_versioned_docs.py"
    )
    spec = importlib.util.spec_from_file_location("docs_build_script", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_build_bootstraps_when_gh_pages_branch_is_missing(tmp_path, monkeypatch):
    docs_build = _load_docs_build_script()
    bootstrap_calls = []

    monkeypatch.setattr(docs_build, "_fetch_remote_branch", lambda branch_name: None)
    monkeypatch.setattr(
        docs_build,
        "_build_bootstrap_site",
        lambda output_dir, latest_release_tag: bootstrap_calls.append(
            (output_dir, latest_release_tag)
        ),
    )

    output_dir = tmp_path / "site"
    docs_build._build_main_site(output_dir, "v0.1.0")

    assert bootstrap_calls == [(output_dir, "v0.1.0")]


def test_main_build_bootstraps_when_latest_alias_is_missing(tmp_path, monkeypatch):
    docs_build = _load_docs_build_script()
    published_site = tmp_path / "published"
    (published_site / "v0.1.0").mkdir(parents=True)
    bootstrap_calls = []

    monkeypatch.setattr(
        docs_build, "_fetch_remote_branch", lambda branch_name: "origin/gh-pages"
    )

    @contextmanager
    def fake_worktree(ref):
        assert ref == "origin/gh-pages"
        yield published_site

    monkeypatch.setattr(docs_build, "_temporary_worktree", fake_worktree)
    monkeypatch.setattr(
        docs_build,
        "_dump_multiversion_metadata",
        lambda output_dir, latest_release_tag: {
            "dev": {"name": "dev", "outputdir": "unused"},
            "v0.1.0": {"name": "v0.1.0", "outputdir": "unused"},
        },
    )
    monkeypatch.setattr(
        docs_build,
        "_build_bootstrap_site",
        lambda output_dir, latest_release_tag: bootstrap_calls.append(
            (output_dir, latest_release_tag)
        ),
    )

    output_dir = tmp_path / "site"
    docs_build._build_main_site(output_dir, "v0.1.0")

    assert bootstrap_calls == [(output_dir, "v0.1.0")]


def test_main_build_preserves_release_directories(tmp_path, monkeypatch):
    docs_build = _load_docs_build_script()
    published_site = tmp_path / "published"
    for version_name in ("latest", "v0.1.0", "v0.0.4"):
        version_dir = published_site / version_name
        version_dir.mkdir(parents=True)
        (version_dir / "index.html").write_text(
            f"<html>{version_name}</html>", encoding="utf-8"
        )
        (version_dir / "sitemap.xml").write_text("<xml />", encoding="utf-8")

    metadata = {
        "dev": {
            "name": "dev",
            "outputdir": "unused",
            "confdir": str(tmp_path / "temp-dev-docs"),
            "docnames": ["index"],
        },
        "v0.1.0": {
            "name": "v0.1.0",
            "outputdir": "unused",
            "confdir": str(tmp_path / "temp-v010-docs"),
            "docnames": ["index"],
        },
        "v0.0.4": {
            "name": "v0.0.4",
            "outputdir": "unused",
            "confdir": str(tmp_path / "temp-v004-docs"),
            "docnames": ["index"],
        },
    }
    build_calls = {}

    monkeypatch.setattr(
        docs_build, "_fetch_remote_branch", lambda branch_name: "origin/gh-pages"
    )

    @contextmanager
    def fake_worktree(ref):
        assert ref == "origin/gh-pages"
        yield published_site

    monkeypatch.setattr(docs_build, "_temporary_worktree", fake_worktree)
    monkeypatch.setattr(
        docs_build,
        "_dump_multiversion_metadata",
        lambda output_dir, latest_release_tag: metadata,
    )

    def fake_build_single_version_docs(
        version_name, version_output_dir, version_metadata, latest_release_tag
    ):
        build_calls["version_name"] = version_name
        build_calls["metadata_names"] = set(version_metadata)
        build_calls["dev_confdir"] = version_metadata["dev"]["confdir"]
        build_calls["release_confdir"] = version_metadata["v0.1.0"]["confdir"]
        build_calls["latest_release_tag"] = latest_release_tag
        version_output_dir.mkdir(parents=True)
        (version_output_dir / "index.html").write_text(
            "<html>dev</html>", encoding="utf-8"
        )
        (version_output_dir / "sitemap.xml").write_text("<xml />", encoding="utf-8")

    monkeypatch.setattr(
        docs_build, "_build_single_version_docs", fake_build_single_version_docs
    )

    output_dir = tmp_path / "site"
    docs_build._build_main_site(output_dir, "v0.1.0")

    assert build_calls == {
        "version_name": "dev",
        "metadata_names": {"dev", "v0.1.0", "v0.0.4"},
        "dev_confdir": str(docs_build.DOCS_DIR.resolve()),
        "release_confdir": str(tmp_path / "temp-v010-docs"),
        "latest_release_tag": "v0.1.0",
    }
    assert (output_dir / "latest" / "index.html").read_text(encoding="utf-8") == (
        "<html>latest</html>"
    )
    assert (output_dir / "v0.1.0" / "index.html").read_text(encoding="utf-8") == (
        "<html>v0.1.0</html>"
    )
    assert (output_dir / "v0.0.4" / "index.html").read_text(encoding="utf-8") == (
        "<html>v0.0.4</html>"
    )
    assert (output_dir / "dev" / "index.html").read_text(encoding="utf-8") == (
        "<html>dev</html>"
    )
    assert "latest/" in (output_dir / "index.html").read_text(encoding="utf-8")
    assert not (output_dir / "installation.html").exists()
    assert not (output_dir / "api.html").exists()
    assert not (output_dir / "examples").exists()
    assert not (output_dir / "api").exists()
    assert (output_dir / "CNAME").read_text(encoding="utf-8").strip() == (
        "cnsplots.farid.one"
    )
    assert (output_dir / ".nojekyll").exists()

    sitemap = (output_dir / "sitemap.xml").read_text(encoding="utf-8")
    assert "/latest/sitemap.xml" in sitemap
    assert "/dev/sitemap.xml" in sitemap
    assert "/v0.1.0/sitemap.xml" in sitemap
    assert "/v0.0.4/sitemap.xml" in sitemap


def test_root_404_matches_latest_docs_ui(tmp_path):
    docs_build = _load_docs_build_script()

    output_dir = tmp_path / "site"
    docs_build._write_root_404(output_dir)

    content = (output_dir / "404.html").read_text(encoding="utf-8")

    assert "<title>Page not found | cnsplots</title>" in content
    assert 'href="/"' in content
    assert 'href="/latest/_static/styles/furo.css"' in content
    assert 'href="/latest/_static/css/override.css"' in content
    assert 'class="sidebar-drawer"' in content
    assert 'class="sidebar-brand"' in content
    assert 'src="/latest/_static/logo.svg"' in content
    assert "Go to homepage" in content
    assert '<form class="sidebar-search-container"' not in content
    assert '<div class="sidebar-tree">' not in content
    assert "search.html" not in content
    assert "/latest/getting_started.html" not in content
    assert "/latest/examples/index.html" not in content
    assert "/latest/api.html" not in content
    assert "/latest/_static/images/overview.png" not in content
