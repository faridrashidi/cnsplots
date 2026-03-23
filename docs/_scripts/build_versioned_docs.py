from __future__ import annotations

import argparse
import html
import os
import posixpath
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath

SITE_URL = "https://cnsplots.farid.one/"
DEV_DOCS_NAME = "dev"
LATEST_DOCS_NAME = "latest"
RELEASE_TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
ROBOTS_FILE = DOCS_DIR / "robots.txt"
COMPAT_SITE_DIR = Path(__file__).resolve().parent / "compat"


def _run(*args: str) -> str:
    """Run a command in the repo root and return stripped stdout."""
    return subprocess.check_output(args, cwd=REPO_ROOT, text=True).strip()


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


def _version_sort_key(name: str) -> tuple[int, int, int]:
    """Return a semantic sort key for release tags."""
    match = RELEASE_TAG_PATTERN.fullmatch(name)
    if not match:
        return (-1, -1, -1)
    return tuple(int(part) for part in name[1:].split("."))


def _relative_target(stub_relative_path: Path, target_path: PurePosixPath) -> str:
    """Return a relative redirect target from the stub path to the target path."""
    stub_parent = PurePosixPath(stub_relative_path.parent.as_posix())
    start = "." if str(stub_parent) in {"", "."} else stub_parent.as_posix()
    return posixpath.relpath(target_path.as_posix(), start=start)


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
    """Mirror latest HTML paths at the site root via redirect stubs."""
    latest_alias_dir = output_dir / LATEST_DOCS_NAME
    if not latest_alias_dir.exists():
        raise RuntimeError(f"Latest docs alias was not built at {latest_alias_dir}.")

    latest_alias_prefix = PurePosixPath(LATEST_DOCS_NAME)
    for source_path in latest_alias_dir.rglob("*.html"):
        relative_html = source_path.relative_to(latest_alias_dir)
        if relative_html.name == "404.html":
            continue

        destination_path = output_dir / relative_html
        if relative_html == Path("index.html"):
            target_path = latest_alias_prefix
            relative_target = f"{LATEST_DOCS_NAME}/"
            absolute_target = _latest_absolute_url("/")
        else:
            target_path = latest_alias_prefix / PurePosixPath(relative_html.as_posix())
            relative_target = _relative_target(relative_html, target_path)
            absolute_target = f"{SITE_URL.rstrip('/')}/{target_path.as_posix()}"
        _write_text(
            destination_path,
            _render_redirect_page(relative_target, absolute_target),
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


def _build_versioned_docs(output_dir: Path, latest_release_tag: str) -> None:
    """Build all versioned docs into the output directory."""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    compat_path = str(COMPAT_SITE_DIR)
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        compat_path
        if not existing_pythonpath
        else f"{compat_path}{os.pathsep}{existing_pythonpath}"
    )
    env["CNSPLOTS_DOCS_LATEST_VERSION"] = latest_release_tag

    subprocess.run(
        [
            "sphinx-multiversion",
            str(DOCS_DIR),
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
        env=env,
    )


def build(output_dir: Path) -> None:
    """Build versioned docs and package them for GitHub Pages."""
    latest_release_tag = _find_latest_release_tag()
    _build_versioned_docs(output_dir, latest_release_tag)
    _write_latest_release_alias(output_dir, latest_release_tag)
    _write_root_redirects(output_dir)
    shutil.copy2(ROBOTS_FILE, output_dir / "robots.txt")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    _write_root_404(output_dir)
    _write_root_sitemap_index(output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build versioned Sphinx docs and package them for GitHub Pages."
    )
    parser.add_argument(
        "output_dir", type=Path, help="Directory to write the site into."
    )
    args = parser.parse_args()
    build(args.output_dir.resolve())


if __name__ == "__main__":
    main()
