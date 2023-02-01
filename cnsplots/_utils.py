import itertools

import matplotlib.pyplot as plt
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


def _p_value_helper(test, data, x, ax, plotting, pairs):
    if pairs == "all":
        pairs = list(itertools.combinations(data[x].unique(), 2))
    annotator = saa.Annotator(ax, pairs, **plotting)
    annotator.configure(
        test=test,
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
    annotator.apply_and_annotate()
    if test == "Mann-Whitney":
        print("   ---> P values were determined by two-sided Mann-Whitney U test.")
    if test == "t-test_welch":
        print("   ---> P values were determined by two-sided Welch's t-test.")
