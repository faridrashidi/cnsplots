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

## Install the Agent Skill

cnsplots includes an Agent Skills-compatible guide for building
publication-ready plots. Install it for Codex and Claude Code with:

```bash
cnsplots skill install
```

The default user-scope destinations are `~/.agents/skills/cnsplots` for Codex
and `~/.claude/skills/cnsplots` for Claude Code. You can target one agent or
install into the current project:

```bash
cnsplots skill install --agent codex
cnsplots skill install --agent claude --scope project
```

Invoke the installed skill as `$cnsplots` in Codex or `/cnsplots` in Claude
Code. The `install`, `status`, and `uninstall` commands all accept
`--agent all|codex|claude` (default: `all`) and `--scope user|project`
(default: `user`). Project scope uses `.agents/skills/cnsplots` and
`.claude/skills/cnsplots` beneath the current directory.

Inspect installed skills without changing any files:

```bash
cnsplots skill status
cnsplots skill status --agent codex --scope project
```

Status reports each resolved destination, installed cnsplots version (or
`unknown`), and whether its content `matches` or `differs` from the bundled
skill (`unavailable` when it cannot be compared). The installation state is
`missing`, `current`, `modified`, `outdated`, or `unmanaged`. Installations
without an ownership manifest are unmanaged. Changed or missing managed files
are reported as modified; otherwise, a different version or packaged content
is reported as outdated.

After upgrading cnsplots, update an existing skill with:

```bash
cnsplots skill install --force
```

Each installation records its version and managed file hashes in
`.cnsplots-manifest.json`. A forced update overwrites current packaged files,
including local edits to those files. It removes obsolete managed files only
when their content is unchanged, and preserves modified obsolete files and
unrelated files. If a newly introduced packaged file conflicts with a different
unrelated file in a managed installation, the update fails instead of overwriting
that file.

For legacy installations without a manifest, `install --force` overwrites the
current package's file paths and starts ownership tracking. It preserves other
existing files, including obsolete files that have no recorded ownership.

Remove an installed skill with:

```bash
cnsplots skill uninstall
cnsplots skill uninstall --agent claude --scope project
```

Uninstall removes unchanged managed files and the ownership manifest. Modified
and unrelated files remain in place and become unmanaged. An already missing
installation succeeds without changes. An existing installation without a
manifest cannot be uninstalled automatically; use `install --force` first only
if overwriting the current package's file paths is acceptable. Uninstall has no
`--force` option.

Commands refuse symlinked destinations, destination path components, or managed
paths. Unrelated symlinks are preserved.

Use `cnsplots skill --help` or `cnsplots skill <command> --help` for command
options. Successful commands return exit code `0`; status also returns `0` for
missing or differing installations. Operational errors return `1`, and invalid
command usage returns `2`.

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
