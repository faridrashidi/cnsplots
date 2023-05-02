from pathlib import Path

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
    ],
    extras_require={
        "doc": [
            r.strip()
            for r in (Path("docs") / "requirements.txt").read_text("utf-8").splitlines()
            if not r.startswith("-r")
        ],
        "dev": [
            "pre-commit",
        ],
    },
    packages=find_packages(),
)
