# API

Import cnsplots as:

```python
import cnsplots as cns
```

## Plotting Functions

### Distribution & Comparison Plots

```{eval-rst}
.. currentmodule:: cnsplots
.. autosummary::
   :toctree: .
   :nosignatures:

   boxplot
   violinplot
   stripplot
   barplot
   histplot
   distplot
   kdeplot
   ridgeplot
```

### Scatter & Regression Plots

```{eval-rst}
.. autosummary::
   :toctree: .
   :nosignatures:

   scatterplot
   regplot
   lineplot
   slopeplot
```

### Heatmaps & Matrix Plots

```{eval-rst}
.. autosummary::
   :toctree: .
   :nosignatures:

   heatmapplot
   dotplot
   confusionplot
```

### Categorical & Proportion Plots

```{eval-rst}
.. autosummary::
   :toctree: .
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
.. autosummary::
   :toctree: .
   :nosignatures:

   survivalplot
   cumulativeincidenceplot
   forestplot
```

### Genomics & Statistical Plots

```{eval-rst}
.. autosummary::
   :toctree: .
   :nosignatures:

   volcanoplot
   gseaplot
   rocplot
   qqplot
```

### Specialized Plots

```{eval-rst}
.. autosummary::
   :toctree: .
   :nosignatures:

   phyloplot
```

## Statistical Models

```{eval-rst}
.. autosummary::
   :toctree: .
   :nosignatures:

   CoxModel
   LogisticModel
   prerank
```

## Figure & Layout Utilities

```{eval-rst}
.. autosummary::
   :toctree: .
   :nosignatures:

   figure
   savefig
   multipanel
   add_panel_label
   take_legend_out
```

## Configuration & Setup

```{eval-rst}
.. autosummary::
   :toctree: .
   :nosignatures:

   setup_matplotlib
   setup_scanpy
   setup_ax
   setup_ggplot
```

## Color Palettes

```{eval-rst}
.. autosummary::
   :toctree: .
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

Default settings:

- `PALETTE_QUAL` - Default qualitative palette ('Ecotyper1')
- `PALETTE_SEQ` - Default sequential colormap ('gnuplot')
- `FONTSIZE_TITLE` - Title font size (8)
- `FONTSIZE_LEGEND` - Legend font size (7)
- `LINEWIDTH_AXES` - Axes line width (0.5)
