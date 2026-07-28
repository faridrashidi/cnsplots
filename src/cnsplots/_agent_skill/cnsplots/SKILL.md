---
name: cnsplots
description: Create, revise, and troubleshoot publication-ready scientific plots in Python with cnsplots, including distribution, regression, heatmap, genomics, survival, set, flow, and multi-panel figures. Use when a user asks for cnsplots code, Cell/Nature/Science-style visualization, precise pixel-sized figures, statistical plot annotations, or editable SVG/PDF publication output.
---

# CNSPlots

Build plots against the installed `cnsplots` version. Favor a short, runnable
script that preserves the user's data semantics and produces the requested
artifact.

## Workflow

1. Inspect the input data before choosing a plot.
   - Confirm the relevant columns, dtypes, missing values, units, category
     order, and event coding.
   - Ask only when an unresolved choice would change the scientific meaning.
   - Never invent labels, comparisons, thresholds, statistical tests, or units.

2. Choose the narrowest suitable public plot function.
   - Read [references/plot-catalog.md](references/plot-catalog.md) when selecting
     a plot type or composing a multi-panel figure.
   - Prefer `import cnsplots as cns` and the public names on `cns`.
   - Do not call private modules or functions.

3. Verify the installed API instead of guessing a signature.

   ```bash
   python - <<'PY'
   import inspect
   import cnsplots as cns

   print(cns.__version__)
   print(inspect.signature(cns.boxplot))
   print(cns.boxplot.__doc__)
   PY
   ```

   Replace `boxplot` with the selected public function. If `cnsplots` cannot be
   imported, report that clearly and ask before changing the user's environment.

4. Build the figure.
   - In headless execution, set `MPLBACKEND=Agg` or call
     `matplotlib.use("Agg")` before importing plotting backends.
   - Start single-panel figures with `cns.figure(width=..., height=...)`.
     Dimensions are in pixels.
   - Pass `ax=` explicitly when composing with existing Matplotlib axes.
   - Use `cns.multipanel` for labeled publication panels.
   - Add titles and axis labels through the returned Matplotlib axes.
   - Use `cns.settings.context(...)` for temporary style overrides rather than
     leaving global settings changed.

5. Save and validate the result.
   - Use `cns.savefig(...)`. Prefer SVG or PDF for editable publication output
     and PNG for a raster preview.
   - Run the complete script, confirm the output exists and is non-empty, and
     inspect or render it when visual tools are available.
   - Check clipping, unreadable labels, misleading scales, legend collisions,
     color distinguishability, and panel alignment.
   - Return the runnable code, output path, and any scientific assumptions.

## Baseline Pattern

```python
import matplotlib

matplotlib.use("Agg")

import cnsplots as cns

cns.figure(width=180, height=150)
ax = cns.boxplot(data=df, x="group", y="value")
ax.set(xlabel="Group", ylabel="Value")
cns.savefig("figure.svg")
```

Adapt this only after inspecting the selected function's installed signature and
docstring.

## Statistical Integrity

- Treat `pairs`, event codes, reference groups, transformations, and thresholds
  as analysis choices, not decoration.
- State tests and comparison directions reflected by the installed function
  documentation.
- Do not imply causality or significance beyond the supplied data and chosen
  analysis.
- Preserve raw observations when the user requests them; do not silently replace
  distributions with summaries.
