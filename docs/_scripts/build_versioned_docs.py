from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
from string import Template
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


def _latest_site_path(relative_path: str = "") -> str:
    """Return a site-root path for the latest docs alias."""
    suffix = f"/{relative_path.lstrip('/')}" if relative_path else ""
    return f"/{LATEST_DOCS_NAME}{suffix}"


def _render_root_404_page() -> str:
    """Render a branded site-wide 404 page."""
    return Template(
        """<!DOCTYPE html>
<html class="no-js" lang="en">
  <head>
    <meta charset="utf-8">
    <title>Page not found | cnsplots</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="light dark">
    <meta name="description" content="The page you requested could not be found. Return to the latest cnsplots documentation.">
    <meta name="robots" content="noindex, nofollow">
    <meta name="theme-color" content="#003262">
    <link rel="prefetch" href="$logo_src" as="image">
    <link rel="icon" type="image/svg+xml" href="$favicon_src">
    <link rel="stylesheet" type="text/css" href="$furo_css_src">
    <link rel="stylesheet" type="text/css" href="$furo_extensions_css_src">
    <link rel="stylesheet" type="text/css" href="$override_css_src">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="preconnect" href="https://fonts.prefix.dev" crossorigin>
    <link
      rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400;1,500;1,600;1,700&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600;1,700&display=swap"
    >
    <style>
      body {
        --color-code-background: #f2f2f2;
        --color-code-foreground: #1e1e1e;
        --color-brand-primary: #003262;
        --color-brand-content: #003262;
      }

      @media not print {
        body[data-theme="dark"] {
          --color-code-background: #202020;
          --color-code-foreground: #d0d0d0;
        }

        @media (prefers-color-scheme: dark) {
          body:not([data-theme="light"]) {
            --color-code-background: #202020;
            --color-code-foreground: #d0d0d0;
          }
        }
      }

      .root-404-shell .page {
        min-height: 100vh;
      }

      .root-404-shell .sidebar-search-container,
      .root-404-shell #searchbox,
      .root-404-shell .sidebar-tree {
        display: none;
      }

      .root-404-shell .sidebar-sticky {
        gap: 0;
      }

      .root-404-shell .sidebar-scroll {
        min-height: 0;
      }

      .root-404-shell .content {
        padding-top: 0;
      }

      .root-404-shell .article-container {
        max-width: 52rem;
      }

      .root-404-shell .not-found-root {
        max-width: 46rem;
        padding: clamp(2rem, 9vh, 5rem) 0 3rem;
      }

      .root-404-shell .not-found-root > :first-child {
        margin-top: 0;
      }

      .root-404-shell .eyebrow {
        display: inline-flex;
        margin-bottom: 1rem;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        background: color-mix(
          in srgb,
          var(--color-brand-primary) 12%,
          var(--color-background-primary)
        );
        color: var(--color-brand-content);
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .root-404-shell h1 {
        margin: 0;
        font-size: clamp(2.4rem, 6vw, 4.25rem);
        line-height: 1.05;
      }

      .root-404-shell .copy p {
        max-width: 38rem;
        margin: 1rem 0 0;
        color: var(--color-foreground-secondary);
        font-size: 1.05rem;
        line-height: 1.7;
      }

      .root-404-shell .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-top: 1.5rem;
      }

      .root-404-shell .button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 2.85rem;
        padding: 0.8rem 1.15rem;
        border-radius: 999px;
        border: 1px solid transparent;
        font-weight: 700;
        text-decoration: none;
        transition:
          transform 0.2s ease,
          background-color 0.2s ease,
          border-color 0.2s ease,
          color 0.2s ease;
      }

      .root-404-shell .button:hover {
        transform: translateY(-1px);
        text-decoration: none;
      }

      .root-404-shell .button-primary {
        background: var(--color-brand-primary);
        color: #ffffff;
      }

      .root-404-shell .button-primary:hover {
        background: color-mix(in srgb, black 14%, var(--color-brand-primary));
      }

      @media (max-width: 996px) {
        .root-404-shell .content {
          padding-top: 1rem;
        }

        .root-404-shell .not-found-root {
          padding-top: 1.25rem;
        }
      }
    </style>
  </head>
  <body class="root-404-shell">
    <script>
      document.body.dataset.theme = localStorage.getItem("theme") || "auto";
    </script>

    <input
      type="checkbox"
      class="sidebar-toggle"
      name="__navigation"
      id="__navigation"
      aria-label="Toggle site navigation sidebar"
    >
    <label class="overlay sidebar-overlay" for="__navigation"></label>

    <a class="skip-to-content muted-link" href="#furo-main-content">
      Skip to content
    </a>

    <div class="page">
      <header class="mobile-header">
        <div class="header-left">
          <label class="nav-overlay-icon" for="__navigation">
            <span class="icon">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  d="M3 6h18M3 12h18M3 18h18"
                  fill="none"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                ></path>
              </svg>
            </span>
          </label>
        </div>
        <div class="header-center">
          <a href="$home_target"><div class="brand">cnsplots</div></a>
        </div>
        <div class="header-right"></div>
      </header>
      <aside class="sidebar-drawer">
        <div class="sidebar-container">
          <div class="sidebar-sticky">
            <a
              class="sidebar-brand"
              href="$home_target"
              aria-label="cnsplots documentation"
            >
              <div class="sidebar-logo-container">
                <img class="sidebar-logo" src="$logo_src" alt="Logo">
              </div>
            </a>
            <div class="sidebar-scroll" aria-hidden="true"></div>
          </div>
        </div>
      </aside>
      <div class="main">
        <div class="content">
          <div class="article-container">
            <article role="main" id="furo-main-content">
              <section class="not-found-root">
                <div class="copy">
          <div class="eyebrow">404</div>
          <h1>Page not found</h1>
          <p>
            The page you requested does not exist, may have moved, or may have
            been renamed. Return to the documentation homepage to continue.
          </p>
          <div class="actions">
            <a class="button button-primary" href="$home_target">
              Go to homepage
            </a>
          </div>
        </div>
              </section>
            </article>
          </div>
        </div>
        <aside class="toc-drawer no-toc"></aside>
      </div>
    </div>
  </body>
</html>
"""
    ).substitute(
        favicon_src=html.escape(
            _latest_site_path("/_static/images/favicon.svg"), quote=True
        ),
        furo_css_src=html.escape(
            _latest_site_path("/_static/styles/furo.css"), quote=True
        ),
        furo_extensions_css_src=html.escape(
            _latest_site_path("/_static/styles/furo-extensions.css"), quote=True
        ),
        home_target=html.escape("/", quote=True),
        logo_src=html.escape(_latest_site_path("/_static/logo.svg"), quote=True),
        override_css_src=html.escape(
            _latest_site_path("/_static/css/override.css"), quote=True
        ),
    )


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
    _write_text(output_dir / "404.html", _render_root_404_page())


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
    entry: dict[str, object], outputdir: Path, confdir: Path | None = None
) -> dict[str, object]:
    """Return a metadata entry that points to the assembled site tree."""
    rewritten = dict(entry)
    rewritten["outputdir"] = str(outputdir.resolve())
    if confdir is not None:
        rewritten["confdir"] = str(confdir.resolve())
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
            all_metadata[DEV_DOCS_NAME],
            output_dir / DEV_DOCS_NAME,
            DOCS_DIR,
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
