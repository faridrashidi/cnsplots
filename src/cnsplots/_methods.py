from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd

import re

import lifelines as ll
import numpy as np
import pandas as pd
import patsy
import sklearn as skl
from sklearn.linear_model import LogisticRegressionCV


class CoxModel:
    """
    Cox proportional hazards regression model for survival analysis.

    This class fits Cox proportional hazards models to assess the relationship
    between predictor variables and time-to-event data. Supports multiple
    covariates and optional stratification by a grouping variable.

    Parameters
    ----------
    data : pd.DataFrame
        Input DataFrame containing survival data and covariates.
    duration : str
        Column name for the time-to-event or time-to-censoring variable.
    event : str
        Column name for the event indicator (1 = event occurred, 0 = censored).
    variates : list of str
        List of formula strings specifying the covariates to test. Each formula
        can be a simple variable name or a Patsy formula (e.g., 'age',
        'C(treatment)', 'age + C(stage)').
    hue : str, optional
        Column name for grouping variable. If provided, fits separate models
        for each group. Default is None (single model for all data).

    Attributes
    ----------
    results : pd.DataFrame
        Results DataFrame containing hazard ratios, confidence intervals,
        p-values, and -log10(p-values) for all fitted models. Available after
        calling fit().
    name : str
        Model type identifier, always 'cox'.

    See Also
    --------
    survivalplot : Create a Kaplan-Meier survival plot.
    forestplot : Create a forest plot from model results.
    LogisticModel : Logistic regression for binary outcomes.

    Notes
    -----
    The fit() method performs univariate Cox regression for each variate,
    optionally stratified by hue groups. Results include:

    - exp(coef): Hazard ratio
    - exp(coef) lower 95%, exp(coef) upper 95%: 95% confidence interval
    - p: P-value from Wald test
    - log10_pvalue: -log10(p-value) for visualization

    Hazard ratio interpretation:
    - HR = 1: No effect
    - HR > 1: Increased hazard (worse outcome)
    - HR < 1: Decreased hazard (better outcome)

    Examples
    --------
    >>> import cnsplots as cns
    >>> # Simple Cox model
    >>> model = cns.CoxModel(
    ...     data=df,
    ...     duration="time_months",
    ...     event="death",
    ...     variates=["age", "C(stage)", "biomarker"],
    ... )
    >>> model.fit()
    >>> cns.forestplot(model)

    >>> # Stratified by treatment group
    >>> model = cns.CoxModel(
    ...     data=df,
    ...     duration="time_months",
    ...     event="death",
    ...     variates=["age", "stage"],
    ...     hue="treatment",
    ... )
    >>> model.fit()
    >>> print(model.results)
    """

    def __init__(
        self,
        data: pd.DataFrame,
        duration: str,
        event: str,
        variates: list[str],
        hue: str | None = None,
    ) -> None:
        self.data = data
        self.duration = duration
        self.event = event
        self.variates = variates
        self.hue = hue
        self.results = None
        self.name = "cox"

    def fit(self) -> None:
        """
        Fit Cox proportional hazards models for all specified variates.

        This method fits a separate Cox model for each variate, optionally
        stratified by hue groups. Results are stored in the results attribute.

        Returns
        -------
        None
            Results are stored in self.results as a DataFrame.

        Notes
        -----
        The results DataFrame contains:
        - display_label: Cleaned variable name for plotting
        - exp(coef): Hazard ratio
        - exp(coef) lower_err, upper_err: Error bars for forest plot
        - exp(coef) lower 95%, upper 95%: Confidence interval bounds
        - log10_pvalue: -log10(p-value)
        - analysis: Original formula string
        - covariate: Variable name from model
        - hue_group: Group name (or 'All' if no grouping)
        - p: P-value

        The display_label is automatically extracted from formula strings,
        removing formula syntax (Q(), C(), np.log(), etc.) for cleaner
        visualization.

        Examples
        --------
        >>> model = cns.CoxModel(df, "time", "event", ["age", "treatment"])
        >>> model.fit()
        >>> print(model.results[["display_label", "exp(coef)", "p"]])
        """
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
            analysis_str = (
                x["analysis"].split(" + ")[0] if "+" in x["analysis"] else x["analysis"]
            )
            pattern = re.compile(
                r'(?:Q\((?:\'|")?(.*?)(?:\'|")?\)|C\(|np\.log\(|^|\+|\s)([a-zA-Z_]+)?(?=\s|\+|,|$|\))'
            )
            matches = pattern.findall(analysis_str)
            for match in matches:
                result = match[0] if match[0] else match[1]
                if result:
                    return result + ("*" if "+" in x["analysis"] else "")
            return None

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
    """
    Logistic regression model with cross-validation for binary classification.

    This class fits L1-regularized logistic regression models with 5-fold
    cross-validation to predict binary outcomes and assess predictor performance
    using ROC-AUC with bootstrap confidence intervals.

    Parameters
    ----------
    data : pd.DataFrame
        Input DataFrame containing the outcome variable and predictors.
    event : str
        Column name for the binary outcome variable (0 or 1).
    variates : list of str
        List of formula strings specifying the predictors to test. Each formula
        can be a simple variable name or a Patsy formula (e.g., 'age',
        'C(treatment)', 'age + stage').
    hue : str, optional
        Column name for grouping variable. If provided, fits separate models
        for each group. Default is None (single model for all data).

    Attributes
    ----------
    results : pd.DataFrame
        Results DataFrame containing AUC values and confidence intervals for
        all fitted models. Available after calling fit().
    name : str
        Model type identifier, always 'logistic'.

    See Also
    --------
    CoxModel : Cox proportional hazards model for survival data.
    forestplot : Create a forest plot from model results.
    rocplot : Create ROC curves for binary classifiers.

    Notes
    -----
    The fit() method performs:
    - L1-regularized logistic regression with 5-fold cross-validation
    - Automatic penalty parameter selection via cross-validation
    - Bootstrap confidence intervals for AUC (1000 iterations, alpha=0.05)

    Models use the liblinear solver optimized for L1 regularization and are
    scored using ROC-AUC during cross-validation.

    AUC interpretation:
    - AUC = 1.0: Perfect discrimination
    - AUC = 0.5: No discrimination (random)
    - AUC > 0.7: Acceptable discrimination
    - AUC > 0.8: Excellent discrimination

    Examples
    --------
    >>> import cnsplots as cns
    >>> # Simple logistic model
    >>> model = cns.LogisticModel(
    ...     data=df, event="disease", variates=["age", "C(treatment)", "biomarker"]
    ... )
    >>> model.fit()
    >>> cns.forestplot(model)

    >>> # Stratified by cohort
    >>> model = cns.LogisticModel(
    ...     data=df, event="response", variates=["age", "stage"], hue="cohort"
    ... )
    >>> model.fit()
    >>> print(model.results)
    """

    def __init__(
        self,
        data: pd.DataFrame,
        event: str,
        variates: list[str],
        hue: str | None = None,
    ) -> None:
        self.data = data
        self.event = event
        self.variates = variates
        self.hue = hue
        self.results = None
        self.name = "logistic"

    def _compute_auc_ci(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        n_bootstrap: int = 1000,
        alpha: float = 0.05,
    ) -> tuple[float, float, float]:
        """
        Compute bootstrap confidence interval for ROC-AUC.

        Parameters
        ----------
        y_true : array-like
            True binary labels.
        y_pred_proba : array-like
            Predicted probabilities.
        n_bootstrap : int, default: 1000
            Number of bootstrap iterations.
        alpha : float, default: 0.05
            Significance level for confidence interval (0.05 = 95% CI).

        Returns
        -------
        tuple of float
            (auc_mean, lower_bound, upper_bound)
        """
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
        return auc_mean, float(lower), float(upper)

    def fit(self) -> None:
        """
        Fit logistic regression models for all specified variates.

        This method fits a separate L1-regularized logistic regression model
        with 5-fold cross-validation for each variate, optionally stratified
        by hue groups. Results are stored in the results attribute.

        Returns
        -------
        None
            Results are stored in self.results as a DataFrame.

        Notes
        -----
        The results DataFrame contains:
        - predictor: Formula string for the predictor(s)
        - auc: Area under ROC curve
        - lower_ci: Lower error bound (auc - lower confidence limit)
        - upper_ci: Upper error bound (upper confidence limit - auc)
        - hue_group: Group name (or 'All' if no grouping)

        For each model:
        1. Design matrix is created using Patsy (supports formulas)
        2. LogisticRegressionCV fits with L1 penalty and 5-fold CV
        3. AUC and 95% CI are computed via bootstrap (1000 iterations)

        Warnings are printed for hue groups with no outcome variance.
        Errors during fitting are caught and reported.

        Examples
        --------
        >>> model = cns.LogisticModel(df, "outcome", ["age", "treatment"])
        >>> model.fit()
        >>> print(model.results[["predictor", "auc", "hue_group"]])
        """
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


def prerank(
    data: pd.DataFrame,
    gene_sets: str | dict[str, list[str]],
    name_gene: str | None = None,
    name_rank: str | None = None,
    permutation_num: int = 1000,
) -> pd.DataFrame:
    """
    Perform pre-ranked Gene Set Enrichment Analysis (GSEA).

    This function runs GSEA using a pre-ranked gene list, identifying gene sets
    that are enriched at the top or bottom of the ranking. Results are filtered
    and formatted for visualization.

    Parameters
    ----------
    data : pd.DataFrame
        Input DataFrame containing genes and their ranking metric.
    gene_sets : str or dict
        Gene set database name (e.g., 'KEGG_2021_Human', 'GO_Biological_Process_2021')
        or a dictionary mapping set names to lists of genes.
    name_gene : str
        Column name for gene symbols/identifiers.
    name_rank : str
        Column name for the ranking metric (e.g., log2 fold change, -log10 p-value,
        or a composite metric like log2FC * -log10(p)).
    permutation_num : int, default: 1000
        Number of permutations for significance testing.

    Returns
    -------
    pd.DataFrame
        Filtered and formatted GSEA results containing:

        - Term: Gene set name
        - Clean_Term: Cleaned gene set name with improved formatting
        - NES: Normalized Enrichment Score
        - FDR q-val: False Discovery Rate q-value
        - Other columns from gseapy results

        Results are filtered for FDR q-val < 0.25 and \|NES\| > 1.5, and sorted
        by absolute NES value (descending).

    See Also
    --------
    gseaplot : Create a GSEA dot plot visualization.
    volcanoplot : Create a volcano plot for differential expression.

    Notes
    -----
    The function performs several preprocessing steps:

    1. Renames columns to 'Gene' and 'Rank'
    2. Converts gene names to uppercase and strips whitespace
    3. Runs gseapy.prerank with min_size=15, max_size=1000
    4. Cleans term names by:
       - Removing common prefixes (``HALLMARK_``, ``KEGG_``, ``REACTOME_``, ``GO_``, ``BIOCARTA_``)
       - Replacing underscores with spaces
       - Converting to title case
       - Fixing common abbreviations (NF-κB, IL-n, TGF, mTOR, DNA, mRNA)
       - Lowercasing "via" and "and"

    NES interpretation:
    - NES > 0: Enriched in genes with positive ranking metric
    - NES < 0: Enriched in genes with negative ranking metric
    - \|NES\| > 1.5: Moderate enrichment
    - \|NES\| > 2.0: Strong enrichment

    Examples
    --------
    >>> import cnsplots as cns
    >>> # Prepare ranked gene list
    >>> de_results["rank"] = de_results["log2FC"] * -np.log10(de_results["pvalue"])
    >>> de_results = de_results.sort_values("rank", ascending=False)
    >>>
    >>> # Run pre-ranked GSEA
    >>> gsea_results = cns.prerank(
    ...     data=de_results,
    ...     gene_sets="KEGG_2021_Human",
    ...     name_gene="gene_symbol",
    ...     name_rank="rank",
    ...     permutation_num=1000,
    ... )
    >>>
    >>> # Visualize results
    >>> cns.gseaplot(gsea_results, y="Clean_Term", top_term=20)
    """
    try:
        import gseapy as gp
    except ImportError:
        print("pip install gseapy")

    rnk = data.copy()
    rnk = rnk[[name_gene, name_rank]]
    rnk.columns = ["Gene", "Rank"]
    rnk["Gene"] = rnk["Gene"].str.strip().str.upper()
    gsea_res = gp.prerank(
        rnk=rnk,
        gene_sets=gene_sets,  # type: ignore[arg-type]  # gseapy accepts dict[str, list[str]] at runtime
        min_size=15,
        max_size=1000,
        permutation_num=permutation_num,
        seed=42,
    )

    def clean_term(term):
        term = re.sub(r"^(HALLMARK_|KEGG_|REACTOME_|GO_|BIOCARTA_)", "", term)
        term = term.replace("_", " ")
        term = term.title()

        term = re.sub(r"Nfk[ab]", "NF-κB", term, flags=re.IGNORECASE)
        term = re.sub(r"Il(\d+)", r"IL-\1", term)
        term = re.sub(r"Tgf", "TGF", term, flags=re.IGNORECASE)
        term = re.sub(r"Mtor", "mTOR", term, flags=re.IGNORECASE)
        term = re.sub(r"Dna", "DNA", term, flags=re.IGNORECASE)
        term = re.sub(r"Mrna", "mRNA", term, flags=re.IGNORECASE)

        term = term.replace("Via ", "via ")
        term = term.replace("And ", "and ")
        return term

    assert gsea_res.res2d is not None
    gsea_df = gsea_res.res2d.copy()
    gsea_df["Clean_Term"] = gsea_df["Term"].apply(clean_term)
    gsea_df = gsea_df[(gsea_df["FDR q-val"] < 0.25) & (gsea_df["NES"].abs() > 1.5)]
    gsea_df = gsea_df.sort_values(by="NES", key=abs, ascending=False)
    return gsea_df
