# Statistical Methods

cnsplots combines drawing with selected statistical calculations. Choose the
analysis from the study design before choosing an annotation. One row often
represents one observation, but repeated measurements from one subject are not
independent observations. None of the plotting functions establishes a causal
effect or automatically checks every estimator assumption.

This guide describes the implemented defaults. The {doc}`api` gives full public
signatures; links below identify the implementation and primary method or
dependency documentation. Missing-value rules differ by family: there is no
package-wide imputation or complete-case policy.

## Continuous groups and paired observations

`boxplot`, `violinplot`, `barplot`, and `lollipopplot` run comparisons only when
`pairs` is supplied. `pairs="all"` compares displayed category pairs;
`pairs="hue"` compares hue levels within every displayed category. Explicit
hue comparisons use tuples such as `[(("A", "control"), ("A", "treated"))]`.
Here, `pairs` selects group contrasts; it does not identify matched subjects.

| Functions | Default test when comparisons are requested | Other supported tests |
| --- | --- | --- |
| `boxplot`, `violinplot` | `"Mann-Whitney"` | `"t-test_welch"`, `"t-test_paired"`, `"Wilcoxon"` |
| `barplot`, `lollipopplot` | `"t-test_welch"` | `"Mann-Whitney"`, `"t-test_paired"`, `"Wilcoxon"` |

Mann–Whitney and Welch's t-test are two-sided tests of **independent** samples.
Mann–Whitney tests equality of the underlying distributions; interpreting it only
as a median difference requires additional distributional assumptions. It delegates to
SciPy through statannotations, including automatic exact/asymptotic selection
and tie handling. Welch's t-test compares means without assuming equal
variances; its small-sample justification assumes normal populations.
See [SciPy Mann–Whitney](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html)
and [Welch's t-test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html).

For matched or repeated measurements, select `test="t-test_paired"` or
`test="Wilcoxon"` and supply the subject identifier column with
`subject="subject_id"`. Both are two-sided tests and assume independent
subjects. The paired t-test compares the mean within-subject difference with
zero; its small-sample normality assumption concerns those differences.
Wilcoxon tests whether their distribution is symmetric about zero. It uses
SciPy's `zero_method="wilcox"` (discard zero differences from the ranks),
`correction=False`, and `method="auto"`; SciPy determines the p-value method
and tie handling. See [SciPy's paired t-test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_rel.html)
and [Wilcoxon signed-rank test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).
`subject` is required for paired tests and is rejected with independent tests.

These four plots exclude rows missing `x`, `y`, or the selected `hue`, and
exclude levels omitted from `order` or `hue_order`. The resulting rows feed
drawing, summaries, counts, and independent tests. This cleaning does not remove
infinity.
Hiding boxplot outliers does not remove those observations from tests or counts.
Category counts pool the displayed hue levels.

Paired tests additionally align each requested contrast by subject identifier,
regardless of row order. Rows with missing identifiers and subjects absent from
either group are excluded from that test. Each compared group must have at most
one complete displayed observation per subject; duplicates raise an error,
rather than being averaged. Both paired tests require at least two matched
subjects. Nonfinite matched response values and comparisons in which every
within-subject difference is zero are rejected. Ties and mixtures of zero and
nonzero differences otherwise follow SciPy's defaults.
Nonfinite p-values returned by SciPy are rejected before correction or annotation.
Matching is performed separately for every contrast, so different comparisons
can use different subjects. Plot summaries and tick-label counts still use all
displayed observations and can exceed the matched test counts. Selecting a paired
test does not change the plotted summaries, error bars, or bootstrap resampling
unit into a paired analysis.

`get_comparison_results(ax)` returns the tested sample sizes and raw and
adjusted p-values without rerunning tests. It estimates no effect size.
For paired tests, `paired` is `True` and `n1 == n2` is the number of matched
subjects before Wilcoxon discards zero differences from the ranks.
`group1` and `group2` follow categorical axis order, which can differ from the
supplied pair order; the two-sided p-value does not establish a direction of
effect. The accessor reports the latest stored comparisons on the axes, so use
the returned axes explicitly when working with multiple panels.

For independent subjects, select the test and correction explicitly:

```python
import cnsplots as cns
import matplotlib.pyplot as plt
import pandas as pd

independent = pd.DataFrame(
    {
        "group": ["control"] * 5 + ["treated"] * 5,
        "response": [2.1, 3.2, 2.8, 4.0, 3.5, 4.2, 4.8, 3.9, 5.1, 4.5],
    }
)
fig, ax = plt.subplots()
cns.boxplot(
    independent,
    "group",
    "response",
    order=["control", "treated"],
    pairs=[("control", "treated")],
    test="t-test_welch",
    p_adjust="holm",
    ax=ax,
)
comparisons = cns.get_comparison_results(ax)
print(comparisons[["n1", "n2", "paired", "pvalue_raw", "pvalue_adjusted"]])
```

For repeated measurements, select the subject column explicitly. Shuffling
these rows does not change which observations are paired:

```python
import cnsplots as cns
import matplotlib.pyplot as plt
import pandas as pd

paired = (
    pd.DataFrame(
        {
            "subject": ["s1", "s2", "s3", "s4", "s5"],
            "before": [8.0, 7.0, 9.0, 6.0, 8.5],
            "after": [6.5, 6.8, 7.0, 5.0, 7.5],
        }
    )
    .melt(id_vars="subject", var_name="condition", value_name="response")
    .sample(frac=1, random_state=42)
)
fig, ax = plt.subplots()
cns.boxplot(
    paired,
    "condition",
    "response",
    order=["before", "after"],
    pairs=[("before", "after")],
    test="t-test_paired",
    subject="subject",
    p_adjust=None,  # one prespecified comparison
    ax=ax,
)
comparisons = cns.get_comparison_results(ax)
print(comparisons[["n1", "n2", "paired", "pvalue_raw", "pvalue_adjusted"]])
```

`slopeplot` draws paired observations using its `pair` identifier. It requires
one value per condition per subject, exactly two conditions, and one `x` group
per subject; missing values and incomplete or duplicate pairs are rejected.
It performs **no hypothesis test**.

Implementation: [categorical comparisons and results](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/_utils.py),
[distribution plots](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_distribution.py),
and [slopeplot](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_regression.py).

## Correction scope and annotation text

Where `p_adjust` is supported, its default is `None` (unadjusted). Options are
`"bonferroni"` and `"holm"` for family-wise error control, and `"fdr_bh"` and
`"fdr_by"` for false discovery rate control. BH assumes independent or suitably
positively dependent tests; BY accommodates general dependence. These methods
use [statsmodels `multipletests`](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html).

| Family | P-values included in one correction family |
| --- | --- |
| Continuous categorical plots and `stackplot` | All resolved comparisons in one call, including every category for `pairs="hue"` |
| `rocplot` | All requested paired DeLong comparisons in one call |
| `survivalplot` | All requested pairwise Cox Wald tests in one call |

Correction never extends automatically across panels, separate calls, model
formulas, or an entire study. It does not adjust confidence intervals.
Categorical annotation behavior comes from statannotations: Bonferroni labels
show adjusted numerical p-values, while Holm/FDR labels retain raw p-values
and can add a nonsignificance suffix when correction changes significance.
Use `get_comparison_results(ax)["pvalue_adjusted"]` for numerical adjusted
values for every method. ROC annotations display adjusted values; survival
annotations show both raw and adjusted pairwise values.

## Summaries, error bars, and regression

Boxplot boxes show quartiles and medians; default whiskers extend to observations
within 1.5 interquartile ranges. Violin widths show a kernel density estimate.
Neither is a confidence interval. `barplot` and `lollipopplot` show means with
no error bars by default. Changing the plotted estimator does not change the
selected hypothesis test.

For `lollipopplot`, the supported estimators are `"mean"` and `"median"`:

| `errorbar` | Meaning |
| --- | --- |
| `None` | No interval |
| `"sd"` | Plus/minus sample standard deviation (`ddof=1`), also when plotting medians |
| `"se"`, mean | Plus/minus sample SD divided by square root of sample size |
| `"ci"`, mean | Mean plus/minus Student's t critical value at 0.975 with `n-1` degrees of freedom times SE |
| `"se"`, median | Plus/minus SD of 1,000 bootstrap medians |
| `"ci"`, median | 2.5th and 97.5th percentiles of 1,000 bootstrap medians |

Median resampling samples individual rows with replacement, with a new NumPy
generator seeded to 0 for each group. Groups with fewer than two observations
have no estimable SE/CI. Mean t intervals assume independent observations and
normality for exact small-sample coverage; bootstrap intervals depend on the
sample representing the population and the resampling unit matching the study.
See [Student's t distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html)
and the [percentile bootstrap definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).
The bootstrap here is implemented directly, not by calling `scipy.stats.bootstrap`.

`barplot` forwards requested `errorbar` options to Seaborn. `lineplot` defaults
to a mean at each x/group combination and a 95% percentile bootstrap interval
with `n_boot=1000`, `seed=None`. These are pointwise intervals for the summary,
not intervals for individual observations or simultaneous coverage of the
whole line. Set `seed` for reproducibility, or `errorbar=None` to omit them.
Seaborn handles missing plotting values for `lineplot`; it does not use the
categorical cleaning helper. See [Seaborn's error-bar definitions](https://seaborn.pydata.org/tutorial/error_bars.html).

`regplot` removes rows with nonfinite x or y and missing selected hue/color
labels. It fits and annotates each hue separately; a column supplied as `color`
colors points but retains one overall fit and correlation. At least two usable
x/y pairs are required per analysis. The default annotation is a two-sided
Pearson correlation test; `method="spearman"` uses Spearman rank correlation
instead. Observations must be independent across rows; the Pearson null
distribution assumes bivariate-normal x/y pairs, and SciPy's Spearman p-value is an
asymptotic approximation that can be inaccurate with small samples.
There is no multiplicity correction across hue groups.
See [Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html)
and [Spearman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html).

Selecting Spearman changes the annotation only: the default fitted line remains
linear. Its default Seaborn band is a 95% bootstrap interval for the fitted
regression, with 1,000 resamples and no fixed seed; it is not a correlation CI
or a prediction interval. `add_equation=True` adds a separate ordinary linear
equation and R². Custom Seaborn fitting options do not redefine the correlation
test or that equation. See [Seaborn `regplot`](https://seaborn.pydata.org/generated/seaborn.regplot.html).

Distribution-only plots such as histograms, KDEs, and ridge plots do not test
normality or differences. `ridgeplot` drops rows missing its x/hue columns.
`qqplot` passes the selected column directly to
statsmodels, using a normal reference by default, without cnsplots missing-data
cleaning or a normality p-value. Inspect and clean the intended analysis sample
before interpreting these displays.

Implementation: [summary intervals](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_categorical.py)
and [regression/line plots](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_regression.py).

## Counts and classification tables

`stackplot` counts complete bar-category/stack-category rows, then draws
proportions by default (`normalize=True`). With `pairs`, `test="auto"` selects
Fisher's exact test for two stack levels and chi-squared otherwise. Both test
independence using the original counts, before normalization or `n_factor`
scaling. Missing stack values can therefore make tested sample sizes smaller
than the raw category counts shown by `add_count=True`. `stack_order` changes
display order, not the contingency table's inference categories.

Fisher uses SciPy's default two-sided 2×2 test; explicit `"fisher-exact"` on
larger tables delegates to the installed SciPy implementation. Chi-squared
uses `chi2_contingency` defaults, including Yates' continuity correction when
there is one degree of freedom. It relies on sufficiently large expected
counts for its asymptotic approximation. Rows must be independent observations,
not repeat records of the same subject. No odds ratio or other effect is
returned by `stackplot`. See [Fisher's exact test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html)
and [chi-squared contingency tests](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2_contingency.html).

`confusionplot` requires nonmissing predicted `x` and true `y` labels and counts
every row. Orders must contain every observed label exactly once. Its default
`add_pvalue=False` draws counts only. With
`add_pvalue=True`, a 2×2 table receives specificity, sensitivity, predictive
values, Cohen's kappa, a sample odds ratio, and an unadjusted two-sided Fisher
test. Specify `positive_x` and `positive_y`; otherwise the final displayed
label on each axis is positive. The odds ratio is `TP*TN/(FP*FN)`; undefined
ratios are NaN. This is a test of association of prediction and truth, not a
comparison of two classifiers. There are no confidence intervals or correction
options. Implementation: [count plots](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_categorical.py)
and [confusionplot](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_heatmap.py).

## Survival and competing risks

Both survival plot families reject missing duration/event/hue values and require
finite, nonnegative durations. They retain all validated rows. Times and
analysis horizons must share units. The curves assume independent subjects and
noninformative right censoring; these wrappers do not expose delayed entry,
weights, or repeated-event analysis.

`survivalplot` treats **1 as the event and 0 as right censoring**. It fits a
Kaplan–Meier curve per group. `ci_show=False` hides bands by default; enabling
them shows lifelines' pointwise 95% Greenwood log-log intervals, not a
simultaneous band. See [KaplanMeierFitter](https://lifelines.readthedocs.io/en/latest/fitters/univariate/KaplanMeierFitter.html).

The default overall comparison is an unadjusted omnibus log-rank test across
groups. It compares survival distributions; its power is strongest under
proportional hazards and can be poor for crossing curves. `overall_test="trend"`
instead fits a Cox model with equally spaced scores in an explicitly supplied,
complete `hue_order`, and reports a one-degree-of-freedom likelihood-ratio test.
It assumes a log-linear hazard trend across those scores. See
[lifelines survival tests](https://lifelines.readthedocs.io/en/latest/lifelines.statistics.html).

With two groups, a Cox contrast is also fitted by default; with three or more,
no pair is inferred automatically. `pairs=[("control", "treated")]` means
**treated versus control**: HR greater than 1 indicates a higher hazard of the
coded event, which need not be an adverse event. Each pair fits its own Cox
model and reports a two-sided Wald p-value and unadjusted 95% HR interval.
Proportional hazards and an adequately estimable model are required. Use
`pairs=[]` or `show_hazard_ratio=False` to suppress pairwise inference.
For corrected families, failed requested contrasts retain their place using
p=1 only during correction, while their reported results remain unavailable.
Overall and landmark p-values remain unadjusted. See
[CoxPHFitter](https://lifelines.readthedocs.io/en/latest/fitters/regression/CoxPHFitter.html).

`show_median_survival=True` reports the first time survival reaches 0.5, or
`not reached`. `landmark_time=t` reports S(t), including events at t, and for
two groups adds a fixed-time log-minus-log comparison when estimable.
`rmst_time=t` integrates each curve from zero to t to obtain restricted mean
survival time, without a CI or between-group RMST test; see
[lifelines' RMST definition](https://lifelines.readthedocs.io/en/latest/lifelines.utils.html#lifelines.utils.restricted_mean_survival_time).
Both horizons must be
positive and no greater than the minimum of the groups' maximum follow-up
times. `get_survival_results(ax)` exposes estimates, tests, sample/event counts,
and failure reasons. Failed inference warns and displays `unavailable` while
preserving valid curves and estimates.

Use `descriptive_only=True` to skip all tests and Cox fits, including for a
single group or an all-censored cohort. Curve CIs and descriptive summaries
remain available. Here 1 explicitly denotes the event of interest and the
chosen time unit is months; no correction is applied because no tests run:

```python
import cnsplots as cns
import matplotlib.pyplot as plt
import pandas as pd

follow_up = pd.DataFrame(
    {
        "months": [2, 4, 6, 8, 10, 12],
        "event": [1, 0, 1, 0, 1, 0],  # 1 = event, 0 = right censored
        "cohort": ["Study"] * 6,
    }
)
fig, ax = plt.subplots()
cns.survivalplot(
    follow_up,
    "months",
    "event",
    "cohort",
    time_label="Time (months)",
    descriptive_only=True,
    ci_show=True,
    p_adjust=None,
    show_median_survival=True,
    landmark_time=6,
    rmst_time=10,
    ax=ax,
)
print(cns.get_survival_results(ax)[["kind", "estimate", "status"]])
```

`cumulativeincidenceplot` fixes **0=censored, 1=event of interest, and integer
codes 2+=competing events**, even if some codes are absent. It uses the
Aalen–Johansen estimator and displays no confidence bands. Tied event times
may be jittered by lifelines using `seed=0` by default. The default unadjusted
Gray K-sample test (`rho=0`) compares cumulative incidence of event 1 using the
original times. There is no pairwise or `p_adjust` option. Its
`descriptive_only=True` skips Gray's test while retaining curves, including
groups with no event of interest. See [AalenJohansenFitter](https://lifelines.readthedocs.io/en/latest/fitters/univariate/AalenJohansenFitter.html)
and [Gray's original paper](https://doi.org/10.1214/aos/1176350951).
Implementation: [survival plots](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_survival.py)
and [Gray test adapter](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/helpers/_cmprsk.py).

## Models and forest plots

`CoxModel` fits one model per formula and hue group. A formula such as
`"age + C(stage)"` fits those covariates together; separate entries in
`variates` request separate models. `hue` fits independent models per group,
not a single stratified Cox model. All fitted coefficients are retained, with
exponentiated coefficients, 95% Wald intervals, and two-sided Wald p-values.
Continuous HRs are per unit of the formula's covariate; categorical HRs depend
on the formula's reference category. No correction is applied across
coefficients, formulas, or groups. The same proportional-hazards and censoring
assumptions as [lifelines Cox regression](https://lifelines.readthedocs.io/en/latest/fitters/regression/CoxPHFitter.html)
apply.

Missing duration/event/hue values are rejected. Missing formula predictors are
not automatically removed before Cox fitting and can cause failure. Diagnostics
then attempt to count formula-complete eligible rows; those counts do not imply
that a model succeeded. Check `diagnostics.status` and `failure_reason` as well
as `results`. `retain_estimators=True` retains successful fitters for further
diagnostics; no proportional-hazards diagnostic is run automatically.

`LogisticModel` also analyzes each formula/hue separately, but selects complete
predictor rows with Patsy before fitting. Outcomes and optional CV group IDs
stay aligned with retained rows. Missing required outcome/hue/group values
are rejected. The documented outcome convention is **0=negative, 1=positive**;
there is no `pos_label` option. Internally it uses `predict_proba(...)[:, 1]`,
so other binary labels follow scikit-learn's second-class convention. Encode
the intended positive event as 1 explicitly.

Defaults use unshuffled stratified five-fold outer CV and five-fold inner CV.
Inner CV tunes ten C values from 1e-4 to 1e4 by ROC-AUC for L1 logistic
regression with the liblinear solver. Patsy encoding and standardization are
learned only from the training rows of each fit. Outer predictions cover every
analyzed row once; every training and validation partition needs both classes.
Stateful Patsy transforms are unsupported. For repeated subjects, supply
`groups` and group-aware splitters at **both** levels. Overlapping groups are
rejected, but `groups` does not change the interval's resampling unit.
See [nested CV](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

The reported AUC pools **all out-of-fold predictions**, rather than averaging
fold AUCs or bootstrap AUCs. Its nominal 95% interval is a percentile bootstrap
of the fixed label/probability pairs:

1. Initialize `np.random.default_rng(random_state)` for each analysis (default 42).
2. Attempt 1,000 resamples, each drawing n individual rows with replacement.
3. Skip resamples containing only one outcome class, without replacement attempts.
4. Use NumPy's linearly interpolated 2.5th and 97.5th percentiles of valid AUCs.

Preprocessing, C selection, and model fitting are **not rerun** in these
resamples. This describes variability from resampling the observed fixed
predictions; it does not capture full retraining/model-selection variability or
bootstrap subjects/clusters. Dependence among repeated rows and among CV fits
can limit interpretation, so the interval is not a universal 95% coverage
guarantee for future fitted models. No AUC hypothesis test or multiplicity
correction is performed. `lower_ci` and `upper_ci` in `results` are error
distances from AUC, not absolute endpoints. See the
[percentile bootstrap method](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)
and [ROC-AUC definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html).

The following standalone calculation reproduces the interval algorithm for
fixed example predictions; it does not fit a model or call a private API:

```python
import numpy as np
from sklearn.metrics import roc_auc_score

y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])  # positive event = 1
probability = np.array([0.1, 0.4, 0.35, 0.8, 0.3, 0.2, 0.9, 0.6, 0.7, 0.5])
rng = np.random.default_rng(42)
bootstrap_aucs = []
for _ in range(1000):
    rows = rng.choice(len(y), len(y), replace=True)
    if np.unique(y[rows]).size == 2:
        bootstrap_aucs.append(roc_auc_score(y[rows], probability[rows]))
auc = roc_auc_score(y, probability)
limits = np.percentile(bootstrap_aucs, [2.5, 97.5], method="linear")
print(auc, len(bootstrap_aucs), limits)
# 0.72, 999 valid resamples, approximately [0.291667, 1.0]
```

`forestplot` draws estimates already computed by these models or provided in a
table. Table `lower`/`upper` columns are absolute bounds; the caller determines
their method and level. It fits no model, adjusts no p-values, and derives no
new intervals. Cox and logistic model reference lines default to 1 and 0.5,
respectively; table input has no reference by default.
Implementation: [model fitting and AUC interval](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/_methods.py)
and [forestplot](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_specialized.py).

## ROC, precision–recall, and calibration

These functions evaluate supplied scores without fitting a classifier. Use
held-out or appropriately generated out-of-fold predictions for evaluating
generalization. Missing labels/scores and nonfinite numeric values are rejected;
all models use the same supplied rows.

`rocplot` requires both 0 and 1 labels, with **1 positive**, and finite real
scores where larger means more positive. Scores need not lie in [0, 1].
The AUC is the trapezoidal area under the empirical ROC curve. With
`ci_show=True`, it displays a different interval from `LogisticModel`: 1,000
**class-stratified** resamples (seed 42) preserve each class's sample size,
interpolate true-positive rate on 101 false-positive rates from 0 to 1, and
take pointwise 2.5th/97.5th percentiles. These are TPR bands, not an AUC CI or
a simultaneous confidence band. Models are not refitted.

`pairs` requests paired, two-sided DeLong AUC tests: the compared predictions
must belong to the same subjects in each row, with at least two observations
per class. Pair order defines first-AUC minus second-AUC; the p-value is
two-sided. The test accommodates correlated predictions on the same subjects,
but assumes independence across subjects and does not account for a training
procedure. With zero contrast variance the implementation returns p=1 for
equal AUCs and p=0 otherwise. `pairs=None` runs no comparison; `p_adjust=None`
leaves requested tests unadjusted. See [DeLong et al.](https://scholars.duke.edu/publication/712661)
and [scikit-learn ROC metrics](https://scikit-learn.org/stable/modules/model_evaluation.html#roc-metrics).

`precisionrecallplot` accepts two numeric, boolean, or string classes and an
explicit `pos_label` (default 1). Higher scores must indicate that class.
It reports average precision (AP), the recall-increment-weighted precision,
not trapezoidal PR area. The horizontal baseline is positive-class prevalence.
It computes no test or confidence band. See
[average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).

`calibrationplot` also accepts `pos_label`, but scores must be **probabilities
of that class in [0, 1]**. Defaults use five equal-width bins
(`strategy="uniform"`); `"quantile"` computes boundaries separately for each
model. Empty bins remain in results but are omitted from the line. Coordinates
are bin mean prediction and observed positive fraction, not fitted calibration
parameters. The displayed Brier score is mean squared probability error and
reflects more than calibration. There is no recalibration, confidence interval,
test, or multiplicity correction. See [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html).

This example fixes positive-class semantics and the ROC correction explicitly:

```python
import cnsplots as cns
import matplotlib.pyplot as plt
import pandas as pd

predictions = pd.DataFrame(
    {
        "event": [0, 0, 0, 0, 1, 1, 1, 1],  # 1 = positive event
        "model_a": [0.1, 0.4, 0.2, 0.6, 0.3, 0.8, 0.7, 0.9],
        "model_b": [0.2, 0.3, 0.5, 0.4, 0.6, 0.7, 0.3, 0.8],
    }
)
fig, axes = plt.subplots(1, 3, figsize=(12, 3))
cns.rocplot(
    predictions,
    "event",
    ["model_a", "model_b"],
    pairs=[("model_a", "model_b")],
    p_adjust="holm",
    ax=axes[0],
)
cns.precisionrecallplot(
    predictions,
    "event",
    ["model_a", "model_b"],
    pos_label=1,
    ax=axes[1],
)
cns.calibrationplot(
    predictions,
    "event",
    ["model_a", "model_b"],
    pos_label=1,
    n_bins=4,
    strategy="uniform",
    ax=axes[2],
)
```

Retrieve exact curves, metrics, counts, and available comparisons with
`get_roc_results`, `get_precision_recall_results`, and `get_calibration_results`.
Implementation: [ROC plot](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_specialized.py),
[ROC inference](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/helpers/_roc.py),
[PR plot](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_precision_recall.py),
and [calibration](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_calibration.py).

## Genomics and supplied statistical results

`volcanoplot` draws supplied effects and p-values; it does not estimate
differential expression or correct p-values. Positive x values retain the
contrast direction from the upstream analysis. By default y is already
minus-log10 adjusted p-value; `transform_y=True` applies minus-log10 to supplied
p-values, clipping zero to the smallest positive normal float. Default selection
thresholds are p<0.05 and absolute log2 fold change>0.5. Supply adjusted values
if the figure is intended to report adjusted significance: transforming raw
p-values does not adjust them. There is no unified complete-case cleaning here;
prepare finite effect/significance values and usable feature labels upstream.

`prerank` performs an analysis: it rejects missing gene/rank values, strips and
uppercases gene names, then calls GSEApy with gene-set sizes 15–1,000,
`permutation_num=1000`, and seed 42. It uses gene-set permutations, not subject
or phenotype permutations; identifiers, duplicate genes, tied ranks, and the
ranking direction should be resolved deliberately. Positive NES means
enrichment toward the top of the ranking and negative NES toward the bottom.
GSEApy computes nominal p-values and FDR q-values across its tested gene sets;
cnsplots returns only terms with FDR<0.25 and absolute NES>1.5. No additional
`p_adjust` is exposed. See [GSEApy prerank](https://gseapy.readthedocs.io/en/latest/run.html#gseapy.prerank)
and the [GSEA method](https://pmc.ncbi.nlm.nih.gov/articles/PMC1239896/).

`gseaplot` draws supplied results and filters `significance_column` (default
`"FDR q-val"`) at `cutoff=0.05`; its color encoding is independent of that
filter. It performs no enrichment analysis or additional correction. Heatmaps,
dendrograms, and other displays of supplied values likewise do not attach
statistical significance to visible patterns merely by drawing them.
Implementation: [genomics plots](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/plots/_genomics.py)
and [prerank](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/_methods.py).
