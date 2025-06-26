import lifelines as ll
import numpy as np
import pandas as pd
import patsy
import sklearn as skl
from sklearn.linear_model import LogisticRegressionCV


class CoxModel:
    def __init__(self, data, duration, event, variates):
        self.data = data
        self.duration = duration
        self.event = event
        self.variates = variates
        self.results = None
        self.name = "cox"

    def fit(self):
        df = self.data.copy()
        all_results = []
        for var in self.variates:
            cph = ll.CoxPHFitter()
            cph.fit(df, duration_col=self.duration, event_col=self.event, formula=var)
            summary = cph.summary.reset_index()
            summary["analysis"] = var
            all_results.append(summary)
        df = pd.concat(all_results, ignore_index=True)
        df = df.sort_values("exp(coef)").copy()
        df["exp(coef) lower 95%"] = df["exp(coef)"] - df["exp(coef) lower 95%"]
        df["exp(coef) upper 95%"] = df["exp(coef) upper 95%"] - df["exp(coef)"]
        df["log10_pvalue"] = -np.log10(df["p"])

        def display_label_helper(x):
            if "+" in x["analysis"]:
                return x["analysis"] + " (" + x["covariate"] + ")"
            else:
                return x["analysis"]

        df["display_label"] = df.apply(display_label_helper, axis=1)
        self.results = df[
            [
                "display_label",
                "exp(coef)",
                "exp(coef) lower 95%",
                "exp(coef) upper 95%",
                "log10_pvalue",
            ]
        ]


class LogisticModel:
    def __init__(self, data, event, variates):
        self.data = data
        self.event = event
        self.variates = variates
        self.results = None
        self.name = "logistic"

    def _compute_auc_ci(self, y_true, y_pred_proba, n_bootstrap=1000, alpha=0.05):
        aucs = []
        np.random.seed(42)
        n = len(y_true)
        for _ in range(n_bootstrap):
            indices = np.random.choice(n, n, replace=True)
            if len(np.unique(y_true[indices])) < 2:
                continue
            auc = skl.metrics.roc_auc_score(y_true[indices], y_pred_proba[indices])
            aucs.append(auc)
        aucs = np.array(aucs)
        auc_mean = skl.metrics.roc_auc_score(y_true, y_pred_proba)
        lower = np.percentile(aucs, 100 * alpha / 2)
        upper = np.percentile(aucs, 100 * (1 - alpha / 2))
        return auc_mean, lower, upper

    def fit(self):
        df = self.data.copy()
        all_results = []
        for var in self.variates:
            X = patsy.dmatrix(var, df, return_type="dataframe").drop(
                "Intercept", axis=1
            )
            y = df[self.event].values

            model = LogisticRegressionCV(
                cv=5,
                penalty="l1",
                solver="liblinear",
                random_state=42,
                scoring="roc_auc",
            )
            model.fit(X, y)

            y_pred_proba = model.predict_proba(X)[:, 1]
            auc, auc_lower, auc_upper = self._compute_auc_ci(y, y_pred_proba)

            model_result = {
                "predictor": var,
                "auc": auc,
                "auc_lower": auc_lower,
                "auc_upper": auc_upper,
            }
            all_results.append(model_result)

        results_df = pd.DataFrame(all_results)
        results_df = results_df.sort_values("auc")
        results_df["lower_ci"] = results_df["auc"] - results_df["auc_lower"]
        results_df["upper_ci"] = results_df["auc_upper"] - results_df["auc"]
        self.results = results_df[["predictor", "auc", "lower_ci", "upper_ci"]]
