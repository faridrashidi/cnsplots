"""Load tabular package resources used by the gallery."""

from importlib import resources

import pandas as pd

_DATASET_NAMES = frozenset({"flights", "fmri", "iris", "penguins", "tips"})


def get_dataset_names() -> list[str]:
    """List the packaged example datasets without loading data or using the network.

    Returns
    -------
    list[str]
        A new, alphabetically sorted list of names accepted by ``load_dataset``.
    """
    return sorted(_DATASET_NAMES)


def load_dataset(name: str) -> pd.DataFrame:
    """Load a packaged example dataset without network access.

    Parameters
    ----------
    name : str
        One of ``"flights"``, ``"fmri"``, ``"iris"``, ``"penguins"``, or
        ``"tips"``.

    Returns
    -------
    pandas.DataFrame
        A new data frame loaded from the package resources.

    Notes
    -----
    The CSVs are bundled snapshots from seaborn-data. After CSV parsing,
    ``tips`` labels become categorical, ``flights`` months become abbreviated
    categorical labels, and ``penguins`` sex labels become title case. Numeric
    measurements and rows are unchanged.

    Original sources, snapshot revisions, and individual redistribution terms
    are recorded in the distributed ``NOTICE-DATA.md`` and the
    :doc:`example data guide </datasets>`.
    """
    if not isinstance(name, str):
        msg = "Dataset name must be a string."
        raise TypeError(msg)
    if name not in _DATASET_NAMES:
        available = ", ".join(sorted(_DATASET_NAMES))
        msg = f"Unknown dataset {name!r}. Available datasets: {available}."
        raise ValueError(msg)

    data_root = resources.files("cnsplots.datasets").joinpath("_data")
    with data_root.joinpath(f"{name}.csv").open("rb") as stream:
        data = pd.read_csv(stream)

    if name == "tips":
        data["day"] = pd.Categorical(data["day"], ["Thur", "Fri", "Sat", "Sun"])
        data["sex"] = pd.Categorical(data["sex"], ["Male", "Female"])
        data["time"] = pd.Categorical(data["time"], ["Lunch", "Dinner"])
        data["smoker"] = pd.Categorical(data["smoker"], ["Yes", "No"])
    elif name == "flights":
        months = data["month"].str[:3]
        data["month"] = pd.Categorical(months, months.unique())
    elif name == "penguins":
        data["sex"] = data["sex"].str.title()

    return data
