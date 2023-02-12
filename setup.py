from setuptools import find_packages, setup

try:
    from cnsplots import __version__
except ImportError:
    __version__ = "0.0.0"


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
        "PyComplexHeatmap",
        "palettable",
        "altair",
        "altair_saver",
        "numpy",
        "pandas",
        "scipy",
        "natsort",
        "num2tex",
        "statannotations",
    ],
    extras_require={
        "doc": [
            "sphinx",
            "furo",
            "sphinx_gallery",
            "sphinx_design",
            "sphinx_copybutton",
            "sphinx_hoverxref",
            "sphinx_autodoc_typehints",
            "myst_parser",
        ],
        "dev": [
            "pre-commit",
        ],
    },
    packages=find_packages(),
)
