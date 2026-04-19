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
from datetime import datetime
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

SITE_URL = "https://cnsplots.farid.one/"
DEV_DOCS_NAME = "dev"
LATEST_DOCS_NAME = "latest"
GITHUB_PAGES_BRANCH = "gh-pages"
GITHUB_REPO = "https://github.com/faridrashidi/cnsplots"
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
    <title>Page not found - cnsplots</title>
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
    </style>
  </head>
  <body class="root-404-shell">
    <script>
      document.body.dataset.theme = localStorage.getItem("theme") || "auto";
    </script>

    <svg xmlns="http://www.w3.org/2000/svg" style="display: none;">
      <symbol id="svg-toc" viewBox="0 0 24 24">
        <title>Contents</title>
        <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024">
          <path d="M408 442h480c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8H408c-4.4 0-8 3.6-8 8v56c0 4.4 3.6 8 8 8zm-8 204c0 4.4 3.6 8 8 8h480c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8H408c-4.4 0-8 3.6-8 8v56zm504-486H120c-4.4 0-8 3.6-8 8v56c0 4.4 3.6 8 8 8h784c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8zm0 632H120c-4.4 0-8 3.6-8 8v56c0 4.4 3.6 8 8 8h784c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8zM115.4 518.9L271.7 642c5.8 4.6 14.4.5 14.4-6.9V388.9c0-7.4-8.5-11.5-14.4-6.9L115.4 505.1a8.74 8.74 0 0 0 0 13.8z"></path>
        </svg>
      </symbol>
      <symbol id="svg-menu" viewBox="0 0 24 24">
        <title>Menu</title>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </symbol>
      <symbol id="svg-sun" viewBox="0 0 24 24">
        <title>Light mode</title>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="5"></circle>
          <line x1="12" y1="1" x2="12" y2="3"></line>
          <line x1="12" y1="21" x2="12" y2="23"></line>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
          <line x1="1" y1="12" x2="3" y2="12"></line>
          <line x1="21" y1="12" x2="23" y2="12"></line>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
        </svg>
      </symbol>
      <symbol id="svg-moon" viewBox="0 0 24 24">
        <title>Dark mode</title>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
          <path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454z"></path>
        </svg>
      </symbol>
      <symbol id="svg-sun-with-moon" viewBox="0 0 24 24">
        <title>Auto light/dark, in light mode</title>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <path style="opacity: 50%" d="M 5.411 14.504 C 5.471 14.504 5.532 14.504 5.591 14.504 C 3.639 16.319 4.383 19.569 6.931 20.352 C 7.693 20.586 8.512 20.551 9.25 20.252 C 8.023 23.207 4.056 23.725 2.11 21.184 C 0.166 18.642 1.702 14.949 4.874 14.536 C 5.051 14.512 5.231 14.5 5.411 14.5 L 5.411 14.504 Z"></path>
          <line x1="14.5" y1="3.25" x2="14.5" y2="1.25"></line>
          <line x1="14.5" y1="15.85" x2="14.5" y2="17.85"></line>
          <line x1="10.044" y1="5.094" x2="8.63" y2="3.68"></line>
          <line x1="19" y1="14.05" x2="20.414" y2="15.464"></line>
          <line x1="8.2" y1="9.55" x2="6.2" y2="9.55"></line>
          <line x1="20.8" y1="9.55" x2="22.8" y2="9.55"></line>
          <line x1="10.044" y1="14.006" x2="8.63" y2="15.42"></line>
          <line x1="19" y1="5.05" x2="20.414" y2="3.636"></line>
          <circle cx="14.5" cy="9.55" r="3.6"></circle>
        </svg>
      </symbol>
      <symbol id="svg-moon-with-sun" viewBox="0 0 24 24">
        <title>Auto light/dark, in dark mode</title>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <path d="M 8.282 7.007 C 8.385 7.007 8.494 7.007 8.595 7.007 C 5.18 10.184 6.481 15.869 10.942 17.24 C 12.275 17.648 13.706 17.589 15 17.066 C 12.851 22.236 5.91 23.143 2.505 18.696 C -0.897 14.249 1.791 7.786 7.342 7.063 C 7.652 7.021 7.965 7 8.282 7 L 8.282 7.007 Z"></path>
          <line style="opacity: 50%" x1="18" y1="3.705" x2="18" y2="2.5"></line>
          <line style="opacity: 50%" x1="18" y1="11.295" x2="18" y2="12.5"></line>
          <line style="opacity: 50%" x1="15.316" y1="4.816" x2="14.464" y2="3.964"></line>
          <line style="opacity: 50%" x1="20.711" y1="10.212" x2="21.563" y2="11.063"></line>
          <line style="opacity: 50%" x1="14.205" y1="7.5" x2="13.001" y2="7.5"></line>
          <line style="opacity: 50%" x1="21.795" y1="7.5" x2="23" y2="7.5"></line>
          <line style="opacity: 50%" x1="15.316" y1="10.184" x2="14.464" y2="11.036"></line>
          <line style="opacity: 50%" x1="20.711" y1="4.789" x2="21.563" y2="3.937"></line>
          <circle style="opacity: 50%" cx="18" cy="7.5" r="2.169"></circle>
        </svg>
      </symbol>
      <symbol id="svg-pencil" viewBox="0 0 24 24">
        <title>Edit this page</title>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 20h4l10.5 -10.5a2.828 2.828 0 1 0 -4 -4l-10.5 10.5v4"></path>
          <path d="M13.5 6.5l4 4"></path>
          <path d="M20 21l2 -2l-2 -2"></path>
          <path d="M17 17l-2 2l2 2"></path>
        </svg>
      </symbol>
      <symbol id="svg-eye" viewBox="0 0 24 24">
        <title>View this page</title>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
          <path d="M10 12a2 2 0 1 0 4 0a2 2 0 0 0 -4 0"></path>
          <path d="M11.11 17.958c-3.209 -.307 -5.91 -2.293 -8.11 -5.958c2.4 -4 5.4 -6 9 -6c3.6 0 6.6 2 9 6c-.21 .352 -.427 .688 -.647 1.008"></path>
          <path d="M20 21l2 -2l-2 -2"></path>
          <path d="M17 17l-2 2l2 2"></path>
        </svg>
      </symbol>
    </svg>

    <input
      type="checkbox"
      class="sidebar-toggle"
      name="__navigation"
      id="__navigation"
      aria-label="Toggle site navigation sidebar"
    >
    <input
      type="checkbox"
      class="sidebar-toggle"
      name="__toc"
      id="__toc"
      aria-label="Toggle table of contents sidebar"
    >
    <label class="overlay sidebar-overlay" for="__navigation"></label>
    <label class="overlay toc-overlay" for="__toc"></label>

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
        <div class="header-right">
          <div class="theme-toggle-container theme-toggle-header">
            <button class="theme-toggle" aria-label="Toggle Light / Dark / Auto color theme">
              <svg class="theme-icon-when-auto-light"><use href="#svg-sun-with-moon"></use></svg>
              <svg class="theme-icon-when-auto-dark"><use href="#svg-moon-with-sun"></use></svg>
              <svg class="theme-icon-when-dark"><use href="#svg-moon"></use></svg>
              <svg class="theme-icon-when-light"><use href="#svg-sun"></use></svg>
            </button>
          </div>
          <label class="toc-overlay-icon toc-header-icon no-toc" for="__toc">
            <span class="icon"><svg><use href="#svg-toc"></use></svg></span>
          </label>
        </div>
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
            <a href="#" class="back-to-top muted-link">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path d="M13 20h-2V8l-5.5 5.5-1.42-1.42L12 4.16l7.92 7.92-1.42 1.42L13 8v12z"></path>
              </svg>
              <span>Back to top</span>
            </a>
            <div class="content-icon-container">
              <div class="view-this-page">
                <a class="muted-link" href="$view_page_target" title="View this page">
                  <svg><use href="#svg-eye"></use></svg>
                  <span class="visually-hidden">View this page</span>
                </a>
              </div>
              <div class="edit-this-page">
                <a class="muted-link" href="$edit_page_target" rel="edit" title="Edit this page">
                  <svg><use href="#svg-pencil"></use></svg>
                  <span class="visually-hidden">Edit this page</span>
                </a>
              </div>
              <div class="theme-toggle-container theme-toggle-content">
                <button class="theme-toggle" aria-label="Toggle Light / Dark / Auto color theme">
                  <svg class="theme-icon-when-auto-light"><use href="#svg-sun-with-moon"></use></svg>
                  <svg class="theme-icon-when-auto-dark"><use href="#svg-moon-with-sun"></use></svg>
                  <svg class="theme-icon-when-dark"><use href="#svg-moon"></use></svg>
                  <svg class="theme-icon-when-light"><use href="#svg-sun"></use></svg>
                </button>
              </div>
              <label class="toc-overlay-icon toc-content-icon no-toc" for="__toc">
                <span class="icon"><svg><use href="#svg-toc"></use></svg></span>
              </label>
            </div>
            <article role="main" id="furo-main-content">
              <section class="not-found-root" aria-labelledby="root-404-title">
                <h1 id="root-404-title">Page not found</h1>
                <div class="not-found-page">
                  <p>
                    <strong>
                      The page you requested does not exist, may have moved, or
                      may have been renamed.
                    </strong>
                  </p>
                  <p>
                    <a href="$home_target">Return to the documentation homepage</a>.
                  </p>
                </div>
              </section>
            </article>
          </div>
          <footer>
            <div class="related-pages"></div>
            <div class="bottom-of-page">
              <div class="left-details">
                <div class="copyright">
                  Copyright &#169; $copyright_notice
                </div>
              </div>
              <div class="right-details">
                <div class="icons">
                  <a class="muted-link" href="$github_repo" aria-label="GitHub">
                    <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                      <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                    </svg>
                  </a>
                </div>
              </div>
            </div>
          </footer>
        </div>
        <aside class="toc-drawer no-toc"></aside>
      </div>
    </div>
    <script src="$furo_script_src"></script>
  </body>
</html>
"""
    ).substitute(
        copyright_notice=html.escape(f"2023-{datetime.now().year}, Farid Rashidi"),
        edit_page_target=html.escape(
            f"{GITHUB_REPO}/edit/main/docs/404.md", quote=True
        ),
        favicon_src=html.escape(
            _latest_site_path("/_static/images/favicon.svg"), quote=True
        ),
        furo_css_src=html.escape(
            _latest_site_path("/_static/styles/furo.css"), quote=True
        ),
        furo_extensions_css_src=html.escape(
            _latest_site_path("/_static/styles/furo-extensions.css"), quote=True
        ),
        furo_script_src=html.escape(
            _latest_site_path("/_static/scripts/furo.js"), quote=True
        ),
        github_repo=html.escape(GITHUB_REPO, quote=True),
        home_target=html.escape("/", quote=True),
        logo_src=html.escape(_latest_site_path("/_static/logo.svg"), quote=True),
        override_css_src=html.escape(
            _latest_site_path("/_static/css/override.css"), quote=True
        ),
        view_page_target=html.escape(
            f"{GITHUB_REPO}/blob/main/docs/404.md?plain=true", quote=True
        ),
    )


def _remove_path(path: Path) -> None:
    """Remove a filesystem path regardless of whether it is a file or directory."""
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.exists():
        shutil.rmtree(path)


def _write_version_symlink(output_dir: Path, alias_name: str, target_name: str) -> None:
    """Create a relative symlink alias for a published docs version."""
    target_dir = output_dir / target_name
    if not target_dir.exists():
        raise RuntimeError(f"Cannot link {alias_name} to missing docs at {target_dir}.")

    alias_path = output_dir / alias_name
    _remove_path(alias_path)
    alias_path.symlink_to(target_name)


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


def _copy_preserved_versions(
    existing_site_dir: Path,
    output_dir: Path,
    *,
    include_dev: bool = False,
    exclude_names: set[str] | None = None,
) -> tuple[list[str], bool]:
    """Copy published version directories into output_dir without alias symlinks."""
    excluded_names = exclude_names or set()
    preserved_release_names: list[str] = []
    preserved_dev = False

    for path in existing_site_dir.iterdir():
        if path.name in excluded_names or path.is_symlink() or not path.is_dir():
            continue
        if RELEASE_TAG_PATTERN.fullmatch(path.name):
            shutil.copytree(path, output_dir / path.name, symlinks=True)
            preserved_release_names.append(path.name)
            continue
        if include_dev and path.name == DEV_DOCS_NAME:
            shutil.copytree(path, output_dir / path.name, symlinks=True)
            preserved_dev = True

    return sorted(preserved_release_names, key=_version_sort_key), preserved_dev


def _resolve_published_latest_release(
    existing_site_dir: Path, preserved_release_names: list[str]
) -> str | None:
    """Return the stable release currently published as latest on gh-pages."""
    latest_alias = existing_site_dir / LATEST_DOCS_NAME
    if latest_alias.is_symlink():
        target_name = Path(os.readlink(latest_alias)).name
        if target_name in preserved_release_names and RELEASE_TAG_PATTERN.fullmatch(
            target_name
        ):
            return target_name

    if not preserved_release_names:
        return None

    return max(preserved_release_names, key=_version_sort_key)


def _rewrite_metadata_entry(
    entry: dict[str, object], outputdir: Path, confdir: Path | None = None
) -> dict[str, object]:
    """Return a metadata entry that points to the assembled site tree."""
    rewritten = dict(entry)
    rewritten["outputdir"] = str(outputdir.resolve())
    if confdir is not None:
        rewritten["confdir"] = str(confdir.resolve())
    return rewritten


def _build_version_metadata(
    all_metadata: dict[str, dict[str, object]],
    output_dir: Path,
    version_names: list[str],
    current_version_name: str,
    current_confdir: Path,
) -> dict[str, dict[str, object]]:
    """Return metadata rewritten for the assembled site tree."""
    if current_version_name not in all_metadata:
        raise RuntimeError(
            f"Missing metadata for the current docs build version {current_version_name}."
        )

    metadata: dict[str, dict[str, object]] = {}
    for name in version_names:
        entry = all_metadata.get(name)
        if entry is None:
            continue
        confdir = current_confdir if name == current_version_name else None
        metadata[name] = _rewrite_metadata_entry(entry, output_dir / name, confdir)
    return metadata


def _build_single_version_docs(
    version_name: str,
    output_dir: Path,
    metadata: dict[str, dict[str, object]],
    latest_release_tag: str,
    *,
    docs_dir: Path = DOCS_DIR,
    cwd: Path = REPO_ROOT,
) -> None:
    """Build a single docs version using precomputed multiversion metadata."""
    _remove_path(output_dir)

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
            str(docs_dir),
            str(output_dir),
            env=env,
            cwd=cwd,
        )


def _build_bootstrap_site(output_dir: Path, latest_release_tag: str) -> None:
    """Build a minimal site from scratch with dev and the newest release."""
    all_metadata = _dump_multiversion_metadata(output_dir, latest_release_tag)
    _ensure_clean_dir(output_dir)

    version_names = [DEV_DOCS_NAME, latest_release_tag]

    with _temporary_worktree(DEV_DOCS_NAME) as dev_worktree:
        dev_docs_dir = dev_worktree / "docs"
        dev_metadata = _build_version_metadata(
            all_metadata,
            output_dir,
            version_names,
            DEV_DOCS_NAME,
            dev_docs_dir,
        )
        _build_single_version_docs(
            DEV_DOCS_NAME,
            output_dir / DEV_DOCS_NAME,
            dev_metadata,
            latest_release_tag,
            docs_dir=dev_docs_dir,
            cwd=dev_worktree,
        )

    with _temporary_worktree(latest_release_tag) as release_worktree:
        release_docs_dir = release_worktree / "docs"
        release_metadata = _build_version_metadata(
            all_metadata,
            output_dir,
            version_names,
            latest_release_tag,
            release_docs_dir,
        )
        _build_single_version_docs(
            latest_release_tag,
            output_dir / latest_release_tag,
            release_metadata,
            latest_release_tag,
            docs_dir=release_docs_dir,
            cwd=release_worktree,
        )

    _write_version_symlink(output_dir, LATEST_DOCS_NAME, latest_release_tag)
    _finalize_site(output_dir)


def _build_main_site(output_dir: Path, latest_release_tag: str) -> None:
    """Build only dev docs and preserve published releases from gh-pages."""
    remote_ref = _fetch_remote_branch(GITHUB_PAGES_BRANCH)
    if remote_ref is None:
        _build_bootstrap_site(output_dir, latest_release_tag)
        return

    with _temporary_worktree(remote_ref) as existing_site_dir:
        preserved_release_names = sorted(
            (
                path.name
                for path in existing_site_dir.iterdir()
                if path.is_dir()
                and not path.is_symlink()
                and RELEASE_TAG_PATTERN.fullmatch(path.name)
            ),
            key=_version_sort_key,
        )
        published_latest_release_tag = _resolve_published_latest_release(
            existing_site_dir, preserved_release_names
        )
        if published_latest_release_tag is None:
            _build_bootstrap_site(output_dir, latest_release_tag)
            return

        _ensure_clean_dir(output_dir)
        preserved_release_names, _ = _copy_preserved_versions(
            existing_site_dir, output_dir
        )

    all_metadata = _dump_multiversion_metadata(output_dir, published_latest_release_tag)
    if published_latest_release_tag not in all_metadata:
        raise RuntimeError(
            "Missing metadata for the latest published release tag "
            f"{published_latest_release_tag}."
        )

    metadata = _build_version_metadata(
        all_metadata,
        output_dir,
        [DEV_DOCS_NAME, *preserved_release_names],
        DEV_DOCS_NAME,
        DOCS_DIR,
    )
    _build_single_version_docs(
        DEV_DOCS_NAME,
        output_dir / DEV_DOCS_NAME,
        metadata,
        published_latest_release_tag,
    )

    _write_version_symlink(output_dir, LATEST_DOCS_NAME, published_latest_release_tag)
    _finalize_site(output_dir)


def _build_release_site(output_dir: Path, latest_release_tag: str) -> None:
    """Build only the newest release docs and preserve existing published versions."""
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
        _ensure_clean_dir(output_dir)
        preserved_release_names, preserved_dev = _copy_preserved_versions(
            existing_site_dir,
            output_dir,
            include_dev=True,
            exclude_names={latest_release_tag},
        )

    version_names = [
        *([DEV_DOCS_NAME] if preserved_dev or DEV_DOCS_NAME in all_metadata else []),
        *preserved_release_names,
        latest_release_tag,
    ]

    if not preserved_dev and DEV_DOCS_NAME in all_metadata:
        with _temporary_worktree(DEV_DOCS_NAME) as dev_worktree:
            dev_docs_dir = dev_worktree / "docs"
            dev_metadata = _build_version_metadata(
                all_metadata,
                output_dir,
                version_names,
                DEV_DOCS_NAME,
                dev_docs_dir,
            )
            _build_single_version_docs(
                DEV_DOCS_NAME,
                output_dir / DEV_DOCS_NAME,
                dev_metadata,
                latest_release_tag,
                docs_dir=dev_docs_dir,
                cwd=dev_worktree,
            )

    release_metadata = _build_version_metadata(
        all_metadata,
        output_dir,
        version_names,
        latest_release_tag,
        DOCS_DIR,
    )
    _build_single_version_docs(
        latest_release_tag,
        output_dir / latest_release_tag,
        release_metadata,
        latest_release_tag,
    )

    _write_version_symlink(output_dir, LATEST_DOCS_NAME, latest_release_tag)
    _finalize_site(output_dir)


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
