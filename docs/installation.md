# Installation

## Prerequisites

- Python 3.10 or higher (< 4.0)
- pip (Python package installer)

## Basic Installation

Install cnsplots using pip:

```bash
pip install cnsplots
```

This installs every supported plotting and scientific integration. Imports
remain lazy, so those backends are loaded only when their APIs are first used.

## Verify Installation

After installation, verify that cnsplots is correctly installed:

```python
import cnsplots

print(cnsplots.__version__)
```

## Development Installation

To contribute or modify cnsplots, first install [uv](https://docs.astral.sh/uv/):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then clone the repository and install:

```bash
git clone https://github.com/faridrashidi/cnsplots
cd cnsplots
make install
```

This uses `uv sync --extra dev` to install the package in editable mode with
the project's development and documentation extras, and sets up pre-commit
hooks.

## Dependencies

cnsplots installs Matplotlib, seaborn, pandas, NumPy, SciPy, Scanpy, Lifelines,
GSEApy, Biopython, PyComplexHeatmap, and the set-plotting libraries
automatically.

For Illustrator-optimized SVG post-processing, you can optionally install
MuPDF's `mutool`. Without it, `cns.savefig("figure.svg")` still works and
falls back to a standard matplotlib SVG with a warning.

## Troubleshooting

### Installation fails with compiler errors

Some dependencies require compilation. Ensure you have the necessary build tools:

- **macOS**: Install Xcode Command Line Tools: `xcode-select --install`
- **Linux**: Install build essentials: `sudo apt-get install build-essential`
- **Windows**: Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### Conflicts with existing packages

If you experience dependency conflicts, try installing in a fresh virtual environment as shown above.
