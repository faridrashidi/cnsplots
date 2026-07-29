# Python palette parity fixtures

These files freeze the palette behavior used by cnsplots `0.5.0` at
source commit `e678e2d5e975c4595b1d7c8bc4d07b4030a29d14`.

- `python-v0.5.0-palette-metadata.csv`: canonical names, types, provenance,
  defaults, and historical names. Historical names are audit metadata, not
  accepted aliases.
- `python-v0.5.0-qualitative-palettes.csv`: all 28 qualitative palettes in
  exact Python order, normalized with `matplotlib.colors.to_hex()`.
- `python-v0.5.0-continuous-controls.csv`: original RGB control points for the
  five custom continuous palettes, including their equally spaced positions.
- `python-v0.5.0-continuous-lut.csv`: fixed 256-entry LUTs for all five custom
  palettes plus Matplotlib builtins `gnuplot` and `hot`.

Fixture runtime versions:

- Matplotlib `3.10.8`
- Palettable `3.3.3`

Custom LUTs were built with
`LinearSegmentedColormap.from_list(name, controls, N=256)` and sampled at
`seq(0, 1, length.out = 256)` equivalents. The R runtime should sample these
fixed LUTs instead of regenerating gradients with a potentially different
interpolation or rounding implementation.

Current defaults are `Ecotyper1` for qualitative cycles and `gnuplot` for
continuous colour maps. Python categorical cycles repeat when groups exceed
available colours.
