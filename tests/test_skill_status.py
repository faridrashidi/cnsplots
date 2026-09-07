from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from cnsplots import __version__, _cli


@pytest.fixture
def packaged_skill(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    source = tmp_path / "packaged"
    source.mkdir()
    (source / "SKILL.md").write_text("packaged skill\n", encoding="utf-8")
    (source / "references").mkdir()
    (source / "references" / "guide.md").write_text("guide\n", encoding="utf-8")
    monkeypatch.setattr(_cli, "_skill_source", lambda: source)
    return source


def _destination(base: Path, agent: str) -> Path:
    directory = ".agents" if agent == "codex" else ".claude"
    return base / directory / "skills" / "cnsplots"


def _installed_skill(source: Path, base: Path, agent: str = "codex") -> Path:
    destination = _destination(base, agent)
    files = {}
    for item in source.rglob("*"):
        if item.is_file():
            relative = item.relative_to(source)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            content = item.read_bytes()
            target.write_bytes(content)
            files[relative.as_posix()] = hashlib.sha256(content).hexdigest()
    (destination / _cli._MANIFEST).write_text(
        json.dumps({"schema_version": 1, "version": __version__, "files": files}),
        encoding="utf-8",
    )
    return destination


def _snapshot(base: Path) -> dict[Path, tuple[int, bytes | None]]:
    return {
        path.relative_to(base): (
            path.stat().st_mtime_ns,
            path.read_bytes() if path.is_file() else None,
        )
        for path in [base, *sorted(base.rglob("*"))]
    }


def test_status_reports_missing_agents_without_creating_directories(
    tmp_path: Path, packaged_skill: Path
) -> None:
    base = tmp_path / "not-created"

    results = _cli.skill_status("all", base_dir=base)

    assert [result.agent for result in results] == ["codex", "claude"]
    for result in results:
        assert result.destination == _destination(base, result.agent).resolve()
        assert result.state == "missing"
        assert result.version is None
        assert result.content_match is None
    assert not base.exists()


def test_status_rejects_unsupported_agent_without_writes(tmp_path: Path) -> None:
    before = _snapshot(tmp_path)

    with pytest.raises(ValueError, match="unsupported agent"):
        _cli.skill_status("other", base_dir=tmp_path)

    assert _snapshot(tmp_path) == before


def test_status_reports_current_skill_and_ignores_unrelated_files(
    tmp_path: Path, packaged_skill: Path
) -> None:
    destination = _installed_skill(packaged_skill, tmp_path)
    (destination / "notes.txt").write_text("keep my notes", encoding="utf-8")
    before = _snapshot(tmp_path)

    (result,) = _cli.skill_status("codex", base_dir=tmp_path)

    assert result.destination == destination.resolve()
    assert result.state == "current"
    assert result.version == __version__
    assert result.content_match is True
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("change", ["edit", "delete"])
def test_status_reports_modified_managed_file(
    tmp_path: Path, packaged_skill: Path, change: str
) -> None:
    destination = _installed_skill(packaged_skill, tmp_path)
    guide = destination / "references" / "guide.md"
    if change == "edit":
        guide.write_text("local changes", encoding="utf-8")
    else:
        guide.unlink()
    before = _snapshot(tmp_path)

    (result,) = _cli.skill_status("codex", base_dir=tmp_path)

    assert result.state == "modified"
    assert result.version == __version__
    assert result.content_match is False
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("change", ["version", "content", "added", "removed"])
def test_status_distinguishes_outdated_from_locally_modified(
    tmp_path: Path, packaged_skill: Path, change: str
) -> None:
    destination = _installed_skill(packaged_skill, tmp_path)
    version = __version__
    if change == "version":
        manifest = destination / _cli._MANIFEST
        metadata = json.loads(manifest.read_text(encoding="utf-8"))
        metadata["version"] = version = "0.0.0"
        manifest.write_text(json.dumps(metadata), encoding="utf-8")
    elif change == "content":
        (packaged_skill / "SKILL.md").write_text("new release", encoding="utf-8")
    elif change == "added":
        (packaged_skill / "new.md").write_text("new guide", encoding="utf-8")
    else:
        (packaged_skill / "references" / "guide.md").unlink()
    before = _snapshot(tmp_path)

    (result,) = _cli.skill_status("codex", base_dir=tmp_path)

    assert result.state == "outdated"
    assert result.version == version
    assert result.content_match is (change == "version")
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("matches", [True, False])
def test_status_compares_legacy_skill_without_claiming_its_version(
    tmp_path: Path, packaged_skill: Path, matches: bool
) -> None:
    destination = _installed_skill(packaged_skill, tmp_path)
    (destination / _cli._MANIFEST).unlink()
    if not matches:
        (destination / "SKILL.md").write_text("old skill", encoding="utf-8")
    before = _snapshot(tmp_path)

    (result,) = _cli.skill_status("codex", base_dir=tmp_path)

    assert result.state == "unmanaged"
    assert result.version is None
    assert result.content_match is matches
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("scope", ["user", "project"])
@pytest.mark.parametrize("agent", ["all", "codex", "claude"])
def test_cli_status_targets_requested_scope_and_agents(
    tmp_path: Path,
    packaged_skill: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    scope: str,
    agent: str,
) -> None:
    user = tmp_path / "user"
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: user))
    monkeypatch.chdir(project)
    base = user if scope == "user" else project
    selected = ("codex", "claude") if agent == "all" else (agent,)
    for selected_agent in selected:
        _installed_skill(packaged_skill, base, selected_agent)
    before = _snapshot(tmp_path)

    result = _cli.main(["skill", "status", "--agent", agent, "--scope", scope])

    assert result == 0
    output = capsys.readouterr()
    assert output.err == ""
    for selected_agent in selected:
        assert selected_agent in output.out
        assert str(_destination(base, selected_agent).resolve()) in output.out
    if agent != "all":
        other = "claude" if agent == "codex" else "codex"
        assert other not in output.out
    assert "current" in output.out
    assert __version__ in output.out
    assert "matches" in output.out
    assert _snapshot(tmp_path) == before


def test_cli_status_defaults_to_all_user_skills(
    tmp_path: Path,
    packaged_skill: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    user = tmp_path / "user"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: user))
    before = _snapshot(tmp_path)

    assert _cli.main(["skill", "status"]) == 0

    output = capsys.readouterr()
    assert output.err == ""
    for agent in ("codex", "claude"):
        assert agent in output.out
        assert str(_destination(user, agent).resolve()) in output.out
    assert "missing" in output.out
    assert "unknown" in output.out
    assert "unavailable" in output.out
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("state", ["modified", "outdated", "unmanaged"])
def test_cli_status_reports_noncurrent_installations_successfully(
    tmp_path: Path,
    packaged_skill: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    state: str,
) -> None:
    destination = _installed_skill(packaged_skill, tmp_path)
    if state == "modified":
        (destination / "SKILL.md").write_text("my edits", encoding="utf-8")
    elif state == "outdated":
        (packaged_skill / "SKILL.md").write_text("next release", encoding="utf-8")
    else:
        (destination / _cli._MANIFEST).unlink()
    monkeypatch.chdir(tmp_path)
    before = _snapshot(tmp_path)

    assert _cli.main(["skill", "status", "--scope", "project"]) == 0

    output = capsys.readouterr()
    assert output.err == ""
    assert state in output.out
    assert "installed" in output.out
    assert ("matches" if state == "unmanaged" else "differs") in output.out
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("command", ["status", "uninstall"])
def test_cli_help_describes_targeting_and_exit_codes(
    command: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        _cli.main(["skill", command, "--help"])

    assert exc.value.code == 0
    output = capsys.readouterr().out.lower()
    assert "--agent" in output
    assert "{all,codex,claude}" in output
    assert "--scope" in output
    assert "{user,project}" in output
    assert "default: all" in output
    assert "default: user" in output
    assert "--force" not in output
    assert "0" in output
    assert "1" in output
    assert "2" in output
    if command == "status":
        assert "read-only" in output
    else:
        assert "missing" in output
        assert "modified" in output


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["skill"],
        ["skill", "status", "--agent", "other"],
        ["skill", "status", "--scope", "global"],
        ["skill", "status", "--force"],
        ["skill", "uninstall", "--force"],
    ],
)
def test_cli_invalid_usage_exits_two(
    arguments: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        _cli.main(arguments)

    assert exc.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_cli_status_reports_read_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    def fail_status(*args: object, **kwargs: object) -> None:
        raise PermissionError("cannot read installed skill")

    monkeypatch.setattr(_cli, "skill_status", fail_status)

    assert _cli.main(["skill", "status", "--scope", "project"]) == 1
    output = capsys.readouterr()
    assert "error:" in output.err
    assert "cannot read installed skill" in output.err


def test_cli_status_rejects_invalid_manifest_without_changing_files(
    tmp_path: Path,
    packaged_skill: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    destination = _installed_skill(packaged_skill, tmp_path)
    (destination / _cli._MANIFEST).write_text("not JSON", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    before = _snapshot(tmp_path)

    assert _cli.main(["skill", "status", "--scope", "project"]) == 1

    assert "manifest" in capsys.readouterr().err.lower()
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("target", ["agent", "skill", "manifest", "file"])
def test_cli_status_rejects_symlinks_without_changes(
    tmp_path: Path,
    packaged_skill: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    target: str,
) -> None:
    destination = _installed_skill(packaged_skill, tmp_path)
    paths = {
        "agent": tmp_path / ".agents",
        "skill": destination,
        "manifest": destination / _cli._MANIFEST,
        "file": destination / "SKILL.md",
    }
    path = paths[target]
    outside = tmp_path / "outside"
    path.rename(outside)
    path.symlink_to(outside, target_is_directory=outside.is_dir())
    monkeypatch.chdir(tmp_path)
    before = _snapshot(tmp_path)

    assert _cli.main(["skill", "status", "--scope", "project"]) == 1

    assert "symlink" in capsys.readouterr().err.lower()
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("scope", ["user", "project"])
@pytest.mark.parametrize("agent", ["all", "codex", "claude"])
def test_cli_uninstall_targets_requested_scope_and_agents(
    tmp_path: Path,
    packaged_skill: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    scope: str,
    agent: str,
) -> None:
    user = tmp_path / "user"
    project = tmp_path / "project"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: user))
    for base in (user, project):
        for installed_agent in ("codex", "claude"):
            _installed_skill(packaged_skill, base, installed_agent)
    monkeypatch.chdir(project)

    assert _cli.main(["skill", "uninstall", "--agent", agent, "--scope", scope]) == 0

    selected_base = user if scope == "user" else project
    selected_agents = ("codex", "claude") if agent == "all" else (agent,)
    output = capsys.readouterr()
    assert output.err == ""
    for base in (user, project):
        for installed_agent in ("codex", "claude"):
            destination = _destination(base, installed_agent)
            selected = base == selected_base and installed_agent in selected_agents
            assert destination.exists() is not selected
            if selected:
                assert installed_agent in output.out
                assert str(destination.resolve()) in output.out


def test_cli_uninstall_missing_is_idempotent_and_defaults_to_user(
    tmp_path: Path,
    packaged_skill: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    user = tmp_path / "user"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: user))
    before = _snapshot(tmp_path)

    assert _cli.main(["skill", "uninstall"]) == 0
    assert _cli.main(["skill", "uninstall"]) == 0

    output = capsys.readouterr()
    assert output.err == ""
    for agent in ("codex", "claude"):
        assert agent in output.out
        assert str(_destination(user, agent).resolve()) in output.out
    assert _snapshot(tmp_path) == before


def test_cli_uninstall_reports_retained_local_files(
    tmp_path: Path,
    packaged_skill: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    destination = _installed_skill(packaged_skill, tmp_path)
    skill = destination / "SKILL.md"
    skill.write_text("local edits", encoding="utf-8")
    notes = destination / "notes.txt"
    notes.write_text("my notes", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert _cli.main(["skill", "uninstall", "--scope", "project"]) == 0

    output = capsys.readouterr()
    assert output.err == ""
    assert "retain" in output.out.lower()
    assert str(destination.resolve()) in output.out
    assert skill.read_text(encoding="utf-8") == "local edits"
    assert notes.read_text(encoding="utf-8") == "my notes"
    assert not (destination / "references" / "guide.md").exists()
    assert not (destination / _cli._MANIFEST).exists()


def test_cli_uninstall_refuses_unmanaged_skill_without_changes(
    tmp_path: Path,
    packaged_skill: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    destination = _installed_skill(packaged_skill, tmp_path)
    (destination / _cli._MANIFEST).unlink()
    monkeypatch.chdir(tmp_path)
    before = _snapshot(tmp_path)

    assert _cli.main(["skill", "uninstall", "--scope", "project"]) == 1

    assert "manifest" in capsys.readouterr().err.lower()
    assert _snapshot(tmp_path) == before
