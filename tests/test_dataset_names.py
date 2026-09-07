from __future__ import annotations

import socket
import subprocess
import sys
from importlib import resources
from typing import get_type_hints

import pandas as pd
import pytest

import cnsplots as cns
from cnsplots.datasets import _loader


def test_get_dataset_names_lists_every_packaged_dataset() -> None:
    data_root = resources.files("cnsplots.datasets").joinpath("_data")
    packaged_names = sorted(
        entry.name.removesuffix(".csv")
        for entry in data_root.iterdir()
        if entry.is_file() and entry.name.endswith(".csv")
    )

    names = cns.datasets.get_dataset_names()

    assert names == packaged_names
    for name in names:
        assert not cns.datasets.load_dataset(name).empty


def test_get_dataset_names_returns_sorted_independent_lists() -> None:
    first = cns.datasets.get_dataset_names()
    second = cns.datasets.get_dataset_names()

    assert first == second == ["flights", "fmri", "iris", "penguins", "tips"]
    assert first is not second
    first.clear()
    first.append("missing")
    assert cns.datasets.get_dataset_names() == second
    assert get_type_hints(cns.datasets.get_dataset_names)["return"] == list[str]


def test_get_dataset_names_does_not_load_data_or_use_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_io(*args: object, **kwargs: object) -> None:
        raise AssertionError("Dataset discovery must not load data or use the network")

    monkeypatch.setattr(resources, "files", fail_io)
    monkeypatch.setattr(pd, "read_csv", fail_io)
    monkeypatch.setattr(_loader, "load_dataset", fail_io)
    monkeypatch.setattr(cns.datasets, "load_dataset", fail_io)
    monkeypatch.setattr(socket, "create_connection", fail_io)
    monkeypatch.setattr(socket.socket, "connect", fail_io)

    assert cns.datasets.get_dataset_names() == [
        "flights",
        "fmri",
        "iris",
        "penguins",
        "tips",
    ]


def test_get_dataset_names_preserves_lazy_imports() -> None:
    script = """
import sys

import cnsplots as cns

assert "cnsplots.datasets" not in sys.modules
assert cns.datasets.get_dataset_names() == [
    "flights", "fmri", "iris", "penguins", "tips"
]
assert not {
    "Bio",
    "PyComplexHeatmap",
    "anndata",
    "gseapy",
    "lifelines",
    "matplotlib",
    "scanpy",
    "scipy",
    "seaborn",
    "sklearn",
    "statsmodels",
} & {name.split(".")[0] for name in sys.modules}
"""
    subprocess.run([sys.executable, "-c", script], check=True)
