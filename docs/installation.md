# Installation

## Prerequisites

- Python 3.9 or higher (< 4.0)
- pip (Python package installer)

## Basic Installation

Install cnsplots using pip:

```bash
pip install cnsplots
```

To install in an isolated environment (recommended):

```bash
python -m venv cnsplots-env
source cnsplots-env/bin/activate  # On Windows: cnsplots-env\Scripts\activate
pip install cnsplots
```

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

This uses `uv sync --all-extras` to install the package in editable mode with
the project's development and documentation extras, and sets up pre-commit
hooks.

### Development Commands

After installation, you can use the following commands:

| Command                          | Description                       |
| -------------------------------- | --------------------------------- |
| `make help`                      | Show available commands           |
| `make lint`                      | Run linting and formatting        |
| `make test`                      | Run all unit tests                |
| `make doc`                       | Build and serve documentation     |
| `make release [patch|minor|major]` | Bump the package version for a release |
| `make clean`                     | Clean build artifacts             |

## Dependencies

cnsplots relies on the following main packages (installed automatically):

- matplotlib, seaborn - Visualization
- pandas, numpy - Data manipulation
- scipy, scikit-learn - Statistical analysis
- scanpy - Single-cell analysis
- lifelines - Survival analysis
- gseapy - Gene set enrichment analysis

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
