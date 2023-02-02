import itertools

import matplotlib.pyplot as plt
import num2tex
import palettable
import pandas as pd
import scipy.stats as stats
from statannotations.Annotator import Annotator
from statannotations.PValueFormat import PValueFormat
from statannotations.utils import DEFAULT

import cnsplots as cns


def figure(height=150, width=150, color_cycle="Set1", color_map="parula"):
    cns.setup_matplotlib(color_cycle, color_map)
    plt.figure(figsize=(width / 72, height / 72), dpi=72)


def take_legend_out(title=None):
    if title is None:
        ax = plt.gca()
        title = ax.get_legend().get_title().get_text()
    plt.legend(
        bbox_to_anchor=(1, 1.02),
        loc="upper left",
        title=title,
    )


def _p_value_helper(test, data, ax, plotting, pairs, contingency=None):
    class PValueFormatNew(PValueFormat):
        def __init__(self):
            super(PValueFormat, self).__init__()
            self._pvalue_format_string = "{:.3e}"
            self._simple_format_string = "{:.2f}"
            self._text_format = "star"
            self.fontsize = "medium"
            self._default_pvalue_thresholds = True
            self._pvalue_thresholds = self._get_pvalue_thresholds(DEFAULT)
            self._correction_format = "{star} ({suffix})"
            self.show_test_name = True

        def format_data(self, result):
            text = f"{result.test_short_name} " if self.show_test_name else ""
            return r"${}P = {}{}$".format("{}", self.pvalue_format_string, "{}").format(
                text, num2tex.num2tex(result.pvalue), result.significance_suffix
            )

    if pd.api.types.is_numeric_dtype(data[plotting["x"]]):
        plotting["orient"] = "h"
        if pairs == "all":
            pairs = list(itertools.combinations(data[plotting["y"]].unique(), 2))
    else:
        if pairs == "all":
            pairs = list(itertools.combinations(data[plotting["x"]].unique(), 2))

    annotator = Annotator(ax, pairs, **plotting)
    annotator._pvalue_format = PValueFormatNew()
    annotator.configure(
        test=test if contingency is None else None,
        text_format="full",
        loc="outside",
        line_width=0.8,
        line_offset=0,
        line_offset_to_group=0,
        text_offset=0.5,
        color="black",
        show_test_name=False,
        pvalue_format_string="{:.1e}",
        use_fixed_offset=True,
        verbose=0,
    )

    pvalues = []
    if test == "fisher-exact":
        for pair in pairs:
            pvalues.append(stats.fisher_exact(contingency.loc[list(pair)].values)[1])
    if test == "chi-squared":
        for pair in pairs:
            pvalues.append(
                stats.chi2_contingency(contingency.loc[list(pair)].values)[1]
            )

    if contingency is None:
        annotator.apply_and_annotate()
    else:
        annotator.set_pvalues(pvalues=pvalues)
        annotator.annotate()

    if test == "Mann-Whitney":
        print("   ---> P values were determined by two-sided Mann-Whitney U test.")
    if test == "t-test_welch":
        print("   ---> P values were determined by two-sided Welch's t-test.")
    if test == "fisher-exact":
        print("   ---> P values were determined by two-sided Fisher's exact test")
    if test == "chi-squared":
        print("   ---> P values were determined by two-sided Chi-squared test")


def palettes(color):
    if color == "Set1":
        return palettable.colorbrewer.qualitative.Set1_9.mpl_colors
    elif color == "Tableau":
        return palettable.tableau.Tableau_10.mpl_colors
    elif color == "Bold":
        return palettable.cartocolors.qualitative.Bold_10.mpl_colors
    elif color == "BlueRed":
        return palettable.tableau.BlueRed_6.mpl_colors
    else:
        return RuntimeError("Wrong Choice!")
