"""Guard the release gate's SHA, failure, and artifact handoff contracts."""

from pathlib import Path
import shlex

import yaml


WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
VALIDATION = "./.github/workflows/validate-package.yml"


def _workflow(name):
    # BaseLoader preserves GitHub's `on` key instead of treating it as YAML 1.1 True.
    return yaml.load((WORKFLOWS / name).read_text(), Loader=yaml.BaseLoader)


def _action_steps(job, action):
    return [
        step for step in job["steps"] if step.get("uses", "").split("@")[0] == action
    ]


def test_release_requires_shared_validation_before_publication():
    release = _workflow("release-publish.yml")["jobs"]
    ci = _workflow("ci-tests.yml")["jobs"]

    assert release["validation"]["uses"] == ci["validation"]["uses"] == VALIDATION
    assert release["publish"]["needs"] == "validation"
    assert release["github-release"]["needs"] == "publish"
    for job_name in ("validation", "publish", "github-release"):
        assert "if" not in release[job_name]
        assert "continue-on-error" not in release[job_name]
    assert release["publish"]["permissions"]["id-token"] == "write"


def test_tag_validation_uses_the_event_sha_without_branch_or_check_lookups():
    release = _workflow("release-publish.yml")
    validation = _workflow("validate-package.yml")

    # Ordinary releases and tags pushed manually both enter through this trigger.
    # No branch name, previous CI run, or caller-provided ref selects the checkout.
    assert release["on"] == {"push": {"tags": ["v*"]}}
    assert validation["on"] == {"workflow_call": ""}
    assert "with" not in release["jobs"]["validation"]
    for job in validation["jobs"].values():
        checkouts = _action_steps(job, "actions/checkout")
        assert len(checkouts) == 1
        assert checkouts[0]["with"]["ref"] == "${{ github.sha }}"


def test_required_validation_cannot_ignore_test_or_package_failures():
    jobs = _workflow("validate-package.yml")["jobs"]
    test_job = jobs["test"]
    package_job = jobs["package"]

    for job in (test_job, package_job):
        assert "if" not in job
        assert "continue-on-error" not in job
        for step in job["steps"]:
            assert "continue-on-error" not in step

    test_steps = [step for step in test_job["steps"] if step.get("run") == "make test"]
    assert len(test_steps) == 1
    assert "if" not in test_steps[0]
    for step in package_job["steps"]:
        assert "if" not in step


def test_publishing_downloads_the_same_distributions_after_wheel_validation():
    package_job = _workflow("validate-package.yml")["jobs"]["package"]
    release = _workflow("release-publish.yml")["jobs"]
    steps = package_job["steps"]
    uploads = _action_steps(package_job, "actions/upload-artifact")

    assert len(uploads) == 1
    upload = uploads[0]
    assert upload["with"]["if-no-files-found"] == "error"
    assert upload["with"]["path"].rstrip("/") == "dist"
    smoke_steps = [
        step for step in steps if "pip install dist/*.whl" in step.get("run", "")
    ]
    assert len(smoke_steps) == 1
    commands = [shlex.split(line) for line in smoke_steps[0]["run"].splitlines()]
    imports = [command for command in commands if "-c" in command]
    assert ["python", "-m", "venv", ".pkg-venv"] in commands
    assert [".", ".pkg-venv/bin/activate"] in commands
    assert imports
    # Isolated Python excludes the source checkout and PYTHONPATH from imports.
    assert all(command[:3] == ["python", "-I", "-c"] for command in imports)
    smoke_index = steps.index(smoke_steps[0])
    assert smoke_index < steps.index(upload)
    assert any("python -m build" in step.get("run", "") for step in steps[:smoke_index])
    assert any(
        "twine check dist/*" in step.get("run", "") for step in steps[:smoke_index]
    )
    # A second build or mutation after the smoke test would publish untested bytes.
    assert steps[smoke_index + 1 :] == [upload]

    for job_name in ("publish", "github-release"):
        downloads = _action_steps(release[job_name], "actions/download-artifact")
        assert len(downloads) == 1
        assert downloads[0]["with"]["name"] == upload["with"]["name"]
        assert downloads[0]["with"]["path"].rstrip("/") == "dist"
        assert "run-id" not in downloads[0]["with"]
        assert "repository" not in downloads[0]["with"]
        assert not any("run" in step for step in release[job_name]["steps"])
