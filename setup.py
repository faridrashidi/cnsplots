from setuptools import find_packages, setup

try:
    from cnsplots import __version__
except ImportError:
    __version__ = "0.0.1"


setup(
    name="cnsplots",
    version=__version__,
    install_requires=[
        "matplotlib",
        "seaborn",
        "scanpy",
        "lifelines",
        "pydeseq2",
        "upsetplot",
        "adjustText",
        "matplotlib_venn",
        "pycomplexheatmap",
        "palettable",
        "numpy",
        "pandas",
        "scipy",
        "natsort",
        "num2tex",
        "statannotations",
        "scikit_learn",
        "sphinx",
        "furo",
        "sphinx_gallery",
        "sphinx_design",
        "sphinx_copybutton",
        "sphinx_hoverxref",
        "sphinx_autodoc_typehints",
        "myst_parser",
        "pre-commit",
    ],
    extras_require={
        "doc": [],
        "dev": [],
    },
    packages=find_packages(),
)
