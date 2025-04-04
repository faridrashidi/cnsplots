from setuptools import find_packages, setup

try:
    from cnsplots import __version__
except ImportError:
    __version__ = "0.0.1"


setup(
    name="cnsplots",
    version=__version__,
    install_requires=[
        "matplotlib<=3.8.4",
        "seaborn",
        "scanpy",
        "lifelines",
        "pydeseq2",
        "upsetplot",
        "adjustText",
        "matplotlib-venn<=0.11.10",
        "pycomplexheatmap",
        "palettable",
        "numpy",
        "pandas",
        "scipy",
        "natsort",
        "num2tex",
        "statannotations @ git+https://github.com/trevismd/statannotations@master",
        "scikit-learn",
    ],
    extras_require={
        "doc": [
            "sphinx",
            "furo",
            "sphinx-gallery",
            "sphinx_design",
            "sphinx-copybutton",
            "sphinx-hoverxref",
            "sphinx-autodoc-typehints",
            "myst-parser",
        ],
        "dev": [
            "pre_commit",
        ],
    },
    packages=find_packages(),
)
