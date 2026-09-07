# API

Import cnsplots as:

```python
import cnsplots as cns
```

## Plotting Functions

Every plotting function accepts a keyword-only `ax` argument for composition
inside an existing Matplotlib layout. Most return the target
`matplotlib.axes.Axes`; `heatmapplot`, `dotplot`, `upsetplot`, and `vennplot`
instead preserve their backend-native results: `ClusterMapPlotterNew`,
`DotClustermapPlotterNew`, a dictionary of panel axes, and a matplotlib-venn
diagram object, respectively.

### Distribution & Comparison Plots

```{eval-rst}
.. currentmodule:: cnsplots
.. apirootsummary::
   :toctree: api
   :nosignatures:

   boxplot
   violinplot
   stripplot
   barplot
   lollipopplot
   dumbbellplot
   histplot
   distplot
   kdeplot
   ridgeplot
```

### Scatter & Regression Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   scatterplot
   regplot
   lineplot
   slopeplot
```

### Heatmaps & Matrix Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   heatmapplot
   dotplot
   confusionplot
```

### Categorical & Proportion Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   stackplot
   pieplot
   donutplot
   vennplot
   upsetplot
   sankeyplot
```

### Survival Analysis Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   survivalplot
   cumulativeincidenceplot
```

### Genomics & Statistical Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   volcanoplot
   gseaplot
   rocplot
   qqplot
   forestplot
```

### Specialized Plots

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   phyloplot
   placeholderplot
```

## Statistical Models

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   CoxModel
   LogisticModel
   prerank
```

## Figure & Layout Utilities

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   figure
   savefig
   multipanel
   add_panel_label
   take_legend_out
```

## Example Datasets

The gallery datasets are bundled with cnsplots, so loading them does not
require network access.

Discover the packaged tabular datasets without loading them:

```python
import cnsplots as cns

cns.datasets.get_dataset_names()
# ['flights', 'fmri', 'iris', 'penguins', 'tips']
tips = cns.datasets.load_dataset("tips")
```

Showcase results support named access as well as the existing positional
indexing and unpacking. The default `ShowcaseData` has 13 fields;
`include_showcase_images=True` returns `ShowcaseDataWithImages` with the same
fields followed by `showcase_images` as the 14th field. Both modes generate
all showcase datasets, so named access selects from the complete result:

```python
survival_df = cns.datasets.get_showcase_data().survival_df
showcase = cns.datasets.get_showcase_data(include_showcase_images=True)
images = showcase.showcase_images
```

```{eval-rst}
.. currentmodule:: cnsplots.datasets
.. apirootsummary::
   :toctree: api
   :nosignatures:

   load_dataset
   get_dataset_names
   get_showcase_data
   ShowcaseData
   ShowcaseDataWithImages
```

## Configuration & Setup

```{eval-rst}
.. currentmodule:: cnsplots
.. apirootsummary::
   :toctree: api
   :nosignatures:

   setup_matplotlib
   setup_scanpy
   setup_ax
   setup_ggplot
```

## Settings

`cnsplots` exposes its package-wide defaults through `cns.settings`.
Use it to inspect current defaults, set global styling and helper behavior,
restore package defaults with `cns.settings.reset()`, or apply temporary
overrides with `cns.settings.context(...)`.

```python
print(cns.settings)
cns.settings.title_fontsize = 10

with cns.settings.context(palette_qual="Dark2", figure_width=200):
    ...

cns.settings.reset()
```

See the {doc}`settings reference <settings>` for the full catalog of settings
and the runnable {doc}`settings example <examples/settings>` for end-to-end
usage.

```{toctree}
:hidden: true

settings
```

## Color Palettes

Discover built-in and registered cnsplots palettes, optionally filtering by
`"qualitative"` or `"continuous"`. Names available only in Matplotlib or Seaborn
are outside this registry.

```python
cns.available_palettes()
cns.available_palettes(kind="qualitative")
cns.available_palettes(kind="continuous")
```

Register a nonempty sequence of Matplotlib-compatible colors to reuse a
qualitative palette by name. Registration copies the colors and lasts for the
current Python process. Existing cnsplots and Matplotlib palette names cannot
be overwritten.

```python
cns.register_palette("MyLab", ["#4477AA", "#EE6677", "#228833"])
colors = cns.palettes("MyLab")
cns.figure(color_cycle="MyLab")
```

Use `get_palette_colors()` to select colors by zero-based index from a named
palette or an explicit color sequence. It returns hex strings and defaults to
`"Set1"` when `palette` is omitted or `None`. The original
`get_hexcolors_from_apalette()` name remains supported, including its `alist`
keyword.

```python
cns.get_palette_colors([0, 2])
cns.get_palette_colors(indices=[2, 0], palette="MyLab")
cns.get_palette_colors([1], palette=["red", "blue"])
cns.get_hexcolors_from_apalette(alist=[0, 2], palette="Set1")
```

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   palettes
   available_palettes
   register_palette
   get_palette_colors
   get_hexcolors_from_apalette
```

## Constants

The following color constants are available:

- `RED` - #D6372E
- `BLUE` - #5189BB
- `GREEN` - #70B460
- `PURPLE` - #985EA8
- `ORANGE` - #F08F35
- `YELLOW` - #FADD4B
- `BROWN` - #9C5732
- `PINK` - #E787E5
- `GRAY` - #A3A3A3
- `VIOLET` - #442288
- `CHOCOLATE` - #662506
