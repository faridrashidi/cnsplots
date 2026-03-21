import importlib
import inspect
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

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

_GALLERY_CATEGORIES = [
    {
        "title": "Getting Started",
        "description": (
            "Start here for the core cnsplots workflow: overview figures, global "
            "settings, figure setup, color palettes, and publication-style "
            "multipanel layouts."
        ),
        "examples": [
            "showcase",
            "settings",
            "figure_setup",
            "palettes",
            "multipanel",
        ],
    },
    {
        "title": "Comparison & Categories",
        "description": (
            "Examples in this section focus on comparing groups and compositions "
            "with categorical plots, proportion charts, and flow-based visual "
            "summaries."
        ),
        "examples": [
            "boxplot",
            "stackplot",
            "barplot",
            "lollipopplot",
            "stripplot",
            "violinplot",
            "dotplot",
            "pieplot",
            "donutplot",
            "sankeyplot",
        ],
    },
    {
        "title": "Distributions & Trends",
        "description": (
            "These examples highlight continuous data, distribution shapes, "
            "relationships, and trend-oriented visualizations for exploratory "
            "and publication figures."
        ),
        "examples": [
            "histplot",
            "kdeplot",
            "distplot",
            "ridgeplot",
            "qqplot",
            "scatterplot",
            "regplot",
            "lineplot",
            "slopeplot",
        ],
    },
    {
        "title": "Analysis & Evaluation",
        "description": (
            "This section collects analysis-driven examples including "
            "enrichment, survival, classification, overlap, and evaluation "
            "plots commonly used in scientific workflows."
        ),
        "examples": [
            "heatmapplot",
            "survivalplot",
            "forestplot",
            "gseaplot",
            "volcanoplot",
            "confusionplot",
            "rocplot",
            "vennplot",
            "upsetplot",
        ],
    },
    {
        "title": "Integrations",
        "description": (
            "These examples show how to combine cnsplots styling, sizing, and "
            "export helpers with native matplotlib, seaborn, and scanpy "
            "workflows."
        ),
        "examples": [
            "matplotlib_integration",
            "seaborn_integration",
            "scanpy_integration",
        ],
    },
]

_GALLERY_EXAMPLE_ORDER = [
    f"{example}.py"
    for category in _GALLERY_CATEGORIES
    for example in category["examples"]
]


class GalleryExampleOrder:
    """Keep gallery examples in a stable, curated order."""

    def __init__(self, src_dir: str):
        del src_dir
        self.positions = {
            name: index for index, name in enumerate(_GALLERY_EXAMPLE_ORDER)
        }

    def __call__(self, filename: str) -> tuple[int, str]:
        name = Path(filename).name
        return (self.positions.get(name, len(self.positions)), name)

    def __repr__(self) -> str:
        return "<GalleryExampleOrder>"


sphinx_gallery_conf = {
    "filename_pattern": r"/.*\.py$",
    "ignore_pattern": "/todo_",
    "examples_dirs": "../examples",  # path to your example scripts
    "gallery_dirs": "examples",  # path to where to save gallery generated output
    "within_subsection_order": GalleryExampleOrder,
    "backreferences_dir": "gen_modules/backreferences",  # Where to store backreferences
    "doc_module": ("cnsplots",),  # The module containing your functions
    "reference_url": {
        "cnsplots": None,  # Module to create cross-references for
    },
}


def _build_repo_stats_context(repo_url: str) -> dict[str, str]:
    """Return template context for the docs repo stats card."""
    parsed_url = urlparse(repo_url)
    repo_parts = [part for part in parsed_url.path.split("/") if part]
    user = repo_parts[0] if len(repo_parts) > 0 else ""
    repo = repo_parts[1] if len(repo_parts) > 1 else ""
    return {
        "repo_stats_url": repo_url,
        "repo_stats_user": user,
        "repo_stats_repo": repo,
        "repo_stats_type": "github",
    }


repo_stats_context = _build_repo_stats_context(github_repo)


# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]
html_extra_path = ["robots.txt"]
html_title = "cnsplots"
html_logo = "_static/images/logo.svg"
html_favicon = "_static/images/favicon.ico"
html_css_files = ["css/override.css"]
html_js_files = [
    "https://code.iconify.design/iconify-icon/3.0.0/iconify-icon.min.js",
    "js/third_party/snarkdown.umd.js",
    "js/repo-stats.js",
    "js/release-notes.js",
]
html_baseurl = site_url
html_copy_source = False
html_context = repo_stats_context.copy()
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


def _render_gallery_category_section(
    title: str, description: str, thumbnail_blocks: list[str]
) -> str:
    """Render a grouped gallery section using Sphinx-Gallery thumbnail markup."""
    underline = "-" * len(title)
    parts = [
        title,
        underline,
        "",
        description,
        "",
        "",
        ".. raw:: html",
        "",
        '    <div class="sphx-glr-thumbnails">',
        "",
        ".. thumbnail-parent-div-open",
        "",
    ]
    for block in thumbnail_blocks:
        parts.append(block.rstrip())
        parts.append("")
    parts.extend(
        [
            ".. thumbnail-parent-div-close",
            "",
            ".. raw:: html",
            "",
            "    </div>",
            "",
            "",
        ]
    )
    return "\n".join(parts)


def _regroup_flat_gallery_index(app, env, docnames) -> None:
    """Group the root examples gallery without requiring example subfolders."""
    del app, env, docnames

    gallery_index = _docs_dir / "examples" / "index.rst"
    if not gallery_index.exists():
        return

    content = gallery_index.read_text(encoding="utf-8")
    thumbnails_open = '.. raw:: html\n\n    <div class="sphx-glr-thumbnails">\n'
    thumbnails_start = content.find(thumbnails_open)
    toctree_start = content.find("\n.. toctree::\n")
    if (
        thumbnails_start == -1
        or toctree_start == -1
        or toctree_start <= thumbnails_start
    ):
        return

    thumbnail_block_pattern = re.compile(
        r'\.\. raw:: html\n\n    <div class="sphx-glr-thumbcontainer".*?\n    </div>\n\n',
        re.S,
    )
    blocks = thumbnail_block_pattern.findall(content[thumbnails_start:toctree_start])
    if not blocks:
        return

    blocks_by_slug = {}
    ordered_blocks: list[tuple[str | None, str]] = []
    for block in blocks:
        match = re.search(r":doc:`/examples/([^`]+)`", block)
        slug = match.group(1) if match else None
        ordered_blocks.append((slug, block.rstrip()))
        if slug is not None:
            blocks_by_slug[slug] = block.rstrip()

    preamble = content[:thumbnails_start].rstrip() + "\n\n"
    suffix = content[toctree_start:].lstrip("\n")
    sections = []
    used = set()
    for category in _GALLERY_CATEGORIES:
        category_blocks = []
        for slug in category["examples"]:
            block = blocks_by_slug.get(slug)
            if block is None:
                continue
            used.add(slug)
            category_blocks.append(block)
        if category_blocks:
            sections.append(
                _render_gallery_category_section(
                    category["title"], category["description"], category_blocks
                )
            )

    remaining_blocks = [
        block for slug, block in ordered_blocks if slug is None or slug not in used
    ]
    if remaining_blocks:
        sections.append(
            _render_gallery_category_section(
                "More Examples",
                "Additional examples that are not assigned to a named gallery section.",
                remaining_blocks,
            )
        )

    regrouped = preamble + "".join(sections) + suffix
    if regrouped != content:
        gallery_index.write_text(regrouped, encoding="utf-8")


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
    app.connect("env-before-read-docs", _regroup_flat_gallery_index)
    app.connect("html-page-context", _override_source_links)
    app.connect("html-page-context", _inject_page_seo)
