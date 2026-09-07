# cnsplots

<p align="center">
  <img src="https://raw.githubusercontent.com/faridrashidi/cnsplots/main/docs/_static/images/logo.svg" alt="cnsplots logo" width="240">
</p>

<div align="center">

[![Tests](https://img.shields.io/github/actions/workflow/status/faridrashidi/cnsplots/ci-tests.yml?branch=main&logo=github&logoColor=white&style=flat-square&label=tests&labelColor=000000&cacheSeconds=0)](https://github.com/faridrashidi/cnsplots/actions/workflows/ci-tests.yml)
[![Docs](https://img.shields.io/website?url=https%3A%2F%2Fcnsplots.farid.one%2F&up_message=online&down_message=offline&logo=readthedocs&logoColor=white&style=flat-square&label=docs&labelColor=000000&cacheSeconds=0)](https://cnsplots.farid.one/)
[![Downloads](https://img.shields.io/pepy/dt/cnsplots?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI%2BPHBhdGggZmlsbD0iI2ZmZiIgZD0iTTExIDNoMnYxMGwzLjUtMy41IDEuNCAxLjQtNS45IDUuOS01LjktNS45IDEuNC0xLjRMMTEgMTNWM3pNNSAxOGgxNHYzSDV6Ii8%2BPC9zdmc%2B&style=flat-square&label=downloads&labelColor=000000&cacheSeconds=0)](https://pepy.tech/project/cnsplots)
[![PyPI](https://img.shields.io/pypi/v/cnsplots?logo=pypi&logoColor=white&style=flat-square&labelColor=000000&cacheSeconds=0)](https://pypi.org/project/cnsplots/)
[![Python Version](https://img.shields.io/badge/python-3.10%20to%203.14-blue?logo=python&logoColor=white&style=flat-square&labelColor=000000&cacheSeconds=0)](https://pypi.org/project/cnsplots/)
[![License](https://img.shields.io/pypi/l/cnsplots?logo=creativecommons&logoColor=white&style=flat-square&labelColor=000000&color=blueviolet&cacheSeconds=0)](https://github.com/faridrashidi/cnsplots/blob/main/LICENSE.md)

**Publication-Ready Scientific Plots for Cell, Nature, and Science Journals**

Create visually stunning, journal-quality figures with minimal code. Built on matplotlib, fully compatible with seaborn, and optimized for Adobe Illustrator.

[Documentation](https://cnsplots.farid.one/) · [Examples Gallery](https://cnsplots.farid.one/latest/examples/index.html) · [Report Bug](https://github.com/faridrashidi/cnsplots/issues) · [Request Feature](https://github.com/faridrashidi/cnsplots/issues)

</div>

---

## Overview

<a href="https://cnsplots.farid.one/latest/examples/showcase.html#figure-1">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://cnsplots.farid.one/latest/_images/sphx_glr_showcase_001_dark.png">
    <source media="(prefers-color-scheme: light)" srcset="https://cnsplots.farid.one/latest/_images/sphx_glr_showcase_001.png">
    <img src="https://cnsplots.farid.one/latest/_images/sphx_glr_showcase_001.png" alt="cnsplots overview">
  </picture>
</a>

**cnsplots** is a Python visualization library designed specifically for creating publication-ready scientific figures. It takes care of the tedious styling details so you can focus on your science.

### Why cnsplots?

- 🎨 **Publication-Ready**: Pre-configured styles matching Cell, Nature, and Science journal requirements
- 🎯 **Simple API**: Create complex multi-panel figures with just a few lines of code
- 📐 **Precise Control**: Specify dimensions in points, inches, or millimeters for publication layouts
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

- **Qualitative**: Cell, Nature, Science, Ecotyper1-6, Set1-3, Tableau, Bold
- **Sequential**: Parula, gnuplot, custom gradients
- **Diverging**: BlueRed, BuRd_custom, OrBu_custom

### 📐 Multi-Panel Figures

Create complex layouts with automatic panel labeling (A, B, C...):

```python
import cnsplots as cns

mp = cns.multipanel(max_width=540)

# Panel A
mp.panel("A", width=150, height=150)
cns.boxplot(data=df1, x="group", y="value")

# Panel B
mp.panel("B", width=150, height=150)
cns.scatterplot(data=df2, x="x", y="y")

# Continues...
```

## Installation

### From PyPI

```bash
pip install cnsplots
```

This installs every supported plotting and scientific integration. Imports
remain lazy, so those backends are loaded only when their APIs are first used.

### Agent Skill

Install the bundled cnsplots skill so Codex and Claude Code can build plots
using the package's current workflow and API:

```bash
cnsplots skill install
```

By default this installs the skill for both agents at user scope. Target one
agent or the current project when needed:

```bash
cnsplots skill install --agent codex
cnsplots skill install --agent claude --scope project
```

Use `$cnsplots` in Codex or `/cnsplots` in Claude Code to invoke it explicitly.
Inspect, update, or remove an installation with the same agent and scope options:

```bash
cnsplots skill status
cnsplots skill install --force
cnsplots skill uninstall --agent claude --scope project
cnsplots skill --help
```

Status reports the destination, installed version, and whether the content
matches the bundled skill. Updates overwrite current packaged files and remove
unchanged obsolete files, while preserving unrelated files and modified obsolete
files. Uninstall removes only unchanged managed files and preserves local edits.
See the [installation guide](docs/installation.md#install-the-agent-skill) for
ownership tracking, legacy installations, and exit codes.

### For Development

First install [uv](https://docs.astral.sh/uv/), then:

```bash
git clone https://github.com/faridrashidi/cnsplots
cd cnsplots
make install
```

This installs the package with its development and documentation dependencies.

## Quick Start

### Basic Usage

```python
import cnsplots as cns

# Load example data
df = cns.datasets.load_dataset("tips")

# Create a figure (width, height in points)
fig = cns.figure(width=100, height=150)

# Create a publication-ready boxplot
cns.boxplot(data=df, x="day", y="total_bill")

# Save as vector graphic
cns.savefig("figure.svg", fig=fig)
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
    test="t-test_welch",
    p_adjust="holm",
)
# Prints: P-values were determined by two-sided Welch's t-test.
```

### Custom Colors

```python
# Use custom color palette
cns.figure(200, 150, color_cycle="Ecotyper1")
cns.violinplot(data=df, x="day", y="total_bill", hue="sex")
```

## Examples Gallery

Explore our comprehensive [examples gallery](https://cnsplots.farid.one/latest/examples/index.html) featuring:

- 📦 Basic statistical plots
- 🧬 Genomics and bioinformatics visualizations
- 📈 Time-series and survival analysis
- 🎯 Machine learning results (ROC, confusion matrices)
- 🔬 Multi-omics data visualization
- 🎨 Custom color schemes and styling

## Documentation

Full documentation is available at [cnsplots.farid.one](https://cnsplots.farid.one/)

- [Installation Guide](https://cnsplots.farid.one/latest/installation.html)
- [API Reference](https://cnsplots.farid.one/latest/api.html)
- [Examples Gallery](https://cnsplots.farid.one/latest/examples/index.html)

## Key Concepts

### Figure Dimensions

Specify width and height in **points** by default: one point is 1/72 inch.
These are the legacy logical 72-DPI units, so existing numeric calls retain
their physical size. Use `unit="pt"`, `unit="in"`, or `unit="mm"` explicitly:

```python
fig = cns.figure(width=100, height=150)
print(fig.get_size_inches())  # [1.38888889 2.08333333]
print(fig.canvas.get_width_height())  # (200, 300) at the default display DPI of 144

# Equivalent 2 × 1 inch canvases
cns.figure(144, 72, unit="pt")
cns.figure(2, 1, unit="in")
cns.figure(50.8, 25.4, unit="mm")
```

`figure` dimensions describe the whole canvas. Display DPI determines its
pixel dimensions; export DPI determines raster resolution without changing
the physical size. The 100 × 150 point canvas exports as 400 × 600 pixels at
the default export DPI of 288 when saved with `bbox_inches=None`. The default
`bbox_inches="tight"` instead crops around artists and adds `pad_inches`
(in inches), so the saved dimensions can differ from the full canvas.

`cns.multipanel(max_width=..., unit="mm")` sets the full canvas width and the
unit inherited by explicit `mp.panel(..., width=..., height=...)` sizes.
Panel sizes describe the axes area; labels, titles, and margins contribute
to the layout and total height. A panel can override `unit` independently.
Margins remain in points and label `pad_left`/`pad_top` remain in display
pixels. Omitted dimensions always use settings stored in points, regardless
of `unit`.

`cns.figure(...)` returns the Matplotlib `Figure` and makes it current for
subsequent plotting calls. Retain it to export a specific figure with `fig=`.

### Color Palettes

Access curated color palettes:

```python
# Qualitative palettes (for categorical data)
cns.figure(color_cycle="Ecotyper1")  # Default, optimized for journals
cns.figure(color_cycle="Cell")  # Custom Cell-inspired journal palette
cns.figure(color_cycle="Nature")  # Nature-inspired journal palette
cns.figure(color_cycle="Science")  # Science-inspired journal palette
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
# Boxplot with Mann-Whitney U test and Holm correction
cns.boxplot(
    data=df,
    x="group",
    y="value",
    pairs="all",
    test="Mann-Whitney",
    p_adjust="holm",
)

# Barplot with Mann-Whitney U test and false-discovery-rate correction
cns.barplot(
    data=df,
    x="group",
    y="value",
    pairs=[("A", "B"), ("A", "C")],
    test="Mann-Whitney",
    p_adjust="fdr_bh",
)

# Stackplot with an explicit chi-squared test and Bonferroni correction
cns.stackplot(
    data=df,
    x="group",
    stack="category",
    pairs="all",
    test="chi-squared",
    p_adjust="bonferroni",
)
```

### Export for Publication

```python
# SVG for vector graphics (recommended)
cns.savefig("figure.svg")

# High-resolution PNG
cns.savefig("figure.png", dpi=300, transparent=False)

# PDF with editable text
cns.savefig("figure.pdf")

# Keep the full figure canvas instead of cropping to its contents
cns.savefig("figure-full.pdf", bbox_inches=None)
```

`savefig` uses the current figure unless `fig=` is supplied. Omitted export
options use `cns.settings`; per-call `dpi`, `transparent`, `bbox_inches`, and
`pad_inches` overrides leave those settings unchanged. Use
`bbox_inches="tight", pad_inches=0.1` for a tight crop with padding in inches.

For Illustrator-optimized SVG post-processing, install MuPDF's `mutool`.
Without it, `cns.savefig("figure.svg")` falls back to a standard matplotlib SVG
and emits a warning instead of failing.

## Requirements

- Python ≥ 3.10
- Core: matplotlib, numpy, pandas, seaborn
- Included integrations: lifelines, gseapy, scanpy, and other plotting backends
- Optional external tool: MuPDF's `mutool` for enhanced SVG post-processing

See [pyproject.toml](pyproject.toml) for complete dependency list.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

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

This project is licensed under the BSD 3-Clause License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

Built with:

- [matplotlib](https://matplotlib.org/) - Core plotting library
- [seaborn](https://seaborn.pydata.org/) - Statistical visualizations
- [lifelines](https://lifelines.readthedocs.io/) - Survival analysis
- [PyComplexHeatmap](https://github.com/DingWB/PyComplexHeatmap) - Complex heatmaps
- [UpSetPlot](https://upsetplot.readthedocs.io/) - Set intersections

Inspired by the visualization standards of Cell, Nature, and Science journals.

## Support

- 📖 [Documentation](https://cnsplots.farid.one/)
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

[⭐ Star us on GitHub](https://github.com/faridrashidi/cnsplots) · [📖 Documentation](https://cnsplots.farid.one/)

</div>
