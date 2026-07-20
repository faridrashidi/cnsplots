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
   forestplot
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

```{eval-rst}
.. currentmodule:: cnsplots.datasets
.. apirootsummary::
   :toctree: api
   :nosignatures:

   load_dataset
   get_showcase_data
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

```{eval-rst}
.. apirootsummary::
   :toctree: api
   :nosignatures:

   palettes
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
