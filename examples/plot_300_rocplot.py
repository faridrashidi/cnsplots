"""
rocplot
-------

Create ROC (Receiver Operating Characteristic) curves for classifier evaluation.

ROC plots visualize the trade-off between true positive rate and false
positive rate at various classification thresholds. cnsplots automatically
calculates AUC values and displays them in the legend.
"""

# %%
# Load packages
# ~~~~~~~~~~~~~
import numpy as np
import pandas as pd
import seaborn as sns

import cnsplots as cns

# %%
# Generate classification data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create synthetic predictions from multiple models.
np.random.seed(42)
iris = sns.load_dataset("iris")
iris["true_labels"] = (iris["species"] == "setosa").astype(int)
n_samples = len(iris)
iris["model1_prob"] = np.clip(
    iris["true_labels"] + np.random.normal(0, 0.4, n_samples), 0, 1
)
iris["model2_prob"] = np.clip(
    iris["true_labels"] + np.random.normal(0, 0.7, n_samples), 0, 1
)
iris["model3_prob"] = np.random.uniform(0, 1, n_samples)


# %%
# Compare multiple classifiers
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ROC curves for three models with different performance.
cns.figure(150, 150)
cns.rocplot(
    iris,
    "true_labels",
    ["model1_prob", "model2_prob", "model3_prob"],
)
cns.take_legend_out()


# %%
# Single model ROC curve
# ~~~~~~~~~~~~~~~~~~~~~~
# Display ROC for the best performing model.
cns.figure(150, 150)
ax = cns.rocplot(iris, "true_labels", ["model1_prob"])
ax.set_title("Best Model ROC")


# %%
# Two model comparison
# ~~~~~~~~~~~~~~~~~~~~
# Compare the two best models.
cns.figure(150, 150)
ax = cns.rocplot(iris, "true_labels", ["model1_prob", "model2_prob"])
ax.set_title("Top 2 Models")
cns.take_legend_out()


# %%
# Random classifier baseline
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Show that random predictions give AUC = 0.5.
cns.figure(150, 150)
ax = cns.rocplot(iris, "true_labels", ["model3_prob"])
ax.set_title("Random Classifier")


# %%
# Biomarker classification
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Simulate biomarker-based disease classification.
np.random.seed(42)
n_patients = 200
biomarker_data = pd.DataFrame(
    {
        "disease": np.random.binomial(1, 0.4, n_patients),
    }
)
# Good biomarker
biomarker_data["marker_A"] = np.clip(
    biomarker_data["disease"] * 0.7 + np.random.normal(0.2, 0.2, n_patients), 0, 1
)
# Medium biomarker
biomarker_data["marker_B"] = np.clip(
    biomarker_data["disease"] * 0.5 + np.random.normal(0.3, 0.25, n_patients), 0, 1
)
# Poor biomarker
biomarker_data["marker_C"] = np.clip(
    biomarker_data["disease"] * 0.2 + np.random.normal(0.4, 0.3, n_patients), 0, 1
)

cns.figure(150, 150)
ax = cns.rocplot(
    biomarker_data,
    "disease",
    ["marker_A", "marker_B", "marker_C"],
)
ax.set_title("Biomarker Comparison")
cns.take_legend_out()


# %%
# Gene signature classification
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare gene signatures for predicting response.
np.random.seed(42)
n_samples = 150
gene_sig = pd.DataFrame(
    {
        "responder": np.random.binomial(1, 0.35, n_samples),
    }
)
gene_sig["signature_1"] = np.clip(
    gene_sig["responder"] * 0.6 + np.random.normal(0.25, 0.2, n_samples), 0, 1
)
gene_sig["signature_2"] = np.clip(
    gene_sig["responder"] * 0.8 + np.random.normal(0.1, 0.15, n_samples), 0, 1
)
gene_sig["signature_3"] = np.clip(
    gene_sig["responder"] * 0.4 + np.random.normal(0.35, 0.25, n_samples), 0, 1
)

cns.figure(150, 150)
ax = cns.rocplot(
    gene_sig,
    "responder",
    ["signature_1", "signature_2", "signature_3"],
)
ax.set_title("Gene Signatures")
cns.take_legend_out()


# %%
# Perfect vs poor classifiers
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contrast perfect separation with random.
np.random.seed(42)
n = 100
contrast_data = pd.DataFrame(
    {
        "true": np.concatenate([np.zeros(n // 2), np.ones(n // 2)]),
    }
)
# Near-perfect classifier
contrast_data["perfect"] = np.concatenate(
    [np.random.uniform(0, 0.3, n // 2), np.random.uniform(0.7, 1, n // 2)]
)
# Random classifier
contrast_data["random"] = np.random.uniform(0, 1, n)

cns.figure(150, 150)
ax = cns.rocplot(contrast_data, "true", ["perfect", "random"])
ax.set_title("Perfect vs Random")
cns.take_legend_out()


# %%
# Machine learning model comparison
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Simulate predictions from different ML algorithms.
np.random.seed(42)
n = 300
ml_data = pd.DataFrame(
    {
        "outcome": np.random.binomial(1, 0.3, n),
    }
)
# Random Forest
ml_data["rf_pred"] = np.clip(
    ml_data["outcome"] * 0.75 + np.random.normal(0.15, 0.15, n), 0, 1
)
# Logistic Regression
ml_data["lr_pred"] = np.clip(
    ml_data["outcome"] * 0.6 + np.random.normal(0.25, 0.2, n), 0, 1
)
# SVM
ml_data["svm_pred"] = np.clip(
    ml_data["outcome"] * 0.7 + np.random.normal(0.18, 0.18, n), 0, 1
)
# Neural Network
ml_data["nn_pred"] = np.clip(
    ml_data["outcome"] * 0.8 + np.random.normal(0.12, 0.12, n), 0, 1
)

cns.figure(160, 160)
ax = cns.rocplot(
    ml_data,
    "outcome",
    ["rf_pred", "lr_pred", "svm_pred", "nn_pred"],
)
ax.set_title("ML Model Comparison")
cns.take_legend_out()


# %%
# Comparing ROC curves with multipanel
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Side-by-side ROC analyses for different endpoints.
np.random.seed(42)
n = 200

# Endpoint 1: Overall survival
os_data = pd.DataFrame(
    {
        "event": np.random.binomial(1, 0.4, n),
    }
)
os_data["model_A"] = np.clip(
    os_data["event"] * 0.65 + np.random.normal(0.2, 0.2, n), 0, 1
)
os_data["model_B"] = np.clip(
    os_data["event"] * 0.5 + np.random.normal(0.3, 0.25, n), 0, 1
)

# Endpoint 2: Response
resp_data = pd.DataFrame(
    {
        "event": np.random.binomial(1, 0.35, n),
    }
)
resp_data["model_A"] = np.clip(
    resp_data["event"] * 0.7 + np.random.normal(0.18, 0.18, n), 0, 1
)
resp_data["model_B"] = np.clip(
    resp_data["event"] * 0.55 + np.random.normal(0.28, 0.22, n), 0, 1
)

mp = cns.multipanel(max_width=350)

mp.panel("A", 130, 130)
cns.rocplot(os_data, "event", ["model_A", "model_B"])
mp.get_axes("A").legend().remove()
mp.get_axes("A").set_title("Overall Survival")

mp.panel("B", 130, 130)
cns.rocplot(resp_data, "event", ["model_A", "model_B"])
mp.get_axes("B").set_title("Response")


# %%
# Training vs validation performance
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Compare model performance on different datasets.
np.random.seed(42)
n = 150

# Training set (often overfit)
train_data = pd.DataFrame(
    {
        "outcome": np.random.binomial(1, 0.4, n),
    }
)
train_data["pred"] = np.clip(
    train_data["outcome"] * 0.85 + np.random.normal(0.1, 0.1, n), 0, 1
)

# Validation set (more realistic)
val_data = pd.DataFrame(
    {
        "outcome": np.random.binomial(1, 0.4, n),
    }
)
val_data["pred"] = np.clip(
    val_data["outcome"] * 0.6 + np.random.normal(0.25, 0.2, n), 0, 1
)

mp = cns.multipanel(max_width=350)

mp.panel("A", 130, 130)
cns.rocplot(train_data, "outcome", ["pred"])
mp.get_axes("A").set_title("Training Set")

mp.panel("B", 130, 130)
cns.rocplot(val_data, "outcome", ["pred"])
mp.get_axes("B").set_title("Validation Set")


# %%
# Multi-class problem (one-vs-rest)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ROC for each class in a multi-class setting.
np.random.seed(42)
n = 200

# Create three classes
classes = np.random.choice([0, 1, 2], n, p=[0.4, 0.35, 0.25])
multiclass = pd.DataFrame({"true_class": classes})

# Predictions for class 0
multiclass["class0_label"] = (multiclass["true_class"] == 0).astype(int)
multiclass["class0_prob"] = np.clip(
    multiclass["class0_label"] * 0.6 + np.random.normal(0.25, 0.2, n), 0, 1
)

# Predictions for class 1
multiclass["class1_label"] = (multiclass["true_class"] == 1).astype(int)
multiclass["class1_prob"] = np.clip(
    multiclass["class1_label"] * 0.7 + np.random.normal(0.2, 0.18, n), 0, 1
)

# Predictions for class 2
multiclass["class2_label"] = (multiclass["true_class"] == 2).astype(int)
multiclass["class2_prob"] = np.clip(
    multiclass["class2_label"] * 0.5 + np.random.normal(0.3, 0.25, n), 0, 1
)

mp = cns.multipanel(max_width=450)

mp.panel("A", 110, 110)
cns.rocplot(multiclass, "class0_label", ["class0_prob"])
mp.get_axes("A").set_title("Class 0 vs Rest")

mp.panel("B", 110, 110)
cns.rocplot(multiclass, "class1_label", ["class1_prob"])
mp.get_axes("B").set_title("Class 1 vs Rest")

mp.panel("C", 110, 110, margin_right=0)
cns.rocplot(multiclass, "class2_label", ["class2_prob"])
mp.get_axes("C").set_title("Class 2 vs Rest")
