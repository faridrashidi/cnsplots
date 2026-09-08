from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.name == "nt" or shutil.which("make") is None,
    reason="Makefile tests require make and a POSIX shell",
)


@pytest.fixture
def docs_repo(tmp_path: Path) -> Path:
    shutil.copyfile(
        Path(__file__).resolve().parents[1] / "Makefile", tmp_path / "Makefile"
    )
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "Makefile").write_text(
        ".PHONY: html clean\n"
        "clean:\n"
        "\trm -rf build\n"
        "html:\n"
        "\tmkdir -p build/html\n"
        "\tprintf 'built documentation\\n' > build/html/index.html\n",
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("uv", "python"):
        command = bin_dir / name
        command.write_text(
            "#!/bin/sh\n"
            'printf "%s\\n" "$@" > "$CNSPLOTS_TEST_ROOT/preview-args"\n'
            'test -f "$CNSPLOTS_TEST_ROOT/docs/build/html/index.html"\n',
            encoding="utf-8",
        )
        command.chmod(0o755)
    return tmp_path


def _run_make(
    repo_root: Path, target: str, ci: str | None = None
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("CI", None)
    if ci is not None:
        env["CI"] = ci
    env["PATH"] = str(repo_root / "bin") + os.pathsep + env.get("PATH", "")
    env["CNSPLOTS_TEST_ROOT"] = str(repo_root)
    return subprocess.run(
        ["make", target],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


@pytest.mark.parametrize("ci", [None, "true"])
def test_doc_build_exits_and_refreshes_only_docs_output(
    docs_repo: Path, ci: str | None
) -> None:
    artifacts = (
        ".coverage",
        ".coverage.previous",
        "coverage.xml",
        "htmlcov/index.html",
        ".pytest_cache/sentinel",
        "tests/__pycache__/sentinel",
        "build/sentinel",
        "dist/sentinel",
    )
    for relative_path in artifacts:
        artifact = docs_repo / relative_path
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("preserve me", encoding="utf-8")
    obsolete_page = docs_repo / "docs/build/html/obsolete.html"
    obsolete_page.parent.mkdir(parents=True)
    obsolete_page.write_text("obsolete documentation", encoding="utf-8")

    result = _run_make(docs_repo, "doc", ci)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (docs_repo / "docs/build/html/index.html").read_text() == (
        "built documentation\n"
    )
    assert not obsolete_page.exists()
    assert not (docs_repo / "preview-args").exists()
    for relative_path in artifacts:
        assert (docs_repo / relative_path).read_text() == "preserve me"


@pytest.mark.parametrize("target", ["doc", "doc-serve"])
def test_docs_build_failure_propagates_without_serving(
    docs_repo: Path, target: str
) -> None:
    (docs_repo / "docs/Makefile").write_text(
        ".PHONY: html clean\n"
        "clean:\n"
        "\trm -rf build\n"
        "html:\n"
        "\tprintf 'documentation build failed\\n' >&2\n"
        "\texit 7\n",
        encoding="utf-8",
    )

    result = _run_make(docs_repo, target)

    assert result.returncode != 0
    assert "documentation build failed" in result.stderr
    assert not (docs_repo / "preview-args").exists()


def test_doc_serve_starts_preview_after_build(docs_repo: Path) -> None:
    result = _run_make(docs_repo, "doc-serve")

    assert result.returncode == 0, result.stdout + result.stderr
    args = (docs_repo / "preview-args").read_text().splitlines()
    assert args[args.index("python") :] == [
        "python",
        "-m",
        "http.server",
        "8080",
        "--directory",
        "docs/build/html",
    ]
