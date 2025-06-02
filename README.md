# cnsplots

[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg?logo=visualstudiocode&logoColor=FFFFFF&style=flat-square)](https://github.com/python/black)
[![License](https://img.shields.io/pypi/l/cnsplots.svg?logo=creativecommons&logoColor=FFFFFF&style=flat-square&color=blueviolet)](https://github.com/faridrashidi/cnsplots/blob/main/LICENSE)

Creating visually appealing plots for scientific publications, including prestigious
journals such as Cell, Nature, and Science. The goal is to enhance the aesthetic quality
of your charts while maintaining simplicity and clarity. It ensures that the PDF font
type is compatible with Adobe Illustrator, ensuring seamless integration into your
publication workflow. It is fully compatible with all Matplotlib-based packages,
including Seaborn.

[![Overview](docs/_static/images/overview.png?raw=true)](https://farid.one/cnsplots/auto_examples/index.html)

## Usage

To install:

```bash
pip install cnsplots
```

To use:

```python
import cnsplots as cns
import seaborn as sns
import matplotlib.pyplot as plt

df = sns.load_dataset("tips")  # The data in pandas format
cns.figure(150, 100)  # Create figure size (height x weight) in pixels
cns.boxplot(data=df, x="day", y="total_bill")  # Generate the boxplot from data
plt.savefig("figure.svg")  # Save the figure
```

## Installation

```
poetry lock
poetry install --extras "dev doc"
rm -rf .Rprofile && Rscript -e 'renv::init(); renv::settings$use.cache(FALSE)'
poetry run python install_r_packages.py
```

## TODO:

- gseaplot: [example](https://gseapy.readthedocs.io/en/latest/gseapy_example.html)
- heatmapplot truncate dendrogram: [see](https://stackoverflow.com/questions/66180002/scipy-cluster-hierarchy-dendrogram-exactly-what-does-truncate-mode-level-do)
- heatmapplot adjust labels: [see](https://jokergoo.github.io/ComplexHeatmap-reference/book/more-examples.html#visualize-cell-heterogeneity-from-single-cell-rnaseq)
- heatmapplot shrink cbar width
- networkplot
- phyloplot: [stream](https://github.com/pinellolab/STREAM)
- dotplot number of dots in the dot size legend: [see](https://github.com/DingWB/PyComplexHeatmap/blob/main/PyComplexHeatmap/dotHeatmap.py#L608)
- regplot hue
- sns.FacetGrid: [see](https://seaborn.pydata.org/tutorial/axis_grids.html)
