#!/usr/bin/env python3
"""Layer 0 pytest: MCP tool smoke tests.

Parametrized over ``tier == smoke`` rows in ``tool_contracts.py``.  Requires a
live MCP endpoint (``bench/config/mcp_live.json``); tagged ``live`` so the fast
per-PR offline CI job can skip them:

    pytest bench/tests/test_tool_contracts.py -q              # all smoke, live
    pytest bench/tests/test_tool_contracts.py -m "not live"   # skip instantly

Run nightly and before release, after ``--warm-up`` if the server may be cold:

    python bench/mcp_probe.py --warm-up
    pytest bench/tests/test_tool_contracts.py -q
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pytest

BENCH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BENCH))

from mcp_probe import NEEDS_RERUN_STATUSES, probe_tool  # noqa: E402
from tool_contracts import CONTRACTS  # noqa: E402

MCP_CONFIG = BENCH / "config" / "mcp_live.json"

SMOKE_CONTRACTS = [c for c in CONTRACTS if c["tier"] == "smoke"]


@pytest.fixture(scope="session", autouse=False)
def mcp_config_present():
    if not MCP_CONFIG.exists():
        pytest.skip("bench/config/mcp_live.json not found — live MCP config required for Layer 0")


@pytest.mark.live
@pytest.mark.parametrize("contract", SMOKE_CONTRACTS, ids=lambda c: c["tool"])
def test_tool_contract(contract, mcp_config_present):  # noqa: F811
    """Call the tool with declared_args and assert liveness + field shape."""
    result = probe_tool(contract, MCP_CONFIG)

    # Hard failure: the tool raised an exception.
    assert result["status"] != "error", (
        f"Tool '{contract['tool']}' errored: {result.get('error')}"
    )

    # Transient / infrastructure state: skip so CI is not red on cold-start.
    if result["status"] in NEEDS_RERUN_STATUSES:
        pytest.skip(
            f"Tool '{contract['tool']}' needs rerun: status={result['status']}"
        )

    # link_only: no record-count assertion — just liveness.
    if contract["return_kind"] == "link_only":
        return

    # Record count gate.
    min_records = contract.get("min_records", 1)
    assert result["record_count"] >= min_records, (
        f"Tool '{contract['tool']}' returned {result['record_count']} records "
        f"(expected ≥ {min_records})"
    )

    # Required-field key presence on first record.
    # Null values are drift signals (see null_rate_by_field), not hard failures.
    required = contract.get("required_fields", [])
    if result["record_count"] > 0 and required:
        first = result.get("first_record") or {}
        missing = [f for f in required if f not in first]
        assert not missing, (
            f"Tool '{contract['tool']}' first record missing fields: {missing}"
        )

    # Null-rate warning: non-fatal; logged for visibility.
    for field, rate in result.get("null_rate_by_field", {}).items():
        if rate > 0.5:
            warnings.warn(
                f"Tool '{contract['tool']}': field '{field}' is null in "
                f"{rate:.0%} of records — possible data drift",
                stacklevel=2,
            )
