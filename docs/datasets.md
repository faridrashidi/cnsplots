# Example data sources

`cns.datasets.load_dataset` reads five bundled CSV snapshots without network
access. `cns.datasets.get_showcase_data` combines two of those datasets with
synthetic examples and, optionally, four bundled images.

The [packaged data notices](https://github.com/faridrashidi/cnsplots/blob/main/NOTICE-DATA.md)
record each file's source, snapshot, attribution, upstream transformations, and
redistribution terms. They are shipped as `NOTICE-DATA.md` in the source archive
and in the wheel's `.dist-info/licenses` directory. The software's BSD license
does not supply a common license for third-party data or images.

## CSV snapshots

All five files match
[seaborn-data revision `71e2436`](https://github.com/mwaskom/seaborn-data/tree/71e2436a092d714350de0fc409ca8a8714e7e78f)
byte for byte. That revision identifies the matching upstream content; it is
not a claim about the original download date. The original sources and their
terms are documented individually in the packaged notices.

| File | Original source | Source terms |
| --- | --- | --- |
| `tips.csv` | Bryant and Smith (1995), via [reshape2](https://github.com/hadley/reshape/blob/03373426695f28edbf2a542fa43353dbdab3c4a6/man/tips.Rd) | reshape2 is MIT licensed; an original data-specific grant has not been verified. |
| `iris.csv` | Fisher's Iris, [UCI record](https://archive.ics.uci.edu/dataset/53/iris), matching the corrected `bezdekIris.data` variant | CC BY 4.0; retain credit, license link, and transformation notice. |
| `flights.csv` | [R AirPassengers](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/AirPassengers.html), citing Box, Jenkins, and Reinsel (1994) | No data-specific redistribution grant was located in the source documentation. |
| `penguins.csv` | [Palmer Penguins](https://allisonhorst.github.io/palmerpenguins/), collected by Kristen Gorman and Palmer Station LTER | CC0; scientific attribution is provided in the notices. |
| `fmri.csv` | [Waskom et al. (2017)](https://github.com/mwaskom/Waskom_CerebCortex_2017), via seaborn's processed example | The original repository's BSD notice refers to code; its scope for the data remains unconfirmed. |

### Loader transformations

Each call reads a fresh DataFrame using `pandas.read_csv`. Numeric measurements
are unchanged; missing entries retain pandas' CSV parsing behavior. The loader
does not drop rows, impute measurements, or fetch newer upstream data.

| Dataset | Changes after reading the CSV |
| --- | --- |
| `tips` | Convert `day`, `sex`, `time`, and `smoker` to categorical dtype with categories, respectively, `Thur/Fri/Sat/Sun`, `Male/Female`, `Lunch/Dinner`, and `Yes/No`. These categories are not marked ordered. |
| `flights` | Abbreviate month names to three characters and convert them to categorical dtype in first-appearance order, January through December. |
| `penguins` | Title-case the `sex` labels, producing `Male` and `Female` while preserving missing values. |
| `iris`, `fmri` | No changes after CSV parsing. |

Individual examples may perform additional grouping, filtering, or reshaping;
those steps are visible in each example's source.

## Synthetic showcase data

Only `iris_df` and `tips_df` come from the CSV snapshots. The other showcase
fields are synthetic demonstrations, not patient records or measured gene
expression. The generation code in
[`gallery.py`](https://github.com/faridrashidi/cnsplots/blob/main/src/cnsplots/datasets/gallery.py)
is part of the BSD-licensed cnsplots software.

Random examples use a local NumPy generator seeded with `42`. Scanpy's
[`datasets.blobs`](https://scanpy.readthedocs.io/en/stable/generated/scanpy.datasets.blobs.html)
uses its own default seed (`0`) to generate Gaussian clusters through
scikit-learn. Repeated calls are deterministic within the same dependency
environment; this does not promise identical output across backend versions.

| Returned field | Generation and transformations |
| --- | --- |
| `survival_df` | Exponential survival times, Bernoulli event indicators, normally distributed ages converted to integers, and sampled stages for two groups. |
| `blobs` | Scanpy Gaussian blobs with artificial `TP53`, `KRAS`, `Ensemble`, `Selected`, and `Cluster` annotations; subtract the matrix-wide mean and transpose the result. The gene-like labels are illustrative. |
| `volcano_df` | Normal log fold changes and constructed, clipped p-value-like numbers transformed with negative base-10 logarithms. The `adjp` column label does not represent a real multiple-testing analysis. |
| `gene_sets` | Random subsets of artificial `Gene` identifiers. |
| `roc_df` | Bernoulli labels and two label-dependent scores with Gaussian noise. |
| `slope_df` | Normal samples with fixed means for combinations of site and health label, plus artificial pairing identifiers. |
| `confusion_df`, `line_df` | Fixed illustrative labels and numbers written directly in the generator. |
| `cumulative_incidence_df` | Exponential times and sampled censoring/event codes for two groups. |
| `forest_df` | Simulated risk, stage, age, and marker values with risk/stage-dependent times and event probabilities. |
| `upset_sets` | Fixed overlapping slices of artificial `Gene1` through `Gene60` identifiers. |

## Showcase images

The four WebP resources are separate from the generated data. Setting
`include_showcase_images=True` returns their resource directory without decoding
or modifying the files. The showcase reads them with Matplotlib and scales them
into figure panels.

| Resource | Showcase panel | Provenance |
| --- | --- | --- |
| `showcase/image1.webp` | Figure 2A, pathology | Xue et al. (2022), *Liver tumour immune microenvironment subtypes and neutrophil heterogeneity*, [Figure 4f](https://www.nature.com/articles/s41586-022-05400-x/figures/4), liver photographs cropped from the panel. Exclusive publisher license; redistribution permission is unverified. |
| `showcase/image2.webp` | Figure 2B, immunofluorescence | Xue et al. (2022), [Figure 2f](https://www.nature.com/articles/s41586-022-05400-x/figures/2), top TIME-IE microscopy image cropped from the panel. Exclusive publisher license; redistribution permission is unverified. |
| `showcase/image3.webp` | Figure 2H, H&E histology | Ma et al. (2019), [*Tumor Cell Biodiversity Drives Microenvironmental Reprogramming in Liver Cancer*](https://doi.org/10.1016/j.ccell.2019.08.007), Figure 2E; CC BY 4.0. The packaged image is a panel crop in WebP format. |
| `showcase/image4.webp` | Figure 2E, western blot | Original source and redistribution permission have not been established. |

Source attribution alone does not establish permission. Outstanding source or
permission records are listed in `NOTICE-DATA.md`; retain those qualifications
when redistributing the examples. Cite the software and any methods used as
described in the {doc}`citation guide <citation>`.
