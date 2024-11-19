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
        "matplotlib_venn<=0.11.10",
        "pycomplexheatmap",
        "palettable",
        "numpy",
        "pandas<=1.5.3",
        "scipy<=1.12.0",
        "natsort",
        "num2tex",
        "statannotations @ git+https://github.com/trevismd/statannotations@master",
        "scikit_learn",
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
