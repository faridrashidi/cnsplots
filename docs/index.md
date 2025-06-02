# Documentation

**cnsplots** is a Python visualization library designed to create publication-ready
plots for scientific journals, including high-impact publications like Cell, Nature,
and Science. Built on top of matplotlib and fully compatible with seaborn, cnsplots
enhances the aesthetic quality of your scientific visualizations while maintaining
simplicity and clarity. The library ensures PDF font compatibility with
Adobe Illustrator for seamless integration into publication workflows.
With an intuitive API, cnsplots makes it easy to generate professional-quality
figures with just a few lines of code, helping researchers present their data with the
visual excellence expected in top-tier scientific publications. To use:

```python
import cnsplots as cns
import seaborn as sns
import matplotlib.pyplot as plt

df = sns.load_dataset("tips")  # The data in pandas format
cns.figure(150, 100)  # Create figure size (height x weight) in pixels
cns.boxplot(data=df, x="day", y="total_bill")  # Generate the boxplot from data
plt.savefig("figure.svg")  # Save the figure
```

::::{grid} 2
:gutter: 2

:::{grid-item-card} Installation {octicon}`plug;1em;`
:link: installation
:link-type: doc

New to _cnsplots_? Check out the installation guide.
:::

:::{grid-item-card} API reference {octicon}`book;1em;`
:link: api
:link-type: doc

The API reference contains a detailed description of
the cnsplots API.
:::

:::{grid-item-card} Examples {octicon}`star;1em;`
:link: auto_examples/index
:link-type: doc

The gallery of examples provides detailed examples for what you can do with cnsplots.
:::

:::{grid-item-card} GitHub {octicon}`mark-github;1em;`
:link: https://github.com/faridrashidi/cnsplots

Find a bug? Interested in improving cnsplots? Checkout our GitHub
for the latest developments.
:::
::::

```{toctree}
:hidden: true
:maxdepth: 2
:titlesonly: true

installation
api
auto_examples/index
```
