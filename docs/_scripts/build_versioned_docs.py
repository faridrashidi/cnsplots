from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

SITE_URL = "https://cnsplots.farid.one/"
DEV_DOCS_NAME = "dev"
LATEST_DOCS_NAME = "latest"
GITHUB_PAGES_BRANCH = "gh-pages"
RELEASE_TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
ROBOTS_FILE = DOCS_DIR / "robots.txt"
COMPAT_SITE_DIR = Path(__file__).resolve().parent / "compat"


def _run(*args: str, env: dict[str, str] | None = None, cwd: Path = REPO_ROOT) -> str:
    """Run a command in the repo root and return stripped stdout."""
    return subprocess.check_output(args, cwd=cwd, env=env, text=True).strip()


def _run_checked(
    *args: str, env: dict[str, str] | None = None, cwd: Path = REPO_ROOT
) -> None:
    """Run a command in the repo root and require success."""
    subprocess.run(args, cwd=cwd, env=env, check=True)


def _find_latest_release_tag() -> str:
    """Return the newest release tag that matches vX.Y.Z."""
    tags = _run("git", "tag", "--list", "v*", "--sort=-version:refname").splitlines()
    for tag in tags:
        if RELEASE_TAG_PATTERN.fullmatch(tag):
            return tag
    raise RuntimeError("No release tag matching vX.Y.Z was found.")


def _write_text(path: Path, content: str) -> None:
    """Write UTF-8 text to disk, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _ensure_clean_dir(path: Path) -> None:
    """Replace a directory with an empty copy."""
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _version_sort_key(name: str) -> tuple[int, int, int]:
    """Return a semantic sort key for release tags."""
    match = RELEASE_TAG_PATTERN.fullmatch(name)
    if not match:
        return (-1, -1, -1)
    return tuple(int(part) for part in name[1:].split("."))


def _render_redirect_page(relative_target: str, absolute_target: str) -> str:
    """Render a simple HTML redirect page."""
    escaped_relative = html.escape(relative_target, quote=True)
    escaped_absolute = html.escape(absolute_target, quote=True)
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Redirecting...</title>
    <meta http-equiv="refresh" content="0; url={escaped_relative}">
    <link rel="canonical" href="{escaped_absolute}">
    <script>
      window.location.replace({relative_target!r});
    </script>
  </head>
  <body>
    <p>Redirecting to <a href="{escaped_relative}">the latest release docs</a>.</p>
  </body>
</html>
"""


def _latest_absolute_url(relative_path: str = "") -> str:
    """Return the absolute public URL for the latest docs alias."""
    suffix = f"/{relative_path.lstrip('/')}" if relative_path else ""
    return f"{SITE_URL.rstrip('/')}/{LATEST_DOCS_NAME}{suffix}"


def _rewrite_latest_alias_content(
    content: str, latest_release_tag: str, suffix: str
) -> str:
    """Rewrite copied latest-release files to use the stable /latest public URL."""
    rewritten = content.replace(
        f"{SITE_URL.rstrip('/')}/{latest_release_tag}/",
        _latest_absolute_url("/"),
    )
    if suffix == ".xml":
        rewritten = rewritten.replace(
            f"<loc>{SITE_URL}",
            f"<loc>{_latest_absolute_url('/')}",
        )
    if suffix == ".html":
        rewritten = rewritten.replace(
            f'<span class="docs-version-switcher-current">{latest_release_tag}</span>',
            f'<span class="docs-version-switcher-current">{LATEST_DOCS_NAME}</span>',
        )
        rewritten = re.sub(
            rf'(<option value="[^"]+" selected>){re.escape(latest_release_tag)}(</option>)',
            rf"\1{LATEST_DOCS_NAME}\2",
            rewritten,
        )
    return rewritten


def _write_latest_release_alias(output_dir: Path, latest_release_tag: str) -> None:
    """Copy the newest release docs into the stable /latest alias."""
    latest_release_dir = output_dir / latest_release_tag
    latest_alias_dir = output_dir / LATEST_DOCS_NAME
    if not latest_release_dir.exists():
        raise RuntimeError(
            f"Latest release docs were not built at {latest_release_dir}."
        )

    shutil.copytree(latest_release_dir, latest_alias_dir)
    for path in latest_alias_dir.rglob("*"):
        if not path.is_file() or path.suffix not in {".html", ".xml"}:
            continue
        content = path.read_text(encoding="utf-8")
        rewritten = _rewrite_latest_alias_content(
            content, latest_release_tag, path.suffix
        )
        if rewritten != content:
            path.write_text(rewritten, encoding="utf-8")


def _write_root_redirects(output_dir: Path) -> None:
    """Write only the site-root redirect to the latest stable docs."""
    latest_alias_dir = output_dir / LATEST_DOCS_NAME
    if not latest_alias_dir.exists():
        raise RuntimeError(f"Latest docs alias was not built at {latest_alias_dir}.")

    _write_text(
        output_dir / "index.html",
        _render_redirect_page(f"{LATEST_DOCS_NAME}/", _latest_absolute_url("/")),
    )


def _write_root_404(output_dir: Path) -> None:
    """Write a site-wide 404 page that points users to the latest release."""
    home_target = f"{LATEST_DOCS_NAME}/"
    _write_text(
        output_dir / "404.html",
        f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Page not found</title>
    <meta name="robots" content="noindex, nofollow">
  </head>
  <body>
    <main>
      <h1>Page not found</h1>
      <p>The page you requested does not exist, may have moved, or may have been renamed.</p>
      <p><a href="{html.escape(home_target, quote=True)}">Return to the latest documentation homepage</a>.</p>
    </main>
  </body>
</html>
""",
    )


def _write_root_sitemap_index(output_dir: Path) -> None:
    """Write a sitemap index that points to each published docs version."""
    version_names: list[str] = []
    for path in output_dir.iterdir():
        if not path.is_dir():
            continue
        if path.name in {
            DEV_DOCS_NAME,
            LATEST_DOCS_NAME,
        } or RELEASE_TAG_PATTERN.fullmatch(path.name):
            if (path / "sitemap.xml").exists():
                version_names.append(path.name)

    release_names = sorted(
        (
            name
            for name in version_names
            if name not in {DEV_DOCS_NAME, LATEST_DOCS_NAME}
        ),
        key=_version_sort_key,
        reverse=True,
    )
    version_names = (
        ([LATEST_DOCS_NAME] if LATEST_DOCS_NAME in version_names else [])
        + ([DEV_DOCS_NAME] if DEV_DOCS_NAME in version_names else [])
        + release_names
    )

    sitemap_entries = "\n".join(
        (
            "  <sitemap>\n"
            f"    <loc>{SITE_URL.rstrip('/')}/{name}/sitemap.xml</loc>\n"
            "  </sitemap>"
        )
        for name in version_names
    )
    _write_text(
        output_dir / "sitemap.xml",
        (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{sitemap_entries}\n"
            "</sitemapindex>\n"
        ),
    )


def _write_cname(output_dir: Path) -> None:
    """Write the custom domain used by GitHub Pages when configured."""
    hostname = urlparse(SITE_URL).hostname
    if hostname:
        _write_text(output_dir / "CNAME", f"{hostname}\n")


def _docs_env(latest_release_tag: str) -> dict[str, str]:
    """Return the environment used for docs builds."""
    env = os.environ.copy()
    compat_path = str(COMPAT_SITE_DIR)
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        compat_path
        if not existing_pythonpath
        else f"{compat_path}{os.pathsep}{existing_pythonpath}"
    )
    env["CNSPLOTS_DOCS_LATEST_VERSION"] = latest_release_tag
    return env


def _build_full_versioned_docs(output_dir: Path, latest_release_tag: str) -> None:
    """Build all versioned docs into the output directory."""
    _ensure_clean_dir(output_dir)
    env = _docs_env(latest_release_tag)

    _run_checked("sphinx-multiversion", str(DOCS_DIR), str(output_dir), env=env)


def _finalize_site(output_dir: Path) -> None:
    """Write the top-level files expected by GitHub Pages."""
    if not (output_dir / LATEST_DOCS_NAME).exists():
        raise RuntimeError(
            f"Latest docs alias was not assembled at {output_dir / LATEST_DOCS_NAME}."
        )

    _write_root_redirects(output_dir)
    shutil.copy2(ROBOTS_FILE, output_dir / "robots.txt")
    _write_text(output_dir / ".nojekyll", "")
    _write_cname(output_dir)
    _write_root_404(output_dir)
    _write_root_sitemap_index(output_dir)


def _build_full_site(output_dir: Path, latest_release_tag: str) -> None:
    """Build a complete multiversion site and package it for publishing."""
    _build_full_versioned_docs(output_dir, latest_release_tag)
    _write_latest_release_alias(output_dir, latest_release_tag)
    _finalize_site(output_dir)


def _dump_multiversion_metadata(
    output_dir: Path, latest_release_tag: str
) -> dict[str, dict[str, object]]:
    """Return sphinx-multiversion metadata without building HTML."""
    env = _docs_env(latest_release_tag)
    payload = _run(
        "sphinx-multiversion",
        "--dump-metadata",
        str(DOCS_DIR),
        str(output_dir),
        env=env,
    )
    return json.loads(payload)


def _remote_branch_exists(branch_name: str) -> bool:
    """Return whether the named remote branch exists on origin."""
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", branch_name],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _fetch_remote_branch(branch_name: str) -> str | None:
    """Fetch a remote branch into a local remote-tracking ref."""
    if not _remote_branch_exists(branch_name):
        return None

    remote_ref = f"refs/remotes/origin/{branch_name}"
    _run_checked(
        "git",
        "fetch",
        "--depth=1",
        "origin",
        f"+refs/heads/{branch_name}:{remote_ref}",
    )
    return remote_ref


@contextmanager
def _temporary_worktree(ref: str) -> Iterator[Path]:
    """Check out a detached git ref in a temporary worktree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        worktree_path = Path(tmpdir)
        _run_checked("git", "worktree", "add", "--detach", str(worktree_path), ref)
        try:
            yield worktree_path
        finally:
            _run_checked("git", "worktree", "remove", "--force", str(worktree_path))


def _copy_preserved_versions(existing_site_dir: Path, output_dir: Path) -> list[str]:
    """Copy published release directories and the stable alias into output_dir."""
    release_names: list[str] = []
    for path in existing_site_dir.iterdir():
        if not path.is_dir():
            continue
        if RELEASE_TAG_PATTERN.fullmatch(path.name):
            shutil.copytree(path, output_dir / path.name)
            release_names.append(path.name)

    latest_alias_dir = existing_site_dir / LATEST_DOCS_NAME
    if latest_alias_dir.exists():
        shutil.copytree(latest_alias_dir, output_dir / LATEST_DOCS_NAME)

    return sorted(release_names, key=_version_sort_key)


def _rewrite_metadata_entry(
    entry: dict[str, object], outputdir: Path
) -> dict[str, object]:
    """Return a metadata entry that points to the assembled site tree."""
    rewritten = dict(entry)
    rewritten["outputdir"] = str(outputdir.resolve())
    return rewritten


def _build_metadata_for_main_site(
    all_metadata: dict[str, dict[str, object]],
    output_dir: Path,
    preserved_release_names: list[str],
) -> dict[str, dict[str, object]]:
    """Return metadata for the dev build plus preserved release versions."""
    if DEV_DOCS_NAME not in all_metadata:
        raise RuntimeError("Missing dev metadata for the current main docs build.")

    metadata = {
        DEV_DOCS_NAME: _rewrite_metadata_entry(
            all_metadata[DEV_DOCS_NAME], output_dir / DEV_DOCS_NAME
        )
    }
    for name in preserved_release_names:
        entry = all_metadata.get(name)
        if entry is None:
            continue
        metadata[name] = _rewrite_metadata_entry(entry, output_dir / name)
    return metadata


def _build_single_version_docs(
    version_name: str,
    output_dir: Path,
    metadata: dict[str, dict[str, object]],
    latest_release_tag: str,
) -> None:
    """Build a single docs version using precomputed multiversion metadata."""
    if output_dir.exists():
        shutil.rmtree(output_dir)

    env = _docs_env(latest_release_tag)
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir) / "versions.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        _run_checked(
            sys.executable,
            "-m",
            "sphinx",
            "-D",
            f"smv_metadata_path={metadata_path}",
            "-D",
            f"smv_current_version={version_name}",
            str(DOCS_DIR),
            str(output_dir),
            env=env,
        )


def _build_bootstrap_site(output_dir: Path, latest_release_tag: str) -> None:
    """Build the full site for the initial gh-pages bootstrap."""
    _build_full_site(output_dir, latest_release_tag)


def _build_main_site(output_dir: Path, latest_release_tag: str) -> None:
    """Build only dev docs and preserve published releases from gh-pages."""
    remote_ref = _fetch_remote_branch(GITHUB_PAGES_BRANCH)
    if remote_ref is None:
        _build_bootstrap_site(output_dir, latest_release_tag)
        return

    all_metadata = _dump_multiversion_metadata(output_dir, latest_release_tag)
    if latest_release_tag not in all_metadata:
        raise RuntimeError(
            f"Missing metadata for the latest release tag {latest_release_tag}."
        )

    with _temporary_worktree(remote_ref) as existing_site_dir:
        if (
            not (existing_site_dir / LATEST_DOCS_NAME).exists()
            or not (existing_site_dir / latest_release_tag).exists()
        ):
            _build_bootstrap_site(output_dir, latest_release_tag)
            return

        _ensure_clean_dir(output_dir)
        preserved_release_names = _copy_preserved_versions(
            existing_site_dir, output_dir
        )
        if latest_release_tag not in preserved_release_names:
            _build_bootstrap_site(output_dir, latest_release_tag)
            return

        metadata = _build_metadata_for_main_site(
            all_metadata, output_dir, preserved_release_names
        )
        _build_single_version_docs(
            DEV_DOCS_NAME,
            output_dir / DEV_DOCS_NAME,
            metadata,
            latest_release_tag,
        )

    _finalize_site(output_dir)


def _build_release_site(output_dir: Path, latest_release_tag: str) -> None:
    """Build the full multiversion site for a tagged release."""
    _build_full_site(output_dir, latest_release_tag)


def build(output_dir: Path, mode: str) -> None:
    """Build docs and package them for GitHub Pages."""
    latest_release_tag = _find_latest_release_tag()
    if mode == "bootstrap":
        _build_bootstrap_site(output_dir, latest_release_tag)
        return
    if mode == "main":
        _build_main_site(output_dir, latest_release_tag)
        return
    if mode == "release":
        _build_release_site(output_dir, latest_release_tag)
        return
    raise ValueError(f"Unsupported build mode: {mode}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build versioned Sphinx docs and package them for GitHub Pages."
    )
    parser.add_argument(
        "--mode",
        choices=("bootstrap", "main", "release"),
        default="bootstrap",
        help="Build mode for docs publishing.",
    )
    parser.add_argument(
        "output_dir", type=Path, help="Directory to write the site into."
    )
    args = parser.parse_args()
    build(args.output_dir.resolve(), args.mode)


if __name__ == "__main__":
    main()
