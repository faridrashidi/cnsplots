"""
Precision-Recall Curves
------------------------

Evaluate binary prediction scores with precision-recall curves. The legend
reports average precision (AP), which weights precision by increases in recall,
and a horizontal reference marks the positive-class prevalence. AP differs from
trapezoidal area under a precision-recall curve.
"""

# %%
# Generate imbalanced binary predictions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This synthetic example needs no downloaded datasets. Larger scores indicate
# stronger evidence for a positive outcome; decision scores need not lie in [0, 1].
import numpy as np
import pandas as pd

import cnsplots as cns

rng = np.random.default_rng(42)
truth = np.r_[np.zeros(160, dtype=int), np.ones(40, dtype=int)]
data = pd.DataFrame(
    {
        "outcome": truth,
        "Model A": truth + rng.normal(0, 0.6, len(truth)),
        "Model B": truth + rng.normal(0, 1.0, len(truth)),
    }
)

# %%
# Compare models and retrieve exact values
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Recall and precision are unitless fractions. Models appear in the supplied
# column order. AP and prevalence are descriptive metrics: no confidence bands
# or statistical comparison tests are calculated.
cns.figure(180, 150)
ax = cns.precisionrecallplot(data, "outcome", ["Model A", "Model B"])
ax.set_title("Imbalanced classification")
results = cns.get_precision_recall_results(ax)
print(results["metrics"])

# The last curve row per model is sklearn's (recall=0, precision=1) endpoint.
# Its threshold is NaN because the endpoint has no associated score cutoff.
print(results["curves"].groupby("model", sort=False).tail(1))

# %%
# Explicit positive labels in a multipanel figure
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Both classes must be observed. Missing labels/scores and nonfinite values are
# rejected, so all reported counts and prevalence refer to the complete input.
# Plotting leaves the caller's DataFrame unchanged.
labeled = data.assign(status=np.where(truth == 1, "case", "control"))
mp = cns.multipanel(max_width=380)
mp.panel("A", 130, 130)
cns.precisionrecallplot(labeled, "status", "Model A", pos_label="case")
mp.get_axes("A").set_title("Model A")
mp.panel("B", 130, 130)
target = mp.get_axes("B")
cns.precisionrecallplot(labeled, "status", "Model B", pos_label="case", ax=target)
target.set_title("Model B")
