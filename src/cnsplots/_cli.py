"""Command-line helpers for cnsplots."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from importlib import resources
from importlib.metadata import version
from pathlib import Path

if sys.version_info >= (3, 11):
    from importlib.resources.abc import Traversable  # pragma: no cover
else:
    from importlib.abc import Traversable  # pragma: no cover

_AGENT_SKILL_DIRS = {
    "codex": Path(".agents") / "skills",
    "claude": Path(".claude") / "skills",
}
_MANIFEST = ".cnsplots-manifest.json"
_PACKAGE_VERSION = version("cnsplots")


@dataclass
class _Manifest:
    version: str
    files: dict[str, str]


@dataclass
class _SkillStatus:
    agent: str
    destination: Path
    state: str
    version: str | None
    content_match: bool | None


@dataclass
class _Plan:
    destination: Path
    writes: dict[str, bytes]
    removals: tuple[str, ...]


def _skill_source() -> Traversable:
    return resources.files("cnsplots").joinpath("_agent_skill").joinpath("cnsplots")


def _validate_name(name: str) -> None:
    if (
        not name
        or "\\" in name
        or ":" in name
        or any(part in ("", ".", "..", _MANIFEST) for part in name.split("/"))
    ):
        raise ValueError(f"unsafe managed file name: {name!r}")


def _checked_path(root: Path, name: str) -> Path:
    path = root
    for part in name.split("/"):
        if path.exists() and not path.is_dir():
            raise NotADirectoryError(f"not a skill directory: {path}")
        path = path / part
        if path.is_symlink():
            raise ValueError(f"refusing to follow skill symlink: {path}")
    return path


def _destinations(agent: str, base_dir: Path) -> tuple[tuple[str, Path], ...]:
    names = tuple(_AGENT_SKILL_DIRS) if agent == "all" else (agent,)
    root = base_dir.resolve()
    destinations = []
    for name in names:
        if name not in _AGENT_SKILL_DIRS:
            raise ValueError(f"unsupported agent: {name}")
        path = _checked_path(root, (_AGENT_SKILL_DIRS[name] / "cnsplots").as_posix())
        if path.exists() and not path.is_dir():
            raise NotADirectoryError(f"not a skill directory: {path}")
        destinations.append((name, path))
    return tuple(destinations)


def _packaged_files() -> dict[str, bytes]:
    files: dict[str, bytes] = {}

    def read_tree(source: Traversable, prefix: str = "") -> None:
        if isinstance(source, Path) and source.is_symlink():
            raise ValueError(f"packaged skill contains a symlink: {source}")
        if source.is_dir():
            for item in source.iterdir():
                name = f"{prefix}/{item.name}" if prefix else item.name
                _validate_name(name)
                read_tree(item, name)
        elif source.is_file():
            files[prefix] = source.read_bytes()
        else:
            raise ValueError(f"invalid packaged skill entry: {source}")

    read_tree(_skill_source())
    if not files.get("SKILL.md"):
        raise ValueError("packaged skill must contain a nonempty SKILL.md")
    return files


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _file_digest(destination: Path, name: str) -> str | None:
    path = _checked_path(destination, name)
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f"expected a managed skill file: {path}")
    return _digest(path.read_bytes())


def _read_manifest(destination: Path) -> _Manifest | None:
    path = _checked_path(destination, _MANIFEST)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ValueError(f"invalid skill manifest: {path}") from exc
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != 1
        or not isinstance(data.get("version"), str)
        or not isinstance(data.get("files"), dict)
    ):
        raise ValueError(f"invalid skill manifest: {path}")
    files = data["files"]
    for name, digest in files.items():
        _validate_name(name)
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"invalid file hash in skill manifest: {path}")
        if any(parent.as_posix() in files for parent in Path(name).parents):
            raise ValueError(f"conflicting file paths in skill manifest: {path}")
    return _Manifest(data["version"], files)


def _apply_plans(plans: Sequence[_Plan]) -> None:
    """Stage every target, then swap trees; restore originals on an I/O failure."""
    staged: list[tuple[_Plan, Path]] = []
    backups: list[tuple[Path, Path]] = []
    installed: list[tuple[Path, Path]] = []
    cleanup = True
    try:
        for plan in plans:
            destination = plan.destination
            destination.parent.mkdir(parents=True, exist_ok=True)
            work = Path(tempfile.mkdtemp(prefix=".cnsplots-", dir=destination.parent))
            staged.append((plan, work))
            tree = work / "new"
            if destination.exists():
                shutil.copytree(destination, tree, symlinks=True)
            else:
                tree.mkdir()
            for name in plan.removals:
                path = tree / name
                path.unlink(missing_ok=True)
                parent = path.parent
                while parent != tree and parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
            for name, content in plan.writes.items():
                path = tree / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        for plan, work in staged:
            destination = plan.destination
            if destination.exists():
                destination.rename(work / "old")
                backups.append((destination, work / "old"))
            tree = work / "new"
            if any(tree.iterdir()):
                tree.rename(destination)
                installed.append((destination, tree))
    except OSError:
        try:
            for destination, tree in reversed(installed):
                destination.rename(tree)
            for destination, backup in reversed(backups):
                backup.rename(destination)
        except OSError as exc:
            cleanup = False
            paths = ", ".join(str(work) for _, work in staged)
            raise OSError(
                f"skill rollback failed; recovery copies retained at {paths}"
            ) from exc
        raise
    finally:
        if cleanup:
            for _, work in staged:
                shutil.rmtree(work, ignore_errors=True)


def install_skill(
    agent: str,
    *,
    force: bool,
    base_dir: Path,
) -> tuple[tuple[str, Path], ...]:
    """Install and track packaged files, requiring force to update existing skills.

    Forced updates overwrite current managed files, including local edits. Only
    unchanged obsolete files are removed. Legacy installs are overlaid without
    deleting untracked files; new conflicts in managed installs are refused.
    All targets are validated and staged before replacing any installation.
    """
    destinations = _destinations(agent, base_dir)
    conflicts = tuple(path for _, path in destinations if path.exists())
    if conflicts and not force:
        paths = ", ".join(str(path) for path in conflicts)
        raise FileExistsError(
            f"refusing to overwrite existing skill at {paths}; pass --force to update"
        )

    files = _packaged_files()
    hashes = {name: _digest(content) for name, content in files.items()}
    manifest_bytes = (
        json.dumps(
            {"schema_version": 1, "version": _PACKAGE_VERSION, "files": hashes},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    plans = []
    for _, destination in destinations:
        manifest = _read_manifest(destination)
        old_files = manifest.files if manifest else {}
        old_hashes = {name: _file_digest(destination, name) for name in old_files}
        for name, digest in hashes.items():
            existing = _file_digest(destination, name)
            if manifest and name not in old_files and existing not in (None, digest):
                raise FileExistsError(
                    f"untracked skill file conflicts with update: {destination / name}"
                )
        removals = tuple(
            name
            for name, digest in old_files.items()
            if name not in files and old_hashes[name] == digest
        )
        plans.append(_Plan(destination, {**files, _MANIFEST: manifest_bytes}, removals))
    _apply_plans(plans)
    return destinations


def skill_status(agent: str, *, base_dir: Path) -> tuple[_SkillStatus, ...]:
    """Inspect selected paths without writes; unrelated files do not affect matches.

    States are missing, unmanaged (no manifest), modified (managed files changed
    or missing), outdated (unchanged but differs from this package), and current.
    """
    destinations = _destinations(agent, base_dir)
    hashes = {name: _digest(content) for name, content in _packaged_files().items()}
    statuses = []
    for name, destination in destinations:
        if not destination.exists():
            statuses.append(_SkillStatus(name, destination, "missing", None, None))
            continue
        manifest = _read_manifest(destination)
        installed = {name: _file_digest(destination, name) for name in hashes}
        matches = installed == hashes
        state = "unmanaged"
        version = None
        if manifest:
            version = manifest.version
            managed = {name: _file_digest(destination, name) for name in manifest.files}
            if managed != manifest.files:
                state = "modified"
            elif manifest.files != hashes or version != _PACKAGE_VERSION:
                state = "outdated"
            else:
                state = "current"
            matches = matches and manifest.files.keys() == hashes.keys()
        statuses.append(_SkillStatus(name, destination, state, version, matches))
    return tuple(statuses)


def uninstall_skill(agent: str, *, base_dir: Path) -> tuple[tuple[str, Path], ...]:
    """Remove unchanged managed files; retain edits and unrelated content.

    Missing paths succeed. Existing directories without a manifest are refused.
    Retained files become unmanaged when the ownership manifest is removed.
    """
    destinations = _destinations(agent, base_dir)
    plans = []
    for _, destination in destinations:
        if not destination.exists():
            continue
        manifest = _read_manifest(destination)
        if manifest is None:
            raise ValueError(
                f"no ownership manifest at {destination}; run install --force to track "
                "packaged files before uninstall (overwrites packaged paths)"
            )
        removals = tuple(
            name
            for name, digest in manifest.files.items()
            if _file_digest(destination, name) == digest
        )
        plans.append(_Plan(destination, {}, (*removals, _MANIFEST)))
    _apply_plans(plans)
    return destinations


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cnsplots")
    commands = parser.add_subparsers(dest="command", required=True)
    skill = commands.add_parser("skill", help="manage the cnsplots agent skill")
    skill_commands = skill.add_subparsers(dest="skill_command", required=True)
    for command, description in (
        ("install", "install the agent skill"),
        (
            "status",
            "show read-only installation status (exit 0 even if missing or changed)",
        ),
        (
            "uninstall",
            "remove unchanged managed files; retain modified and unrelated files "
            "(missing installations succeed)",
        ),
    ):
        subparser = skill_commands.add_parser(
            command,
            help=description,
            description=description,
            epilog="Exit codes: 0 success, 1 operational error, 2 invalid arguments.",
        )
        subparser.add_argument(
            "--agent",
            choices=("all", "codex", "claude"),
            default="all",
            help="agent to target (default: all)",
        )
        subparser.add_argument(
            "--scope",
            choices=("user", "project"),
            default="user",
            help="target the user's home or the current project (default: user)",
        )
        if command == "install":
            subparser.add_argument(
                "--force",
                action="store_true",
                help="update existing files, overwriting edits to current packaged files",
            )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI; return 0 on success or 1 on operational errors.

    Status reports succeed even for missing or differing installations. Invalid
    arguments are handled by argparse with exit code 2.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        base_dir = Path.home() if args.scope == "user" else Path.cwd()
        if args.skill_command == "status":
            for status in skill_status(args.agent, base_dir=base_dir):
                state = (
                    "missing"
                    if status.state == "missing"
                    else f"installed ({status.state})"
                )
                content = (
                    "unavailable"
                    if status.content_match is None
                    else "matches packaged skill"
                    if status.content_match
                    else "differs from packaged skill"
                )
                print(
                    f"{status.agent}: {state}; version {status.version or 'unknown'}; "
                    f"content {content}; path {status.destination}"
                )
            return 0
        if args.skill_command == "install":
            destinations = install_skill(
                args.agent, force=args.force, base_dir=base_dir
            )
        else:
            destinations = uninstall_skill(args.agent, base_dir=base_dir)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for agent, destination in destinations:
        if args.skill_command == "install":
            print(f"Installed cnsplots skill for {agent}: {destination}")
        else:
            retained = (
                "; retained modified or unrelated files" if destination.exists() else ""
            )
            print(
                f"Uninstalled managed cnsplots skill files for {agent}: {destination}{retained}"
            )
    return 0
