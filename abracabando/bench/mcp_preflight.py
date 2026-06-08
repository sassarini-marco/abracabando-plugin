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
    "mcp_layer_partial",   # MCP returned some but not all expected records
    "skill_layer_bug",
    "stale_ground_truth",  # golden had records but MCP data drifted
    "golden_missing",      # golden was never captured (placeholder) — fixture debt
    "needs_rerun",         # infrastructure issue (cold-start, file-path deferral,
                           # audit unparseable) — neither pass nor fail
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
    """True if the MCP records diverge from the golden.

    The golden is intentionally a small sample (1-2 representative records)
    while MCP returns a full page (up to 10). Divergence means the golden's
    records are no longer a *subset* of what the MCP returns (i.e. previously
    known records have disappeared), or a pinned field value has changed.

    Uses ``record_identity()`` so Consip (url), TED (publication_number), and
    ANAC (cig/cup) records all resolve to the same stable key regardless of
    which field the source uses.
    """
    g = {record_identity(r): r for r in golden if record_identity(r)}
    m = {record_identity(r): r for r in mcp if record_identity(r)}
    # Golden must be a subset — MCP is allowed to return more records than the golden captured.
    if not set(g).issubset(set(m)):
        return True
    # For each shared record, check pinned *stable* field values match.
    # Exclude free-text / annotation fields whose formatting varies across captures
    # (title truncation, appended suffixes, note vs summary, etc.).
    _TEXT_FIELDS = {"title", "note", "summary", "description", "object", "oggetto"}
    for rid, gr in g.items():
        mr = m[rid]
        for k, v in gr.items():
            if k in _TEXT_FIELDS:
                continue
            if k not in mr:
                continue
            mv = mr[k]
            # Normalise list vs scalar: ["72514100","72514100"] == "72514100".
            # Convert both to sorted unique lists so types are always comparable.
            def _norm(x):  # noqa: E306
                if isinstance(x, list):
                    return sorted({str(i) for i in x})
                return [str(x)]
            if _norm(v) != _norm(mv):
                return True
    return False


def _is_no_data_answer(answer: str) -> bool:
    return "Dati non disponibili" in answer


# --------------------------------------------------------------------------- #
# Layer attribution
# --------------------------------------------------------------------------- #

def attribute_layer(
    answer: str,
    mcp_records: list[dict],
    golden_records: list[dict],
    *,
    golden_is_placeholder: bool = False,
    is_aggregating: bool = False,
) -> Layer:
    """Classify a case result against the independent golden oracle.

    ``golden_is_placeholder`` distinguishes fixture debt (golden was never
    captured) from genuine data drift — both are INCONCLUSIVE but for different
    reasons that need different follow-up actions.

    ``is_aggregating`` marks skills that synthesise/aggregate records and
    legitimately do not echo raw record ids in their output (profilo-sa,
    reconciliation-pnrr, etc.). These are scored on correctness, not surfacing.
    """
    golden_ids = _ids(golden_records)
    mcp_ids = _ids(mcp_records)

    if not golden_ids:
        # Oracle says there should be nothing (empty golden).
        if mcp_ids:
            # Distinguish: fixture never captured vs genuine content drift.
            return "golden_missing" if golden_is_placeholder else "stale_ground_truth"
        return "skill_ok_no_data" if _is_no_data_answer(answer) else "skill_layer_bug"

    # Oracle has records.
    if not mcp_ids:
        return "mcp_layer_empty"
    if _divergent(golden_records, mcp_records):
        return "mcp_layer_wrong"

    # MCP agrees with the golden.
    # Aggregating skills don't print raw record ids — surfacing check doesn't apply.
    if not is_aggregating:
        missing = [gid for gid in golden_ids if gid not in answer]
        if missing:
            return "skill_layer_bug"
    return "skill_ok"


# --------------------------------------------------------------------------- #
# Probe-backed layer attribution
# --------------------------------------------------------------------------- #

# Probe statuses that indicate infrastructure noise rather than a semantic failure.
_INFRA_PROBE_STATUSES = frozenset(
    {"cold_start", "file_path_deferred", "audit_unparseable", "audit_drift", "needs_rerun"}
)


def attribute_layer_from_probe(
    answer: str,
    mcp_records: list[dict],
    golden_records: list[dict],
    probe_results: dict[str, dict],
    *,
    golden_is_placeholder: bool = False,
    is_aggregating: bool = False,
) -> Layer:
    """Like ``attribute_layer`` but uses pre-computed ``mcp_probe_result`` dicts.

    ``probe_results`` maps tool name → ``mcp_probe_result`` as written by
    ``mcp_probe.run_probes()``.  This replaces the heuristic ``_divergent()``
    reconstruction with the grounded cross-tool consistency signal from the
    ANAC probe row.

    Infrastructure statuses (cold-start, file-path deferral, etc.) from the
    probe map to ``'needs_rerun'`` — neither a pass nor a failure.

    Falls back to ``attribute_layer()`` when no probe result covers the
    tools used in this case.
    """
    # Collect the probe status and divergent flag for tools used in this case.
    # We look for the ANAC awards probe as the primary consistency signal.
    probe = probe_results.get("anac_search_awards") or {}
    probe_status = probe.get("status", "ok")

    if probe_status in _INFRA_PROBE_STATUSES:
        return "needs_rerun"

    golden_ids = _ids(golden_records)
    mcp_ids = _ids(mcp_records)

    if not golden_ids:
        if mcp_ids:
            return "golden_missing" if golden_is_placeholder else "stale_ground_truth"
        return "skill_ok_no_data" if _is_no_data_answer(answer) else "skill_layer_bug"

    if not mcp_ids:
        return "mcp_layer_empty"

    # Use the grounded divergent signal from the probe instead of _divergent().
    if probe.get("divergent"):
        return "mcp_layer_wrong"

    # Partial overlap: MCP returned some but not all golden records.
    missing_from_mcp = golden_ids - mcp_ids
    if missing_from_mcp:
        return "mcp_layer_partial"

    # MCP agrees with golden — aggregating skills don't surface raw ids.
    if not is_aggregating:
        missing_from_answer = [gid for gid in golden_ids if gid not in answer]
        if missing_from_answer:
            return "skill_layer_bug"
    return "skill_ok"


# --------------------------------------------------------------------------- #
# Live MCP preflight
# --------------------------------------------------------------------------- #

def _http_call_tool(tool: str, params: dict, url: str) -> object:
    """Invoke a single MCP tool over streamable-http.

    Handles the Mcp-Session-Id header that FastMCP streamable-http requires:
    the initialize response carries the session ID which must be echoed back
    in all subsequent requests.
    """
    import urllib.request as _urlreq

    session_id: list[str] = []  # mutable container for closure

    def _post(body: dict) -> dict:
        data = json.dumps(body).encode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if session_id:
            headers["Mcp-Session-Id"] = session_id[0]
        req = _urlreq.Request(url, data=data, headers=headers)
        with _urlreq.urlopen(req, timeout=30) as resp:
            sid = resp.headers.get("Mcp-Session-Id")
            if sid and not session_id:
                session_id.append(sid)
            raw = resp.read()
            ct = resp.headers.get("Content-Type", "")
            if "event-stream" in ct:
                for line in raw.decode().splitlines():
                    if line.startswith("data:"):
                        return json.loads(line[5:].strip())
                raise MCPEmptyError(f"empty SSE response from {url}")
            return json.loads(raw)

    _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                      "clientInfo": {"name": "preflight", "version": "0"}}})
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"})
    resp = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                  "params": {"name": tool, "arguments": params}})
    return resp.get("result", resp)


def _default_call_tool(tool: str, params: dict, mcp_config: Path) -> object:
    """Invoke a single MCP tool using the server declared in ``mcp_config``.

    Supports both stdio (local) and streamable-http (hosted) server types.
    """
    cfg = json.loads(Path(mcp_config).read_text())
    server = next(iter(cfg["mcpServers"].values()))
    server_type = server.get("type", "stdio")

    if server_type == "streamable-http":
        return _http_call_tool(tool, params, server["url"])

    # stdio path
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
        cfg = mcp_config or (BENCH / "config" / "mcp_live.json")
        def call_tool(t: str, p: dict) -> object:  # noqa: E306
            return _default_call_tool(t, p, cfg)

    payload = call_tool(tool, params)
    records = extract_records(payload)
    if not records:
        raise MCPEmptyError(f"MCP tool {tool!r} returned an empty payload for params {params!r}")
    return PreflightResult(tool=tool, params=params, record_count=len(records), raw=payload)


__all__ = [
    "Layer",
    "MCPEmptyError",
    "PreflightResult",
    "assert_mcp_nonempty",
    "attribute_layer",
    "attribute_layer_from_probe",
    "extract_records",
    "record_identity",
]
