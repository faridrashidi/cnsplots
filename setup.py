from setuptools import find_packages, setup

meta = {}
exec(open("./cnsplots/__init__.py").read(), meta)


setup(
    name="cnsplots",
    version=meta["__version__"],
    install_requires=[
        "matplotlib",
        "seaborn",
        "scanpy",
        "lifelines",
        "upsetplot",
        "adjustText",
        "git+https://github.com/DingWB/PyComplexHeatmap",
        "palettable",
        "altair",
        "altair_saver",
        "numpy",
        "pandas",
        "scipy",
        "statannotations",
        "natsort",
        "num2tex",
    ],
    packages=find_packages(),
)
