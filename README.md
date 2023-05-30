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

mplscience.available_styles()
mplscience.set_style()
df = sns.load_dataset("anscombe")
sns.scatterplot(x="x", y="y", hue="dataset", data=df)
```


## TODO:
- add examples to the end of each function: [see](https://sphinx-gallery.github.io/stable/configuration.html?highlight=mini#references-to-examples)
- heatmapplot truncate dendrogram: [see](https://stackoverflow.com/questions/66180002/scipy-cluster-hierarchy-dendrogram-exactly-what-does-truncate-mode-level-do)
- heatmapplot adjust labels: [see](https://jokergoo.github.io/ComplexHeatmap-reference/book/more-examples.html#visualize-cell-heterogeneity-from-single-cell-rnaseq)
- gseaplot: [example](https://gseapy.readthedocs.io/en/latest/gseapy_example.html)
- hazardplot: [see](https://lifelines.readthedocs.io/en/latest/Survival%20Regression.html)
- networkplot
- phyloplot: [stream](https://github.com/pinellolab/STREAM)
