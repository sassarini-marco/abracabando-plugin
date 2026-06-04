"""Content assertions for the three CI workflows.

These check WHAT the workflows do (install deps, run the right commands, are
guarded/scheduled correctly), not merely that the YAML parses — a syntactically
valid workflow that forgets to install deps or drops the secret guard is exactly
the failure mode we want to catch.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

WF = pathlib.Path(__file__).resolve().parent.parent / ".github" / "workflows"
STATIC = WF / "eval-static.yml"
MODEL = WF / "eval-model.yml"
LIVE = WF / "eval-live.yml"


def _load(path: pathlib.Path) -> tuple[dict, str]:
    text = path.read_text()
    return yaml.safe_load(text), text


def test_static_workflow_installs_deps_and_runs_pytest_without_secrets():
    data, text = _load(STATIC)
    assert data is not None
    # PyYAML parses the bare `on:` key as the boolean True (the "Norway problem").
    assert (True in data) or ("on" in data)
    assert "pull_request" in text
    assert "pip install -r requirements-dev.txt" in text
    assert "pytest" in text
    assert "secrets." not in text, "static tier must not reference any secret"


def test_model_workflow_is_secret_guarded_and_installs_claude():
    data, text = _load(MODEL)
    assert data is not None
    assert "secrets.ANTHROPIC_API_KEY" in text
    assert "npm i -g @anthropic-ai/claude-code" in text
    assert "pip install -r requirements-dev.txt" in text
    assert "eval_runner.py --frozen" in text
    assert "eval_report.py --gate" in text


def test_live_workflow_is_scheduled_and_installs_mcp_server():
    data, text = _load(LIVE)
    assert data is not None
    assert "schedule" in text
    assert "uv tool install industrial-mcp" in text
    assert "actions/cache" in text
    assert "~/.cache/industrial-mcp" in text
    assert "eval_runner.py --live" in text


@pytest.mark.parametrize("path", [STATIC, MODEL, LIVE])
def test_workflows_are_valid_yaml(path):
    data, _ = _load(path)
    assert isinstance(data, dict)
    assert "jobs" in data
