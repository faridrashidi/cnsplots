"""
Probability Calibration
-----------------------

Compare mean predicted probabilities with observed event frequencies using
uniform or quantile bins. In an analysis, supply held-out or out-of-fold
probabilities for the positive class; cnsplots never fits or recalibrates a
model. This example uses synthetic observations and requires no downloads.

The Brier score measures overall probabilistic prediction quality, including
calibration and discrimination. Lower scores are better; the reliability curve
shows calibration directly. All probabilities and frequencies are on [0, 1].
"""

# %%
# Generate synthetic predictions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import numpy as np
import pandas as pd

import cnsplots as cns

rng = np.random.default_rng(42)
probability = rng.uniform(0.02, 0.98, 500)
data = pd.DataFrame(
    {
        "outcome": np.where(rng.binomial(1, probability), "case", "control"),
        "Reference": probability,
        "Overconfident": probability**2 / (probability**2 + (1 - probability) ** 2),
    }
)

# %%
# Compare binning strategies
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Uniform bins have equal widths. Quantile bins target similar sample counts
# using separate boundaries for each model. Ties may still leave bins empty.
# Missing/nonfinite probabilities, probabilities outside [0, 1], missing labels,
# and outcomes with fewer or more than two classes are rejected.
mp = cns.multipanel(max_width=450)
uniform_ax = mp.panel("A", width=150, height=150)
cns.calibrationplot(
    data,
    "outcome",
    ["Reference", "Overconfident"],
    pos_label="case",
    n_bins=8,
    ax=uniform_ax,
)
uniform_ax.set_title("Uniform bins")

quantile_ax = mp.panel("B", width=150, height=150)
cns.calibrationplot(
    data,
    "outcome",
    ["Reference", "Overconfident"],
    pos_label="case",
    n_bins=8,
    strategy="quantile",
    brier_show=False,
    ax=quantile_ax,
)
quantile_ax.set_title("Quantile bins")

# %%
# Inspect counts and probability quality
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Results follow model-column order, then ascending bin order. Empty bins have
# count zero and NaN means and are omitted from plotted lines. Returned tables
# are copies; they can be edited or exported without changing the plotted data.
# Brier scores remain available even when their legend annotations are hidden.
results = cns.get_calibration_results(quantile_ax)
print(results["bins"].to_string(index=False))
print(results["metrics"].to_string(index=False))
