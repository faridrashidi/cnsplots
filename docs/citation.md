# Citing cnsplots

If you use cnsplots in your research, cite the software version used to produce
your results. The
[CITATION.cff snapshot](https://github.com/faridrashidi/cnsplots/blob/ef82066d5269116b4d51044c75ac52184754e6fc/CITATION.cff)
provides machine-readable metadata for the release documented here.

For version 0.7.0:

> Rashidi, F. (2026). cnsplots: Publication-Ready Scientific Plots
> (Version 0.7.0) [Computer software].
> [GitHub release](https://github.com/faridrashidi/cnsplots/releases/tag/v0.7.0).

```bibtex
@software{cnsplots,
  author = {Rashidi, Farid},
  title = {cnsplots: Publication-Ready Scientific Plots},
  version = {0.7.0},
  date = {2026-08-28},
  year = {2026},
  url = {https://github.com/faridrashidi/cnsplots/releases/tag/v0.7.0}
}
```

For another release, use its version, publication date, and URL from the
[release history](https://github.com/faridrashidi/cnsplots/releases). For an
unreleased checkout, record the full Git commit identifier and its repository
URL so readers can recover the code you ran; do not describe it as the
published release merely because the package version has not changed.

## Software and statistical-method references

The cnsplots citation credits this plotting library. In your methods section,
also describe the actual statistical test or estimator, its options, and any
multiple-testing correction. Cite the primary method papers and backend
packages used by that analysis, following their citation instructions. The
{doc}`statistical_methods` guide links each supported analysis to the relevant
method or dependency documentation, including SciPy, lifelines, and GSEApy.

Dataset attribution is separate as well: when using the bundled examples,
consult the {doc}`datasets` guide for the source and reuse information for each
dataset.

## Metadata sources and maintenance

The author and citation title follow the existing
[release README](https://github.com/faridrashidi/cnsplots/blob/v0.7.0/README.md);
the author is also recorded in
[the documentation configuration](https://github.com/faridrashidi/cnsplots/blob/v0.7.0/docs/conf.py).
The project name, version, repository URL, and license are recorded in
[pyproject.toml](https://github.com/faridrashidi/cnsplots/blob/v0.7.0/pyproject.toml).
The release date, August 28, 2026, is the UTC publication date of the
[v0.7.0 GitHub release](https://github.com/faridrashidi/cnsplots/releases/tag/v0.7.0).
No verified software DOI is recorded in these project sources, so the citation
uses the release URL. No DOI, ORCID, or additional author identity is inferred.

Citation metadata is maintained manually for published releases. Maintainers
update `CITATION.cff` and both displayed examples together, using the published
version and UTC release date; documentation rebuilds do not change that date.
See the
[contributor instructions](https://github.com/faridrashidi/cnsplots/blob/ef82066d5269116b4d51044c75ac52184754e6fc/.github/CONTRIBUTING.md)
for validation and release maintenance. Creating citation metadata does not
publish or deposit the software with any external archive; a deposit requires
separate maintainer authorization.
