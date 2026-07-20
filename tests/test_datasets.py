from __future__ import annotations

import inspect
from importlib import resources
from typing import cast

import numpy as np
import pandas as pd
import pytest
import seaborn as sns

import cnsplots as cns


@pytest.mark.parametrize(
    ("name", "shape"),
    [
        ("flights", (144, 3)),
        ("fmri", (1064, 5)),
        ("iris", (150, 5)),
        ("penguins", (344, 7)),
        ("tips", (244, 7)),
    ],
)
def test_load_dataset_uses_packaged_snapshots(
    name: str, shape: tuple[int, int]
) -> None:
    data = cns.datasets.load_dataset(name)

    assert data.shape == shape
    assert (
        resources.files("cnsplots.datasets")
        .joinpath("_data")
        .joinpath(f"{name}.csv")
        .is_file()
    )


def test_load_dataset_preserves_gallery_categories() -> None:
    tips = cns.datasets.load_dataset("tips")
    assert list(tips["day"].cat.categories) == ["Thur", "Fri", "Sat", "Sun"]
    assert list(tips["sex"].cat.categories) == ["Male", "Female"]
    assert list(tips["time"].cat.categories) == ["Lunch", "Dinner"]
    assert list(tips["smoker"].cat.categories) == ["Yes", "No"]

    flights = cns.datasets.load_dataset("flights")
    assert list(flights["month"].cat.categories) == [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    penguins = cns.datasets.load_dataset("penguins")
    assert set(penguins["sex"].dropna()) == {"Female", "Male"}


def test_load_dataset_returns_fresh_dataframes() -> None:
    first = cns.datasets.load_dataset("iris")
    first.loc[0, "species"] = "changed"

    second = cns.datasets.load_dataset("iris")
    assert second.loc[0, "species"] == "setosa"


def test_load_dataset_rejects_invalid_names() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        cns.datasets.load_dataset(1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Unknown dataset 'missing'"):
        cns.datasets.load_dataset("missing")


def test_showcase_data_is_offline_deterministic_and_uses_local_rng(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    def fail_network_fixture(name: str):
        raise AssertionError(f"Unexpected network-backed dataset: {name}")

    monkeypatch.setattr(sns, "load_dataset", fail_network_fixture)
    monkeypatch.chdir(tmp_path)
    np.random.seed(123)
    state_before = cast(tuple[object, ...], np.random.get_state())

    first = cns.datasets.get_showcase_data(include_showcase_images=True)

    state_after = cast(tuple[object, ...], np.random.get_state())
    assert state_before[0] == state_after[0]
    np.testing.assert_array_equal(state_before[1], state_after[1])
    assert state_before[2:] == state_after[2:]
    assert len(first) == 14
    image_root = first[-1]
    assert image_root.name == "showcase"
    for name in ["image1.webp", "image2.webp", "image3.webp", "image4.webp"]:
        image = image_root.joinpath(name)
        assert image.is_file()
        with image.open("rb") as stream:
            assert stream.read(4) == b"RIFF"

    second = cns.datasets.gallery.get_showcase_data()
    assert len(second) == 13
    pd.testing.assert_frame_equal(first[0], second[0])
    pd.testing.assert_frame_equal(first[1], second[1])
    pd.testing.assert_frame_equal(first[2], second[2])
    np.testing.assert_allclose(first[3].X, second[3].X)
    pd.testing.assert_frame_equal(first[4], second[4])
    assert first[5] == second[5]
    pd.testing.assert_frame_equal(first[6], second[6])
    pd.testing.assert_frame_equal(first[7], second[7])
    pd.testing.assert_frame_equal(first[8], second[8])
    pd.testing.assert_frame_equal(first[9], second[9])
    pd.testing.assert_frame_equal(first[10], second[10])
    pd.testing.assert_frame_equal(first[11], second[11])
    assert first[12] == second[12]


def test_showcase_data_moved_to_datasets_namespace() -> None:
    assert (
        "caller_file"
        not in inspect.signature(cns.datasets.get_showcase_data).parameters
    )
    assert cns.datasets.get_showcase_data is cns.datasets.gallery.get_showcase_data
    assert not hasattr(cns, "get_showcase_data")
    assert not hasattr(cns.utils, "get_showcase_data")
