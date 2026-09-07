from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest

from cnsplots.plots._categorical import _compute_lollipop_error


@pytest.mark.parametrize("errorbar", ["se", "ci"])
@pytest.mark.parametrize(
    "values",
    [
        [1.0, 9.0],
        [1.0, 2.0, 10.0],
        [0.0, 1.0, 1.0, 4.0, 20.0, 100.0],
        [1.0, 2.0, np.nan, 9.0, 16.0, np.nan],
    ],
)
def test_median_bootstrap_matches_unbatched_reference(
    values: list[float], errorbar: str
) -> None:
    group = pd.Series(values)
    samples = group.dropna().to_numpy(dtype=float)
    indices = np.random.default_rng(0).integers(
        0, len(samples), size=(1000, len(samples))
    )
    bootstrap_medians = np.median(samples[indices], axis=1)
    if errorbar == "se":
        expected = float(bootstrap_medians.std(ddof=1))
    else:
        lower, upper = np.percentile(bootstrap_medians, [2.5, 97.5])
        estimate = float(np.median(samples))
        expected = estimate - float(lower), float(upper) - estimate

    assert _compute_lollipop_error(group, errorbar, "median") == expected


@pytest.mark.parametrize("errorbar", ["se", "ci"])
@pytest.mark.parametrize("values", [[], [np.nan], [3.0], [np.nan, 3.0, np.nan]])
def test_median_bootstrap_skips_groups_with_fewer_than_two_values(
    values: list[float], errorbar: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_rng(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Groups with fewer than two values must not be bootstrapped")

    monkeypatch.setattr(np.random, "default_rng", unexpected_rng)

    assert np.isnan(
        _compute_lollipop_error(pd.Series(values, dtype=float), errorbar, "median")
    )


def test_median_bootstrap_bounds_index_and_sample_allocations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample_size = 10_000
    batch_limit = 64
    original_rng = np.random.default_rng
    original_median = np.median
    index_shapes: list[tuple[int, int]] = []
    sample_shapes: list[tuple[int, int]] = []

    class TrackingRng:
        def __init__(self, seed: int) -> None:
            self.rng = original_rng(seed)

        def integers(self, low: int, high: int, *, size: tuple[int, int]) -> Any:
            assert size[0] <= batch_limit
            indices = self.rng.integers(low, high, size=size)
            index_shapes.append(indices.shape)
            assert indices.nbytes <= batch_limit * sample_size * 8
            return indices

    def track_median(values: np.ndarray, *args: Any, **kwargs: Any) -> Any:
        if values.ndim == 2:
            sample_shapes.append(values.shape)
            assert values.shape[0] <= batch_limit
            assert values.nbytes <= batch_limit * sample_size * 8
        return original_median(values, *args, **kwargs)

    monkeypatch.setattr(np.random, "default_rng", TrackingRng)
    monkeypatch.setattr(np, "median", track_median)

    error = _compute_lollipop_error(
        pd.Series(np.arange(sample_size, dtype=float)), "se", "median"
    )

    assert isinstance(error, float)
    assert error > 0
    assert sample_shapes == index_shapes
    assert sum(rows for rows, _ in index_shapes) == 1000
    assert all(columns == sample_size for _, columns in index_shapes)
