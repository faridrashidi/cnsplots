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
        "git+https://github.com/DingWB/PyComplexHeatmap",
        "altair",
        "altair_saver",
        "numpy",
        "pandas",
        "scipy",
        "statannotations",
    ],
    packages=find_packages(),
)
