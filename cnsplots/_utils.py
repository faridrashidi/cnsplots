import itertools
import operator

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import num2tex
import palettable
import pandas as pd
import scipy.stats as stats
import seaborn as sns
from statannotations.Annotator import Annotator
from statannotations.PValueFormat import PValueFormat
from statannotations.utils import DEFAULT

import cnsplots as cns

RED = "#E41A1C"
BLUE = "#377EB8"
GREEN = "#4DAF4A"
PURPLE = "#984EA3"
ORANGE = "#FF7F00"
YELLOW = "#FFFF33"
BROWN = "#A65628"
PINK = "#F781BF"
GRAY = "#999999"


def figure(height=150, width=150, color_cycle="Set1", color_map="parula"):
    cns.setup_matplotlib(color_cycle, color_map)
    plt.figure(figsize=(width / 72, height / 72), dpi=72 * 2)


def take_legend_out(title=None):
    if title is None:
        ax = plt.gca()
        title = ax.get_legend().get_title().get_text()
    plt.legend(
        bbox_to_anchor=(1, 1.02),
        loc="upper left",
        title=title,
    )


def get_hexcolors_from_apalette(
    alist, palette=palettable.colorbrewer.qualitative.Set1_9.hex_colors
):
    return list(operator.itemgetter(*alist)(palette))


def _is_qualitative_cmap(cmap_name):
    if isinstance(cmap_name, list) or isinstance(cmap_name, dict):
        return True
    else:
        cmap = plt.get_cmap(cmap_name)
        return cmap.N < 33


def _get_hex_colors_from_colorbar(cmap_name, n_colors):
    cmap = plt.cm.get_cmap(cmap_name)
    if _is_qualitative_cmap(cmap_name):
        colors = [mcolors.to_hex(cmap(i)) for i in range(0, n_colors)]
    else:
        colors = [mcolors.to_hex(cmap(i)) for i in range(0, cmap.N, cmap.N // n_colors)]
    return colors


def _remove_edge_from_legend_items(ax):
    handles, labels = ax.get_legend_handles_labels()
    for handle in handles:
        handle.set_edgecolor("none")
    ax.legend(handles, labels)


def _addcount_helper(data, attr, ax):
    xtick_labels = ax.get_xticklabels()
    new_xtick_labels = []
    for label in xtick_labels:
        n = len(data[data[attr] == label.get_text()])
        new_xtick_labels.append(f"{label.get_text()}\n(n={n})")
    ax.set_xticklabels(new_xtick_labels)


def _p_value_helper(test, data, ax, plotting, pairs, contingency=None, format="full"):
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

        if format == "full":

            def format_data(self, result):
                text = f"{result.test_short_name} " if self.show_test_name else ""
                if result.pvalue > 0.05:
                    return "ns"
                return r"${}P = {}{}$".format(
                    "{}", self.pvalue_format_string, "{}"
                ).format(
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
        text_format=format,
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
        print("   ---> P-values were determined by two-sided Mann-Whitney U test.")
    if test == "t-test_welch":
        print("   ---> P-values were determined by two-sided Welch's t-test.")
    if test == "fisher-exact":
        print("   ---> P-values were determined by two-sided Fisher's exact test.")
    if test == "chi-squared":
        print("   ---> P-values were determined by two-sided Chi-squared test.")


def palettes(color):
    if isinstance(color, list):
        return sns.color_palette(color)
    else:
        if color == "Set1":
            return palettable.colorbrewer.qualitative.Set1_9.mpl_colors
        elif color == "Set2":
            return palettable.colorbrewer.qualitative.Set2_8.mpl_colors
        elif color == "Set3":
            return palettable.colorbrewer.qualitative.Set3_12.mpl_colors
        elif color == "Pastel1":
            return palettable.colorbrewer.qualitative.Pastel1_9.mpl_colors
        elif color == "Pastel2":
            return palettable.colorbrewer.qualitative.Pastel2_8.mpl_colors
        elif color == "Paired":
            return palettable.colorbrewer.qualitative.Paired_12.mpl_colors
        elif color == "Dark2":
            return palettable.colorbrewer.qualitative.Dark2_8.mpl_colors
        elif color == "Accent":
            return palettable.colorbrewer.qualitative.Accent_8.mpl_colors
        elif color == "Tableau":
            return palettable.tableau.Tableau_10.mpl_colors
        elif color == "Bold":
            return palettable.cartocolors.qualitative.Bold_10.mpl_colors
        elif color == "BlueRed":
            return palettable.tableau.BlueRed_6.mpl_colors
        elif color == "ECharts":
            colors = [
                "#5470c6",
                "#91cc75",
                "#fac858",
                "#ee6666",
                "#9a60b4",
                "#73c0de",
                "#3ba272",
                "#fc8452",
                "#27727b",
                "#ea7ccc",
                "#d7504b",
                "#e87c25",
                "#b5c334",
                "#fe8463",
                "#26c0c0",
                "#f4e001",
            ]
            return sns.color_palette(colors)
        elif color == "Ecotyper1":
            colors = [
                "#D6372E",
                "#5189BB",
                "#70B460",
                "#985EA8",
                "#F08F35",
                "#FADD4B",
                "#A3A3A3",
                "#B7D3E5",
                "#E6D8C2",
            ]
            # colors = [
            #     "#D6372E",
            #     "#FADD4B",
            #     "#70B460",
            #     "#E690C1",
            #     "#985EA8",
            #     "#A3A3A3",
            #     "#B7D3E5",
            #     "#E6D8C2",
            #     "#F08F35",
            #     "#5189BB",
            # ]
            return sns.color_palette(colors)
        elif color == "Ecotyper2":
            colors = ["#EB7D5B", "#FED23F", "#B5D33D", "#6CA2EA", "#442288"]
            return sns.color_palette(colors)
        elif color == "Ecotyper3":
            colors = [
                "#D13570",
                "#569AB4",
                "#70AC58",
                "#74509D",
                "#ED7E30",
                "#F5C945",
                "#9C5732",
                "#E787E5",
            ]
            return sns.color_palette(colors)
        elif color == "Ecotyper4":
            colors = [
                "#386cb0",
                "#fdb462",
                "#7fc97f",
                "#ef3b2c",
                "#662506",
                "#a6cee3",
                "#fb9a99",
                "#984ea3",
                "#ffff33",
            ]
            return sns.color_palette(colors)
        elif color == "Ecotyper5":
            colors = [
                "#E41A71",
                "#379DB8",
                "#5BAF4A",
                "#7B4EA3",
                "#FF7600",
                "#FFC800",
                "#A65328",
                "#F781EC",
                "#999999",
                "#A6DCE3",
                "#BBDF8A",
                "#FB9A99",
                "#FDB96F",
                "#BEB2D6",
                "#1B9E5E",
                "#D95802",
                "#707EB3",
                "#E729D3",
                "#E69F02",
                "#8DD3B9",
                "#FFFAB3",
                "#BABFDA",
                "#FB7F72",
                "#80C5D3",
                "#FDAE62",
                "#BEDE69",
                "#FCCDF7",
            ]
            return sns.color_palette(colors)
        elif color == "Ecotyper6":
            colors = [
                "#FDC086",
                "#386CB0",
                "#F0027F",
                "#FFFF99",
                "#BF5B17",
                "#7FC97F",
                "lightblue",
                "#BEAED4",
                "#66C2A5",
                "#FC8D62",
                "#8DA0CB",
                "#E78AC3",
                "#A6D854",
                "#FFD92F",
                "#E5C494",
                "#B3B3B3",
                "#FBB4AE",
                "#B3CDE3",
                "#CCEBC5",
                "#DECBE4",
                "#FED9A6",
                "#FFFFCC",
                "#E5D8BD",
                "#FDDAEC",
            ]
            return sns.color_palette(colors)
        elif color == "parula":
            cm_data = [
                [0.2081, 0.1663, 0.5292],
                [0.2116238095, 0.1897809524, 0.5776761905],
                [0.212252381, 0.2137714286, 0.6269714286],
                [0.2081, 0.2386, 0.6770857143],
                [0.1959047619, 0.2644571429, 0.7279],
                [0.1707285714, 0.2919380952, 0.779247619],
                [0.1252714286, 0.3242428571, 0.8302714286],
                [0.0591333333, 0.3598333333, 0.8683333333],
                [0.0116952381, 0.3875095238, 0.8819571429],
                [0.0059571429, 0.4086142857, 0.8828428571],
                [0.0165142857, 0.4266, 0.8786333333],
                [0.032852381, 0.4430428571, 0.8719571429],
                [0.0498142857, 0.4585714286, 0.8640571429],
                [0.0629333333, 0.4736904762, 0.8554380952],
                [0.0722666667, 0.4886666667, 0.8467],
                [0.0779428571, 0.5039857143, 0.8383714286],
                [0.079347619, 0.5200238095, 0.8311809524],
                [0.0749428571, 0.5375428571, 0.8262714286],
                [0.0640571429, 0.5569857143, 0.8239571429],
                [0.0487714286, 0.5772238095, 0.8228285714],
                [0.0343428571, 0.5965809524, 0.819852381],
                [0.0265, 0.6137, 0.8135],
                [0.0238904762, 0.6286619048, 0.8037619048],
                [0.0230904762, 0.6417857143, 0.7912666667],
                [0.0227714286, 0.6534857143, 0.7767571429],
                [0.0266619048, 0.6641952381, 0.7607190476],
                [0.0383714286, 0.6742714286, 0.743552381],
                [0.0589714286, 0.6837571429, 0.7253857143],
                [0.0843, 0.6928333333, 0.7061666667],
                [0.1132952381, 0.7015, 0.6858571429],
                [0.1452714286, 0.7097571429, 0.6646285714],
                [0.1801333333, 0.7176571429, 0.6424333333],
                [0.2178285714, 0.7250428571, 0.6192619048],
                [0.2586428571, 0.7317142857, 0.5954285714],
                [0.3021714286, 0.7376047619, 0.5711857143],
                [0.3481666667, 0.7424333333, 0.5472666667],
                [0.3952571429, 0.7459, 0.5244428571],
                [0.4420095238, 0.7480809524, 0.5033142857],
                [0.4871238095, 0.7490619048, 0.4839761905],
                [0.5300285714, 0.7491142857, 0.4661142857],
                [0.5708571429, 0.7485190476, 0.4493904762],
                [0.609852381, 0.7473142857, 0.4336857143],
                [0.6473, 0.7456, 0.4188],
                [0.6834190476, 0.7434761905, 0.4044333333],
                [0.7184095238, 0.7411333333, 0.3904761905],
                [0.7524857143, 0.7384, 0.3768142857],
                [0.7858428571, 0.7355666667, 0.3632714286],
                [0.8185047619, 0.7327333333, 0.3497904762],
                [0.8506571429, 0.7299, 0.3360285714],
                [0.8824333333, 0.7274333333, 0.3217],
                [0.9139333333, 0.7257857143, 0.3062761905],
                [0.9449571429, 0.7261142857, 0.2886428571],
                [0.9738952381, 0.7313952381, 0.266647619],
                [0.9937714286, 0.7454571429, 0.240347619],
                [0.9990428571, 0.7653142857, 0.2164142857],
                [0.9955333333, 0.7860571429, 0.196652381],
                [0.988, 0.8066, 0.1793666667],
                [0.9788571429, 0.8271428571, 0.1633142857],
                [0.9697, 0.8481380952, 0.147452381],
                [0.9625857143, 0.8705142857, 0.1309],
                [0.9588714286, 0.8949, 0.1132428571],
                [0.9598238095, 0.9218333333, 0.0948380952],
                [0.9661, 0.9514428571, 0.0755333333],
                [0.9763, 0.9831, 0.0538],
            ]
            return mpl.colors.LinearSegmentedColormap.from_list("parula", cm_data)
        else:
            return RuntimeError("Wrong Choice!")
