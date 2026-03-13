import importlib
import inspect
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

import cnsplots as cns

# -- Project information -----------------------------------------------------

project = "cnsplots"
copyright = f"2023-{datetime.now().year}, Farid Rashidi"
author = "Farid Rashidi"
version = cns.__version__
release = cns.__version__
site_url = "https://cnsplots.farid.one/"
site_description = (
    "Publication-ready scientific visualizations for Cell, Nature, and Science "
    "journals built on matplotlib and seaborn."
)
social_preview_image = f"{site_url.rstrip('/')}/_static/images/overview.png"

# -- General configuration ---------------------------------------------------

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "_ext"))

extensions = [
    "sphinx_gallery.gen_gallery",
    "sphinx_design",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx.ext.autosummary",
    "root_page_autosummary",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.extlinks",
    "sphinx.ext.linkcode",
    "sphinx_sitemap",
]
github_repo = "https://github.com/faridrashidi/cnsplots"
templates_path = ["_templates"]
exclude_patterns = ["_build", "**.ipynb_checkpoints"]

nbsphinx_execute = "never"

master_doc = "index"

todo_include_todos = False

# Generate the API documentation when building
autosummary_generate = True
add_module_names = False
autodoc_member_order = "bysource"
bibtex_reference_style = "author_year"
napoleon_google_docstring = True  # for pytorch lightning
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_use_rtype = True  # having a separate entry generally helps readability
napoleon_use_param = True
napoleon_custom_sections = [("Params", "Parameters")]
typehints_defaults = "braces"
todo_include_todos = False
numpydoc_show_class_members = False
annotate_defaults = True  # scanpydoc option, look into why we need this
myst_enable_extensions = [
    "colon_fence",
    "dollarmath",
    "amsmath",
]
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "matplotlib": ("https://matplotlib.org/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "seaborn": ("https://seaborn.pydata.org/", None),
    "anndata": ("https://anndata.readthedocs.io/en/latest/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference/", None),
}

sphinx_gallery_conf = {
    "filename_pattern": "/plot_",
    "ignore_pattern": "/todo_",
    "examples_dirs": "../examples",  # path to your example scripts
    "gallery_dirs": "examples",  # path to where to save gallery generated output
    "within_subsection_order": "sphinx_gallery.sorting.FileNameSortKey",
    "backreferences_dir": "gen_modules/backreferences",  # Where to store backreferences
    "doc_module": ("cnsplots",),  # The module containing your functions
    "reference_url": {
        "cnsplots": None,  # Module to create cross-references for
    },
}


# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]
html_extra_path = ["robots.txt"]
html_title = "cnsplots"
html_logo = "_static/images/logo.svg"
html_favicon = "_static/images/favicon.ico"
html_css_files = ["css/override.css"]
html_baseurl = site_url
html_copy_source = False
sitemap_url_scheme = "{link}"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_show_sphinx = False
sitemap_excludes = ["404.html", "search.html", "genindex.html", "py-modindex.html"]


html_theme_options = {
    "source_repository": github_repo,
    "source_branch": "main",
    "source_directory": "docs/",
    "sidebar_hide_name": True,
    "light_css_variables": {
        "color-brand-primary": "#003262",
        "color-brand-content": "#003262",
        "admonition-font-size": "var(--font-size-normal)",
        "admonition-title-font-size": "var(--font-size-normal)",
        "code-font-size": "var(--font-size--small)",
    },
    "footer_icons": [
        {
            "name": "GitHub",
            "url": github_repo,
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}


# -- Config for linkcode -------------------------------------------


def git(*args):
    """Run git command and return output as string."""
    return subprocess.check_output(["git", *args]).strip().decode()


# https://github.com/DisnakeDev/disnake/blob/7853da70b13fcd2978c39c0b7efa59b34d298186/docs/conf.py#L192
# Current git reference. Uses branch/tag name if found, otherwise uses commit hash
git_ref = None
try:
    git_ref = git("name-rev", "--name-only", "--no-undefined", "HEAD")
    git_ref = re.sub(r"^(remotes/[^/]+|tags)/", "", git_ref)
except Exception:  # noqa: B902
    pass

# (if no name found or relative ref, use commit hash instead)
if not git_ref or re.search(r"[\^~]", git_ref):
    try:
        git_ref = git("rev-parse", "HEAD")
    except Exception:  # noqa: B902
        git_ref = "main"

# https://github.com/DisnakeDev/disnake/blob/7853da70b13fcd2978c39c0b7efa59b34d298186/docs/conf.py#L192
_cnsplots_tools_module_path = os.path.dirname(
    importlib.util.find_spec("cnsplots").origin
)
_docs_dir = Path(__file__).resolve().parent
_repo_root = _docs_dir.parent


def _resolve_gallery_source_path(pagename: str) -> str | None:
    """Return the repository path for gallery sources, if applicable."""
    gallery_root = "examples"
    if pagename == gallery_root:
        relative_source = PurePosixPath(gallery_root) / "README.rst"
    elif pagename.startswith(f"{gallery_root}/"):
        gallery_page = PurePosixPath(pagename)
        if gallery_page.name == "index":
            relative_source = gallery_page.parent / "README.rst"
        else:
            relative_source = gallery_page.with_suffix(".py")
    else:
        return None

    source_path = _repo_root / Path(relative_source)
    if not source_path.exists():
        return None

    return relative_source.as_posix()


def _resolve_source_info(obj: Any) -> dict[str, Any] | None:
    """Return repository-relative source information for a Python object."""
    try:
        obj = inspect.unwrap(obj)
        if isinstance(obj, property):
            obj = inspect.unwrap(obj.fget)

        path = os.path.relpath(
            inspect.getsourcefile(obj), start=_cnsplots_tools_module_path
        )
        src, lineno = inspect.getsourcelines(obj)
    except Exception:  # noqa: B902
        return None

    return {
        "path": (PurePosixPath("src/cnsplots") / PurePosixPath(path)).as_posix(),
        "lineno": lineno,
        "end_lineno": lineno + len(src) - 1,
    }


def _resolve_api_source_info(app, pagename: str) -> dict[str, Any] | None:
    """Return source information for autosummary API object pages."""
    if not pagename.startswith("api/"):
        return None

    github_url = app.env.metadata.get(pagename, {}).get("github_url")
    if not github_url:
        return None

    try:
        module_name, *parts = github_url.split(".")
        obj: Any = importlib.import_module(module_name)
        for part in parts:
            obj = getattr(obj, part)
    except Exception:  # noqa: B902
        return None

    return _resolve_source_info(obj)


def _override_source_links(
    app, pagename: str, templatename, context: dict[str, Any], doctree
):
    """Point source buttons at repo-root example files and API implementations."""
    del templatename, doctree

    gallery_source_path = _resolve_gallery_source_path(pagename)
    if gallery_source_path is not None:
        context["theme_source_edit_link"] = (
            f"{github_repo}/edit/{git_ref}/{gallery_source_path}"
        )
        context["theme_source_view_link"] = (
            f"{github_repo}/blob/{git_ref}/{gallery_source_path}?plain=true"
        )
        return

    api_source_info = _resolve_api_source_info(app, pagename)
    if api_source_info is None:
        return

    source_path = api_source_info["path"]
    line_range = f"#L{api_source_info['lineno']}-L{api_source_info['end_lineno']}"
    context["theme_source_edit_link"] = f"{github_repo}/edit/{git_ref}/{source_path}"
    context["theme_source_view_link"] = (
        f"{github_repo}/blob/{git_ref}/{source_path}{line_range}"
    )


def _build_page_url(app, pagename: str) -> str:
    """Return the public URL for the current documentation page."""
    target_uri = app.builder.get_target_uri(pagename)
    baseurl = app.config.html_baseurl.rstrip("/")
    if not target_uri:
        return f"{baseurl}/"
    return f"{baseurl}/{target_uri}"


def _build_page_description(pagename: str, title: str) -> str:
    """Return a concise search and social description for a page."""
    descriptions = {
        "index": site_description,
        "getting_started": (
            "Get started with cnsplots and create publication-ready scientific "
            "figures with a compact matplotlib-compatible API."
        ),
        "installation": (
            "Install cnsplots and optional documentation dependencies for "
            "publication-ready scientific plotting."
        ),
        "api": (
            "API reference for cnsplots, a Python plotting library for "
            "publication-ready scientific figures."
        ),
        "404": "Page not found.",
    }

    if pagename in descriptions:
        return descriptions[pagename]
    if pagename.startswith("examples/"):
        return (
            f"{title} examples for cnsplots, a Python library for "
            "publication-ready scientific plotting."
        )
    if pagename.startswith("api/"):
        return (
            f"{title} reference for cnsplots, a Python library for "
            "publication-ready scientific plotting."
        )
    return f"{title} in the cnsplots documentation. {site_description}"


def _inject_page_seo(
    app, pagename: str, templatename, context: dict[str, Any], doctree
):
    """Add canonical URLs and social metadata to every HTML page."""
    del templatename, doctree

    title = str(context.get("title") or project)
    if pagename == "index" or title == project:
        seo_title = project
    else:
        seo_title = f"{title} - {project}"

    noindex_pages = {"404", "search", "genindex", "py-modindex"}
    context["seo_title"] = seo_title
    context["seo_description"] = _build_page_description(pagename, title)
    context["seo_canonical_url"] = _build_page_url(app, pagename)
    context["seo_image_url"] = social_preview_image
    context["seo_image_alt"] = "Overview of cnsplots visualizations"
    context["seo_robots"] = (
        "noindex, nofollow" if pagename in noindex_pages else "index, follow"
    )
    context["seo_og_type"] = "website" if pagename == "index" else "article"


def linkcode_resolve(domain, info):
    """Determine the URL corresponding to Python object."""
    if domain != "py":
        return None

    try:
        obj: Any = sys.modules[info["module"]]
        for part in info["fullname"].split("."):
            obj = getattr(obj, part)
    except Exception:  # noqa: B902
        return None

    source_info = _resolve_source_info(obj)
    if source_info is None:
        return None

    return (
        f"{github_repo}/blob/{git_ref}/{source_info['path']}"
        f"#L{source_info['lineno']}-L{source_info['end_lineno']}"
    )


def setup(app):
    """Register Sphinx hooks for page metadata and source link overrides."""
    app.connect("html-page-context", _override_source_links)
    app.connect("html-page-context", _inject_page_seo)
