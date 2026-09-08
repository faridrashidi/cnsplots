from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _report(report_path: Path) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "tools" / "report_coverage.py"
    return subprocess.run(
        [sys.executable, str(script), str(report_path)],
        cwd=report_path.parent,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_report_distinguishes_real_statement_and_branch_coverage(tmp_path: Path):
    sample = tmp_path / "sample.py"
    sample.write_text(
        "def choose(value):\n"
        "    if value:\n"
        "        value += 1\n"
        "    return value\n"
        "choose(True)\n",
        encoding="utf-8",
    )
    data_file = tmp_path / ".coverage.sample"
    report_path = tmp_path / "coverage.json"
    for args in (
        ["run", "--branch", "--source=.", str(sample)],
        ["json", "--fail-under=0", "-o", str(report_path)],
    ):
        subprocess.run(
            [
                sys.executable,
                "-m",
                "coverage",
                args[0],
                f"--rcfile={os.devnull}",
                f"--data-file={data_file}",
                *args[1:],
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )

    assert json.loads(report_path.read_text())["totals"]["percent_covered"] < 100

    result = _report(report_path)

    assert result.returncode == 0, result.stderr
    assert "| Coverage | Covered | Total | Percent | Policy |" in result.stdout
    assert (
        "| Statements | 5 | 5 | 100.00% | 100% required by `make test` |"
        in result.stdout
    )
    assert "| Branches | 1 | 2 | 50.00% | Reporting only |" in result.stdout


@pytest.mark.parametrize("covered,total,percent", [(9, 10, "90.00%"), (0, 0, "n/a")])
def test_report_does_not_apply_a_combined_coverage_gate(
    tmp_path: Path, covered: int, total: int, percent: str
):
    report_path = tmp_path / "coverage.json"
    report_path.write_text(
        json.dumps(
            {
                "meta": {"branch_coverage": True},
                "totals": {
                    "covered_lines": covered,
                    "num_statements": total,
                    "covered_branches": covered,
                    "num_branches": total,
                },
            }
        ),
        encoding="utf-8",
    )

    result = _report(report_path)

    assert result.returncode == 0, result.stderr
    assert f"| Statements | {covered} | {total} | {percent} |" in result.stdout
    assert f"| Branches | {covered} | {total} | {percent} |" in result.stdout


def test_report_rejects_statement_only_data(tmp_path: Path):
    report_path = tmp_path / "coverage.json"
    report_path.write_text(
        json.dumps({"meta": {"branch_coverage": False}}), encoding="utf-8"
    )

    result = _report(report_path)

    assert result.returncode != 0
    assert "Expected a branch coverage report" in result.stderr
