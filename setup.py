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
            "sphinx",
            "furo",
            "sphinx_gallery",
            "sphinx_design",
            "sphinx_copybutton",
            "sphinx_hoverxref",
            "sphinx_autosummary",
            "sphinx_autodoc_typehints",
            "myst_parser",
        ],
    },
    packages=find_packages(),
)

# TODO: complete the api for other functions
# TODO: tree plot
# TODO: add view source code in docs
# TODO: hoverxref doesn't work
# TODO: add examples to the end of each function
