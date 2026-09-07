from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, Protocol, cast

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd

import inspect
import re
import warnings

import numpy as np
import pandas as pd
import sklearn as skl
from patsy.build import build_design_matrices
from patsy.desc import ModelDesc
from patsy.eval import EvalEnvironment
from patsy.highlevel import dmatrix
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold, check_cv
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from cnsplots._validation import (
    validate_column_type,
    validate_columns_exist,
    validate_dataframe,
    validate_dataframe_not_empty,
    validate_no_nulls,
)


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
        Values must be finite, real, non-negative numbers, excluding booleans.
    event : str
        Column name for the event indicator (1 or True = event occurred,
        0 or False = censored). Cohorts with all events observed are supported.
    variates : list of str
        List of formula strings specifying the covariates to test. Each formula
        can be a simple variable name or a Patsy formula (e.g., 'age',
        'C(treatment)', 'age + C(stage)').
    hue : str, optional
        Column name for grouping variable. If provided, fits separate models
        for each group. Default is None (single model for all data).
    retain_estimators : bool, optional
        Retain successful fitted lifelines estimators in ``estimators``.
        Default is False because these objects contain training data.

    Attributes
    ----------
    results : pd.DataFrame
        Results DataFrame containing hazard ratios, confidence intervals,
        p-values, and -log10(p-values) for all fitted models. Available after
        calling fit().
    diagnostics : pd.DataFrame
        One row per requested formula and hue group, including failed fits.
        Columns are ``analysis_id``, ``analysis``, ``hue_group``, ``status``,
        ``n_input``, ``n_analyzed``, ``n_dropped``, ``event_count``, and
        ``failure_reason``. Counts describe rows with complete formula
        predictors, even when fitting fails; unknown counts are null.
    estimators : dict of int to lifelines.CoxPHFitter
        Successful fitted estimators keyed by diagnostic ``analysis_id``,
        populated only when ``retain_estimators=True``. IDs follow requested
        group/formula order, starting at zero. These are the estimators used
        for the reported hazard ratios; no additional refit is performed.
    name : str
        Model type identifier, always 'cox'.

    See Also
    --------
    survivalplot : Create a Kaplan-Meier survival plot.
    forestplot : Create a forest plot from model results.
    LogisticModel : Logistic regression for binary outcomes.

    Notes
    -----
    The fit() method fits one Cox regression model for each formula,
    optionally stratified by hue groups. Every fitted coefficient is retained.
    Results include:

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
        *,
        retain_estimators: bool = False,
    ) -> None:
        self.data = data
        self.duration = duration
        self.event = event
        self.variates = variates
        self.hue = hue
        self.retain_estimators = retain_estimators
        self.results = None
        self.diagnostics = pd.DataFrame()
        self.estimators: dict[int, Any] = {}
        self.name = "cox"

    def fit(self) -> None:
        """
        Fit Cox proportional hazards models for all specified variates.

        This method fits a separate Cox model for each variate, optionally
        stratified by hue groups. Results are stored in the results attribute.
        Each call first clears results, diagnostics, and retained estimators,
        including calls that fail input validation.

        Returns
        -------
        None
            Results are stored in self.results as a DataFrame.

        Raises
        ------
        ValueError
            If durations or event indicators are invalid. Input validation
            occurs before fitting any models; individual fitting failures
            instead emit RuntimeWarning.

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

        For formulas with one coefficient, display_label is automatically
        extracted from the formula string. For formulas with multiple
        coefficients, it combines the formula and coefficient names so every
        estimate remains distinct in visualizations.

        Diagnostics use ``status='success'`` or ``status='failed'``. For a
        failed fit, ``failure_reason`` contains the exception message.
        ``n_input`` is the group size; ``n_analyzed`` counts rows retained by
        the formula's missing-value handling, ``n_dropped`` is the difference,
        and ``event_count`` counts observed events in those retained rows.
        These counts describe eligible rows, not a successful fit. As in
        lifelines, missing formula predictors can cause a fit failure; this
        method does not automatically drop rows before fitting. If the
        formula cannot be evaluated, the eligible-row counts are null.

        Examples
        --------
        >>> model = cns.CoxModel(df, "time", "event", ["age", "treatment"])
        >>> model.fit()
        >>> print(model.results[["display_label", "exp(coef)", "p"]])
        """
        self.results = None
        self.diagnostics = pd.DataFrame()
        self.estimators = {}

        import lifelines as ll
        from lifelines.utils import CovariateParameterMappings

        validate_dataframe(self.data, "data", "CoxModel.fit")
        validate_dataframe_not_empty(self.data, "CoxModel.fit")
        required_columns = [self.duration, self.event]
        if self.hue is not None:
            required_columns.append(self.hue)
        validate_columns_exist(self.data, required_columns, "CoxModel.fit")
        validate_no_nulls(self.data, required_columns, "CoxModel.fit")
        validate_column_type(self.data, self.duration, ["numeric"], "CoxModel.fit")

        durations = self.data[self.duration]
        if pd.api.types.is_complex_dtype(durations.dtype) or pd.api.types.is_bool_dtype(
            durations.dtype
        ):
            raise ValueError(
                f"[CoxModel.fit] Column '{self.duration}' must contain real-valued "
                "numeric durations."
            )
        if not np.isfinite(durations).all():
            raise ValueError(
                f"[CoxModel.fit] Column '{self.duration}' must contain only finite "
                "durations."
            )
        if (durations < 0).any():
            raise ValueError(
                f"[CoxModel.fit] Column '{self.duration}' must contain only "
                "non-negative durations."
            )

        events = self.data[self.event]
        if np.iscomplexobj(events.to_numpy()) or not events.isin([0, 1]).all():
            raise ValueError(
                f"[CoxModel.fit] Column '{self.event}' must contain only 0 and 1 "
                "event indicators (False = censored, True = event occurred)."
            )

        df = self.data.copy()
        all_results = []
        diagnostics = []

        if self.hue is None:
            hue_groups = [("All", df)]
        else:
            hue_groups = [
                (str(hue_group), df[df[self.hue] == hue_group].copy())
                for hue_group in df[self.hue].unique()
            ]

        for hue_group, hue_data in hue_groups:
            for var in self.variates:
                analysis_id = len(diagnostics)
                diagnostic: dict[str, Any] = {
                    "analysis_id": analysis_id,
                    "analysis": var,
                    "hue_group": hue_group,
                    "status": "failed",
                    "n_input": len(hue_data),
                    "n_analyzed": None,
                    "n_dropped": None,
                    "event_count": None,
                    "failure_reason": None,
                }
                try:
                    cph = ll.CoxPHFitter()
                    cph.fit(
                        hue_data,
                        duration_col=self.duration,
                        event_col=self.event,
                        formula=var,
                    )
                    summary = cph.summary.reset_index()
                    if summary.empty:
                        raise ValueError(
                            f"Formula {var!r} produced no fitted coefficients"
                        )
                    summary["analysis"] = var
                    summary["hue_group"] = hue_group
                    all_results.append(summary)
                    diagnostic.update(
                        status="success",
                        n_analyzed=len(hue_data),
                        n_dropped=0,
                        event_count=int(hue_data[self.event].sum()),
                    )
                    if self.retain_estimators:
                        self.estimators[analysis_id] = cph
                except Exception as exc:
                    diagnostic["failure_reason"] = str(exc)
                    # Recover eligibility using lifelines' formula engine without
                    # changing its fit behavior or emitting duplicate warnings.
                    try:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            indexed_data = hue_data.reset_index(drop=True).sort_values(
                                [self.duration, self.event]
                            )
                            predictors = indexed_data.drop(
                                columns=[self.duration, self.event]
                            )
                            mapping = CovariateParameterMappings(
                                {"beta_": var}, predictors, force_no_intercept=True
                            )
                            design = mapping.mappings["beta_"].get_model_matrix(
                                predictors
                            )
                        diagnostic.update(
                            n_analyzed=len(design),
                            n_dropped=len(hue_data) - len(design),
                            event_count=int(
                                indexed_data.loc[design.index, self.event].sum()
                            ),
                        )
                    except Exception:
                        pass
                    warnings.warn(
                        f"Error fitting {var} for hue group {hue_group}: {exc}",
                        RuntimeWarning,
                        stacklevel=2,
                    )
                diagnostics.append(diagnostic)

        self.diagnostics = pd.DataFrame(diagnostics)

        if not all_results:
            warnings.warn("No successful model fits", RuntimeWarning, stacklevel=2)
            return

        df = pd.concat(all_results, ignore_index=True)
        df = df.sort_values(["exp(coef)", "hue_group"], ascending=False).copy()

        df["exp(coef) lower_err"] = df["exp(coef)"] - df["exp(coef) lower 95%"]
        df["exp(coef) upper_err"] = df["exp(coef) upper 95%"] - df["exp(coef)"]
        df["log10_pvalue"] = -np.log10(df["p"])
        df["coefficient_count"] = df.groupby("analysis")["covariate"].transform(
            "nunique"
        )

        def display_label_helper(x):
            if x["coefficient_count"] > 1:
                return f"{x['analysis']} ({x['covariate']})"
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
        label_counts = (
            df[["display_label", "analysis", "covariate"]]
            .drop_duplicates()
            .groupby("display_label", dropna=False)
            .size()
        )
        duplicate_labels = df["display_label"].map(label_counts).fillna(1).gt(1)
        df.loc[duplicate_labels, "display_label"] = df.loc[duplicate_labels].apply(
            lambda x: f"{x['analysis']} ({x['covariate']})", axis=1
        )

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


class _LogisticDesign(TransformerMixin, BaseEstimator):
    """Learn Patsy encoding on training rows and reuse it for held-out rows."""

    def __init__(self, formula: str) -> None:
        self.formula = formula

    def fit(self, X: pd.DataFrame, y: np.ndarray | None = None) -> _LogisticDesign:
        design = dmatrix(self.formula, X, return_type="dataframe", NA_action="raise")
        self.design_info_ = design.design_info
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        design = build_design_matrices(
            [self.design_info_], X, return_type="dataframe", NA_action="raise"
        )[0]
        return design.drop("Intercept", axis=1)


class _CVSplitter(Protocol):
    def split(
        self, X: Any, y: Any, groups: Any = None
    ) -> Iterable[tuple[np.ndarray, np.ndarray]]: ...


def _logistic_splits(
    cv: int | _CVSplitter,
    X: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray | None,
    level: str,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Validate the actual partitions before learning any preprocessing state."""
    splitter = check_cv(cv, y=y, classifier=True)
    if isinstance(splitter, StratifiedKFold):
        if pd.Series(y).value_counts().min() < splitter.n_splits:
            raise ValueError(
                f"{level} {splitter.n_splits}-fold cross-validation requires at least "
                f"{splitter.n_splits} observations in each outcome class"
            )
        splits = list(splitter.split(X, y))
    else:
        splits = list(splitter.split(X, y, groups))
    if not splits:
        raise ValueError(f"{level} cross-validation yielded no splits")
    validated = []
    for train, test in splits:
        train, test = np.asarray(train), np.asarray(test)
        for indices in (train, test):
            if (
                indices.ndim != 1
                or not np.issubdtype(indices.dtype, np.integer)
                or len(indices) == 0
                or (indices < 0).any()
                or (indices >= len(y)).any()
                or len(np.unique(indices)) != len(indices)
            ):
                raise ValueError(f"{level} cross-validation has invalid row indices")
        if np.intersect1d(train, test).size:
            raise ValueError(f"{level} cross-validation train/validation rows overlap")
        if any(len(np.unique(y[indices])) != 2 for indices in (train, test)):
            raise ValueError(
                f"{level} cross-validation requires both outcome classes in every "
                "training and validation partition for ROC-AUC"
            )
        if groups is not None and pd.Index(groups[train]).isin(groups[test]).any():
            raise ValueError(
                f"{level} cross-validation splits a group between training and "
                "validation; use group-aware splitters at both levels"
            )
        validated.append((train, test))
    return validated


class LogisticModel:
    """
    Logistic regression model with cross-validation for binary classification.

    This class fits L1-regularized logistic regression models with nested
    cross-validation to predict binary outcomes and assess predictor
    performance using ROC-AUC with percentile bootstrap intervals conditional
    on the fixed out-of-fold predictions.

    Parameters
    ----------
    data : pd.DataFrame
        Input DataFrame containing the outcome variable and predictors.
    event : str
        Column name for the binary outcome variable (0 or 1).
    variates : list of str
        List of formula strings specifying the predictors to test. Each formula
        can be a simple variable name or a Patsy formula (e.g., 'age',
        'C(treatment)', 'age + stage'). Stateful Patsy transforms such as
        ``bs``, ``cr``, ``center``, and ``standardize`` are not supported.
    hue : str, optional
        Column name for grouping variable. If provided, fits separate models
        for each group. Default is None (single model for all data).
    inner_cv, outer_cv : int or cross-validation splitter, default: 5
        Splitters for tuning and out-of-fold evaluation, respectively. Integers
        select unshuffled stratified folds. Splitters receive the complete
        predictor rows for each analysis; inner splitters receive only the
        current outer training subset. Every training and validation partition
        must contain both outcome classes. Outer validation partitions must
        cover every analyzed row exactly once (repeated CV and partial-coverage
        splitters such as TimeSeriesSplit are therefore unsupported).
    groups : str or one-dimensional array-like, optional
        Column containing subject/group identifiers, or one identifier per input
        row, aligned by position even for a Series. Identifiers are subset with
        hue groups and predictor exclusions. Missing identifiers are rejected.
        Use group-aware splitters at both levels; any train/validation group
        overlap is rejected. This is separate from ``hue``, which fits separate
        analyses.
    random_state : int or None, default: 42
        Seed for the logistic solver and AUC bootstrap. Configure shuffling and
        its seed on supplied splitters themselves. None permits nondeterminism.
    retain_estimators : bool, default: False
        Retain the selected pipeline from each outer fold for successful
        analyses. No additional model is fitted on the full dataset.

    Attributes
    ----------
    results : pd.DataFrame
        Results for successful analyses. ``auc`` is the AUC of all out-of-fold
        predictions, not a mean of fold or bootstrap AUCs. ``lower_ci`` and
        ``upper_ci`` are distances from this point estimate to the percentile
        interval limits. Available after calling fit().
    diagnostics : pd.DataFrame
        One row per requested formula/hue pair, in request order, with
        ``analysis_id``, ``analysis``, ``hue_group``, ``status`` (success/failed),
        ``n_input``, ``n_analyzed``, ``n_dropped``, ``class_counts``, and
        ``failure_reason``. Analyzed counts describe complete predictor rows,
        including when fitting fails. Counts are missing if formula evaluation
        fails. Counts are aggregate; diagnostics do not store input row copies.
    estimators : dict of int to list of sklearn.pipeline.Pipeline
        When retention is enabled, maps diagnostics ``analysis_id`` to fitted
        outer-fold pipelines in splitter order. These are evaluation models
        refitted on each outer training subset after inner tuning, not a final
        full-data refit. Pipelines include learned Patsy encoding, scaling, and
        classifier state, without storing training rows or outcomes. Empty
        otherwise. All fit state is cleared at the start of every fit, including
        when input validation fails.
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

    - Outer cross-validation for out-of-fold predictions (5 folds by default)
    - Inner ROC-AUC tuning of the complete pipeline (5 folds by default)
    - Fixed-prediction percentile intervals for AUC (1000 bootstrap attempts,
      alpha=0.05, using ``random_state``)

    The bootstrap resamples individual analyzed rows, keeping each label and
    its out-of-fold probability together. It does not refit preprocessing,
    models, or hyperparameter selection. ``groups`` controls CV splitting only;
    the interval does not account for dependence between repeated observations.
    The nominal 95% interval has no universal coverage guarantee. Inference for
    dependent observations or uncertainty in the entire retraining and model
    selection procedure requires a study-specific resampling design.

    Models use the liblinear solver optimized for L1 regularization and are
    scored using ROC-AUC during cross-validation. See :meth:`fit` for the
    preprocessing boundaries and supported formula behavior.

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
    >>> print(model.diagnostics)

    >>> # Keep repeated subjects together at both validation levels
    >>> from sklearn.model_selection import GroupKFold
    >>> model = cns.LogisticModel(
    ...     df,
    ...     event="response",
    ...     variates=["age"],
    ...     groups="subject_id",
    ...     outer_cv=GroupKFold(3),
    ...     inner_cv=GroupKFold(2),
    ...     retain_estimators=True,
    ... )
    >>> model.fit()
    >>> outer_pipelines = model.estimators[0]
    """

    def __init__(
        self,
        data: pd.DataFrame,
        event: str,
        variates: list[str],
        hue: str | None = None,
        *,
        inner_cv: int | _CVSplitter = 5,
        outer_cv: int | _CVSplitter = 5,
        groups: str | Sequence[Any] | np.ndarray | pd.Series | None = None,
        random_state: int | None = 42,
        retain_estimators: bool = False,
    ) -> None:
        self.data = data
        self.event = event
        self.variates = variates
        self.hue = hue
        self.inner_cv = inner_cv
        self.outer_cv = outer_cv
        self.groups = groups
        self.random_state = random_state
        self.retain_estimators = retain_estimators
        self.results = None
        self.diagnostics = pd.DataFrame()
        self.estimators: dict[int, list[Pipeline]] = {}
        self.name = "logistic"

    def _compute_auc_ci(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        n_bootstrap: int = 1000,
        alpha: float = 0.05,
    ) -> tuple[float, float, float]:
        """
        Compute a percentile interval from fixed label/probability pairs.

        Parameters
        ----------
        y_true : array-like
            True binary labels.
        y_pred_proba : array-like
            Fixed predicted probabilities, out-of-fold when called by ``fit``.
        n_bootstrap : int, default: 1000
            Number of bootstrap attempts. Single-class samples are skipped
            without drawing replacements, so fewer replicates may be retained.
        alpha : float, default: 0.05
            Significance level for confidence interval (0.05 = 95% CI).

        Returns
        -------
        tuple of float
            (auc, lower_bound, upper_bound), where ``auc`` is computed from all
            predictions and bootstrap samples are used only for the bounds.

        Notes
        -----
        Each attempt samples ``len(y_true)`` row indices uniformly with
        replacement, applying the same indices to labels and probabilities.
        A new ``numpy.random.default_rng(self.random_state)`` is used on each
        call. Bounds are the ``alpha / 2`` and ``1 - alpha / 2`` quantiles of
        retained AUCs, using NumPy's default linear percentile interpolation.
        No model fitting or group resampling is performed.
        """
        y_true = np.asarray(y_true)
        y_pred_proba = np.asarray(y_pred_proba)
        auc = skl.metrics.roc_auc_score(y_true, y_pred_proba)
        aucs = []
        rng = np.random.default_rng(self.random_state)
        n = len(y_true)
        for _ in range(n_bootstrap):
            indices = rng.choice(n, n, replace=True)
            if len(np.unique(y_true[indices])) < 2:
                continue
            bootstrap_auc = skl.metrics.roc_auc_score(
                y_true[indices], y_pred_proba[indices]
            )
            aucs.append(bootstrap_auc)
        aucs = np.array(aucs)
        lower = np.percentile(aucs, 100 * alpha / 2)
        upper = np.percentile(aucs, 100 * (1 - alpha / 2))
        return float(auc), float(lower), float(upper)

    def fit(self) -> None:
        """
        Fit logistic regression models for all specified variates.

        This method fits a separate L1-regularized logistic regression model
        with nested cross-validation for each variate, optionally stratified
        by hue groups. Results are stored in the results attribute.

        Returns
        -------
        None
            Results are stored in self.results as a DataFrame.

        Notes
        -----
        The results DataFrame contains:
        - predictor: Formula string for the predictor(s)
        - auc: AUC of all pooled out-of-fold predictions
        - lower_ci: Lower error bound (auc - lower confidence limit)
        - upper_ci: Upper error bound (upper confidence limit - auc)
        - hue_group: Group name (or 'All' if no grouping)

        For each model:

        1. Stateful Patsy transforms are rejected before learning any design state.
           A stateless formula evaluation identifies complete predictor rows and
           aligns their outcomes; its design information is discarded.
        2. Outer CV holds out each row once. Within each outer
           training fold, inner CV tunes 10 values of C,
           logarithmically spaced from 1e-4 to 1e4, using ROC-AUC.
        3. Each inner fit learns Patsy encoding and standardization on its training
           rows only, followed by L1 logistic regression. The selected pipeline
           is refitted on the outer training rows to predict the outer held-out
           rows. Defaults use unshuffled stratified 5-fold CV at both levels
           and a solver seed of 42. Feasibility is checked against the actual
           partitions after predictor exclusions.
        4. AUC is computed from all out-of-fold predictions, not averaged over
           folds or bootstrap replicates. For the nominal 95% interval, 1000
           bootstrap attempts each sample as many individual rows as analyzed,
           uniformly with replacement. Each sampled label stays paired with its
           fixed out-of-fold probability. Single-class samples are skipped
           without replacement attempts. The limits are the 2.5th and 97.5th
           percentiles of retained AUCs, using NumPy's default linear
           interpolation. A fresh ``numpy.random.default_rng(random_state)``
           supplies the draws for each analysis (default seed 42).

        The interval conditions on the existing out-of-fold predictions: no
        preprocessing, model fitting, or hyperparameter selection is repeated
        in the bootstrap. Groups control CV splitting only, not resampling.
        Repeated or dependent observations and uncertainty from the full
        retraining/model-selection procedure require a study-specific approach;
        nominal 95% coverage is not guaranteed for every study design.

        Formulas must use row-wise expressions. Stateful Patsy transforms
        (including splines, centering, and standardization) are unsupported until
        fold-local state and missing-value handling are implemented together.
        Categorical levels are learned from training rows and reused for
        validation. An unseen validation level causes a fitting warning; known
        levels can be declared in advance with ``C(column, levels=[...])`` or a
        pandas categorical dtype.

        Runtime warnings are emitted for hue groups with no outcome variance.
        Errors during fitting are caught and surfaced as warnings, with one
        diagnostics entry for every requested analysis. Invalid required input
        columns or group arrays raise ValueError before any analysis. Results,
        diagnostics, and retained estimators are reset before validation.

        Examples
        --------
        >>> model = cns.LogisticModel(df, "outcome", ["age", "treatment"])
        >>> model.fit()
        >>> print(model.results[["predictor", "auc", "hue_group"]])
        """
        self.results = None
        self.diagnostics = pd.DataFrame()
        self.estimators = {}
        validate_dataframe(self.data, "data", "LogisticModel.fit")
        validate_dataframe_not_empty(self.data, "LogisticModel.fit")
        required_columns = [self.event]
        if self.hue is not None:
            required_columns.append(self.hue)
        validate_columns_exist(self.data, required_columns, "LogisticModel.fit")
        validate_no_nulls(self.data, required_columns, "LogisticModel.fit")

        groups = None
        if self.groups is not None:
            if isinstance(self.groups, str):
                validate_columns_exist(self.data, [self.groups], "LogisticModel.fit")
                groups = self.data[self.groups].to_numpy()
            else:
                groups = np.asarray(self.groups)
            if groups.ndim != 1 or len(groups) != len(self.data):
                raise ValueError(
                    "[LogisticModel.fit] groups must be one-dimensional with one "
                    "identifier per input row"
                )
            if pd.isna(groups).any():
                raise ValueError(
                    "[LogisticModel.fit] groups must not contain missing values"
                )

        df = self.data.reset_index(drop=True)
        all_results = []
        diagnostics: list[dict[str, Any]] = []
        regularization_options: dict[str, Any] = (
            {"l1_ratio": 1}
            if inspect.signature(LogisticRegression).parameters["l1_ratio"].default == 0
            else {"penalty": "l1"}
        )

        if self.hue is None:
            hue_groups = [("All", df)]
        else:
            hue_groups = [
                (str(hue_group), df[df[self.hue] == hue_group].copy())
                for hue_group in df[self.hue].unique()
            ]

        for hue_group, hue_data in hue_groups:
            for var in self.variates:
                diagnostic: dict[str, Any] = {
                    "analysis_id": len(diagnostics),
                    "analysis": var,
                    "hue_group": hue_group,
                    "status": "failed",
                    "n_input": len(hue_data),
                    "n_analyzed": None,
                    "n_dropped": None,
                    "class_counts": None,
                    "failure_reason": None,
                }
                diagnostics.append(diagnostic)
                try:
                    formula = ModelDesc.from_formula(var)
                    eval_env = EvalEnvironment.capture(0)
                    for term in formula.rhs_termlist:
                        for factor in term.factors:
                            if factor.memorize_passes_needed({}, eval_env):
                                raise ValueError(
                                    "Stateful Patsy transforms are not supported by "
                                    "LogisticModel; use a formula with row-wise "
                                    "predictor expressions"
                                )
                    # Use this evaluation only for row selection, never encoding.
                    complete_rows = (
                        dmatrix(var, hue_data, return_type="dataframe")
                        .drop("Intercept", axis=1)
                        .index
                    )
                    X = hue_data.loc[complete_rows]
                    y = X[self.event].to_numpy()
                    class_counts = pd.Series(y).value_counts()
                    diagnostic.update(
                        n_analyzed=len(y),
                        n_dropped=len(hue_data) - len(y),
                        class_counts=class_counts.to_dict(),
                    )
                    if len(class_counts) < 2:
                        diagnostic["failure_reason"] = "No variance in outcome"
                        warnings.warn(
                            f"No variance in outcome for {var} in hue group {hue_group}",
                            RuntimeWarning,
                            stacklevel=2,
                        )
                        continue
                    if len(class_counts) > 2:
                        raise ValueError(
                            "Logistic regression requires exactly two outcome classes"
                        )

                    analysis_groups = None if groups is None else groups[X.index]
                    outer_splits = _logistic_splits(
                        self.outer_cv, X, y, analysis_groups, "Outer"
                    )
                    held_out = np.concatenate([test for _, test in outer_splits])
                    if not np.array_equal(np.sort(held_out), np.arange(len(y))):
                        raise ValueError(
                            "Outer cross-validation must hold out each analyzed row "
                            "exactly once"
                        )
                    inner_splits = [
                        _logistic_splits(
                            self.inner_cv,
                            X.iloc[train],
                            y[train],
                            None if analysis_groups is None else analysis_groups[train],
                            "Inner",
                        )
                        for train, _ in outer_splits
                    ]
                    y_pred_proba = np.empty(len(y), dtype=float)
                    fitted_estimators = []
                    for (train, test), inner in zip(outer_splits, inner_splits):
                        model = GridSearchCV(
                            make_pipeline(
                                _LogisticDesign(var),
                                StandardScaler(),
                                LogisticRegression(
                                    solver="liblinear",
                                    random_state=self.random_state,
                                    **regularization_options,
                                ),
                            ),
                            {"logisticregression__C": np.logspace(-4, 4, 10)},
                            cv=inner,
                            scoring="roc_auc",
                            error_score="raise",
                        )
                        model.fit(X.iloc[train], y[train])
                        y_pred_proba[test] = model.predict_proba(X.iloc[test])[:, 1]
                        if self.retain_estimators:
                            fitted_estimators.append(model.best_estimator_)
                    auc, auc_lower, auc_upper = self._compute_auc_ci(y, y_pred_proba)
                    model_result = {
                        "predictor": var,
                        "auc": auc,
                        "auc_lower": auc_lower,
                        "auc_upper": auc_upper,
                        "hue_group": hue_group,
                    }
                    all_results.append(model_result)
                    diagnostic["status"] = "success"
                    if self.retain_estimators:
                        self.estimators[diagnostic["analysis_id"]] = fitted_estimators
                except Exception as exc:
                    diagnostic["failure_reason"] = str(exc)
                    warnings.warn(
                        f"Error fitting {var} for hue group {hue_group}: {exc}",
                        RuntimeWarning,
                        stacklevel=2,
                    )

        self.diagnostics = pd.DataFrame(diagnostics)
        results_df = pd.DataFrame(all_results)
        if len(results_df) == 0:
            warnings.warn(
                "No successful model fits",
                RuntimeWarning,
                stacklevel=2,
            )
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

        Results are filtered for FDR q-val < 0.25 and abs(NES) > 1.5, and sorted
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
    - abs(NES) > 1.5: Moderate enrichment
    - abs(NES) > 2.0: Strong enrichment

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
    validate_dataframe(data, "data", "prerank")
    validate_dataframe_not_empty(data, "prerank")
    if name_gene is None or name_rank is None:
        raise ValueError(
            "[prerank] Parameters 'name_gene' and 'name_rank' must be provided."
        )
    validate_columns_exist(data, [name_gene, name_rank], "prerank")
    validate_no_nulls(data, [name_gene, name_rank], "prerank")
    validate_column_type(data, name_gene, ["string"], "prerank")
    validate_column_type(data, name_rank, ["numeric"], "prerank")

    try:
        import gseapy as gp
    except ImportError as exc:
        raise ImportError(
            "[prerank] gseapy is required but not installed. "
            "Install with: pip install gseapy"
        ) from exc

    rnk = data.copy()
    rnk = rnk[[name_gene, name_rank]]
    rnk.columns = ["Gene", "Rank"]
    rnk["Gene"] = rnk["Gene"].str.strip().str.upper()
    gsea_res = gp.prerank(
        rnk=rnk,
        gene_sets=cast(
            Any, gene_sets
        ),  # gseapy accepts dict[str, list[str]] at runtime
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
