"""Command-line helpers for cnsplots."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from importlib import resources
from pathlib import Path

if sys.version_info >= (3, 11):
    from importlib.resources.abc import Traversable  # pragma: no cover
else:
    from importlib.abc import Traversable  # pragma: no cover

_AGENT_SKILL_DIRS = {
    "codex": Path(".agents") / "skills",
    "claude": Path(".claude") / "skills",
}


def _skill_source() -> Traversable:
    return resources.files("cnsplots").joinpath("_agent_skill").joinpath("cnsplots")


def _copy_skill_tree(source: Traversable, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            _copy_skill_tree(item, target)
        else:
            target.write_bytes(item.read_bytes())


def install_skill(
    agent: str,
    *,
    force: bool,
    base_dir: Path,
) -> tuple[tuple[str, Path], ...]:
    """Install the packaged skill into one or more agent skill directories."""
    agent_names = tuple(_AGENT_SKILL_DIRS) if agent == "all" else (agent,)
    destinations = tuple(
        (name, base_dir / _AGENT_SKILL_DIRS[name] / "cnsplots")
        for name in agent_names
    )

    conflicts = tuple(path for _, path in destinations if path.exists())
    if conflicts and not force:
        paths = ", ".join(str(path) for path in conflicts)
        raise FileExistsError(
            f"refusing to overwrite existing skill at {paths}; pass --force to update"
        )

    source = _skill_source()
    for _, destination in destinations:
        _copy_skill_tree(source, destination)
    return destinations


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cnsplots")
    commands = parser.add_subparsers(dest="command", required=True)
    skill = commands.add_parser("skill", help="manage the cnsplots agent skill")
    skill_commands = skill.add_subparsers(dest="skill_command", required=True)
    install = skill_commands.add_parser("install", help="install the agent skill")
    install.add_argument(
        "--agent",
        choices=("all", "codex", "claude"),
        default="all",
        help="agent to configure (default: all)",
    )
    install.add_argument(
        "--scope",
        choices=("user", "project"),
        default="user",
        help="install globally for the user or into the current project",
    )
    install.add_argument(
        "--force",
        action="store_true",
        help="update files in an existing cnsplots skill",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the cnsplots command line interface."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    base_dir = Path.home() if args.scope == "user" else Path.cwd()

    try:
        destinations = install_skill(
            args.agent,
            force=args.force,
            base_dir=base_dir,
        )
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for agent, destination in destinations:
        print(f"Installed cnsplots skill for {agent}: {destination}")
    return 0
