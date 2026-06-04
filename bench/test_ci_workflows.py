"""Content assertions for the CI workflow.

Checks WHAT the workflow does (installs deps, runs the right commands, no
secret leakage), not merely that the YAML parses.
"""
from __future__ import annotations

import pathlib

import yaml

WF = pathlib.Path(__file__).resolve().parent.parent / ".github" / "workflows"
STATIC = WF / "eval-static.yml"


def _load(path: pathlib.Path) -> tuple[dict, str]:
    text = path.read_text()
    return yaml.safe_load(text), text


def test_static_workflow_installs_deps_and_runs_pytest_without_secrets():
    data, text = _load(STATIC)
    assert data is not None
    assert (True in data) or ("on" in data)
    assert "pull_request" in text
    assert "pip install -r requirements-dev.txt" in text
    assert "pytest" in text
    assert "secrets." not in text, "static tier must not reference any secret"


def test_static_workflow_is_valid_yaml():
    data, _ = _load(STATIC)
    assert isinstance(data, dict)
    assert "jobs" in data
