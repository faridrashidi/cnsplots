import re

import lifelines as ll
import numpy as np
import pandas as pd
import patsy
import sklearn as skl
from sklearn.linear_model import LogisticRegressionCV


class CoxModel:
    def __init__(self, data, duration, event, variates, hue=None):
        self.data = data
        self.duration = duration
        self.event = event
        self.variates = variates
        self.hue = hue
        self.results = None
        self.name = "cox"

    def fit(self):
        df = self.data.copy()
        all_results = []

        if self.hue is None:
            for var in self.variates:
                cph = ll.CoxPHFitter()
                cph.fit(
                    df, duration_col=self.duration, event_col=self.event, formula=var
                )
                summary = cph.summary.iloc[[0]].reset_index()
                summary["analysis"] = var
                summary["hue_group"] = "All"
                all_results.append(summary)
        else:
            hue_groups = df[self.hue].unique()
            for hue_group in hue_groups:
                hue_data = df[df[self.hue] == hue_group].copy()
                for var in self.variates:
                    cph = ll.CoxPHFitter()
                    cph.fit(
                        hue_data,
                        duration_col=self.duration,
                        event_col=self.event,
                        formula=var,
                    )
                    summary = cph.summary.iloc[[0]].reset_index()
                    summary["analysis"] = var
                    summary["hue_group"] = str(hue_group)
                    all_results.append(summary)

        df = pd.concat(all_results, ignore_index=True)
        df = df.sort_values(["exp(coef)", "hue_group"], ascending=False).copy()

        df["exp(coef) lower_err"] = df["exp(coef)"] - df["exp(coef) lower 95%"]
        df["exp(coef) upper_err"] = df["exp(coef) upper 95%"] - df["exp(coef)"]
        df["log10_pvalue"] = -np.log10(df["p"])

        def display_label_helper(x):
            pattern = r'(?:Q\((?:\'|")?(.*?)(?:\'|")?\)|C\(|np\.log\(|^|\+|\s)([a-zA-Z_]+)?(?=\s|\+|,|$|\))'
            matches = re.findall(pattern, x["analysis"])
            out = None
            for match in matches:
                out = match[0] if match[0] else match[1]
            if "+" in x["analysis"]:
                return out + "*"
            else:
                return out

        df["display_label"] = df.apply(display_label_helper, axis=1)

        self.results = df[
            [
                "display_label",
                "exp(coef)",
                "exp(coef) lower_err",
                "exp(coef) upper_err",
                "exp(coef) lower 95%",
                "exp(coef) upper 95%",
                "log10_pvalue",
                "analysis",
                "covariate",
                "hue_group",
                "p",
            ]
        ]


class LogisticModel:
    def __init__(self, data, event, variates, hue=None):
        self.data = data
        self.event = event
        self.variates = variates
        self.hue = hue
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

        if self.hue is None:
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
                    "hue_group": "All",
                }
                all_results.append(model_result)
        else:
            hue_groups = df[self.hue].unique()
            for hue_group in hue_groups:
                hue_data = df[df[self.hue] == hue_group].copy()

                for var in self.variates:
                    try:
                        X = patsy.dmatrix(var, hue_data, return_type="dataframe").drop(
                            "Intercept", axis=1
                        )
                        y = hue_data[self.event].values
                        if len(np.unique(y)) < 2:
                            print(
                                f"Warning: No variance in outcome for {var} in hue"
                                f" group {hue_group}"
                            )
                            continue
                        model = LogisticRegressionCV(
                            cv=5,
                            penalty="l1",
                            solver="liblinear",
                            random_state=42,
                            scoring="roc_auc",
                        )
                        model.fit(X, y)
                        y_pred_proba = model.predict_proba(X)[:, 1]
                        auc, auc_lower, auc_upper = self._compute_auc_ci(
                            y, y_pred_proba
                        )
                        model_result = {
                            "predictor": var,
                            "auc": auc,
                            "auc_lower": auc_lower,
                            "auc_upper": auc_upper,
                            "hue_group": str(hue_group),
                        }
                        all_results.append(model_result)
                    except Exception as e:
                        print(f"Error fitting {var} for hue group {hue_group}: {e}")
                        continue

        results_df = pd.DataFrame(all_results)
        if len(results_df) == 0:
            print("No successful model fits")
            return
        results_df = results_df.sort_values(
            ["auc", "hue_group"], ascending=False
        ).copy()
        results_df["lower_ci"] = results_df["auc"] - results_df["auc_lower"]
        results_df["upper_ci"] = results_df["auc_upper"] - results_df["auc"]
        self.results = results_df[
            ["predictor", "auc", "lower_ci", "upper_ci", "hue_group"]
        ]
