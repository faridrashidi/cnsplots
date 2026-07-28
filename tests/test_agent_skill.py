from __future__ import annotations

from pathlib import Path

import pytest

from cnsplots import _cli


def test_install_skill_copies_packaged_files_for_all_agents(tmp_path: Path) -> None:
    destinations = _cli.install_skill(
        "all",
        force=False,
        base_dir=tmp_path,
    )

    expected = (
        ("codex", tmp_path / ".agents" / "skills" / "cnsplots"),
        ("claude", tmp_path / ".claude" / "skills" / "cnsplots"),
    )
    assert destinations == expected

    for _, destination in destinations:
        skill = (destination / "SKILL.md").read_text(encoding="utf-8")
        assert skill.startswith("---\nname: cnsplots\n")
        assert "publication-ready scientific plots" in skill
        assert (destination / "agents" / "openai.yaml").is_file()
        assert (destination / "references" / "plot-catalog.md").is_file()


def test_install_skill_selects_one_project_agent(tmp_path: Path) -> None:
    destinations = _cli.install_skill(
        "claude",
        force=False,
        base_dir=tmp_path,
    )

    assert destinations == (("claude", tmp_path / ".claude" / "skills" / "cnsplots"),)
    assert not (tmp_path / ".agents").exists()


def test_install_skill_preflights_conflicts_before_copying(tmp_path: Path) -> None:
    existing = tmp_path / ".agents" / "skills" / "cnsplots"
    existing.mkdir(parents=True)

    with pytest.raises(FileExistsError, match="pass --force to update"):
        _cli.install_skill("all", force=False, base_dir=tmp_path)

    assert not (tmp_path / ".claude").exists()


def test_install_skill_force_updates_existing_files(tmp_path: Path) -> None:
    destination = tmp_path / ".agents" / "skills" / "cnsplots"
    destination.mkdir(parents=True)
    (destination / "SKILL.md").write_text("stale", encoding="utf-8")

    _cli.install_skill("codex", force=True, base_dir=tmp_path)

    assert (
        (destination / "SKILL.md")
        .read_text(encoding="utf-8")
        .startswith("---\nname: cnsplots\n")
    )


def test_cli_installs_and_reports_project_skill(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    result = _cli.main(["skill", "install", "--agent", "codex", "--scope", "project"])

    assert result == 0
    assert (
        f"Installed cnsplots skill for codex: "
        f"{tmp_path / '.agents' / 'skills' / 'cnsplots'}" in capsys.readouterr().out
    )


def test_cli_reports_existing_skill(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    destination = tmp_path / ".claude" / "skills" / "cnsplots"
    destination.mkdir(parents=True)

    result = _cli.main(["skill", "install", "--agent", "claude", "--scope", "project"])

    assert result == 1
    assert "error: refusing to overwrite existing skill" in capsys.readouterr().err
