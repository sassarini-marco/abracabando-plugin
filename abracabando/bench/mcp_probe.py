#!/usr/bin/env python3
"""MCP tool probe — Layer 0 of the eval architecture.

Executes tool contracts from ``tool_contracts.py`` against the live MCP server
and emits one ``mcp_probe_result`` JSON per contract row.  Results are consumed
by ``mcp_preflight.attribute_layer_from_probe`` to replace heuristic
``mcp_layer_wrong`` reconstruction with a grounded cross-tool consistency check.

Caveats handled
---------------
Cold start (280 MB ANAC/TED download):
  One warm-up gate with a 600 s budget; a warm-up timeout sets
  ``status=cold_start`` and routes to ``needs-rerun`` — never a false failure.

ted_pin_italy file-path returns:
  When the tool returns a filesystem path instead of JSON, the file is opened
  and parsed as NDJSON; ``status=file_path_deferred``, never ``empty``.

Free-tier budget:
  The ``smoke`` tier uses ≤8 calls and fits within the 10-call/session limit.
  Run ``--tier full --pro`` for the remaining tools on an unmetered config.

link_only tools (programmazione_*, env_*):
  These do no HTTP.  Their response is accepted as long as no hard error is
  raised; record counts are never asserted.

mcp_probe_result schema
-----------------------
{
  "tool": str,
  "declared_args": dict,
  "runtime_args": dict,          # same as declared_args for direct probe calls
  "return_kind": str,            # json_records | file_path | link_only
  "status": str,                 # ok | cold_start | file_path_deferred |
                                 # empty | error | needs_rerun
  "record_count": int,
  "null_rate_by_field": dict,    # field -> fraction null (drift signal)
  "snapshot_date": str | None,   # from server_capabilities
  "divergent": bool,             # True if cross-tool consistency check fails
  "first_record": dict | None,   # for required-fields check
}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from mcp_preflight import (  # noqa: E402
    MCPEmptyError,
    _default_call_tool,
    extract_records,
)
from tool_contracts import CONTRACTS  # noqa: E402

DEFAULT_MCP_CONFIG = BENCH / "config" / "mcp_live.json"
PROBE_RESULTS_DIR = BENCH / "probe_results"

NEEDS_RERUN_STATUSES = frozenset({"cold_start", "file_path_deferred", "needs_rerun"})


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #

def _call(tool: str, args: dict, mcp_config: Path) -> Any:
    return _default_call_tool(tool, args, mcp_config)


def _is_file_path_payload(payload: Any) -> str | None:
    """Return the file path when the payload is a path-only response, else None."""
    if isinstance(payload, str):
        stripped = payload.strip()
        if re.match(r"^/[^\s]+\.(jsonl|ndjson|json|tmp)$", stripped):
            return stripped
    if isinstance(payload, dict):
        content = payload.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = (block.get("text") or "").strip()
                    if re.match(r"^/[^\s]+\.(jsonl|ndjson|json|tmp)$", text):
                        return text
    return None


def _parse_ndjson_file(path: str) -> list[dict]:
    """Read a NDJSON/JSON file returned by ted_pin_italy."""
    p = Path(path)
    if not p.exists():
        return []
    text = p.read_text(errors="replace")
    records: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                records.append(obj)
            elif isinstance(obj, list):
                records.extend(r for r in obj if isinstance(r, dict))
        except ValueError:
            continue
    return records


def _null_rate(records: list[dict], fields: list[str]) -> dict[str, float]:
    if not records or not fields:
        return {}
    return {
        f: sum(1 for r in records if not r.get(f)) / len(records)
        for f in fields
    }


# --------------------------------------------------------------------------- #
# Warm-up gate
# --------------------------------------------------------------------------- #

def warm_up(mcp_config: Path, budget_seconds: int = 600) -> str:
    """Run a warm-up gate to absorb the cold-start download.

    Returns one of: ``'ok'``, ``'cold_start'``, ``'error'``.
    """
    t0 = time.time()
    try:
        _call("server_capabilities", {}, mcp_config)
        elapsed = time.time() - t0
        if elapsed > budget_seconds:
            return "cold_start"
        # Trivial ANAC call to trigger any remaining index build.
        try:
            _call("anac_search_awards", {"q": "prova", "rows": 1}, mcp_config)
        except MCPEmptyError:
            pass  # empty result is fine — the server responded
        return "ok"
    except Exception:
        elapsed = time.time() - t0
        return "cold_start" if elapsed >= budget_seconds else "error"


# --------------------------------------------------------------------------- #
# Per-tool probe
# --------------------------------------------------------------------------- #

def probe_tool(contract: dict, mcp_config: Path) -> dict:
    """Execute one contract row and return an ``mcp_probe_result`` dict."""
    tool = contract["tool"]
    declared_args = contract["declared_args"]
    return_kind = contract["return_kind"]
    required_fields = contract.get("required_fields", [])
    min_records = contract.get("min_records", 1)

    result: dict = {
        "tool": tool,
        "declared_args": declared_args,
        "runtime_args": declared_args,
        "return_kind": return_kind,
        "status": "ok",
        "record_count": 0,
        "null_rate_by_field": {},
        "snapshot_date": None,
        "divergent": False,
        "first_record": None,
    }

    # link_only: accept any non-exception response; never assert record count.
    if return_kind == "link_only":
        try:
            _call(tool, declared_args, mcp_config)
        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)
        return result

    try:
        payload = _call(tool, declared_args, mcp_config)
    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        return result

    # File-path response (e.g. ted_pin_italy large result sets).
    file_path = _is_file_path_payload(payload)
    if file_path:
        records = _parse_ndjson_file(file_path)
        result["status"] = "file_path_deferred"
        result["record_count"] = len(records)
        if records:
            result["first_record"] = records[0]
        result["null_rate_by_field"] = _null_rate(records, required_fields)
        return result

    records = extract_records(payload)
    result["record_count"] = len(records)

    if len(records) < min_records:
        result["status"] = "empty"
        return result

    if records:
        result["first_record"] = records[0]

    # Required-field key check (null values are drift signals, not hard failures).
    if records and required_fields:
        missing = [f for f in required_fields if f not in records[0]]
        if missing:
            result["status"] = "error"
            result["error"] = f"required_fields missing from first record: {missing}"
            return result

    result["null_rate_by_field"] = _null_rate(records, required_fields)
    return result


# --------------------------------------------------------------------------- #
# Cross-tool consistency check
# --------------------------------------------------------------------------- #

def check_cross_tool_consistency(mcp_config: Path) -> tuple[bool, str]:
    """Verify that ``anac_award_detail`` agrees with ``anac_search_awards``.

    Returns ``(divergent: bool, reason: str)``.  ``divergent=True`` means the
    tool layer has an internal data inconsistency — a strong signal that a
    fix belongs in ``../industrial-data-mcp``.
    """
    try:
        search_payload = _call(
            "anac_search_awards", {"q": "software", "rows": 3}, mcp_config
        )
        search_records = extract_records(search_payload)
    except Exception as exc:
        return False, f"search_awards call failed: {exc}"

    if not search_records:
        return False, "no search records to compare"

    first = search_records[0]
    cig = first.get("cig")
    if not cig:
        return False, "no cig field in search result"

    try:
        detail_payload = _call("anac_award_detail", {"cig": cig}, mcp_config)
        detail_records = extract_records(detail_payload)
        detail = detail_records[0] if detail_records else (
            detail_payload if isinstance(detail_payload, dict) else {}
        )
    except Exception as exc:
        return False, f"award_detail call failed: {exc}"

    for field in ("importo", "stazione_appaltante", "sa"):
        sv = first.get(field)
        dv = detail.get(field)
        if sv is not None and dv is not None and str(sv).strip() != str(dv).strip():
            return True, f"field {field!r} diverges: search={sv!r} != detail={dv!r}"

    return False, "consistent"


# --------------------------------------------------------------------------- #
# Snapshot date
# --------------------------------------------------------------------------- #

def _read_snapshot_date(mcp_config: Path) -> str | None:
    try:
        payload = _call("server_capabilities", {}, mcp_config)
        if isinstance(payload, dict):
            return payload.get("snapshot_date")
        recs = extract_records(payload)
        return recs[0].get("snapshot_date") if recs else None
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Main probe runner
# --------------------------------------------------------------------------- #

def run_probes(
    mcp_config: Path,
    tier: str = "smoke",
    output_dir: Path | None = None,
    include_consistency: bool = True,
) -> list[dict]:
    """Execute all contracts at ``tier`` and return probe results.

    Each result is written to ``output_dir/<tool>.json`` when ``output_dir`` is
    provided.  The results are also returned for programmatic use.
    """
    contracts = [c for c in CONTRACTS if c["tier"] == tier]
    snapshot_date = _read_snapshot_date(mcp_config)
    results: list[dict] = []

    for contract in contracts:
        tool = contract["tool"]
        print(f"  [{tool}] probing...", end=" ", flush=True)
        result = probe_tool(contract, mcp_config)
        result["snapshot_date"] = snapshot_date
        status = result["status"]
        flag = " [NEEDS-RERUN]" if status in NEEDS_RERUN_STATUSES else ""
        print(f"status={status} records={result['record_count']}{flag}")
        results.append(result)

    if include_consistency:
        print("  [consistency] checking anac cross-tool...", end=" ", flush=True)
        divergent, reason = check_cross_tool_consistency(mcp_config)
        print(f"divergent={divergent} ({reason})")
        # Attach the consistency signal to the anac_search_awards row.
        for r in results:
            if r["tool"] == "anac_search_awards":
                r["divergent"] = divergent
                r["consistency_reason"] = reason

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        for result in results:
            name = result["tool"].replace("_", "-") + ".json"
            (output_dir / name).write_text(
                json.dumps(result, ensure_ascii=False, indent=2)
            )

    return results


def load_probe_results(probe_dir: Path | None = None) -> dict[str, dict]:
    """Load all ``mcp_probe_result`` JSON files from ``probe_dir``.

    Returns a dict mapping tool name → probe result.  Returns empty dict when
    the directory does not exist (probe has not been run yet).
    """
    d = probe_dir or PROBE_RESULTS_DIR
    if not d.exists():
        return {}
    results = {}
    for f in d.glob("*.json"):
        try:
            obj = json.loads(f.read_text())
            tool = obj.get("tool") or f.stem.replace("-", "_")
            results[tool] = obj
        except Exception:
            continue
    return results


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    ap = argparse.ArgumentParser(
        description="MCP tool probe — Layer 0 of the eval architecture."
    )
    ap.add_argument(
        "--tier", choices=["smoke", "full"], default="smoke",
        help="Contract tier (smoke=≤8 calls fits free budget; full=all tools).",
    )
    ap.add_argument(
        "--pro", action="store_true",
        help="Indicate this run uses an unmetered/pro config (informational only).",
    )
    ap.add_argument(
        "--mcp-config", dest="mcp_config", type=Path, default=None,
        help="Path to MCP config JSON (default: bench/config/mcp_live.json).",
    )
    ap.add_argument(
        "--output-dir", dest="output_dir", type=Path, default=None,
        help="Directory for per-tool JSON results (default: bench/probe_results/).",
    )
    ap.add_argument(
        "--warm-up", dest="warm_up", action="store_true",
        help="Run warm-up gate before probes (absorbs cold-start download).",
    )
    args = ap.parse_args()

    mcp_config = args.mcp_config or DEFAULT_MCP_CONFIG
    output_dir = args.output_dir or PROBE_RESULTS_DIR

    if not mcp_config.exists():
        print(f"ERROR: MCP config not found: {mcp_config}", file=sys.stderr)
        sys.exit(1)

    if args.warm_up:
        print("Running warm-up gate (may take up to 10 min on cold start)...")
        status = warm_up(mcp_config)
        print(f"Warm-up: {status}")
        if status == "cold_start":
            print("Server is still cold-starting. Re-run once data download completes.")
            sys.exit(2)
        if status == "error":
            print("ERROR: MCP server did not respond during warm-up.")
            sys.exit(1)

    print(f"Running {args.tier} tier probes against {mcp_config}...\n")
    results = run_probes(mcp_config, tier=args.tier, output_dir=output_dir)

    ok = sum(1 for r in results if r["status"] == "ok")
    deferred = sum(1 for r in results if r["status"] == "file_path_deferred")
    empty = sum(1 for r in results if r["status"] == "empty")
    errors = sum(1 for r in results if r["status"] == "error")
    needs_rerun = sum(1 for r in results if r["status"] in NEEDS_RERUN_STATUSES)

    print(
        f"\nSummary: {ok} ok, {deferred} file_path_deferred, "
        f"{empty} empty, {errors} errors, {needs_rerun} needs-rerun"
    )
    if output_dir:
        print(f"Results written to {output_dir}/")

    if errors or empty:
        sys.exit(1)


if __name__ == "__main__":
    main()
