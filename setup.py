from setuptools import find_packages, setup
from setuptools.extension import Extension

try:
    from trisicell import __version__
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
    packages=find_packages(),
)
