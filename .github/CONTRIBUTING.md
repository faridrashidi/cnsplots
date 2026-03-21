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

This uses `uv sync --all-extras` to install the package in editable mode with all dependencies, and sets up pre-commit hooks.

### Development Commands

After installation, you can use the following commands:

| Command                              | Description                            |
| ------------------------------------ | -------------------------------------- |
| `make help`                          | Show available commands                |
| `make lint`                          | Run linting and formatting             |
| `make test`                          | Run all unit tests                     |
| `make doc`                           | Build and serve documentation          |
| `make release [patch\|minor\|major]` | Bump the package version for a release |
| `make clean`                         | Clean build artifacts                  |

### 3. Verify Installation

```bash
python -c "import cnsplots as cns; print(cns.__version__)"
```

The project is CI-tested on Python 3.9 through 3.14.

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
    cns.boxplot(data=df, x="x", y="y")
    assert fig is not None


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

Maintainers can create a release on the main branch (no PR needed) with:

```bash
make release patch
```

You can replace `patch` with `minor` or `major` as needed. This bumps the
package version, creates the release tag, and prepares the release commit.
After pushing the commit and tag, GitHub Actions will:

- publish the package to PyPI
- create a draft GitHub release for the new tag
- generate release notes from merged PRs since the previous tag

Before publishing the draft release, add a short human-written summary under
the `Added`, `Changed`, and `Fixed` headings, then verify the generated PR list
and changelog link.

## Community

### Getting Help

- Check the [documentation](https://cnsplots.farid.one/)
- Browse [examples](https://cnsplots.farid.one/examples/index.html)
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
