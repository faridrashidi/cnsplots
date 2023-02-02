import cnsplots as cns

# -- Project information -----------------------------------------------------

project = "cnsplots"
copyright = "2023, Farid Rashidi"
author = "Farid Rashidi"
version = cns.__version__
release = cns.__version__

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx_gallery.gen_gallery",
    "sphinx_design",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx.ext.autosummary",
    "hoverxref.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
]
templates_path = ["_templates"]
exclude_patterns = ["_build", "**.ipynb_checkpoints"]

nbsphinx_execute = "never"

master_doc = "index"

# Generate the API documentation when building
autosummary_generate = True
autodoc_member_order = "bysource"
napoleon_google_docstring = True  # for pytorch lightning
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_use_rtype = True  # having a separate entry generally helps readability
napoleon_use_param = True
napoleon_custom_sections = [("Params", "Parameters")]
todo_include_todos = False
numpydoc_show_class_members = False
annotate_defaults = True  # scanpydoc option, look into why we need this
myst_enable_extensions = [
    "colon_fence",
    "dollarmath",
    "amsmath",
]
intersphinx_mapping = {
    "matplotlib": ("https://matplotlib.org/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "seaborn": ("https://seaborn.pydata.org/", None),
    "anndata": ("https://anndata.readthedocs.io/en/latest/", None),
}

sphinx_gallery_conf = {
    "filename_pattern": "/plot_",
    "ignore_pattern": "/todo_",
    "examples_dirs": "../examples",  # path to your example scripts
    "gallery_dirs": "auto_examples",  # path to where to save gallery generated output
}


# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]
html_title = "cnsplots"
html_logo = "_static/images/logo.svg"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_css_files = ["css/override.css"]
html_show_sphinx = False


html_theme_options = {
    "source_repository": "https://github.com/faridrashidi/cnsplots/",
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
}

hoverx_default_type = "tooltip"
hoverxref_domains = ["py"]
hoverxref_role_types = dict.fromkeys(
    ["ref", "class", "func", "meth", "attr", "exc", "data", "mod"],
    "tooltip",
)
hoverxref_intersphinx = [
    "python",
    "numpy",
    "scanpy",
    "anndata",
    "scipy",
    "pandas",
]
