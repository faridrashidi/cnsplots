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
        "upsetplot",
        "adjustText",
        # "git+https://github.com/DingWB/PyComplexHeatmap",
        "palettable",
        "altair",
        "altair_saver",
        "numpy",
        "pandas",
        "scipy",
        # "statannotations",
        "natsort",
        "num2tex",
        "statsmodels",
    ],
    extras_require={
        "docs": [
            "furo",
            "sphinx",
            "sphinx_gallery",
            "sphinx_design",
            "myst_parser",
            "sphinx_copybutton",
            "sphinx_hoverxref",
            "sphinx_autosummary",
        ],
    },
    packages=find_packages(),
)
