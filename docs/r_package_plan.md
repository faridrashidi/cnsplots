> **Status:** historical architecture draft. The implemented direct API in `r/README.md` is authoritative; token-object examples below are not current user API.

# Native R Package Plan

Status: Internal architecture approved; upstream RFC pending
Target location: `r/`
Proposed package name: `cnsplots` (upstream confirmation pending)
Initial development version: `0.0.0.9000`
First release version: `0.1.0`
Python reference: `0.5.0` at commit `e678e2d5e975c4595b1d7c8bc4d07b4030a29d14`

## 1. Context

The existing project is a Python package built around matplotlib, seaborn, and
specialized scientific plotting backends. Its R support is currently limited to
`setup_ggplot()`, which returns a short string containing a basic ggplot2
`theme()` definition. It does not provide a native R package, R plotting APIs,
palette scales, figure profiles, export helpers, tests, or R documentation.

The native R implementation should solve two concrete ggplot2 problems:

1. publication styling often requires many repeated `theme()` statements; and
2. one fixed theme cannot meet the needs of distribution plots, embeddings,
   matrix plots, survival plots, and multi-panel figures at the same time.

This work is therefore an R-native design derived from the intent of cnsplots,
not a line-by-line translation of its Python implementation.

## 2. Repository decision

The R package will live in a self-contained `r/` subdirectory of the existing
repository.

```text
cnsplots/
├── src/cnsplots/          # existing Python package
├── tests/                 # existing Python tests
├── docs/                  # shared project documentation
├── examples/              # existing Python examples
└── r/                     # native R package root
    ├── DESCRIPTION
    ├── NAMESPACE
    ├── R/
    ├── man/
    ├── tests/testthat/
    ├── vignettes/
```

This boundary keeps the Python package unchanged, makes the R package
installable from a GitHub subdirectory, and allows it to be split into a
separate repository later without redesigning its internals.

The repository root will not become a simultaneous Python and R package root.

## 3. Product scope

### 3.1 Full phase-one goals

The first usable R release, `0.1.0`, will provide:

- validated design tokens for typography, lines, spacing, and panel labels;
- a publication-oriented base ggplot2 theme;
- composable theme components for axes, legends, facets, grids, and panels;
- figure-context profiles rather than journal-name-only themes;
- qualitative, sequential, and diverging palettes corresponding to the Python
  package;
- discrete and continuous `scale_colour_*()` and `scale_fill_*()` helpers;
- physical figure specifications expressed in `mm`, `in`, or `pt`;
- PDF, SVG, PNG, and TIFF export helpers with explicit device behavior;
- examples showing how the system reduces repeated `theme()` code;
- unit tests, visual regression tests where appropriate, and complete function
  documentation.

### 3.2 Phase-one non-goals

The first release will not:

- reproduce all 31 Python plot functions;
- reimplement Cox, logistic regression, GSEA, or competing-risk analysis;
- emulate the mutable matplotlib `Axes` API;
- emulate Scanpy or accept AnnData as the primary R interface;
- promise pixel-identical output across matplotlib and ggplot2;
- claim formal Cell, Nature, or Science compliance without a separately
  verified journal specification.

Plot recipes and domain integrations will be added in later, independently
reviewable phases.

## 4. Design principles

### 4.1 Use R-native composition

Public functions should return standard ggplot2-compatible objects that can be
added with `+`. Package loading must not change the user's global theme,
options, devices, or fonts.

Users may explicitly call `ggplot2::theme_set(setup_ggplot())` when they want a
session-wide default, but cnsplots will not do this automatically.

### 4.2 Separate four concerns

The implementation must keep these concerns separate:

1. statistical computation;
2. plot geometry and data transformations;
3. non-data appearance controlled by ggplot2 themes; and
4. export and physical figure specifications.

A plot type must not silently choose a statistical test merely because a
particular geometry is used.

### 4.3 Make composition precedence deterministic

Appearance should resolve in this order:

1. package design-token defaults;
2. the selected figure profile;
3. optional component modifiers; and
4. the user's final explicit ggplot2 `theme()` call.

The final user override must always win.

The following is a hard architecture contract:

> `settings()` is the single source of design values. `setup_ggplot()` returns a
> complete theme composed from the base theme and one semantic profile. Public
> theme components are incomplete patches applied afterward, and a user-supplied
> final `theme()` always has the highest precedence. No constructor mutates
> ggplot2's global theme or package options.

### 4.4 Prefer physical publication units

Journal widths and exported sizes will be represented in millimetres, inches,
or points. Raster pixel dimensions will be derived from physical dimensions and
DPI. The package will not describe a value as a final pixel size when it is
actually a 72-DPI layout unit.

### 4.5 Keep the core dependency surface small

The theme and palette core should remain usable with ggplot2 and base/recommended
R packages. Specialized plotting, layout, font, and device integrations should
be optional where practical.

## 5. Proposed architecture

### 5.1 Design tokens

`R/tokens.R` will own stable primitive values such as:

- base font family and fallback policy;
- title, axis-title, axis-text, legend, strip, annotation, and tag sizes;
- font faces;
- axis, tick, grid, and border line widths;
- tick lengths;
- plot, legend, strip, and panel spacing;
- foreground, background, and muted colours.

Tokens should be represented by a validated object rather than an unstructured
list of package options. A constructor such as `settings()` will allow a user
to derive a modified token set without mutating package state. A companion
`settings_update()` may provide validated derivation without exposing object
internals.

Physical units require an explicit conversion layer. Font sizes remain in
points, line widths are converted deliberately to the units expected by the
supported ggplot2 version, and tick lengths and margins use `grid::unit()`.
Python numeric line-width values must not be copied into ggplot2 unchanged and
assumed to have the same physical meaning.

### 5.2 Base theme

`R/theme-base.R` will implement the shared publication baseline:

- predictable typography hierarchy;
- explicit plot and panel backgrounds;
- explicit axis lines and ticks;
- explicit legend keys and spacing;
- no implicit grid unless a profile requests it;
- stable margins suitable for subsequent composition.

The primary entry point is:

```r
setup_ggplot(
  profile = "standard",
  tokens = settings()
)
```

Typography and other design values are configured only through `settings()`
so that the theme does not have two competing configuration sources. The
portable defaults are `base_family = "sans"`, `base_size = 8` pt, secondary text
at 7 pt, black foreground, and white plot and panel backgrounds. A project may
explicitly lock Arial, Helvetica, or another installed family.

### 5.3 Theme components

`R/theme-components.R` will provide small additive modifiers for recurring
decisions, for example:

```r
theme_axes(...)
theme_legend(...)
theme_facet(...)
theme_grid(...)
theme_spacing(...)
```

These functions must change only the elements they own so that they compose
without resetting unrelated theme elements. `theme_spacing()` owns plot
margins and panel, legend, and strip spacing. Facet components do not control
facet construction, and axis components do not control scales, limits, or
coordinates.

### 5.4 Figure-context profiles

`R/theme-profiles.R` will provide named starting points based on figure
semantics, not a claim that one journal has one universal theme.

The profile registry is deliberately small and semantic:

| Delivery | Profile | Intended behavior |
|---|---|---|
| PR 1 | `standard` | Complete left/bottom axes, no grid, regular legend |
| PR 1 | `embedding` | Minimal or absent axes for UMAP/t-SNE/spatial embeddings |
| Phase one | `distribution` | Full category/value axes with distribution-safe spacing |
| Phase one | `matrix` | Matrix-oriented ticks, strips, and legend spacing |

`compact` and `multipanel` are orthogonal layout or spacing concerns rather than
mutually exclusive figure semantics; they belong to components or a later
composition layer. `polar` and `survival` will be evaluated with their plot
recipes because their reliable contracts involve coordinates or auxiliary
layouts. Profiles remain thin combinations of tokens and theme elements.
Geometries, coordinates, statistics, and data transformations never belong to a
theme profile.

### 5.5 Palettes and scales

`R/palettes.R`, `R/scales-colour.R`, and `R/scales-fill.R` will separate raw
palette access from ggplot2 scales.

Proposed APIs are:

```r
palette_names(kind = "all")
palettes(color, n = NULL, direction = 1)

scale_colour_palette(palette = "Ecotyper1", ...)
scale_fill_palette(palette = "Ecotyper1", ...)
scale_colour_map(palette = "BuRd_custom", ...)
scale_fill_map(palette = "BuRd_custom", ...)
```

American spelling aliases may be provided only when they do not increase the
maintenance burden significantly.

Palette names such as `Cell`, `Nature`, and `Science` will be described as
journal-inspired palettes, not complete journal themes.

Discrete palettes must define behavior when `n` exceeds the available number
of colours. The default should fail clearly rather than silently recycle or
interpolate qualitative colours. Palette metadata will record type, canonical
name, source, and the Python reference version.

### 5.6 Figure specifications and export

`R/figure-spec.R` will represent width, height, units, DPI, background, and
optional rasterization policy in a small validated figure-specification object.

`R/export.R` will provide an explicit export helper such as:

```r
savefig(
  filename,
  plot,
  spec = figure(width = 89, height = 70, units = "mm"),
  device = NULL,
  ...
)
```

Expected device policy:

- PDF: editable vector output with a Cairo-compatible path when available;
- SVG: editable text through `svglite` when available;
- PNG: high-quality raster output through `ragg` when available;
- TIFF: explicit compression and publication DPI;
- dense point layers: layer-level rasterization is documented separately and
  the entire figure is not flattened by default.

Fallbacks and optional-package requirements must be explicit. The export helper
must not silently select a device that changes text into paths. The file
extension and an explicitly supplied device must agree. DPI affects raster
output only; vector output ignores it. The default export background is white,
with transparency available only by explicit request.

The first release will not ship universal `single-column` or `double-column`
presets. Such dimensions vary by journal and article format. Users can pass
verified physical dimensions directly; named journal specifications may be
added only after checking primary journal guidance.

## 6. Proposed package tree

The following is the full phase-one target, not a request to create empty files
during the first implementation PR:

```text
r/
├── DESCRIPTION
├── NAMESPACE
├── LICENSE
├── README.Rmd
├── README.md
├── NEWS.md
├── .Rbuildignore
├── R/
│   ├── cnsplots-package.R
│   ├── tokens.R
│   ├── validation.R
│   ├── palettes.R
│   ├── scales.R
│   ├── theme-base.R
│   ├── theme-components.R
│   ├── theme-profiles.R
│   ├── figure-spec.R
│   ├── export.R
│   └── units.R
├── tests/
│   ├── testthat.R
│   └── testthat/
│       ├── test-tokens.R
│       ├── test-palettes.R
│       ├── test-scales.R
│       ├── test-themes.R
│       ├── test-export.R
│       └── fixtures/
│           └── python-v0.5.0-palettes.csv
├── vignettes/
│   ├── getting-started.Rmd
│   ├── theme-system.Rmd
│   ├── publication-workflow.Rmd
│   └── python-to-r.Rmd
└── man/
```

PR 1 creates only files with real content. `_pkgdown.yml`, runtime `inst/`
data, visual snapshots, and other infrastructure are deferred until there is a
demonstrated need. Generated documentation in `man/` will be produced from
roxygen2 comments and committed before a release. Examples initially use base R
data or deterministic test fixtures; they do not imply parity with the Python
`datasets` API.

## 7. Dependency policy

The planned minimums are `R (>= 4.1.0)` and `ggplot2 (>= 3.4.0)`. The
ggplot2 floor is motivated by the `linewidth` API and remains provisional until
it is exercised in CI.

### Runtime core

- `ggplot2 (>= 3.4.0)`;
- `grid` and `grDevices` when directly used;
- `scales (>= 1.2.0)` only if source code calls its public API directly.

### Optional development or integration dependencies

- `testthat (>= 3.1.0)` for behavior tests;
- `vdiffr` for selected visual regression tests;
- `svglite` for SVG output;
- `ragg` for raster output;
- `knitr` and `rmarkdown` when vignettes are added;
- `patchwork` only after a concrete composition API or compatibility test exists.

`cowplot`, `systemfonts`, and `showtext` are not preselected. Optional
dependencies are added only with a concrete use, and development tools such as
`roxygen2`, `rcmdcheck`, `pkgdown`, `lintr`, and `styler` do not become runtime
imports.

No dependency will be added until its concrete API use and maintenance cost are
agreed. Specialized analysis packages will remain in `Suggests` or in later
extension packages where possible.

The first release will not add an `renv.lock`. A reusable library should test a
supported R/ggplot2 range rather than lock users to one developer environment.

## 8. Testing and quality strategy

### 8.1 Behavior tests

Tests will verify:

- token validation and inheritance;
- exact default theme element values;
- component isolation and composition precedence;
- exact palette colour values and interpolation behavior;
- scale behavior for discrete and continuous data;
- figure-spec unit conversion;
- export extension dispatch, dimensions, and error messages;
- absence of package-load global side effects.

### 8.2 Visual tests

Visual snapshots will cover a small, representative matrix rather than every
parameter combination:

- distribution plot;
- grouped scatter plot;
- faceted plot;
- embedding-style plot;
- matrix-style plot;
- multi-panel tagged figure.

Snapshots do not replace structural tests. Font-dependent snapshots must use a
controlled CI font or a generic `sans` family and tolerate platform differences
explicitly.

### 8.3 Cross-language parity tests

Palette hex values and stable design tokens can be compared directly with the
Python package. Plot output should be reviewed against shared visual criteria,
not pixel equality between two graphics engines.

### 8.4 Validation gates

Before an R-package pull request is considered ready:

- `R CMD build` succeeds;
- `R CMD check` completes with no errors or warnings;
- package tests pass in a clean R library;
- representative vignettes render;
- existing Python `make test` and `make lint` still pass;
- any CI or root build-file change has been approved separately.

## 9. Documentation strategy

The R documentation must explain both how to use the API and why the layers are
separate.

Required examples will show:

1. the repeated raw ggplot2 `theme()` code being replaced;
2. a base theme plus one component override;
3. two figure types using different profiles but the same typography tokens;
4. a final user `theme()` override winning over package defaults;
5. discrete and continuous palette scales;
6. physical-size export at two explicitly supplied widths without claiming a
   universal single- or double-column standard;
7. known limits, optional devices, and font reproducibility.

The Python and R APIs do not need identical syntax. Documentation will include a
feature-correspondence table so users can understand conceptual parity.

## 10. Versioning and release strategy

The R package will initially version independently from the Python package:

- Python package: existing `0.5.x` series;
- initial R development: `0.0.0.9000`;
- first R release: `0.1.0`;
- post-release development: `0.1.0.9000`;
- proposed R tags: `r-v0.1.0`, which do not match the existing Python `v*`
  release trigger.

The package name `cnsplots` was not present in the CRAN package index when
checked on 2026-07-28. Name ownership, maintainer metadata, and submission plans
still require agreement with the upstream author before a public release.

### 10.1 Build, CI, and documentation boundaries

The R package must build from `r/` without reading `../src`, the root
`../LICENSE.md`, or other parent-directory runtime files. A CRAN source tarball
must be self-contained. `r/DESCRIPTION` will use
`License: BSD_3_clause + file LICENSE`, and `r/LICENSE` will carry the
CRAN-compatible year and copyright-holder notice.

If approved by the upstream maintainer, R validation will use a separate
path-filtered workflow for `r/**`. Existing Python test, documentation, package,
and PyPI release workflows will retain their current meanings. Cross-platform
semantic tests may run on Linux, Windows, and macOS; device- or font-sensitive
visual snapshots should be gated only on one controlled Linux environment.

Existing root Makefile targets such as `test`, `lint`, `doc`, and `release` will
not be redefined. Namespaced targets such as `r-check` or `r-document` may be
added only after separate approval. R-only changes must still run the existing
repository checks required by the project.

The first R pull requests will not deploy pkgdown or change the current
`gh-pages` publication. Generated R release archives, check directories, and
site output will not be committed.

## 11. License and attribution

The parent repository uses the BSD 3-Clause license. The R package will retain
the license terms and copyright notice. `DESCRIPTION` will use explicit
`Authors@R` roles after the upstream author and R-package maintainer details are
confirmed.

Directly adapted palette values, algorithms, or documentation will retain clear
source attribution. The package must not imply endorsement by a journal or by
the upstream author beyond the permissions actually granted.

Palette provenance must be checked beyond the immediate Python source when a
palette was originally taken from a third-party project. Font files will not be
bundled without a separately verified redistribution licence.

## 12. Milestones

### Milestone 0: planning and upstream agreement

- approve the internal architecture and full phase-one boundary;
- publish the upstream RFC/issue before implementation;
- ask the upstream author to confirm package name, attribution, maintainer,
  release intent, and whether isolated R CI is acceptable;
- select a reproducible R development environment before installing packages.

### Milestone 1: theme-system architecture proof

- create a minimal self-contained `r/` package skeleton;
- add metadata, self-contained license, namespace generation, and a test harness;
- implement `settings()` and `setup_ggplot()`;
- implement `standard` and `embedding` profiles to prove profile dispatch;
- implement `theme_legend()` to prove additive override behavior;
- implement one representative discrete palette and colour/fill scales;
- add a short README and semantic tests;
- verify install, draw, build, and check behavior before expanding the API.

This milestone is an architecture proof, not completion of the full phase-one
release.

### Milestone 2: theme kernel

- implement and validate design tokens;
- implement the base theme;
- implement component modifiers;
- implement the initial context profiles;
- prove override precedence with tests.

### Milestone 3: palettes and scales

- port and attribute palette definitions;
- add discrete and continuous colour/fill scales;
- test exact colours, interpolation, direction, and invalid inputs;
- document accessibility status without overclaiming.

### Milestone 4: figure specifications and export

- implement physical unit specifications;
- implement device dispatch and explicit fallbacks;
- test dimensions and representative file output;
- document fonts, rasterization, and Illustrator workflows.

### Milestone 5: full phase-one documentation and release readiness

- complete README and vignettes;
- generate reference documentation;
- run R and existing Python validation;
- reconcile the accumulated feature and parity matrices;
- prepare `0.1.0` only after all full phase-one acceptance criteria pass;
- keep later plot recipes out of the foundation release.

### Milestone 6: plot recipes and domain integrations

- prioritize recipes using the feature matrix;
- implement each recipe as a small, separately reviewed change;
- keep statistics optional and explicit;
- add specialized ecosystem integrations only after the core API is stable.

## 13. Upstream delivery sequence

The upstream repository requests prior discussion for major changes. The
recommended delivery sequence is therefore:

1. **RFC/issue:** agree on `r/`, package naming, maintenance responsibility,
   attribution, independent versioning, first-phase scope, and whether R CI is
   acceptable.
2. **PR 1, theme-system architecture proof:** self-contained package metadata,
   `settings()`, `setup_ggplot()` with `standard` and `embedding` profiles,
   `theme_legend()`, one representative discrete palette and colour/fill
   scales, a test harness, and a short README. This proves installation,
   composition, and reviewability before a larger port.
3. **PR 2, theme architecture:** tokens, unit conversion, profiles, components,
   and semantic/visual tests.
4. **PR 3, palettes and scales:** the attributed full registry and parity
   fixtures.
5. **PR 4, physical specifications and export:** device behavior and verified
   dimensions.
6. **Later PRs:** plot recipes grouped by figure family, followed by optional
   domain integrations.

R documentation will initially remain in `r/README.md`, generated reference
pages, and vignettes. A pkgdown site will not overwrite or share the existing
Python `gh-pages` deployment until the upstream maintainer chooses a deployment
strategy.

## 14. Acceptance criteria

### 14.1 PR 1 architecture-proof criteria

PR 1 is ready for review only when:

1. the package installs, builds, and checks independently from `r/`;
2. `setup_ggplot()` returns a complete theme without global side effects;
3. `standard` and `embedding` demonstrate distinct profile contracts;
4. `theme_legend()` and a final user `theme()` prove last-added-wins behavior;
5. one discrete palette has exact-value tests and working colour/fill scales;
6. the README demonstrates the intended composition model; and
7. existing Python validation remains successful.

Passing these checks proves the architecture slice only. It does not mean that
the full phase-one release is complete.

### 14.2 Full phase-one criteria

The full phase-one R foundation is complete only when:

1. `r/` is independently buildable and installable;
2. loading the package has no plotting or option side effects;
3. tokens, profiles, components, and final user overrides compose predictably;
4. all retained Python palette values have tested R counterparts;
5. at least five representative Figure contexts are documented and tested;
6. physical-size exports are verified rather than inferred from successful
   function return values;
7. the documentation clearly distinguishes a palette, theme, profile, plot
   recipe, and export specification;
8. no unverified journal-compliance claim is made;
9. existing Python validation remains successful; and
10. the complete foundation is delivered through coherent, independently
    reviewable pull requests.

## 15. Decisions still requiring upstream confirmation

The internal plan now proposes `cnsplots`, `R >= 4.1.0`,
`ggplot2 >= 3.4.0`, `sans` at 8 pt, white backgrounds, the profile and component
sets above, and `savefig()`. These values can still change in response to the
architecture proof or upstream review.

The remaining external gates are:

- the upstream author's and R maintainer's `Authors@R` roles;
- who will act as `cre` and respond to CRAN correspondence;
- whether the package is intended for GitHub only or eventual CRAN submission;
- third-party provenance and attribution for every migrated palette;
- whether PR 1 may add an isolated path-filtered R CI workflow;
- whether any later root Makefile targets are acceptable; and
- which composition backend, if any, should be adopted after phase one.
