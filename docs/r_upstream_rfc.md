> **Status:** historical RFC draft. The working implementation and direct public API in `r/README.md` supersede code examples below.

# RFC: Add a native R package under r/

Status: Draft for upstream discussion
This document proposes architecture only. It does not represent an implemented
R package or an upstream-approved roadmap.

## Summary

I would like to propose a native R implementation of cnsplots as a
self-contained package under `r/` in this repository.

The proposal does not replace or modify the existing Python package. I would
wait for agreement on repository structure, attribution, maintenance
responsibility, and the first pull-request scope before beginning the
implementation.

## Motivation

cnsplots currently provides a broad Python plotting system. Its R support is
limited to `setup_ggplot()`, which returns a short string containing a basic
ggplot2 `theme()` definition; it is not a native R package.

The proposed R work focuses first on two ggplot2 problems:

- publication figures often repeat many `theme()` settings;
- one universal preset cannot cover every figure type.

Stable typography should be shared, while axes, legends, facets, grids, and
spacing remain adaptable to the Figure context.

The proposed composition model is:

1. validated design tokens;
2. a complete base theme;
3. one semantic Figure profile;
4. optional additive theme components;
5. a final native `theme()` override controlled by the user.

Package loading would not call `theme_set()`, modify options, load fonts, or
change devices.

## Proposed repository layout

```text
cnsplots/
├── src/cnsplots/       # existing Python package
├── tests/              # existing Python tests
└── r/                  # self-contained R package
    ├── DESCRIPTION
    ├── NAMESPACE
    ├── LICENSE
    ├── R/
    ├── man/
    ├── tests/testthat/
    ├── vignettes/
    ├── README.md
    └── NEWS.md
```

The repository root would remain the Python package root. The R package would
not read `../src`, `../LICENSE.md`, or other parent-directory files at build
time. It would be independently buildable with:

```sh
R CMD build r
R CMD check --as-cran cnsplots_*.tar.gz
```

This keeps the Python and R implementations reviewable together while allowing
the R package to be extracted later if their maintainers or release cycles
diverge.

## Initial architecture proof

The first draft pull request would be deliberately small and installable:

- R package metadata and a self-contained licence file;
- `settings()` as the single source of typography and other design values;
- `setup_ggplot()`;
- `standard` and `embedding` profiles;
- one additive legend component;
- one representative discrete palette;
- discrete colour and fill scales;
- semantic tests and a minimal README;
- an isolated R CMD check workflow only if approved.

Two profiles are included so that profile dispatch is exercised. One component
is included so that additive override behavior is tested.

This pull request would prove the theme architecture only. It would not be
presented as a complete R release or full Python parity.

## Proposed API direction

```r
tokens <- settings(
  base_family = "Arial",
  base_size = 8
)

p +
  setup_ggplot(profile = "embedding", tokens = tokens) +
  theme_legend(position = "bottom") +
  theme(plot.margin = margin(2, 2, 2, 2, unit = "mm"))
```

The default family would be the portable `"sans"`; projects could explicitly
lock Arial, Helvetica, or another installed family. A user-supplied final
`theme()` would always have the highest precedence.

Later foundation pull requests would add:

- `distribution` and `matrix` profiles;
- axis, legend, facet, grid, and spacing components;
- the attributed palette registry and continuous/discrete ggplot2 scales;
- physical Figure specifications;
- `savefig()` with explicit vector/raster device behavior.

Cell, Nature, and Science names from the Python package would be described as
journal-inspired palettes, not as verified official journal themes.

## Non-goals for the first pull request

- porting all 31 Python plotting functions;
- statistical-analysis wrappers;
- survival, competing-risk, GSEA, heatmap, or single-cell integrations;
- emulating matplotlib Figure/Axes objects;
- pixel-identical output between matplotlib and ggplot2;
- changes to the Python API or Python package version;
- changes to the current PyPI release workflow;
- automatic CRAN submission;
- pkgdown deployment over the existing Python documentation site.

Plot recipes and domain integrations would be proposed later in small,
figure-family pull requests. Plotting, statistical computation, annotation,
theme, and export behavior would remain separate.

## License and attribution

The R package would retain the repository's BSD-3-Clause license.

Proposed R package metadata:

```text
License: BSD_3_clause + file LICENSE
```

The existing root `LICENSE.md` and its copyright notice would remain unchanged.
The R source package would contain its own CRAN-compatible `r/LICENSE` and would
not link to a parent file.

I propose crediting Farid Rashidi for the original cnsplots design and Python
implementation, and crediting the R implementation contributor separately.
Final `Authors@R` roles and the R package maintainer would only be set after
agreement.

Ported palettes, defaults, algorithms, and documentation would record the
Python reference version and commit. Any third-party origins would be reviewed
for their own attribution and licensing requirements.

## Versioning and releases

I propose independent R versioning:

- initial development: `0.0.0.9000`;
- first R release: `0.1.0`;
- first R tag: `r-v0.1.0`;
- post-release development: `0.1.0.9000`.

The existing Python version would remain `0.5.0`, and existing `v*` tags would
remain reserved for Python releases. The first R release would document Python
0.5.0 at commit
`e678e2d5e975c4595b1d7c8bc4d07b4030a29d14` as its design reference without
claiming complete feature parity.

As of 2026-07-28, I did not find a CRAN package named `cnsplots`. This is only a
point-in-time check and would be repeated before any submission.

## CI and build boundaries

If approved, I propose a separate path-filtered R CMD check workflow for
changes under `r/**`.

The R work would not change the meaning of the existing Python Makefile targets
or modify the current Python test, documentation, package, or PyPI release
workflows. Every R pull request would still run the repository's existing
Python validation in addition to R CMD check.

The first stage would use `r/README.md`, generated function documentation, and
later vignettes. It would not deploy pkgdown to the existing `gh-pages` site.

## Proposed follow-up sequence

1. theme-system architecture proof;
2. complete theme tokens, profiles, components, and unit conversion;
3. palette port with provenance and tests;
4. publication dimensions and `savefig()`;
5. selected plotting recipes submitted by Figure family;
6. optional specialised adapters only after the core contract is stable.

Each implementation pull request would be independently installable,
documented, tested, and reviewable.

## Decisions requested

Before implementation, could you please confirm:

1. Are you open to a native R package under `r/` in this repository?
2. Should the R package use the name `cnsplots`?
3. Do you agree with independent R versions and `r-v*` tags?
4. How should the original author and R contributor be represented in
   `Authors@R`?
5. Who should be the R package maintainer (`cre`)?
6. Is eventual CRAN submission desired, or should releases remain GitHub-only?
7. May the foundation pull request add an isolated R CMD check workflow?
8. Is the proposed architecture-proof scope appropriate?
9. Which palettes or visual defaults, if any, must be present in the first
   complete R release?
