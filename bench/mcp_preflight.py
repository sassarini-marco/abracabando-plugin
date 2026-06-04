#!/usr/bin/env python3
"""MCP non-empty preflight + golden-aware layer attribution.

Two jobs:

1. ``assert_mcp_nonempty`` — before a live run is trusted, prove the MCP server
   actually returns data for a case. An empty payload masquerading as a pass is
   exactly the ``3.1-001`` bug this harness exists to kill.

2. ``attribute_layer`` — given the skill answer, the records the MCP returned,
   and the independent frozen golden (the oracle, see
   ``bench/ground-truth/generate_ground_truth.py``), decide WHICH layer a
   failure belongs to so MCP-data defects are routed to ``../industrial-data-mcp``
   instead of being mistaken for skill bugs.
"""
from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

BENCH = Path(__file__).resolve().parent

Layer = Literal[
    "skill_ok",
    "skill_ok_no_data",
    "mcp_layer_empty",
    "mcp_layer_wrong",
    "skill_layer_bug",
    "stale_ground_truth",
]


class MCPEmptyError(RuntimeError):
    """Raised when the live MCP returns an empty payload for a case that should
    have records (per the golden)."""


@dataclass
class PreflightResult:
    tool: str
    params: dict
    record_count: int
    raw: object


# --------------------------------------------------------------------------- #
# Record extraction / comparison helpers
# --------------------------------------------------------------------------- #

def extract_records(payload: object) -> list[dict]:
    """Best-effort normalisation of an MCP tool result into a list of records.

    Handles: a bare list, a dict wrapping ``items``/``results``/``records``/
    ``data``, and the MCP ``{"content": [{"type": "text", "text": "<json>"}]}``
    envelope (text is parsed as JSON when possible).
    """
    if payload is None:
        return []
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for key in ("items", "results", "records", "data", "notices", "awards"):
            val = payload.get(key)
            if isinstance(val, list):
                return [r for r in val if isinstance(r, dict)]
        content = payload.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    try:
                        return extract_records(json.loads(block.get("text", "")))
                    except (ValueError, TypeError):
                        continue
    return []


# Per-source identity keys, in priority order. consip records carry no id at
# all (just title/url/status), so `url` is the stable surrogate.
IDENTITY_KEYS = (
    "record_id", "publication_number", "cig", "cup",
    "codice_identificativo", "id", "url",
)


def record_identity(record: dict) -> str | None:
    """The stable identity of a single MCP/golden record, source-agnostic."""
    for key in IDENTITY_KEYS:
        val = record.get(key)
        if val:
            return str(val)
    return None


def _ids(records: list[dict]) -> set[str]:
    return {rid for r in records if (rid := record_identity(r))}


def _divergent(golden: list[dict], mcp: list[dict]) -> bool:
    """True if the MCP records diverge from the golden — different id sets, or
    the same ids but a differing value on a field the golden pins."""
    g = {str(r.get("record_id")): r for r in golden if r.get("record_id")}
    m = {str(r.get("record_id")): r for r in mcp if r.get("record_id")}
    if set(g) != set(m):
        return True
    for rid, gr in g.items():
        mr = m[rid]
        for k, v in gr.items():
            if k in mr and mr[k] != v:
                return True
    return False


def _is_no_data_answer(answer: str) -> bool:
    return "Dati non disponibili" in answer


# --------------------------------------------------------------------------- #
# Layer attribution
# --------------------------------------------------------------------------- #

def attribute_layer(answer: str, mcp_records: list[dict], golden_records: list[dict]) -> Layer:
    """Classify a case result against the independent golden oracle."""
    golden_ids = _ids(golden_records)
    mcp_ids = _ids(mcp_records)

    if not golden_ids:
        # Oracle says there should be nothing.
        if mcp_ids:
            return "stale_ground_truth"
        return "skill_ok_no_data" if _is_no_data_answer(answer) else "skill_layer_bug"

    # Oracle has records.
    if not mcp_ids:
        return "mcp_layer_empty"
    if _divergent(golden_records, mcp_records):
        return "mcp_layer_wrong"

    # MCP agrees with the golden — did the skill surface every record?
    missing = [gid for gid in golden_ids if gid not in answer]
    if missing:
        return "skill_layer_bug"
    return "skill_ok"


# --------------------------------------------------------------------------- #
# Live MCP preflight
# --------------------------------------------------------------------------- #

def _default_call_tool(tool: str, params: dict, mcp_config: Path) -> object:
    """Invoke a single MCP tool over stdio using the server in ``mcp_config``.

    Minimal JSON-RPC 2.0 stdio client: initialize, notify initialized,
    tools/call, read the matching response. Used only on the live tier.
    """
    cfg = json.loads(Path(mcp_config).read_text())
    server = next(iter(cfg["mcpServers"].values()))
    cmd = [server["command"], *server.get("args", [])]
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
    )

    def send(obj: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    def recv_id(want_id: int) -> dict:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg.get("id") == want_id:
                return msg
        raise MCPEmptyError(f"no response for id={want_id} from {tool}")

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                         "clientInfo": {"name": "preflight", "version": "0"}}})
        recv_id(1)
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
              "params": {"name": tool, "arguments": params}})
        resp = recv_id(2)
    finally:
        proc.terminate()
    return resp.get("result", resp)


def assert_mcp_nonempty(
    tool: str,
    params: dict,
    *,
    call_tool: Callable[[str, dict], object] | None = None,
    mcp_config: Path | None = None,
) -> PreflightResult:
    """Call ``tool`` and raise ``MCPEmptyError`` if it yields no records."""
    if call_tool is None:
        cfg = mcp_config or (BENCH / "mcp.json")
        def call_tool(t: str, p: dict) -> object:  # noqa: E306
            return _default_call_tool(t, p, cfg)

    payload = call_tool(tool, params)
    records = extract_records(payload)
    if not records:
        raise MCPEmptyError(f"MCP tool {tool!r} returned an empty payload for params {params!r}")
    return PreflightResult(tool=tool, params=params, record_count=len(records), raw=payload)


__all__ = [
    "MCPEmptyError",
    "PreflightResult",
    "assert_mcp_nonempty",
    "attribute_layer",
    "extract_records",
    "record_identity",
]
