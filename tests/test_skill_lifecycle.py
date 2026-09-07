from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from cnsplots import _cli


@pytest.fixture
def skill_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    source = tmp_path / "package"
    _write(source / "SKILL.md", "# Original skill\n")
    _write(source / "references" / "obsolete.md", "Original reference\n")
    _write(source / "agents" / "openai.yaml", "name: cnsplots\n")
    monkeypatch.setattr(_cli, "_skill_source", lambda: source)
    return source


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _destination(base: Path, agent: str = "codex") -> Path:
    directory = ".agents" if agent == "codex" else ".claude"
    return base / directory / "skills" / "cnsplots"


def _snapshot(path: Path) -> dict[str, bytes | str]:
    return {
        str(item.relative_to(path)): (
            f"symlink:{item.readlink()}" if item.is_symlink() else item.read_bytes()
        )
        for item in path.rglob("*")
        if item.is_file() or item.is_symlink()
    }


def test_install_records_file_ownership(tmp_path: Path, skill_source: Path) -> None:
    base = tmp_path / "project"
    _cli.install_skill("codex", force=False, base_dir=base)

    destination = _destination(base)
    manifest = json.loads((destination / _cli._MANIFEST).read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert isinstance(manifest["version"], str)
    assert manifest["version"]
    assert manifest["files"] == {
        item.relative_to(skill_source).as_posix(): hashlib.sha256(
            item.read_bytes()
        ).hexdigest()
        for item in skill_source.rglob("*")
        if item.is_file()
    }


@pytest.mark.parametrize("modified_obsolete", [False, True])
def test_upgrade_prunes_only_unchanged_obsolete_managed_files(
    tmp_path: Path, skill_source: Path, modified_obsolete: bool
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("codex", force=False, base_dir=base)
    destination = _destination(base)
    obsolete = destination / "references" / "obsolete.md"
    if modified_obsolete:
        _write(obsolete, "Personal reference\n")
    _write(destination / "notes" / "mine.md", "Personal notes\n")
    _write(destination / "SKILL.md", "Locally edited current guide\n")
    (skill_source / "references" / "obsolete.md").unlink()
    _write(skill_source / "SKILL.md", "# Updated skill\n")
    _write(skill_source / "references" / "new.md", "New reference\n")

    _cli.install_skill("codex", force=True, base_dir=base)

    assert (destination / "SKILL.md").read_text() == "# Updated skill\n"
    assert (destination / "references" / "new.md").read_text() == "New reference\n"
    assert (destination / "notes" / "mine.md").read_text() == "Personal notes\n"
    assert obsolete.exists() == modified_obsolete
    if modified_obsolete:
        assert obsolete.read_text() == "Personal reference\n"
    manifest = json.loads((destination / _cli._MANIFEST).read_text())
    assert "references/obsolete.md" not in manifest["files"]
    assert "notes/mine.md" not in manifest["files"]


def test_force_migrates_legacy_install_without_purging_user_files(
    tmp_path: Path, skill_source: Path
) -> None:
    base = tmp_path / "project"
    destination = _destination(base)
    _write(destination / "SKILL.md", "Legacy skill")
    _write(destination / "references" / "legacy.md", "Keep this old reference")
    _write(destination / "notes.txt", "User notes")

    _cli.install_skill("codex", force=True, base_dir=base)

    assert (destination / "SKILL.md").read_bytes() == (
        skill_source / "SKILL.md"
    ).read_bytes()
    assert (destination / "references" / "legacy.md").read_text() == (
        "Keep this old reference"
    )
    assert (destination / "notes.txt").read_text() == "User notes"
    manifest = json.loads((destination / _cli._MANIFEST).read_text())
    assert "notes.txt" not in manifest["files"]
    assert "references/legacy.md" not in manifest["files"]


@pytest.mark.parametrize("same_content", [False, True])
def test_new_packaged_files_preserve_conflicting_untracked_files(
    tmp_path: Path, skill_source: Path, same_content: bool
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("all", force=False, base_dir=base)
    destination = _destination(base, "claude")
    content = "Packaged addition" if same_content else "User addition"
    _write(destination / "new.md", content)
    _write(skill_source / "new.md", "Packaged addition")
    before = _snapshot(base)

    if same_content:
        _cli.install_skill("all", force=True, base_dir=base)
        manifest = json.loads((destination / _cli._MANIFEST).read_text())
        assert "new.md" in manifest["files"]
    else:
        with pytest.raises((ValueError, FileExistsError), match="new.md"):
            _cli.install_skill("all", force=True, base_dir=base)
        assert _snapshot(base) == before
    assert (destination / "new.md").read_text() == content


@pytest.mark.parametrize("operation", ["install", "uninstall"])
@pytest.mark.parametrize(
    "manifest",
    [
        "not JSON",
        json.dumps({"schema_version": 2, "version": "1", "files": {}}),
        json.dumps({"schema_version": 1, "version": "1", "files": []}),
        json.dumps(
            {"schema_version": 1, "version": "1", "files": {"../escape": "a" * 64}}
        ),
        json.dumps(
            {"schema_version": 1, "version": "1", "files": {"/escape": "a" * 64}}
        ),
        json.dumps({"schema_version": 1, "version": "1", "files": {"SKILL.md": "bad"}}),
        json.dumps(
            {
                "schema_version": 1,
                "version": "1",
                "files": {"references": "a" * 64, "references/file.md": "b" * 64},
            }
        ),
    ],
)
def test_invalid_manifests_preflight_all_agents(
    tmp_path: Path, skill_source: Path, operation: str, manifest: str
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("all", force=False, base_dir=base)
    _write(_destination(base, "claude") / _cli._MANIFEST, manifest)
    before = _snapshot(base)

    with pytest.raises(ValueError):
        if operation == "install":
            _cli.install_skill("all", force=True, base_dir=base)
        else:
            _cli.uninstall_skill("all", base_dir=base)

    assert _snapshot(base) == before


@pytest.mark.parametrize("entry", ["missing", "empty", "symlink", "unsafe"])
def test_invalid_packaged_files_leave_installs_untouched(
    tmp_path: Path, skill_source: Path, entry: str
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("all", force=False, base_dir=base)
    before = _snapshot(base)
    if entry == "missing":
        (skill_source / "SKILL.md").unlink()
    elif entry == "empty":
        _write(skill_source / "SKILL.md", "")
    elif entry == "symlink":
        (skill_source / "link.md").symlink_to(skill_source / "SKILL.md")
    else:
        _write(skill_source / "unsafe\\name", "Invalid file name")

    with pytest.raises(ValueError):
        _cli.install_skill("all", force=True, base_dir=base)

    assert _snapshot(base) == before


def test_missing_package_source_leaves_installs_untouched(
    tmp_path: Path, skill_source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("all", force=False, base_dir=base)
    before = _snapshot(base)
    monkeypatch.setattr(_cli, "_skill_source", lambda: tmp_path / "missing")

    with pytest.raises(ValueError, match="packaged skill"):
        _cli.install_skill("all", force=True, base_dir=base)

    assert _snapshot(base) == before


@pytest.mark.parametrize("component", [".agents", ".agents/skills/cnsplots"])
def test_install_refuses_nondirectory_destinations(
    tmp_path: Path, skill_source: Path, component: str
) -> None:
    base = tmp_path / "project"
    _write(base / component, "User file")
    before = _snapshot(base)

    with pytest.raises(NotADirectoryError):
        _cli.install_skill("all", force=True, base_dir=base)

    assert _snapshot(base) == before


@pytest.mark.parametrize("operation", ["install", "uninstall"])
def test_replaced_managed_file_directory_is_preserved(
    tmp_path: Path, skill_source: Path, operation: str
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("all", force=False, base_dir=base)
    path = _destination(base, "claude") / "SKILL.md"
    path.unlink()
    _write(path / "notes.md", "User directory")
    before = _snapshot(base)

    with pytest.raises(ValueError, match="managed skill file"):
        if operation == "install":
            _cli.install_skill("all", force=True, base_dir=base)
        else:
            _cli.uninstall_skill("all", base_dir=base)

    assert _snapshot(base) == before


@pytest.mark.parametrize("operation", ["install", "uninstall"])
@pytest.mark.parametrize(
    "component", [".agents", ".agents/skills", ".agents/skills/cnsplots"]
)
def test_selected_symlink_destinations_are_rejected(
    tmp_path: Path, skill_source: Path, operation: str, component: str
) -> None:
    base = tmp_path / "project"
    outside = tmp_path / "outside"
    _write(outside / "keep.md", "Outside data")
    link = base / component
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside, target_is_directory=True)
    before = _snapshot(outside)

    with pytest.raises((ValueError, OSError), match="symlink"):
        if operation == "install":
            _cli.install_skill("codex", force=True, base_dir=base)
        else:
            _cli.uninstall_skill("codex", base_dir=base)

    assert link.is_symlink()
    assert _snapshot(outside) == before


@pytest.mark.parametrize("operation", ["install", "uninstall"])
@pytest.mark.parametrize(
    "relative", ["SKILL.md", "references", ".cnsplots-manifest.json"]
)
def test_managed_symlinks_are_rejected_without_following_them(
    tmp_path: Path, skill_source: Path, operation: str, relative: str
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("all", force=False, base_dir=base)
    destination = _destination(base, "claude")
    target = destination / relative
    outside = tmp_path / "outside"
    if target.is_dir():
        target.rename(outside)
    else:
        outside.write_bytes(target.read_bytes())
        target.unlink()
    target.symlink_to(outside, target_is_directory=outside.is_dir())
    before = _snapshot(base)

    with pytest.raises((ValueError, OSError), match="symlink"):
        if operation == "install":
            _cli.install_skill("all", force=True, base_dir=base)
        else:
            _cli.uninstall_skill("all", base_dir=base)

    assert _snapshot(base) == before
    assert target.is_symlink()


@pytest.mark.parametrize("operation", ["install", "uninstall"])
def test_unrelated_symlinks_survive(
    tmp_path: Path, skill_source: Path, operation: str
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("codex", force=False, base_dir=base)
    destination = _destination(base)
    outside = tmp_path / "outside"
    _write(outside / "notes.md", "Outside data")
    link = destination / "personal"
    link.symlink_to(outside, target_is_directory=True)
    dangling = destination / "dangling"
    dangling.symlink_to(tmp_path / "missing")

    if operation == "install":
        _cli.install_skill("codex", force=True, base_dir=base)
    else:
        _cli.uninstall_skill("codex", base_dir=base)

    assert link.is_symlink()
    assert link.readlink() == outside
    assert dangling.is_symlink()
    assert (outside / "notes.md").read_text() == "Outside data"


def test_uninstall_removes_only_selected_skill(
    tmp_path: Path, skill_source: Path
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("all", force=False, base_dir=base)
    sibling = base / ".agents" / "skills" / "other" / "SKILL.md"
    _write(sibling, "Another skill")
    other_before = _snapshot(_destination(base, "claude"))

    result = _cli.uninstall_skill("codex", base_dir=base)

    assert result == (("codex", _destination(base)),)
    assert not _destination(base).exists()
    assert sibling.read_text() == "Another skill"
    assert _snapshot(_destination(base, "claude")) == other_before


def test_uninstall_preserves_modified_and_untracked_files(
    tmp_path: Path, skill_source: Path
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("codex", force=False, base_dir=base)
    destination = _destination(base)
    _write(destination / "SKILL.md", "Personal skill edits")
    _write(destination / "references" / "personal.md", "Personal reference")

    _cli.uninstall_skill("codex", base_dir=base)

    assert _snapshot(destination) == {
        "SKILL.md": b"Personal skill edits",
        "references/personal.md": b"Personal reference",
    }
    assert not (destination / "agents").exists()


def test_uninstall_tolerates_missing_managed_files(
    tmp_path: Path, skill_source: Path
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("codex", force=False, base_dir=base)
    destination = _destination(base)
    (destination / "SKILL.md").unlink()
    (destination / "references" / "obsolete.md").unlink()
    (destination / "references").rmdir()

    _cli.uninstall_skill("codex", base_dir=base)

    assert not destination.exists()


def test_uninstall_missing_installations_is_idempotent(tmp_path: Path) -> None:
    base = tmp_path / "project"
    expected = (
        ("codex", _destination(base)),
        ("claude", _destination(base, "claude")),
    )

    assert _cli.uninstall_skill("all", base_dir=base) == expected
    assert _cli.uninstall_skill("all", base_dir=base) == expected
    assert not base.exists()


def test_uninstall_refuses_legacy_install_before_modifying_any_agent(
    tmp_path: Path, skill_source: Path
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("codex", force=False, base_dir=base)
    _write(_destination(base, "claude") / "SKILL.md", "Legacy skill")
    before = _snapshot(base)

    with pytest.raises(ValueError, match="manifest"):
        _cli.uninstall_skill("all", base_dir=base)

    assert _snapshot(base) == before


def test_upgrade_copy_failure_preserves_all_installed_files(
    tmp_path: Path, skill_source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("all", force=False, base_dir=base)
    before = _snapshot(base)
    _write(skill_source / "SKILL.md", "Updated skill")
    original = Path.write_bytes

    def fail_copy(path: Path, data: bytes) -> int:
        if path.name == "SKILL.md":
            raise OSError("injected copy failure")
        return original(path, data)

    monkeypatch.setattr(Path, "write_bytes", fail_copy)

    with pytest.raises(OSError, match="injected copy failure"):
        _cli.install_skill("all", force=True, base_dir=base)

    assert _snapshot(base) == before


@pytest.mark.parametrize("operation", ["upgrade", "uninstall"])
def test_staged_removal_failure_preserves_original_installations(
    tmp_path: Path, skill_source: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("all", force=False, base_dir=base)
    before = _snapshot(base)
    (skill_source / "references" / "obsolete.md").unlink()
    original = Path.unlink

    def fail_removal(path: Path, missing_ok: bool = False) -> None:
        if path.name == "obsolete.md":
            raise OSError("injected removal failure")
        original(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", fail_removal)

    with pytest.raises(OSError, match="injected removal failure"):
        if operation == "uninstall":
            _cli.uninstall_skill("all", base_dir=base)
        else:
            _cli.install_skill("all", force=True, base_dir=base)

    assert _snapshot(base) == before


@pytest.mark.parametrize("operation", ["install", "upgrade", "uninstall"])
def test_rename_failure_rolls_back_all_agents(
    tmp_path: Path, skill_source: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    base = tmp_path / "project"
    if operation != "install":
        _cli.install_skill("all", force=False, base_dir=base)
    before = _snapshot(base)
    _write(skill_source / "SKILL.md", "Updated skill")
    second = _destination(base, "claude")
    original = Path.rename
    failed = False

    def fail_second(path: Path, target: Path) -> Path:
        nonlocal failed
        if not failed and (path == second or Path(target) == second):
            failed = True
            raise OSError("injected rename failure")
        return original(path, target)

    monkeypatch.setattr(Path, "rename", fail_second)

    with pytest.raises(OSError, match="injected rename failure"):
        if operation == "uninstall":
            _cli.uninstall_skill("all", base_dir=base)
        else:
            _cli.install_skill("all", force=operation == "upgrade", base_dir=base)

    assert failed
    assert _snapshot(base) == before
    if operation == "install":
        assert not _destination(base).exists()
        assert not second.exists()


def test_failed_rollback_retains_recovery_copy(
    tmp_path: Path, skill_source: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = tmp_path / "project"
    _cli.install_skill("codex", force=False, base_dir=base)
    destination = _destination(base)
    before = _snapshot(destination)
    _write(skill_source / "SKILL.md", "Updated skill")
    original = Path.rename

    def fail_restore(path: Path, target: Path) -> Path:
        if Path(target) == destination:
            raise OSError("injected destination rename failure")
        return original(path, target)

    monkeypatch.setattr(Path, "rename", fail_restore)

    with pytest.raises(OSError, match="recovery copies retained") as error:
        _cli.install_skill("codex", force=True, base_dir=base)

    backups = list(destination.parent.glob(".cnsplots-*/old"))
    assert len(backups) == 1
    assert _snapshot(backups[0]) == before
    assert str(backups[0].parent) in str(error.value)


@pytest.mark.parametrize("scope", ["user", "project"])
def test_cli_uninstall_targets_scope_and_reports_result(
    tmp_path: Path,
    skill_source: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    scope: str,
) -> None:
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    _cli.install_skill("all", force=False, base_dir=project)
    _cli.install_skill("all", force=False, base_dir=home)
    target = home if scope == "user" else project
    other = project if scope == "user" else home
    before = _snapshot(other)

    result = _cli.main(["skill", "uninstall", "--agent", "claude", "--scope", scope])

    assert result == 0
    assert "claude" in capsys.readouterr().out
    assert not _destination(target, "claude").exists()
    assert _destination(target).exists()
    assert _snapshot(other) == before


def test_cli_reports_uninstall_manifest_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    _write(_destination(tmp_path) / "SKILL.md", "Legacy skill")

    result = _cli.main(["skill", "uninstall", "--agent", "codex", "--scope", "project"])

    assert result == 1
    assert "manifest" in capsys.readouterr().err
