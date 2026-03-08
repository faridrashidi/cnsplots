# cnsplots

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/cnsplots?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/cnsplots/)
[![Python Version](https://img.shields.io/pypi/pyversions/cnsplots?logo=python&logoColor=white&style=flat-square)](https://pypi.org/project/cnsplots/)
[![License](https://img.shields.io/pypi/l/cnsplots.svg?logo=creativecommons&logoColor=white&style=flat-square&color=blueviolet)](https://github.com/faridrashidi/cnsplots/blob/main/LICENSE.md)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg?logo=ruff&logoColor=white&style=flat-square)](https://github.com/astral-sh/ruff)

**Publication-Ready Scientific Plots for Cell, Nature, and Science Journals**

Create visually stunning, journal-quality figures with minimal code. Built on matplotlib, fully compatible with seaborn, and optimized for Adobe Illustrator.

[Documentation](https://farid.one/cnsplots/) · [Examples Gallery](https://farid.one/cnsplots/examples/index.html) · [Report Bug](https://github.com/faridrashidi/cnsplots/issues) · [Request Feature](https://github.com/faridrashidi/cnsplots/issues)

</div>

---

## Overview

[![Overview](docs/_static/images/overview.png?raw=true)](https://farid.one/cnsplots/examples/index.html)

**cnsplots** is a Python visualization library designed specifically for creating publication-ready scientific figures. It takes care of the tedious styling details so you can focus on your science.

### Why cnsplots?

- 🎨 **Publication-Ready**: Pre-configured styles matching Cell, Nature, and Science journal requirements
- 🎯 **Simple API**: Create complex multi-panel figures with just a few lines of code
- 📐 **Precise Control**: Specify dimensions in pixels, perfect for journal submission guidelines
- 🖋️ **Adobe Illustrator Compatible**: SVG exports with editable fonts (no text-to-path conversion)
- 📊 **Statistical Integration**: Built-in statistical tests and annotations
- 🔧 **Highly Customizable**: Full control over colors, fonts, and styling
- 🌈 **Rich Color Palettes**: Curated color schemes optimized for scientific visualization
- 🧩 **Multi-Panel Support**: Easy creation of complex figure layouts

## Features

### 📊 25+ Plot Types

**Basic Plots**

- Box plots, violin plots, bar plots, strip plots
- Scatter plots, line plots, regression plots
- Histograms, KDE plots, ridge plots

**Scientific Plots**

- Survival plots (Kaplan-Meier)
- Cumulative incidence plots
- ROC curves and forest plots
- Volcano plots and GSEA plots
- Confusion matrices

**Specialized Plots**

- Heatmaps with hierarchical clustering
- Dot plots for enrichment
- Venn diagrams and UpSet plots
- Sankey diagrams
- Pie and donut charts
- QQ plots and slope plots

### 🎨 Beautiful Color Palettes

Multiple curated palettes including:

- **Qualitative**: Ecotyper1-6, Set1-3, Tableau, Bold
- **Sequential**: Parula, gnuplot, custom gradients
- **Diverging**: BlueRed, BuRd_custom, OrBu_custom

### 📐 Multi-Panel Figures

Create complex layouts with automatic panel labeling (A, B, C...):

```python
import cnsplots as cns

mp = cns.multipanel(max_width=540)

# Panel A
mp.panel("A", height=150, width=150)
cns.boxplot(data=df1, x="group", y="value")

# Panel B
mp.panel("B", height=150, width=150)
cns.scatterplot(data=df2, x="x", y="y")

# Continues...
```

## Installation

### From PyPI

```bash
pip install cnsplots
```

### For Development

First install [uv](https://docs.astral.sh/uv/), then:

```bash
git clone https://github.com/faridrashidi/cnsplots
cd cnsplots
make install
```

## Quick Start

### Basic Usage

```python
import cnsplots as cns
import seaborn as sns
import matplotlib.pyplot as plt

# Load example data
df = sns.load_dataset("tips")

# Create a figure (dimensions in pixels)
cns.figure(height=150, width=100)

# Create a publication-ready boxplot
cns.boxplot(data=df, x="day", y="total_bill")

# Save as vector graphic
plt.savefig("figure.svg")
```

### Statistical Comparisons

```python
# Add statistical significance annotations
cns.figure(150, 150)
cns.boxplot(
    data=df,
    x="day",
    y="total_bill",
    pairs=[("Thur", "Fri"), ("Sat", "Sun")],  # Compare these pairs
)
# Prints: P-values were determined by two-sided Mann-Whitney U test.
```

### Custom Colors

```python
# Use custom color palette
cns.figure(150, 200, color_cycle="Ecotyper1")
cns.violinplot(data=df, x="day", y="total_bill", hue="sex")
```

## Examples Gallery

Explore our comprehensive [examples gallery](https://farid.one/cnsplots/examples/index.html) featuring:

- 📦 Basic statistical plots
- 🧬 Genomics and bioinformatics visualizations
- 📈 Time-series and survival analysis
- 🎯 Machine learning results (ROC, confusion matrices)
- 🔬 Multi-omics data visualization
- 🎨 Custom color schemes and styling

## Documentation

Full documentation is available at [farid.one/cnsplots](https://farid.one/cnsplots/)

- [Installation Guide](https://farid.one/cnsplots/installation.html)
- [API Reference](https://farid.one/cnsplots/api.html)
- [Examples Gallery](https://farid.one/cnsplots/examples/index.html)

## Key Concepts

### Figure Dimensions

Specify sizes in **pixels** for precise control:

```python
cns.figure(height=150, width=100)  # Creates 150px × 100px figure
```

### Color Palettes

Access curated color palettes:

```python
# Qualitative palettes (for categorical data)
cns.figure(color_cycle="Ecotyper1")  # Default, optimized for journals
cns.figure(color_cycle="Set1")  # ColorBrewer Set1

# Sequential palettes (for continuous data)
cns.figure(color_map="parula")  # MATLAB-style
cns.figure(color_map="gnuplot")  # Default sequential

# Get individual colors
red = cns.RED
blue = cns.BLUE
```

### Statistical Tests

Many plot functions include built-in statistical testing:

```python
# Boxplot with Mann-Whitney U test
cns.boxplot(data=df, x="group", y="value", pairs="all")

# Barplot with Welch's t-test
cns.barplot(data=df, x="group", y="value", pairs=[("A", "B")])

# Stackplot with Fisher's exact test
cns.stackplot(data=df, x="group", y="category", pairs=[("A", "B")])
```

### Export for Publication

```python
# SVG for vector graphics (recommended)
plt.savefig("figure.svg")

# High-resolution PNG
plt.savefig("figure.png", dpi=300)

# PDF with editable text
plt.savefig("figure.pdf")
```

## Requirements

- Python ≥ 3.9
- Core: matplotlib, numpy, pandas, seaborn
- Optional: lifelines, gseapy, scanpy (for specific plot types)

See [pyproject.toml](pyproject.toml) for complete dependency list.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

Follow the development installation instructions above, then use `make lint` to run formatters and linters before submitting a PR.

## Citation

If you use cnsplots in your research, please cite:

```bibtex
@software{cnsplots,
  author = {Rashidi, Farid},
  title = {cnsplots: Publication-Ready Scientific Plots},
  year = {2026},
  url = {https://github.com/faridrashidi/cnsplots}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

Built with:

- [matplotlib](https://matplotlib.org/) - Core plotting library
- [seaborn](https://seaborn.pydata.org/) - Statistical visualizations
- [lifelines](https://lifelines.readthedocs.io/) - Survival analysis
- [PyComplexHeatmap](https://github.com/DingWB/PyComplexHeatmap) - Complex heatmaps
- [UpSetPlot](https://upsetplot.readthedocs.io/) - Set intersections

Inspired by the visualization standards of Cell, Nature, and Science journals.

## Support

- 📖 [Documentation](https://farid.one/cnsplots/)
- 🐛 [Issue Tracker](https://github.com/faridrashidi/cnsplots/issues)
- 💬 [Discussions](https://github.com/faridrashidi/cnsplots/discussions)

## Related Projects

- [matplotlib](https://matplotlib.org/) - The foundation of Python plotting
- [seaborn](https://seaborn.pydata.org/) - Statistical data visualization
- [plotnine](https://plotnine.readthedocs.io/) - Grammar of graphics for Python
- [altair](https://altair-viz.github.io/) - Declarative visualization

---

<div align="center">

Made with ❤️ for the scientific community

[⭐ Star us on GitHub](https://github.com/faridrashidi/cnsplots) · [📖 Read the Docs](https://farid.one/cnsplots/)

</div>
