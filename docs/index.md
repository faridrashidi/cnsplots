# cnsplots

**Publication-ready scientific visualizations for Cell, Nature, and Science journals.**

cnsplots is a Python visualization library built on matplotlib and fully compatible with seaborn. It creates figures that meet the high standards of top-tier scientific publications while keeping the API simple and intuitive.

```{image} _static/images/overview.png
:alt: Overview of cnsplots visualizations
:align: center
:target: https://cnsplots.farid.one/examples/showcase.html#figure-1
```

## Key Features

- **Publication-ready defaults** — Figures styled for Cell, Nature, and Science journals
- **Adobe Illustrator compatible** — PDF fonts work seamlessly in publication workflows
- **Familiar API** — Built on matplotlib/seaborn, easy to learn if you know these libraries
- **Precise sizing** — Dimensions in pixels for exact control

## Quick Example

```python
import cnsplots as cns
import seaborn as sns

df = sns.load_dataset("tips")
cns.figure(150, 100)  # Height x Width in pixels; starting canvas when autofit is on
cns.boxplot(data=df, x="day", y="total_bill")
cns.savefig("figure.svg")
```

::::{grid} 2
:gutter: 2

:::{grid-item-card} Getting Started {octicon}`rocket;1em;`
:link: getting_started
:link-type: doc

New to cnsplots? Start here for a quick tutorial.
:::

:::{grid-item-card} Installation {octicon}`plug;1em;`
:link: installation
:link-type: doc

Installation guide and setup instructions.
:::

:::{grid-item-card} Examples {octicon}`star;1em;`
:link: examples/index
:link-type: doc

Gallery of examples showing what you can do with cnsplots.
:::

:::{grid-item-card} API Reference {octicon}`book;1em;`
:link: api
:link-type: doc

Detailed description of all cnsplots functions and parameters.
:::

:::{grid-item-card} Release Notes {octicon}`tag;1em;`
:link: release_notes
:link-type: doc

Published release history and changelog highlights.
:::
::::

```{toctree}
:hidden: true
:maxdepth: 1
:titlesonly: true

getting_started
installation
api
release_notes
examples/index
```
