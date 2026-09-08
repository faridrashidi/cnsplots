# Contributing to cnsplots

Thank you for your interest in contributing to cnsplots! We welcome contributions from the community and appreciate your effort to make this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Contributing Code](#contributing-code)
  - [Improving Documentation](#improving-documentation)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is expected to uphold a respectful and welcoming environment. Please be kind and courteous to others.

## How Can I Contribute?

### Reporting Bugs

Found a bug? Help us fix it by:

1. **Check existing issues**: Search the [issue tracker](https://github.com/faridrashidi/cnsplots/issues) to see if the bug has already been reported.

2. **Create a new issue**: If the bug hasn't been reported, [open a new issue](https://github.com/faridrashidi/cnsplots/issues/new) with:
   - A clear, descriptive title
   - Detailed steps to reproduce the bug
   - Expected vs. actual behavior
   - Your environment (Python version, OS, cnsplots version)
   - Minimal code example that reproduces the issue
   - Screenshots or error messages if applicable

**Example bug report:**

```markdown
**Description**: Boxplot fails when using custom color palette

**Steps to reproduce**:

1. `cns.figure(150, 150, color_cycle="Set3")`
2. `cns.boxplot(data=df, x="group", y="value")`

**Expected**: Plot renders with Set3 colors
**Actual**: ValueError: invalid color cycle

**Environment**:

- Python 3.10
- macOS 14.0
```

### Suggesting Features

Have an idea for a new plot type or enhancement?

1. **Check existing requests**: Search [issues](https://github.com/faridrashidi/cnsplots/issues) and [discussions](https://github.com/faridrashidi/cnsplots/discussions) to see if it's already been suggested.

2. **Open a feature request**: [Create a new issue](https://github.com/faridrashidi/cnsplots/issues/new) or discussion with:
   - Clear description of the feature
   - Use case and motivation
   - Example of how it would work (code snippet)
   - Example visualizations if applicable

### Contributing Code

Ready to write code? Great! Here's how:

1. **Start with an issue**: For major changes, open an issue first to discuss your approach
2. **Fork the repository**: Create your own fork of cnsplots
3. **Create a branch**: Make a new branch for your feature (`git checkout -b feature/my-feature`)
4. **Write code**: Implement your changes following our [code style guidelines](#code-style-guidelines)
5. **Add tests**: Include tests for your changes
6. **Update documentation**: Add docstrings and update relevant documentation
7. **Submit a pull request**: Open a PR with a clear description of your changes

### Improving Documentation

Documentation improvements are always welcome! You can:

- Fix typos or clarify existing documentation
- Add examples to the gallery
- Improve API documentation
- Write tutorials or guides
- Translate documentation

## Development Setup

### 1. Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone and Install

```bash
git clone https://github.com/faridrashidi/cnsplots.git
cd cnsplots
make install
```

This uses `uv sync --locked --extra dev` to install the package in editable mode with all development tools, and sets up pre-commit hooks. The `dev` extra combines the focused extras below and remains available to pip users as `pip install -e '.[dev]'`.

For a smaller environment, select the extra needed for your task:

| Extra | Install command | Tools |
| --- | --- | --- |
| `test` | `uv sync --locked --extra test` | pytest, coverage, visual regression tools, and Sphinx-Gallery for documentation extension tests |
| `docs` | `uv sync --locked --extra docs` | Sphinx, themes, extensions, and gallery example dependencies |
| `lint` | `uv sync --locked --extra lint` | pre-commit, ty, and test dependencies required for type checking |
| `notebook` | `uv sync --locked --extra notebook` | IPython kernel |
| `release` | `uv sync --locked --extra release` | bump-my-version |

All extras include the package's runtime dependencies. `uv sync` selects an exact environment; repeat `--extra` to combine extras or run `make install` to restore the full setup. Make targets select their required extra automatically and use the committed lockfile. After changing dependencies, run `uv lock` and include the updated `uv.lock` in your PR.

### Development Commands

After installation, you can use the following commands:

| Command                              | Description                            |
| ------------------------------------ | -------------------------------------- |
| `make help`                          | Show available commands                |
| `make lint`                          | Run linting and formatting             |
| `make test`                          | Run all unit tests                     |
| `make doc`                           | Build documentation and exit           |
| `make doc-serve`                     | Build and preview documentation on port 8080 |
| `make doc-linkcheck`                 | Check documentation links              |
| `make release [patch\|minor\|major]` | Bump, commit, and tag a version; see [Release Process](#release-process) to defer tagging until after merge |
| `make clean`                         | Clean build artifacts                  |

`make doc` now exits with the build status locally and in CI; `CI=true make doc` remains valid. To use the previous build-and-preview workflow, run `make doc-serve`, open `http://localhost:8080`, and press Ctrl+C to stop the server. Documentation builds clean only `docs/build`, stage generated sources there, and preserve unrelated coverage, test, and package-build artifacts. To remove generated documentation output explicitly, use `make -C docs clean`.

### 3. Verify Installation

```bash
python -c "import cnsplots as cns; print(cns.__version__)"
```

The project is CI-tested on Python 3.10 through 3.14.

## Code Style Guidelines

We use [Ruff](https://github.com/astral-sh/ruff) for code formatting and linting.

### Running Linters

```bash
make lint
```

### Style Guidelines

- Follow [PEP 8](https://pep8.org/) conventions
- Use meaningful variable and function names
- Keep functions focused and concise
- Add docstrings to all public functions and classes
- Use type hints where appropriate

### Docstring Format

Use NumPy-style docstrings:

```python
def example_function(param1, param2):
    """Brief description of the function.

    Longer description if needed, explaining what the function does
    in more detail.

    Parameters
    ----------
    param1 : str
        Description of param1.
    param2 : int
        Description of param2.

    Returns
    -------
    bool
        Description of return value.

    Examples
    --------
    >>> example_function("test", 42)
    True
    """
    pass
```

## Testing

### Running Tests

```bash
make test
```

### Final PDF and SVG exports

`tests/test_export_pipeline.py` checks saved files after export processing. It
renders PDF with MuPDF's `mutool` and SVG with headless Chrome or Chromium, which
supports SVG clipping and transparency masks. These optional executables are
discovered locally; cases requiring an unavailable renderer explicitly skip.
Missing and failed SVG conversion paths are also tested, including when `mutool`
is absent but Chrome is available.

```bash
uv run --locked --extra test pytest tests/test_export_pipeline.py tests/test_svg_font_weights.py --no-cov
```

The suite checks bounds, clipped geometry, alpha, rasterized layers, multipanel
helper axes, and repeated text with different font weights. Geometric tolerances
and ink coverage allow platform font and antialiasing differences; these checks
do not require the pinned environment used for exact visual hashes. On failure,
`mpl-results/export-pipeline/` retains the exported file, Agg reference, rendered
PNG, enhanced difference image, and renderer log when available. Chrome profiles
stay in the test's temporary directory and are excluded from comparison artifacts.
Optimized SVG retains groups that carry clipping or masks, preserving the
coordinate system and shared bounds needed by transformed and rasterized artists.

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_<module>.py`
- Name test functions as `test_<functionality>`
- Use fixtures for common setup
- Test both expected behavior and edge cases

**Example test:**

```python
import cnsplots as cns
import pandas as pd
import pytest


def test_boxplot_basic():
    """Test basic boxplot creation."""
    df = pd.DataFrame({"x": ["A", "B"], "y": [1, 2]})
    fig = cns.figure(150, 150)
    ax = cns.boxplot(data=df, x="x", y="y")
    assert ax.figure is fig


def test_boxplot_invalid_data():
    """Test boxplot with invalid data."""
    with pytest.raises(ValueError):
        cns.boxplot(data=None, x="x", y="y")
```

## Pull Request Process

### Before Submitting

1. Run `make test`
2. Run `make lint`
3. Update documentation if needed
4. Add an example if introducing new functionality

### Submitting Your PR

1. **Title**: Use a clear, descriptive title
   - `✨ Add split violin plot support`
   - `🐛 Fix legend positioning in boxplot`
   - `📝 Clarify survival plot examples`

2. **Description**: Follow the PR template and include:
   - What changed
   - How it was tested
   - Any risks or follow-ups
   - Related issue(s), if any

3. **Release Notes Label**: Ask a maintainer to apply exactly one release label before merge:
   - `bug`
   - `enhancement`
   - `documentation`
   - `maintenance`
   - `ignore-for-release`

4. **Checklist**: Ensure you've completed:
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] All tests pass
   - [ ] Screenshots added for visual changes when helpful

### PR Template

```markdown
## What changed

Describe the main changes in this PR.

## How it was tested

List the checks you ran, for example:

- `make test`
- `make lint`

## Risks or follow-ups

Note any known risks, caveats, or follow-up work.

## Related issue

Closes #(issue number)

## Release Notes Label

Maintainers: apply exactly one release label before merge:
`bug`, `enhancement`, `documentation`, `maintenance`, or
`ignore-for-release`.
```

### Review Process

- Maintainers will review your PR
- Maintainers apply one release label before merge: `bug`, `enhancement`,
  `documentation`, `maintenance`, or `ignore-for-release`
- Address any feedback or requested changes
- Once approved, a maintainer will merge your PR
- Your contribution will be included in the next release

### Release Process

Follow [AGENTS.md](../AGENTS.md): prepare release changes on a branch and merge
them through a PR targeting `main`. Do not make release commits directly on
`main`. In the commands below, replace `X.Y.Z` with the intended version.

1. Start from a clean working tree and an up-to-date `main`, then create the
   release branch:

   ```bash
   git switch main
   git pull --ff-only origin main
   git switch -c chore/release-X.Y.Z
   BUMPVERSION_TAG=false make release patch
   ```

   Replace `patch` with `minor` or `major` as needed. The release target updates
   `pyproject.toml`, `src/cnsplots/__init__.py`, and `uv.lock`, and creates the
   release commit. By default it also creates a local `vX.Y.Z` tag. The
   `BUMPVERSION_TAG=false` override defers tagging until after merge so the tag
   can point to the merged commit, including when the PR is squash-merged.

2. Review the version changes and run both required checks after the final
   changes are in place:

   ```bash
   make test
   make lint
   ```

   Fix failures that are in scope; otherwise stop and report them. If validation
   changes files, review and commit those changes and rerun the checks. Push only
   the branch:

   ```bash
   git push --no-follow-tags -u origin chore/release-X.Y.Z
   ```

   Open a draft PR against `main` following the [PR process](#pull-request-process)
   and `AGENTS.md`, including exactly one release label (`maintenance` for a
   version-only bump). Have the PR reviewed and merged before creating the tag.

3. Fetch the merged result and check out the exact commit to release, replacing
   `MERGED_RELEASE_COMMIT` with the merged PR's commit SHA. Use a detached
   checkout to validate it without making changes on `main`:

   ```bash
   git fetch origin
   git switch --detach MERGED_RELEASE_COMMIT
   git merge-base --is-ancestor HEAD origin/main
   make test
   make lint
   git status --short
   ```

   Proceed only if the commit is on `origin/main`, both checks pass, the working
   tree is clean, and the version matches `X.Y.Z`. Any fixes must go through
   another branch and PR; then validate the resulting merged commit again.

4. Create the tag on that validated commit and push only that tag:

   ```bash
   git tag -a vX.Y.Z -m "Release X.Y.Z" HEAD
   git push --no-follow-tags origin refs/tags/vX.Y.Z
   ```

   Pushing a `v*` tag starts the [release workflow](workflows/release-publish.yml).
   It builds the distributions, checks their metadata with Twine, publishes to
   PyPI, and then creates a **published GitHub release** with distribution
   assets and generated release notes. The workflow does not set `draft: true`;
   there is no manual draft-publication step.

The tag workflow currently does not run tests or check a clean wheel installation;
the validation above is a maintainer prerequisite. Automated validation gates
are a separate proposal in [#175](https://github.com/faridrashidi/cnsplots/issues/175).

#### Release Checklist

- [ ] Release changes were reviewed and merged into `main` through a PR.
- [ ] The exact merged commit passed `make test` and `make lint`, has a clean
      working tree, and contains the intended version in all three version files.
- [ ] The `vX.Y.Z` tag points to that commit and only that tag was pushed.
- [ ] The release workflow succeeded, the version is available on PyPI, and the
      published GitHub release includes the distribution assets.
- [ ] Review the published release's generated PR list and changelog link. Edit
      its notes to add a short human-written summary under `Added`, `Changed`,
      and `Fixed` as appropriate; this edits an already published release.

## Community

### Getting Help

- Check the [documentation](https://cnsplots.farid.one/)
- Browse [examples](https://cnsplots.farid.one/latest/examples/index.html)
- Search [existing issues](https://github.com/faridrashidi/cnsplots/issues)
- Ask in [discussions](https://github.com/faridrashidi/cnsplots/discussions)

### Recognition

All contributors will be:

- Listed in the project's contributor list
- Acknowledged in release notes
- Part of the growing cnsplots community

### Questions?

Feel free to open a [discussion](https://github.com/faridrashidi/cnsplots/discussions) or reach out via [issues](https://github.com/faridrashidi/cnsplots/issues).

---

Thank you for contributing to cnsplots and helping make scientific visualization better for everyone!
