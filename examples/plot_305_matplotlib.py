"""
matplotlib
----------

Use native matplotlib plotting with cnsplots sizing, styling, and export helpers.

These examples intentionally stick to matplotlib's plotting API and only use
``cns.figure()`` and ``cns.save()`` from cnsplots.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
from pathlib import Path
import tempfile

import matplotlib.pyplot as plt
import numpy as np

import cnsplots as cns


# %%
# Generate synthetic assay data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create smooth trajectories plus a noisy measurement track.
rng = np.random.default_rng(42)
time = np.linspace(0, 6 * np.pi, 200)
signal_a = np.sin(time) + 0.15 * np.cos(time / 2)
signal_b = 0.75 * np.cos(time - 0.8)
observed = signal_a + rng.normal(0, 0.12, size=time.size)


# %%
# Line plot with confidence band
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# cnsplots handles the figure setup while matplotlib draws everything.
cns.figure(160, 220)
ax = plt.gca()
ax.plot(time, signal_a, color="#1f77b4", linewidth=2, label="Condition A")
ax.plot(time, signal_b, color="#d62728", linewidth=2, label="Condition B")
ax.fill_between(
    time,
    signal_a - 0.18,
    signal_a + 0.18,
    color="#1f77b4",
    alpha=0.18,
    linewidth=0,
)
ax.set_xlabel("Time (hours)")
ax.set_ylabel("Normalized signal")
ax.set_title("Matplotlib with cns.figure")
ax.legend(frameon=False, loc="upper right")


# %%
# Two-panel matplotlib layout
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# The cnsplots canvas also works with matplotlib's subplot helpers.
cns.figure(160, 300)
fig = plt.gcf()
ax_left, ax_right = fig.subplots(1, 2)

ax_left.scatter(time[::4], observed[::4], color="#2ca02c", s=14, alpha=0.8)
ax_left.plot(time, signal_a, color="#1f77b4", linewidth=1.8)
ax_left.set_xlabel("Time (hours)")
ax_left.set_ylabel("Observed signal")
ax_left.set_title("Measurements")

window = np.linspace(1, 6, 6)
means = np.array([observed[i * 30 : (i + 1) * 30].mean() for i in range(6)])
errors = np.array([observed[i * 30 : (i + 1) * 30].std() for i in range(6)])
ax_right.errorbar(
    window,
    means,
    yerr=errors,
    fmt="o-",
    color="#9467bd",
    linewidth=1.8,
    capsize=3,
)
ax_right.set_xlabel("Replicate")
ax_right.set_ylabel("Mean +/- SD")
ax_right.set_title("Summary")

fig.tight_layout()


# %%
# Save a matplotlib figure with cns.save
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Export the current matplotlib figure using the cnsplots save helper.
export_dir = Path(tempfile.gettempdir()) / "cnsplots-gallery"
export_dir.mkdir(parents=True, exist_ok=True)

cns.figure(140, 180)
ax = plt.gca()
ax.plot(time, signal_a, color="#1f77b4", linewidth=2, label="Condition A")
ax.plot(time, observed, color="#7f7f7f", linewidth=1.2, alpha=0.85, label="Observed")
ax.set_xlabel("Time (hours)")
ax.set_ylabel("Signal")
ax.set_title("Saved with cns.save")
ax.legend(frameon=False, loc="upper right")

export_path = export_dir / "matplotlib_with_cns.svg"
cns.save(export_path)
print(f"Saved demo figure to {export_path}")
