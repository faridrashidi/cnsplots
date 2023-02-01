import itertools

import matplotlib.pyplot as plt
import palettable
import statannotations.Annotator as saa


def figure(height=150, width=150):
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


def _p_value_helper(test, data, x, ax, plotting, pairs, pvalues=None):
    if pairs == "all":
        pairs = list(itertools.combinations(data[x].unique(), 2))
    annotator = saa.Annotator(ax, pairs, **plotting)
    annotator.configure(
        test=test if pvalues is None else None,
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
    )
    if pvalues is None:
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
        return palettable.colorbrewer.qualitative.Set1_9.hex_colors
    elif color == "Tableau":
        return palettable.Tableau.Tableau_10.hex_colors
    elif color == "Bold":
        return palettable.cartocolors.qualitative.Bold_10.hex_colors
    elif color == "BlueRed":
        return palettable.Tableau.BlueRed_6.hex_colors
    else:
        return None
