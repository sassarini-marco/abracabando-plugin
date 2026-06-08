"""Headless-invocation smoke test.

Proves that ``claude -p "/pin-radar ..."`` loads SKILL.md in headless mode and
emits skill-shaped output, replaying a recorded frozen fixture via
``bench/config/mcp_replay.json`` (so no live MCP / 280MB download is needed).

Skipped unless both the ``claude`` binary is on PATH AND an API key is present
(the no-secret static CI tier must skip this cleanly; it runs in the secret-gated
model tier). If ``/skill-name`` ever stops loading skills in headless mode on a
future toolchain, this test fails and REFRESH_PROCEDURE.md §8 documents the
``--append-system-prompt-file skills/<name>/SKILL.md`` fallback.
"""
from __future__ import annotations

import os
import pathlib
import shutil
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import eval_runner  # noqa: E402
from output_rules import (  # noqa: E402
    check_audit_trail_block,
    check_first_line_dataletti,
    check_italian_only,
)

PLUGIN = pathlib.Path(__file__).resolve().parent.parent.parent

pytestmark = pytest.mark.skipif(
    shutil.which("claude") is None or not os.environ.get("ANTHROPIC_API_KEY"),
    reason="needs the claude binary on PATH and ANTHROPIC_API_KEY (secret-gated tier)",
)


def test_headless_pin_radar_emits_skill_shaped_output():
    case = {
        "id": "3.1-001",
        "prompt": "/pin-radar Trova PIN TED attivi per servizi informatici "
                  "(CPV 72000000), probabili gare entro 6 mesi, Italia.",
    }
    os.environ["MCP_REPLAY_CASE"] = "3.1-001"
    answer = eval_runner.run_case(
        case, PLUGIN, PLUGIN / "bench" / "config" / "mcp_replay.json", timeout=300
    )

    assert answer.strip(), "headless run produced no result text"
    assert check_first_line_dataletti(answer).passed, answer[:200]
    assert check_audit_trail_block(answer).passed, "missing '## Audit trail' fenced block"
    assert check_italian_only(answer).passed, "output is not Italian"
