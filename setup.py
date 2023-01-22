from setuptools import find_packages, setup

meta = {}
exec(open("./cnsplots/__init__.py").read(), meta)


setup(
    name="cnsplots",
    version=meta["__version__"],
    install_requires=[
        "seaborn",
        "scanpy",
        "lifelines",
        "altair",
        "altair_saver",
    ],
    packages=find_packages(),
)
