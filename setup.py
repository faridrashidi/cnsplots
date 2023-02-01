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
        "PyComplexHeatmap @ git+ssh://git@github.com/DingWB/PyComplexHeatmap.git",
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
